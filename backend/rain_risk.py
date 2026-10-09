import logging
import pickle
from functools import lru_cache
from pathlib import Path
from typing import Sequence

import joblib
import pandas as pd
from fastapi import HTTPException


logger = logging.getLogger(__name__)
MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "sahana"
    / "models"
    / "heavy_rain_model.pkl"
)
HEAVY_RAIN_THRESHOLD = 0.30


@lru_cache(maxsize=1)
def _load_model():
    if not MODEL_PATH.is_file():
        raise HTTPException(
            status_code=503,
            detail="The heavy-rain prediction model is not available.",
        )

    try:
        return joblib.load(MODEL_PATH)
    except (
        AttributeError,
        EOFError,
        ImportError,
        OSError,
        pickle.UnpicklingError,
        ValueError,
    ) as error:
        logger.exception("Could not load the heavy-rain prediction model")
        raise HTTPException(
            status_code=503,
            detail="The heavy-rain prediction model could not be loaded.",
        ) from error


def estimate_heavy_rain(
    temperature: float,
    humidity: float,
    cloud_cover: float,
    wind_speed: float,
    previous_rain: float,
    month: int,
    hour: int,
) -> dict[str, object]:
    model = _load_model()
    features = pd.DataFrame(
        [
            {
                "temperature_2m": temperature,
                "relative_humidity_2m": humidity,
                "cloud_cover": cloud_cover,
                "wind_speed_10m": wind_speed,
                "previous_rain": previous_rain,
                "month": month,
                "hour": hour,
            }
        ]
    )

    try:
        classes: Sequence[int] = model.classes_
        probability = float(
            model.predict_proba(features)[0][list(classes).index(1)]
        )
    except (AttributeError, IndexError, TypeError, ValueError) as error:
        logger.exception("Heavy-rain model prediction failed")
        raise HTTPException(
            status_code=503,
            detail="The heavy-rain prediction model could not make a prediction.",
        ) from error

    return {
        "heavy_rain_probability": round(probability, 2),
        "risk": "High" if probability >= HEAVY_RAIN_THRESHOLD else "Low",
        "threshold": HEAVY_RAIN_THRESHOLD,
        "target": "Rain amount >= 5 mm in the model's training data.",
        "meaning": (
            "Estimated current heavy-rain risk. The classifier score is not a "
            "calibrated probability or a future forecast."
        ),
    }
