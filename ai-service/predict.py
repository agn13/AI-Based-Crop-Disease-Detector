from pathlib import Path
import json

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
import h5py
import numpy as np
import tensorflow as tf

app = FastAPI()

MODEL_PATH = Path(__file__).resolve().parent / "model.h5"

if not MODEL_PATH.exists():
    raise RuntimeError(f"Model file not found: {MODEL_PATH}")

def _patch_keras3_config(node):
    if isinstance(node, dict):
        if "config" in node and isinstance(node["config"], dict):
            cfg = node["config"]
            dtype_cfg = cfg.get("dtype")
            if isinstance(dtype_cfg, dict) and dtype_cfg.get("class_name") == "DTypePolicy":
                cfg["dtype"] = dtype_cfg.get("config", {}).get("name", "float32")
            cfg.pop("quantization_config", None)

        if node.get("class_name") == "InputLayer" and "config" in node:
            cfg = node["config"]
            if "batch_shape" in cfg and "batch_input_shape" not in cfg:
                cfg["batch_input_shape"] = cfg.pop("batch_shape")
            cfg.pop("optional", None)
        for value in node.values():
            _patch_keras3_config(value)
    elif isinstance(node, list):
        for item in node:
            _patch_keras3_config(item)


def _load_model_with_compat(path: Path):
    try:
        return tf.keras.models.load_model(str(path), compile=False)
    except Exception:
        with h5py.File(path, "r") as h5_file:
            model_config = h5_file.attrs.get("model_config")

        if model_config is None:
            raise

        if isinstance(model_config, bytes):
            model_config = model_config.decode("utf-8")

        config = json.loads(model_config)
        _patch_keras3_config(config)

        model = tf.keras.models.model_from_json(json.dumps(config))
        model.load_weights(str(path))
        return model


# Load trained model using absolute path for stable startup behavior.
model = _load_model_with_compat(MODEL_PATH)

# Replace this list with the exact class order printed after training.
class_names = [
    "Pepper__bell__Bacterial_spot",
    "Pepper__bell__healthy",
    "Potato_Early_blight",
    "Potato_Late_blight",
    "Potato_healthy",
    "Tomato_Bacterial_spot",
    "Tomato_Early_blight",
    "Tomato_Late_blight",
    "Tomato_Leaf_Mold",
    "Tomato_Septoria_leaf_spot",
    "Tomato_Spider_mites_Two_spotted_spider_mite",
    "Tomato_Target_Spot",
    "Tomato_Tomato_YellowLeaf_Curl_Virus",
    "Tomato_Tomato_mosaic_virus",
    "Tomato_healthy",
]

DISPLAY_DISEASE_NAME = {
    "Pepper__bell__Bacterial_spot": "Bacterial Spot",
    "Pepper__bell__healthy": "Healthy",
    "Potato_Early_blight": "Early Blight",
    "Potato_Late_blight": "Late Blight",
    "Potato_healthy": "Healthy",
    "Tomato_Bacterial_spot": "Bacterial Spot",
    "Tomato_Early_blight": "Early Blight",
    "Tomato_Late_blight": "Late Blight",
    "Tomato_Leaf_Mold": "Leaf Mold",
    "Tomato_Septoria_leaf_spot": "Septoria Leaf Spot",
    "Tomato_Spider_mites_Two_spotted_spider_mite": "Spider Mites",
    "Tomato_Target_Spot": "Target Spot",
    "Tomato_Tomato_YellowLeaf_Curl_Virus": "Yellow Leaf Curl Virus",
    "Tomato_Tomato_mosaic_virus": "Mosaic Virus",
    "Tomato_healthy": "Healthy",
}

DISEASE_GUIDANCE = {
    "Pepper__bell__Bacterial_spot": {
        "severity": "High",
        "treatment": "Use copper-based bactericide; avoid overhead irrigation.",
        "steps": [
            "Remove heavily infected leaves.",
            "Spray copper-based bactericide every 7 to 10 days.",
            "Water at soil level to keep foliage dry.",
        ],
    },
    "Pepper__bell__healthy": {
        "severity": "Low",
        "treatment": "No treatment needed. Continue routine monitoring.",
        "steps": [
            "Inspect leaves every 3 to 4 days.",
            "Maintain balanced nutrition and irrigation.",
            "Keep weeds and debris away from crop rows.",
        ],
    },
    "Potato_Early_blight": {
        "severity": "Medium",
        "treatment": "Apply chlorothalonil or mancozeb; remove infected leaves.",
        "steps": [
            "Prune infected lower foliage.",
            "Apply protective fungicide as per label dose.",
            "Rotate with non-solanaceous crops next season.",
        ],
    },
    "Potato_Late_blight": {
        "severity": "High",
        "treatment": "Apply systemic fungicide immediately and isolate infected plants.",
        "steps": [
            "Isolate affected plants immediately.",
            "Apply recommended late blight fungicide.",
            "Destroy severely infected plants to reduce spread.",
        ],
    },
    "Potato_healthy": {
        "severity": "Low",
        "treatment": "No treatment needed. Maintain preventive field hygiene.",
        "steps": [
            "Continue weekly scouting.",
            "Avoid prolonged leaf wetness.",
            "Use clean tools and disease-free seed tubers.",
        ],
    },
    "Tomato_Bacterial_spot": {
        "severity": "High",
        "treatment": "Use copper sprays and remove infected foliage.",
        "steps": [
            "Remove symptomatic leaves.",
            "Spray copper-based bactericide on schedule.",
            "Avoid handling plants when wet.",
        ],
    },
    "Tomato_Early_blight": {
        "severity": "Medium",
        "treatment": "Apply fungicide and improve air circulation around plants.",
        "steps": [
            "Prune lower canopy for airflow.",
            "Apply fungicide at recommended interval.",
            "Mulch soil to reduce spore splash.",
        ],
    },
    "Tomato_Late_blight": {
        "severity": "High",
        "treatment": "Use late blight fungicide and remove severely infected plants.",
        "steps": [
            "Separate affected plants quickly.",
            "Apply curative + protective fungicide program.",
            "Dispose infected plants away from field.",
        ],
    },
    "Tomato_Leaf_Mold": {
        "severity": "Medium",
        "treatment": "Reduce humidity and apply recommended fungicide.",
        "steps": [
            "Ventilate crop area or widen plant spacing.",
            "Irrigate in morning only.",
            "Apply fungicide where symptoms are active.",
        ],
    },
    "Tomato_Septoria_leaf_spot": {
        "severity": "Medium",
        "treatment": "Remove lower infected leaves and apply fungicide.",
        "steps": [
            "Remove infected basal foliage.",
            "Use preventive fungicide spray cycle.",
            "Keep leaves dry during irrigation.",
        ],
    },
    "Tomato_Spider_mites_Two_spotted_spider_mite": {
        "severity": "Medium",
        "treatment": "Use miticide or neem-based control and increase humidity.",
        "steps": [
            "Spray leaf undersides thoroughly.",
            "Rotate miticide modes of action.",
            "Increase humidity and reduce dust stress.",
        ],
    },
    "Tomato_Target_Spot": {
        "severity": "Medium",
        "treatment": "Spray broad-spectrum fungicide and avoid leaf wetness.",
        "steps": [
            "Remove infected foliage early.",
            "Apply broad-spectrum fungicide.",
            "Use drip irrigation instead of overhead watering.",
        ],
    },
    "Tomato_Tomato_YellowLeaf_Curl_Virus": {
        "severity": "High",
        "treatment": "Control whiteflies and remove infected plants.",
        "steps": [
            "Rogue symptomatic plants immediately.",
            "Deploy yellow sticky traps for whiteflies.",
            "Use vector control spray as recommended.",
        ],
    },
    "Tomato_Tomato_mosaic_virus": {
        "severity": "High",
        "treatment": "Remove infected plants and sanitize tools regularly.",
        "steps": [
            "Discard infected plants safely.",
            "Disinfect hands and tools after handling plants.",
            "Avoid tobacco contamination in field operations.",
        ],
    },
    "Tomato_healthy": {
        "severity": "Low",
        "treatment": "No treatment needed. Continue regular monitoring.",
        "steps": [
            "Monitor leaves every few days.",
            "Follow balanced irrigation and nutrition schedule.",
            "Keep field sanitation consistent.",
        ],
    },
}


def _confidence_label(score):
    if score > 0.8:
        return "High"
    if score > 0.5:
        return "Medium"
    return "Low"


@app.get("/")
def home():
    return {"status": "AI service running"}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are allowed")

    try:
        image = Image.open(file.file).convert("RGB")
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="Invalid or corrupted image file")

    image = image.resize((224, 224))

    img_array = np.array(image) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    predictions = model.predict(img_array, verbose=0)
    scores = predictions[0]
    predicted_index = int(np.argmax(scores))
    confidence_score = float(scores[predicted_index])

    if predicted_index >= len(class_names):
        raise HTTPException(status_code=500, detail="Model output does not match class labels")

    disease_name = class_names[predicted_index]
    display_disease_name = DISPLAY_DISEASE_NAME.get(disease_name, disease_name.replace("_", " "))

    confidence_label = _confidence_label(confidence_score)

    default_severity = "High" if "virus" in disease_name.lower() else "Medium"
    guidance = DISEASE_GUIDANCE.get(
        disease_name,
        {
            "severity": default_severity,
            "treatment": "Follow integrated pest and disease management practices.",
            "steps": [
                "Inspect affected plants closely.",
                "Apply locally recommended control method.",
                "Repeat field check after 3 days.",
            ],
        },
    )

    top_indices = np.argsort(scores)[::-1][:3]
    top_predictions = []
    for idx in top_indices:
        idx_int = int(idx)
        class_name = class_names[idx_int]
        score = float(scores[idx_int])
        top_predictions.append(
            {
                "disease": DISPLAY_DISEASE_NAME.get(class_name, class_name.replace("_", " ")),
                "confidenceScore": round(score * 100, 2),
                "confidence": _confidence_label(score),
            }
        )

    return {
        "disease": display_disease_name,
        "confidence": confidence_label,
        "severity": guidance["severity"],
        "treatment": guidance["treatment"],
        "treatmentSteps": guidance["steps"],
        "topPredictions": top_predictions,
    }
