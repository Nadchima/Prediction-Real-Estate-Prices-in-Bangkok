from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Literal
import joblib
import pandas as pd
import os

# Configuration
MODEL_PATH = os.getenv("MODEL_PATH", "models/bkk_condo_prices-v1.pkl")

app = FastAPI(
    title="Bangkok Property Price Prediction API",
    version="1.0.0",
    description="Estimate Bangkok residential property prices from property characteristics."
)

# Enable CORS for browser clients. Restrict origins before production use.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the model at startup.
try:
    model = joblib.load(MODEL_PATH)
    print(f"Model loaded from {MODEL_PATH}")
except Exception as e:
    raise RuntimeError(f"Failed to load the prediction model: {e}")

# Input schema
class CondoInputData(BaseModel):
    area_sqft: float = Field(..., gt=0, le=20_000)
    no_bedroom: int = Field(..., ge=1, le=50)
    no_bathroom: int = Field(..., ge=1, le=50)
    property_type: Literal['Apartment', 'Condo', 'House']

# Health-check endpoint
@app.get("/health", summary="API health check")
def health_check():
    return {
        "status": "ok",
        "model_loaded": True,
        "model_path": MODEL_PATH,
    }

# Prediction endpoint
@app.post("/predict", summary="Predict a residential property price in THB")
def predict_price(data: CondoInputData):
    expected_columns = [
        "Area (sq. ft.)", "Bedrooms", "Bathrooms",
        "Type_Apartment", "Type_Condo", "Type_House"
    ]
    input_data = {
        "Area (sq. ft.)": data.area_sqft,
        "Bedrooms": data.no_bedroom,
        "Bathrooms": data.no_bathroom,
        "Type_Apartment": 0,
        "Type_Condo": 0,
        "Type_House": 0,
    }
    ohe_col = f"Type_{data.property_type}"
    if ohe_col in input_data:
        input_data[ohe_col] = 1

    input_df = pd.DataFrame([input_data], columns=expected_columns)

    try:
        prediction = model.predict(input_df)[0]
        return {
            "predicted_price_thb": max(0, round(prediction)),
            "message": f"Predicted price for a {data.property_type} of {data.area_sqft} sq.ft."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


# Register the catch-all static site after API routes so /health, /predict,
# and /docs remain reachable.
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")
