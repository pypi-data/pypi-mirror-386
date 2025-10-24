# ==========================================
# Flood Depth Prediction - Batch Trial Inference
# Compatible with bayesian_opt_tuning.py outputs
# ==========================================

import os
import re
import glob
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tensorflow as tf
import rasterio
import geopandas as gpd

from sklearn.metrics import mean_squared_error, r2_score
from tensorflow.keras.models import load_model
from rasterio.features import rasterize
from tensorflow.keras.layers import Layer, Dense, Conv2D, Multiply, Reshape, Add, Activation
from tensorflow.keras import backend as K
from tensorflow.keras.regularizers import l2

# -----------------------------
# Reproducibility utilities
# -----------------------------
def set_seed(seed_value: int = 42):
    np.random.seed(seed_value)
    tf.random.set_seed(seed_value)

# -----------------------------
# Mixed precision (use float32 for stability with custom layers)
# -----------------------------
try:
    from tensorflow.keras.mixed_precision import set_global_policy
    set_global_policy('float32')
except Exception:
    pass

# -----------------------------
# Helper I/O functions
# -----------------------------
def natural_sort(file_list):
    def alphanum_key(key):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\\d+)', key)]
    return sorted(file_list, key=alphanum_key)

def load_tiff_images(data_dir):
    images, filenames, crs, transform = [], [], None, None
    for filename in natural_sort([f for f in os.listdir(data_dir) if f.endswith(".tif")]):
        filepath = os.path.join(data_dir, filename)
        with rasterio.open(filepath) as src:
            img = src.read(1)
            if crs is None: crs = src.crs
            if transform is None: transform = src.transform
            images.append(img)
        filenames.append(filename)
    if len(images) == 0:
        raise FileNotFoundError(f"No .tif files found in {data_dir}")
    return np.array(images), filenames, crs, transform

def load_single_tiff_image(filepath):
    with rasterio.open(filepath) as src:
        img = src.read(1)
        crs = src.crs
        transform = src.transform
    return img, crs, transform

def load_water_level_data(data_dir):
    water_level_data = []
    filenames = natural_sort([f for f in os.listdir(data_dir) if f.endswith(".csv")])
    if len(filenames) == 0:
        raise FileNotFoundError(f"No .csv files found in {data_dir}")
    for filename in filenames:
        df = pd.read_csv(os.path.join(data_dir, filename))
        col = 'water_level' if 'water_level' in df.columns else df.columns[-1]
        water_level_data.append(df[col].values)
    return np.array(water_level_data), filenames

def normalize_data_with_nan(data, min_val, max_val):
    nan_mask = np.isnan(data)
    norm_data = 0.1 + 0.9 * (data - min_val) / (max_val - min_val)
    norm_data[nan_mask] = 0
    return norm_data

def denormalize_data(norm_data, min_val, max_val):
    return (norm_data - 0.1) / 0.9 * (max_val - min_val) + min_val

def apply_nan_mask(data, mask):
    out = data.copy()
    out[mask] = np.nan
    return out

def save_tiff_image(data, output_path, reference_dataset):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with rasterio.open(reference_dataset) as src:
        out_meta = src.meta.copy()
    out_meta.update({
        "driver": "GTiff",
        "height": data.shape[0],
        "width": data.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": out_meta["crs"],
        "transform": out_meta["transform"],
    })
    with rasterio.open(output_path, "w", **out_meta) as dest:
        dest.write(data.astype(np.float32), 1)

# -----------------------------
# Custom layers / metrics used by the model (must be present to load models)
# -----------------------------
class StandardCBAM(Layer):
    def __init__(self, ratio=8, kernel_size=7, return_attention=False, **kwargs):
        super().__init__(**kwargs)
        self.ratio = ratio
        self.kernel_size = kernel_size
        self.return_attention = return_attention

    def build(self, input_shape):
        total_channels = input_shape[-1]
        self.feature_channels = total_channels - 1
        self.shared_dense_one = Dense(self.feature_channels // self.ratio, activation='relu', kernel_initializer='he_normal', use_bias=True, bias_initializer='zeros')
        self.shared_dense_two = Dense(self.feature_channels, activation='sigmoid', kernel_initializer='glorot_normal', use_bias=True, bias_initializer='zeros')
        self.conv_spatial = Conv2D(filters=1, kernel_size=self.kernel_size, strides=1, padding='same', activation='sigmoid', kernel_initializer='glorot_normal', use_bias=False)
        super().build(input_shape)

    def call(self, inputs, training=None):
        feature = inputs[..., :self.feature_channels]
        mask = inputs[..., self.feature_channels:]
        # channel attention
        avg_pool = tf.reduce_sum(feature * mask, axis=[1, 2]) / (tf.reduce_sum(mask, axis=[1, 2]) + K.epsilon())
        max_pool = tf.reduce_max(feature * mask + (1.0 - mask) * (-1e9), axis=[1, 2])
        avg_pool = self.shared_dense_two(self.shared_dense_one(avg_pool))
        max_pool = self.shared_dense_two(self.shared_dense_one(max_pool))
        ca = Activation('sigmoid')(Add()([avg_pool, max_pool]))
        ca = Reshape((1, 1, self.feature_channels))(ca)
        refined = feature * ca
        # spatial attention
        sa = self.conv_spatial(refined) * mask
        refined = refined * sa
        return (refined, sa) if self.return_attention else refined

    def get_config(self):
        cfg = super().get_config()
        cfg.update({"ratio": self.ratio, "kernel_size": self.kernel_size, "return_attention": self.return_attention})
        return cfg

class CustomAttentionLayer(Layer):
    def __init__(self, emphasis_factor=1.5, top_k_percent=0.2, **kwargs):
        super().__init__(**kwargs)
        self.emphasis_factor = emphasis_factor
        self.top_k_percent = top_k_percent

    def build(self, input_shape):
        self.W = self.add_weight(name='att_weight', shape=(input_shape[-1], 1), initializer='glorot_normal', trainable=True)
        self.b = self.add_weight(shape=(1,), initializer='zeros', trainable=True, name='bias')
        super().build(input_shape)

    def call(self, x):
        e = K.tanh(K.dot(x, self.W) + self.b)
        a = K.softmax(e, axis=1)
        a = K.squeeze(a, axis=-1)
        k_value = tf.maximum(tf.cast(tf.cast(tf.shape(a)[1], tf.float32) * self.top_k_percent, tf.int32), 1)
        top_k_values, top_k_indices = tf.math.top_k(a, k=k_value)
        mask = tf.one_hot(top_k_indices, depth=tf.shape(a)[1])
        mask = tf.reduce_max(mask, axis=1)
        mask = tf.cast(mask, tf.bool)
        emphasized_a = tf.where(mask, a * self.emphasis_factor, a)
        output = x * tf.expand_dims(emphasized_a, axis=-1)
        summed_output = K.sum(output, axis=1)
        return [summed_output, emphasized_a]

    def get_config(self):
        cfg = super().get_config()
        cfg.update({"emphasis_factor": self.emphasis_factor, "top_k_percent": self.top_k_percent})
        return cfg

class ClusterBasedApplication(Layer):
    def __init__(self, num_stations, height, width, **kwargs):
        super().__init__(**kwargs)
        self.num_stations = num_stations
        self.height = height
        self.width = width

    def build(self, input_shape):
        self.dense_project = Dense(self.height * self.width, activation='relu', kernel_initializer='he_normal', kernel_regularizer=l2(1e-5), name='Dense_Project_Context')
        super().build(input_shape)

    def call(self, inputs):
        attention_outputs, cluster_masks_tensor = inputs
        batch_size = tf.shape(attention_outputs)[0]
        reshaped_context = self.dense_project(attention_outputs)
        reshaped_context = tf.reshape(reshaped_context, (batch_size, self.num_stations, self.height, self.width))
        cluster_masks_expanded = tf.expand_dims(cluster_masks_tensor, axis=0)
        cluster_masks_expanded = tf.tile(cluster_masks_expanded, [batch_size, 1, 1, 1])
        cluster_masks_expanded = tf.cast(cluster_masks_expanded, reshaped_context.dtype)
        localized_context = reshaped_context * cluster_masks_expanded
        cluster_indices = tf.argmax(tf.cast(cluster_masks_tensor, tf.int32), axis=0)
        cluster_indices_one_hot = tf.one_hot(cluster_indices, depth=self.num_stations)
        cluster_indices_one_hot = tf.transpose(cluster_indices_one_hot, perm=[2, 0, 1])
        cluster_indices_one_hot = tf.expand_dims(cluster_indices_one_hot, axis=0)
        cluster_indices_one_hot = tf.tile(cluster_indices_one_hot, [batch_size, 1, 1, 1])
        selected_context = tf.reduce_sum(localized_context * cluster_indices_one_hot, axis=1)
        combined_context = tf.expand_dims(selected_context, axis=-1)
        return combined_context

# masked loss + TrueLoss metric (for model loading)
def masked_mse(y_true, y_pred):
    y_true = tf.cast(y_true, tf.float32); y_pred = tf.cast(y_pred, tf.float32)
    mask = tf.cast(tf.math.not_equal(y_true, 0.0), y_true.dtype)
    mse = tf.square(y_true - y_pred)
    return tf.reduce_sum(mse * mask) / (tf.reduce_sum(mask) + 1e-8)

class TrueLoss(tf.keras.metrics.Metric):
    def __init__(self, name='trueloss', **kwargs):
        super().__init__(name=name, **kwargs)
        self.true_loss = self.add_weight(name='tl', initializer='zeros')
        self.count = self.add_weight(name='count', initializer='zeros')
    def update_state(self, y_true, y_pred, sample_weight=None):
        y_true = tf.cast(y_true, tf.float32); y_pred = tf.cast(y_pred, tf.float32)
        mask = tf.cast(tf.math.not_equal(y_true, 0.0), y_true.dtype)
        mse = tf.square(y_true - y_pred)
        masked = tf.reduce_sum(mse * mask) / (tf.reduce_sum(mask) + 1e-8)
        self.true_loss.assign_add(masked); self.count.assign_add(1.0)
    def result(self): return self.true_loss / self.count
    def reset_state(self): self.true_loss.assign(0.0); self.count.assign(0.0)

# -----------------------------
# Core prediction routine
# -----------------------------
def run_predictions(
    # Required testing directories
    test_atm_pressure_dir: str,
    test_wind_speed_dir: str,
    test_precipitation_dir: str,
    test_river_discharge_dir: str,
    test_water_depth_dir: str,
    test_water_level_dir: str,
    # DEM (single file broadcast across timesteps)
    test_dem_file: str,
    # Checkpoints (produced by bayesian_opt_tuning.run_optimization)
    checkpoint_dir_BO: str = "checkpoint_BO",
    # Optional polygon shapefile (fallback if cluster_masks.npy is missing)
    polygon_clusters_path: str = None,
    # General settings
    sequence_length: int = 6,
    output_root: str = "predictions",
    test_name: str = "testharvey",
    seed_value: int = 42,
):
    """
    Run inference for *all trials* saved under `checkpoint_dir_BO/trial_XXX/best_model.keras`.
    Each trial's predictions are written to: {output_root}/{test_name}/trial_XXX/*.tif
    A summary CSV of metrics is also saved per-trial.
    """
    set_seed(seed_value)

    # ---------- Load inputs ----------
    atm, atm_files, crs, transform = load_tiff_images(test_atm_pressure_dir)
    wspd, _, _, _   = load_tiff_images(test_wind_speed_dir)
    prcp, _, _, _   = load_tiff_images(test_precipitation_dir)
    rdis, _, _, _   = load_tiff_images(test_river_discharge_dir)

    dem_img, _, _   = load_single_tiff_image(test_dem_file)
    T = atm.shape[0]
    dem = np.tile(dem_img, (T, 1, 1))

    # Stack: (T,H,W,C)
    X = np.stack((atm, wspd, dem, prcp, rdis), axis=-1)

    # Build sequences (N,Tseq,H,W,C)
    X_seqs = np.array([X[i:i+sequence_length] for i in range(len(X)-sequence_length+1)])

    # Ground-truth depth rasters (for evaluation + metadata for saving predictions)
    Y_all, Y_files, _, _ = load_tiff_images(test_water_depth_dir)
    Y_seqs = Y_all[sequence_length-1:]
    X_seqs = X_seqs[:len(Y_seqs)]  # align

    # Water-level sequences (stations x time)
    WL_all, wl_filenames = load_water_level_data(test_water_level_dir)
    # Use global min/max from artifacts to normalize (loaded below). For now just shape check after load.

    # ---------- Artifacts ----------
    artifacts_dir = os.path.join(checkpoint_dir_BO, "artifacts")
    norm_path = os.path.join(artifacts_dir, "normalization_params.npz")
    if not os.path.exists(norm_path):
        raise FileNotFoundError(f"Expected normalization params at {norm_path}")
    norm = np.load(norm_path, allow_pickle=True)
    X_train_min_vals = norm["X_train_min_vals"]
    X_train_max_vals = norm["X_train_max_vals"]
    y_train_min = float(norm["y_train_min"])
    y_train_max = float(norm["y_train_max"])
    wl_min = float(norm["water_level_global_min"])
    wl_max = float(norm["water_level_global_max"])

    # Normalize inputs using training stats
    norm_channels = []
    for ch in range(X_seqs.shape[-1]):
        norm_channels.append(normalize_data_with_nan(X_seqs[..., ch], X_train_min_vals[ch], X_train_max_vals[ch]))
    X_norm = np.stack(norm_channels, axis=-1)

    # Normalize water-levels globally
    WL_norm = (WL_all - wl_min) / (wl_max - wl_min)
    WL_seq = np.array([WL_norm[:, i:i+sequence_length] for i in range(WL_norm.shape[1]-sequence_length+1)])
    WL_seq = WL_seq.transpose(0,2,1)  # (N, Tseq, num_stations)

    # Align to min length
    N = min(X_norm.shape[0], WL_seq.shape[0], Y_seqs.shape[0])
    X_norm = X_norm[:N]; WL_seq = WL_seq[:N]; Y_seqs = Y_seqs[:N]
    Y_files_aligned = Y_files[sequence_length-1:sequence_length-1+N]
    Y_nan_mask = np.isnan(Y_seqs)

    # ---------- Mask preparation ----------
    cluster_masks_path = os.path.join(artifacts_dir, "cluster_masks.npy")
    cluster_masks = None
    if os.path.exists(cluster_masks_path):
        cluster_masks = np.load(cluster_masks_path)
    elif polygon_clusters_path is not None and os.path.exists(polygon_clusters_path):
        # fallback: rasterize shapefile
        polygons_gdf = gpd.read_file(polygon_clusters_path)
        masks = []
        H, W = atm.shape[1], atm.shape[2]
        for poly in polygons_gdf.geometry:
            mask = rasterize([(poly,1)], out_shape=(H,W), transform=transform, fill=0, dtype='uint8')
            masks.append(mask)
        cluster_masks = np.array(masks)
    else:
        raise FileNotFoundError("No cluster masks found: expected artifacts/cluster_masks.npy or a valid polygon shapefile.")

    # Build the single mask (union of clusters) and tile to (N,Tseq,H,W,1)
    single_mask = np.max(cluster_masks, axis=0)[..., np.newaxis]
    single_mask = np.tile(single_mask[np.newaxis, np.newaxis, ...], (N, sequence_length, 1, 1, 1))
    M_tensor = tf.constant(single_mask, dtype=tf.float32)

    # ---------- Discover trials ----------
    trial_dirs = [d for d in natural_sort(os.listdir(checkpoint_dir_BO)) if d.startswith("trial_")]
    trial_dirs = [os.path.join(checkpoint_dir_BO, d) for d in trial_dirs if os.path.isdir(os.path.join(checkpoint_dir_BO, d))]

    if len(trial_dirs) == 0:
        raise FileNotFoundError(f"No trial_* directories found in {checkpoint_dir_BO}")

    # Where to write outputs
    root_out = os.path.join(output_root, test_name)
    os.makedirs(root_out, exist_ok=True)

    metrics_rows = []

    for trial_dir in trial_dirs:
        model_path = os.path.join(trial_dir, "best_model.keras")
        if not os.path.exists(model_path):
            print(f"[WARN] best_model.keras not found in {trial_dir}; skipping.")
            continue

        print(f">> Loading model: {model_path}")
        model = load_model(
            model_path,
            custom_objects={
                'StandardCBAM': StandardCBAM,
                'CustomAttentionLayer': CustomAttentionLayer,
                'ClusterBasedApplication': ClusterBasedApplication,
                'masked_mse': masked_mse,
                'TrueLoss': TrueLoss,
            },
        )

        trial_name = os.path.basename(trial_dir)
        out_dir = os.path.join(root_out, trial_name)
        os.makedirs(out_dir, exist_ok=True)

        # Predict and save each timestep
        mse_list, rmse_list, r2_list = [], [], []
        for i in range(N):
            Xb = X_norm[i:i+1]
            Mb = M_tensor[i:i+1]
            WLb = WL_seq[i:i+1]
            pred = model.predict([Xb, Mb, WLb], verbose=0)[0]  # (H,W)

            pred_denorm = denormalize_data(pred, y_train_min, y_train_max)
            pred_denorm = apply_nan_mask(pred_denorm, Y_nan_mask[i])

            fname = Y_files_aligned[i]
            ref = os.path.join(test_water_depth_dir, fname)
            if not os.path.exists(ref):
                print(f"[WARN] Reference {ref} missing; skipping save for {fname}")
                continue
            save_tiff_image(pred_denorm, os.path.join(out_dir, fname), ref)

            # metrics on valid pixels
            y_true = apply_nan_mask(denormalize_data(Y_seqs[i], y_train_min, y_train_max), Y_nan_mask[i])
            valid = ~np.isnan(y_true)
            if np.any(valid):
                mse = mean_squared_error(y_true[valid], pred_denorm[valid])
                rmse = float(np.sqrt(mse))
                try:
                    r2 = float(r2_score(y_true[valid], pred_denorm[valid]))
                except Exception:
                    r2 = float('nan')
                mse_list.append(float(mse)); rmse_list.append(rmse); r2_list.append(r2)

        # Write per-trial summary
        if mse_list:
            summary = {
                "trial": trial_name,
                "N_samples": len(mse_list),
                "avg_MSE": float(np.mean(mse_list)),
                "avg_RMSE": float(np.mean(rmse_list)),
                "avg_R2": float(np.mean(r2_list)),
            }
        else:
            summary = {"trial": trial_name, "N_samples": 0, "avg_MSE": None, "avg_RMSE": None, "avg_R2": None}

        pd.DataFrame([summary]).to_csv(os.path.join(out_dir, "summary_metrics.csv"), index=False)
        metrics_rows.append(summary)
        print(f"Saved predictions + summary for {trial_name} -> {out_dir}")

    # Global summary across trials
    pd.DataFrame(metrics_rows).to_csv(os.path.join(root_out, "all_trials_summary.csv"), index=False)
    print(f"All done. Global summary -> {os.path.join(root_out, 'all_trials_summary.csv')}")

# Optional CLI-style main with sensible defaults; you can import run_predictions in your runner.
def main():
    # Defaults that mirror typical folder names; adjust in your own launcher as needed.
    run_predictions(
        test_atm_pressure_dir=os.path.join(os.getcwd(), 'atm_pressure'),
        test_wind_speed_dir=os.path.join(os.getcwd(), 'wind_speed'),
        test_precipitation_dir=os.path.join(os.getcwd(), 'precipitation'),
        test_river_discharge_dir=os.path.join(os.getcwd(), 'river_discharge'),
        test_water_depth_dir=os.path.join(os.getcwd(), 'water_depth'),
        test_water_level_dir=os.path.join(os.getcwd(), 'testharvey'),
        test_dem_file=os.path.join(os.getcwd(), 'DEM', 'dem_idw.tif'),
        checkpoint_dir_BO="checkpoint_BO",
        polygon_clusters_path=os.path.join(os.getcwd(), 'voronoi_clusters.shp'),
        sequence_length=6,
        output_root="predictions",
        test_name="testharvey",
        seed_value=42,
    )

if __name__ == "__main__":
    main()
