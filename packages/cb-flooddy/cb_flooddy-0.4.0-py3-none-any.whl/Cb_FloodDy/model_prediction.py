
# ==========================================
# Flood Depth Prediction Model - Batch Trial Runner
# ==========================================
# This module loads every Optuna trial (trial_XXX) found under a checkpoint dir,
# loads its saved model + normalization params, runs predictions for a given event,
# and writes outputs into per-trial subfolders.
#
# Usage (from a notebook or script):
#   from Cb_FloodDy import model_prediction as mp
#   mp.set_seed(42)
#   mp.run_all_trials(
#       checkpoint_dir_BO="checkpoint_BO",
#       event_config={
#           "name": "Hurricane Harvey 2017",
#           "test_dirs": {
#               "atm_pressure": "atm_pressure",
#               "wind_speed": "wind_speed",
#               "precipitation": "precipitation",
#               "river_discharge": "river_discharge",
#               "water_depth": "water_depth",
#               "dem_file": "DEM/dem_idw.tif",
#               "water_level": "test_stations_harvey",
#               "polygons_shp": "voronoi_clusters.shp"
#           },
#           "sequence_length": 6,
#           "output_base_dir": "predictions_harvey"
#       }
#   )
#
# Notes:
# - Expects training to have saved per-trial artifacts:
#   * trial_XXX/best_model.keras
#   * trial_XXX/artifacts/normalization_params.npz
#   * trial_XXX/artifacts/cluster_masks.npy   (optional; if missing, shapefile path is used)
# - The model was compiled with custom objects; we register them here for deserialization.
# ==========================================

import os
import re
import numpy as np
import pandas as pd
import tensorflow as tf
import rasterio
import geopandas as gpd
from rasterio.features import rasterize
from tensorflow.keras.models import load_model, Model
from tensorflow.keras.layers import Layer, Dense, Conv2D, Multiply, Reshape, Add, Activation
from tensorflow.keras.regularizers import l2
from tensorflow.keras.initializers import GlorotNormal
from tensorflow.keras import backend as K
from keras.saving import register_keras_serializable

# ----------------------------
# Reproducibility / GPU policy
# ----------------------------
def set_seed(seed: int = 3):
    np.random.seed(seed)
    tf.random.set_seed(seed)
    try:
        gpus = tf.config.experimental.list_physical_devices('GPU')
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except Exception as e:
        print("GPU memory growth not set:", e)
    from tensorflow.keras.mixed_precision import set_global_policy
    set_global_policy('float32')


# ----------------
# Helper utilities
# ----------------
def natural_sort(file_list):
    def alphanum_key(key):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", key)]
    return sorted(file_list, key=alphanum_key)

def load_tiff_images(data_dir):
    images, filenames, crs, transform = [], [], None, None
    for filename in sorted(os.listdir(data_dir)):
        if filename.endswith(".tif"):
            fp = os.path.join(data_dir, filename)
            with rasterio.open(fp) as src:
                img = src.read(1)
                if crs is None: crs = src.crs
                if transform is None: transform = src.transform
                images.append(img)
            filenames.append(filename)
    if not images:
        raise FileNotFoundError(f"No .tif found in {data_dir}")
    return np.array(images), filenames, crs, transform

def load_single_tiff_image(filepath):
    with rasterio.open(filepath) as src:
        img = src.read(1)
        crs = src.crs
        transform = src.transform
    return img, crs, transform

def load_water_level_data(data_dir):
    wl_mat, filenames = [], [f for f in os.listdir(data_dir) if f.endswith(".csv")]
    filenames = natural_sort(filenames)
    for fn in filenames:
        df = pd.read_csv(os.path.join(data_dir, fn))
        if "water_level" in df.columns:
            wl_mat.append(df["water_level"].values)
        else:
            print(f"[WARN] 'water_level' column not in {fn}, skipping.")
    if not wl_mat:
        raise FileNotFoundError(f"No station CSVs with 'water_level' in {data_dir}")
    return np.array(wl_mat), filenames

def normalize_data_with_nan(data, min_val, max_val):
    nan_mask = np.isnan(data)
    norm = 0.1 + 0.9 * (data - min_val) / (max_val - min_val)
    norm[nan_mask] = 0.0
    return norm

def denormalize_data(norm_data, min_val, max_val):
    return (norm_data - 0.1) / 0.9 * (max_val - min_val) + min_val

def apply_nan_mask(data, mask):
    out = data.copy()
    out[mask] = np.nan
    return out

def save_tiff_image(data, output_path, reference_dataset):
    with rasterio.open(reference_dataset) as src:
        out_meta = src.meta.copy()
    out_meta.update({
        "driver": "GTiff",
        "height": data.shape[0],
        "width": data.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": src.crs,
        "transform": src.transform,
    })
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with rasterio.open(output_path, "w", **out_meta) as dest:
        dest.write(data.astype(np.float32), 1)


# ---------------------------
# Custom layers / loss / metric
# ---------------------------
def masked_global_average_pooling2d(inputs, mask):
    masked_inputs = inputs * mask
    sum_pool = tf.reduce_sum(masked_inputs, axis=[1, 2])
    valid_pixels = tf.reduce_sum(mask, axis=[1, 2]) + tf.keras.backend.epsilon()
    return sum_pool / valid_pixels

def masked_global_max_pooling2d(inputs, mask):
    masked_inputs = inputs * mask + (1.0 - mask) * (-1e9)
    return tf.reduce_max(masked_inputs, axis=[1, 2])

@register_keras_serializable(package="Cb_FloodDy", name="StandardCBAM")
class StandardCBAM(Layer):
    def __init__(self, ratio=8, kernel_size=7, return_attention=False, **kwargs):
        super().__init__(**kwargs)
        self.ratio = ratio
        self.kernel_size = kernel_size
        self.return_attention = return_attention
    def build(self, input_shape):
        total_channels = input_shape[-1]
        self.feature_channels = total_channels - 1
        self.shared_dense_one = Dense(self.feature_channels // self.ratio, activation="relu", kernel_initializer="he_normal", use_bias=True, bias_initializer="zeros")
        self.shared_dense_two = Dense(self.feature_channels, activation="sigmoid", kernel_initializer="glorot_normal", use_bias=True, bias_initializer="zeros")
        self.conv_spatial = Conv2D(1, self.kernel_size, strides=1, padding="same", activation="sigmoid", kernel_initializer="glorot_normal", use_bias=False)
        super().build(input_shape)
    def call(self, inputs, training=None):
        feature = inputs[..., :self.feature_channels]
        mask = inputs[..., self.feature_channels:]
        avg_pool = masked_global_average_pooling2d(feature, mask)
        avg_pool = self.shared_dense_one(avg_pool)
        avg_pool = self.shared_dense_two(avg_pool)
        max_pool = masked_global_max_pooling2d(feature, mask)
        max_pool = self.shared_dense_one(max_pool)
        max_pool = self.shared_dense_two(max_pool)
        channel_attention = Add()([avg_pool, max_pool])
        channel_attention = Activation("sigmoid")(channel_attention)
        channel_attention = Reshape((1, 1, self.feature_channels))(channel_attention)
        refined_feature = Multiply()([feature, channel_attention])
        spatial_attention = self.conv_spatial(refined_feature)
        spatial_attention = Multiply()([spatial_attention, mask])
        refined_feature = Multiply()([refined_feature, spatial_attention])
        return [refined_feature, spatial_attention] if self.return_attention else refined_feature
    def get_config(self):
        return {**super().get_config(), "ratio": self.ratio, "kernel_size": self.kernel_size, "return_attention": self.return_attention}

@register_keras_serializable(package="Cb_FloodDy", name="CustomAttentionLayer")
class CustomAttentionLayer(Layer):
    def __init__(self, emphasis_factor=1.5, top_k_percent=0.2, **kwargs):
        super().__init__(**kwargs)
        self.emphasis_factor = emphasis_factor
        self.top_k_percent = top_k_percent
    def build(self, input_shape):
        self.W = self.add_weight(name="att_weight", shape=(input_shape[-1], 1), initializer=GlorotNormal(), trainable=True)
        self.b = self.add_weight(shape=(1,), initializer="zeros", trainable=True, name="bias")
        super().build(input_shape)
    def call(self, x):
        e = K.tanh(K.dot(x, self.W) + self.b)
        a = K.softmax(e, axis=1)
        a = K.squeeze(a, axis=-1)
        k_value = tf.cast(tf.cast(tf.shape(a)[1], tf.float32) * self.top_k_percent, tf.int32)
        k_value = tf.maximum(k_value, 1)
        _, top_k_indices = tf.math.top_k(a, k=k_value)
        mask = tf.one_hot(top_k_indices, depth=tf.shape(a)[1])
        mask = tf.reduce_max(mask, axis=1)
        mask = tf.cast(mask, tf.bool)
        emphasized_a = tf.where(mask, a * self.emphasis_factor, a)
        output = x * tf.expand_dims(emphasized_a, axis=-1)
        summed_output = K.sum(output, axis=1)
        return [summed_output, emphasized_a]
    def get_config(self):
        return {**super().get_config(), "emphasis_factor": self.emphasis_factor, "top_k_percent": self.top_k_percent}

@register_keras_serializable(package="Cb_FloodDy", name="ClusterBasedApplication")
class ClusterBasedApplication(Layer):
    def __init__(self, num_stations, height, width, **kwargs):
        super().__init__(**kwargs)
        self.num_stations = int(num_stations); self.height = int(height); self.width = int(width)
    def build(self, input_shape):
        self.dense_project = Dense(self.height * self.width, activation="relu", kernel_initializer="he_normal", kernel_regularizer=l2(1e-6), name="Dense_Project_Context")
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
    def get_config(self):
        return {**super().get_config(), "num_stations": self.num_stations, "height": self.height, "width": self.width}

@register_keras_serializable(package="Cb_FloodDy", name="masked_mse")
def masked_mse(y_true, y_pred):
    y_true = tf.cast(y_true, tf.float32)
    y_pred = tf.cast(y_pred, tf.float32)
    mask = tf.cast(tf.math.not_equal(y_true, 0.0), y_true.dtype)
    mse = tf.square(y_true - y_pred)
    return tf.reduce_sum(mse * mask) / (tf.reduce_sum(mask) + 1e-8)

@register_keras_serializable(package="Cb_FloodDy", name="TrueLoss")
class TrueLoss(tf.keras.metrics.Metric):
    def __init__(self, name="trueloss", **kwargs):
        super().__init__(name=name, **kwargs)
        self.true_loss = self.add_weight(name="tl", initializer="zeros")
        self.count = self.add_weight(name="count", initializer="zeros")
    def update_state(self, y_true, y_pred, sample_weight=None):
        y_true = tf.cast(y_true, tf.float32); y_pred = tf.cast(y_pred, tf.float32)
        mask = tf.cast(tf.math.not_equal(y_true, 0.0), y_true.dtype)
        mse = tf.square(y_true - y_pred)
        masked = tf.reduce_sum(mse * mask) / (tf.reduce_sum(mask) + 1e-8)
        self.true_loss.assign_add(masked); self.count.assign_add(1.0)
    def result(self): return self.true_loss / self.count
    def reset_state(self): self.true_loss.assign(0.0); self.count.assign(0.0)


# ---------------------------
# Core prediction entrypoints
# ---------------------------
def _build_sequences_stack(features_stack, sequence_length):
    seqs = []
    for i in range(len(features_stack) - sequence_length + 1):
        seqs.append(features_stack[i:i + sequence_length])
    return np.array(seqs)

def _load_trial_artifacts(trial_dir):
    model_path = os.path.join(trial_dir, "best_model.keras")
    norm_path = os.path.join(trial_dir, "artifacts", "normalization_params.npz")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"best_model.keras not found in {trial_dir}")
    if not os.path.exists(norm_path):
        raise FileNotFoundError(f"normalization_params.npz not found in {trial_dir}/artifacts")
    norm = np.load(norm_path)
    model = load_model(model_path, custom_objects={
        "StandardCBAM": StandardCBAM,
        "CustomAttentionLayer": CustomAttentionLayer,
        "ClusterBasedApplication": ClusterBasedApplication,
        "masked_mse": masked_mse,
        "TrueLoss": TrueLoss
    })
    # cluster masks optional (fallback to shapefile if absent)
    cluster_masks_path = os.path.join(trial_dir, "artifacts", "cluster_masks.npy")
    cluster_masks = None
    if os.path.exists(cluster_masks_path):
        try:
            cluster_masks = np.load(cluster_masks_path)
        except Exception as e:
            print("[WARN] Failed loading cluster_masks.npy:", e)
    return model, norm, cluster_masks

def _create_single_mask(cluster_masks, batch_size, sequence_length):
    single_mask = np.max(cluster_masks.astype(np.uint8), axis=0)  # (H, W)
    single_mask = single_mask[..., np.newaxis]  # (H, W, 1)
    single_mask = np.expand_dims(single_mask, axis=(0, 1))  # (1,1,H,W,1)
    single_mask = np.tile(single_mask, (batch_size, sequence_length, 1, 1, 1))
    return single_mask.astype(np.float32)

def _rasterize_clusters_from_shp(shp_path, raster_shape, transform):
    polygons_gdf = gpd.read_file(shp_path)
    masks = []
    for poly in polygons_gdf.geometry:
        mask = rasterize([(poly, 1)], out_shape=raster_shape, transform=transform, fill=0, dtype="uint8")
        masks.append(mask)
    cluster_masks = np.array(masks)
    combined = np.sum(cluster_masks.astype(int), axis=0)
    if np.any(combined > 1):
        raise ValueError("Overlap detected in cluster polygons.")
    return cluster_masks

def run_predictions_for_event(trial_dir, event_config):
    # Load model + normalization
    model, norm, cluster_masks = _load_trial_artifacts(trial_dir)
    X_train_min_vals = norm["X_train_min_vals"]
    X_train_max_vals = norm["X_train_max_vals"]
    y_train_min = float(norm["y_train_min"])
    y_train_max = float(norm["y_train_max"])
    wl_min = float(norm["water_level_global_min"])
    wl_max = float(norm["water_level_global_max"])

    # Paths
    tdirs = event_config["test_dirs"]
    seq_len = int(event_config.get("sequence_length", 6))
    out_base = event_config["output_base_dir"]
    event_name = event_config.get("name", "event")
    # Output per-trial dir
    trial_name = os.path.basename(trial_dir.rstrip(os.sep))
    out_dir = os.path.join(out_base, event_name, trial_name)
    os.makedirs(out_dir, exist_ok=True)

    # Load rasters
    atm, atm_fns, crs, transform = load_tiff_images(tdirs["atm_pressure"])
    wnd, _, _, _ = load_tiff_images(tdirs["wind_speed"])
    prc, _, _, _ = load_tiff_images(tdirs["precipitation"])
    rdc, _, _, _ = load_tiff_images(tdirs["river_discharge"])
    dem_img, _, _ = load_single_tiff_image(tdirs["dem_file"])
    T = atm.shape[0]
    dem = np.tile(dem_img, (T, 1, 1))

    # Stack features -> sequences
    X = np.stack((atm, wnd, dem, prc, rdc), axis=-1)
    X_seq = _build_sequences_stack(X, seq_len)

    # y (for alignment & metrics saving as tif)
    y_all, y_fns, _, _ = load_tiff_images(tdirs["water_depth"])
    y_seq = y_all[seq_len - 1:]
    X_seq = X_seq[:len(y_seq)]  # align

    # Normalize X using training stats
    Xn_list = []
    for i in range(X_seq.shape[-1]):
        Xn_list.append(normalize_data_with_nan(X_seq[..., i], X_train_min_vals[i], X_train_max_vals[i]))
    Xn = np.stack(Xn_list, axis=-1)

    # Water levels
    wl_mat, wl_fns = load_water_level_data(tdirs["water_level"])
    wl_norm = (wl_mat - wl_min) / (wl_max - wl_min)
    wl_seq = []
    for i in range(wl_norm.shape[1] - seq_len + 1):
        wl_seq.append(wl_norm[:, i:i + seq_len])
    wl_seq = np.array(wl_seq).transpose(0, 2, 1)  # (N, seq_len, S)

    # Align
    N = min(Xn.shape[0], wl_seq.shape[0], y_seq.shape[0])
    Xn = Xn[:N]; wl_seq = wl_seq[:N]; y_seq = y_seq[:N]
    y_fns = y_fns[seq_len - 1: seq_len - 1 + N]

    # y normalization for masking NaNs
    y_nan_mask = np.isnan(y_seq)

    # Cluster mask
    if cluster_masks is None:
        cluster_masks = _rasterize_clusters_from_shp(tdirs["polygons_shp"], (Xn.shape[2], Xn.shape[3]), transform)
    mask_bt = _create_single_mask(cluster_masks, batch_size=Xn.shape[0], sequence_length=seq_len)
    mask_tensor = tf.constant(mask_bt, dtype=tf.float32)

    # Predict loop and write tifs
    for i in range(N):
        Xi = Xn[i:i+1]
        Mi = mask_tensor[i:i+1]
        WLi = wl_seq[i:i+1]
        preds = model.predict([Xi, Mi, WLi], verbose=0)
        preds_denorm = denormalize_data(preds[0], y_train_min, y_train_max)
        preds_denorm = apply_nan_mask(preds_denorm, y_nan_mask[i].squeeze())
        fn = y_fns[i]
        ref = os.path.join(tdirs["water_depth"], fn)
        out_path = os.path.join(out_dir, fn)
        if os.path.exists(ref):
            save_tiff_image(preds_denorm, out_path, ref)
        else:
            print(f"[WARN] reference raster missing for {fn}, skipping write.")

    # Save a small manifest
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump({
            "event": event_name,
            "trial_dir": trial_dir,
            "num_predictions": int(N),
            "outputs_dir": out_dir
        }, f, indent=2)

    print(f"[OK] {event_name} — {trial_name}: wrote predictions to {out_dir}")
    return out_dir


def run_all_trials(checkpoint_dir_BO, event_config):
    """Discover all trial_XXX under checkpoint_dir_BO and run predictions for each."""
    trials = []
    for name in os.listdir(checkpoint_dir_BO):
        tdir = os.path.join(checkpoint_dir_BO, name)
        if os.path.isdir(tdir) and name.startswith("trial_") and os.path.exists(os.path.join(tdir, "best_model.keras")):
            trials.append(tdir)
    trials = sorted(trials)
    if not trials:
        raise FileNotFoundError(f"No trials with best_model.keras found in {checkpoint_dir_BO}")

    outputs = []
    for tdir in trials:
        try:
            outputs.append(run_predictions_for_event(tdir, event_config))
        except Exception as e:
            print(f"[ERR] Failed on {tdir}: {e}")
    return outputs
