"""
utils/prediction.py
--------------------
Inference pipeline: loads the trained model ONCE at app startup, preprocesses
uploaded images, returns top-3 predictions with confidence, and can generate
a Grad-CAM heatmap explaining which image regions drove the prediction.
"""

import os
import json
import base64
import io

import numpy as np
from PIL import Image
import tensorflow as tf

from utils.waste_info import CLASS_NAMES, get_confidence_label, get_waste_info

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "model")
MODEL_PATH = os.path.join(MODEL_DIR, "waste_model_final.h5")
CLASS_INDEX_PATH = os.path.join(MODEL_DIR, "class_indices.json")
IMG_SIZE = (224, 224)

_model = None
_idx_to_class = None
_last_conv_layer_name = None


def load_model_once():
    """Load the Keras model and class index mapping a single time (module-level cache)."""
    global _model, _idx_to_class, _last_conv_layer_name
    if _model is not None:
        return _model

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"No trained model found at {MODEL_PATH}. "
            "Run training/train.py first, or place a trained .keras file there."
        )

    _model = tf.keras.models.load_model(MODEL_PATH)

    if os.path.exists(CLASS_INDEX_PATH):
        with open(CLASS_INDEX_PATH) as f:
            idx_to_class = json.load(f)
        _idx_to_class = {int(k): v for k, v in idx_to_class.items()}
    else:
        _idx_to_class = {i: name for i, name in enumerate(CLASS_NAMES)}

    # Find the last conv layer inside the MobileNetV2 base for Grad-CAM
    _last_conv_layer_name = _find_last_conv_layer(_model)

    print("Model loaded. Classes:", _idx_to_class)
    return _model


def _find_last_conv_layer(model):
    """Locate the last 4D-output conv layer, searching nested sub-models too."""
    for layer in reversed(model.layers):
        if len(layer.output_shape) == 4:
            return layer.name
        if hasattr(layer, "layers"):  # nested functional model (e.g. MobileNetV2 base)
            for sub_layer in reversed(layer.layers):
                if len(sub_layer.output_shape) == 4:
                    return sub_layer.name
    return None


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Decode, resize, and normalize an uploaded image for model input."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img = img.resize(IMG_SIZE)
    arr = np.array(img).astype("float32") / 255.0
    return np.expand_dims(arr, axis=0), img


def predict_image(image_bytes: bytes) -> dict:
    """
    Run a full prediction: preprocess -> model.predict -> top-3 -> confidence
    label -> waste metadata lookup. Returns a JSON-serializable dict.
    """
    model = load_model_once()
    input_arr, pil_img = preprocess_image(image_bytes)

    preds = model.predict(input_arr, verbose=0)[0]  # shape: (num_classes,)

    top_indices = preds.argsort()[-3:][::-1]
    top3 = [
        {"class": _idx_to_class[int(i)], "confidence": round(float(preds[i]) * 100, 2)}
        for i in top_indices
    ]

    best_idx = int(top_indices[0])
    best_class = _idx_to_class[best_idx]
    best_confidence = float(preds[best_idx])

    confidence_info = get_confidence_label(best_confidence)
    waste_meta = get_waste_info(best_class)

    return {
        "predicted_class": best_class,
        "confidence": round(best_confidence * 100, 2),
        "confidence_level": confidence_info["level"],
        "confidence_message": confidence_info["message"],
        "top3": top3,
        "waste_info": {
            "display_name": waste_meta["display_name"],
            "material": waste_meta["material"],
            "biodegradable": waste_meta["biodegradable"],
            "recyclable": waste_meta["recyclable"],
            "hazard_level": waste_meta["hazard_level"],
            "special_handling": waste_meta["special_handling"],
            "disposal": waste_meta["disposal"],
            "reuse_ideas": waste_meta["reuse_ideas"],
            "environmental_impact": waste_meta["environmental_impact"],
            "safety_warning": waste_meta["safety_warning"],
            "icon": waste_meta["icon"],
        },
    }


def generate_gradcam(image_bytes: bytes, predicted_class_index: int = None) -> str:
    """
    Generate a Grad-CAM heatmap overlay showing which regions of the image
    most influenced the prediction. Returns a base64-encoded PNG data URI.

    NOTE: this is a visualization aid for explainability, not proof the
    model's reasoning is correct — it is presented to the user as such.
    """
    model = load_model_once()
    if _last_conv_layer_name is None:
        return None

    input_arr, pil_img = preprocess_image(image_bytes)

    # Build a model that maps input -> (last conv layer output, predictions)
    grad_model = tf.keras.models.Model(
        [model.inputs],
        [model.get_layer(_last_conv_layer_name).output if _last_conv_layer_name in
         [l.name for l in model.layers] else _get_nested_layer_output(model, _last_conv_layer_name),
         model.output],
    )

    with tf.GradientTape() as tape:
        conv_output, predictions = grad_model(input_arr)
        if predicted_class_index is None:
            predicted_class_index = tf.argmax(predictions[0])
        class_channel = predictions[:, predicted_class_index]

    grads = tape.gradient(class_channel, conv_output)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    conv_output = conv_output[0]
    heatmap = conv_output @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    heatmap = tf.maximum(heatmap, 0) / (tf.reduce_max(heatmap) + 1e-8)
    heatmap = heatmap.numpy()

    # Overlay heatmap on original image
    heatmap_img = Image.fromarray(np.uint8(255 * heatmap)).resize(IMG_SIZE)
    heatmap_arr = np.array(heatmap_img)

    import matplotlib.cm as cm
    jet = cm.get_cmap("jet")
    jet_colors = jet(np.arange(256))[:, :3]
    jet_heatmap = jet_colors[heatmap_arr]
    jet_heatmap = np.uint8(jet_heatmap * 255)

    base_img = np.array(pil_img.resize(IMG_SIZE))
    overlay = np.uint8(jet_heatmap * 0.4 + base_img * 0.6)
    overlay_img = Image.fromarray(overlay)

    buf = io.BytesIO()
    overlay_img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def _get_nested_layer_output(model, layer_name):
    for layer in model.layers:
        if hasattr(layer, "layers"):
            for sub_layer in layer.layers:
                if sub_layer.name == layer_name:
                    # rebuild a callable path through the nested model
                    return layer.get_layer(layer_name).output
    raise ValueError(f"Layer {layer_name} not found")
