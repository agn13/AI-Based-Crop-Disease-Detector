from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
import numpy as np
import tensorflow as tf

app = FastAPI()

MODEL_PATH = Path(__file__).resolve().parent / "model.h5"

if not MODEL_PATH.exists():
    raise RuntimeError(f"Model file not found: {MODEL_PATH}")

# Load trained model using absolute path for stable startup behavior.
model = tf.keras.models.load_model(str(MODEL_PATH))

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
    predicted_index = int(np.argmax(predictions))
    confidence_score = float(np.max(predictions))

    if predicted_index >= len(class_names):
        raise HTTPException(status_code=500, detail="Model output does not match class labels")

    disease_name = class_names[predicted_index]

    if confidence_score > 0.8:
        confidence_label = "High"
    elif confidence_score > 0.5:
        confidence_label = "Medium"
    else:
        confidence_label = "Low"

    return {
        "disease": disease_name,
        "confidence": confidence_label,
        "severity": "Medium",
        "treatment": "Neem Oil",
    }
