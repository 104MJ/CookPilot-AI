"""Detection d'ingredients dans une image via YOLOv8 fine-tune (local)."""

import logging
from pathlib import Path

from django.conf import settings
from ultralytics import YOLO

logger = logging.getLogger("ai_engine")

MODEL_PATH = Path(settings.BASE_DIR) / "ai_engine" / "ml_models" / "ingredients_yolov8n.pt"

_model = None  # cache : charge le modele une seule fois par process


def _get_model():
    """Charge le modele YOLOv8 (une seule fois)."""
    global _model
    if _model is None:
        logger.info("Chargement du modele YOLOv8 : %s", MODEL_PATH)
        _model = YOLO(str(MODEL_PATH))
    return _model


def detect_ingredients(image_path, confidence=0.2):
    """
    Detecte les ingredients presents sur une image.

    image_path : chemin vers l'image (frigo/placard)
    confidence : seuil minimum de confiance

    Retourne une liste triee de noms d'ingredients detectes (uniques).
    """
    model = _get_model()
    results = model.predict(source=image_path, conf=confidence, verbose=False)

    names = results[0].names
    detected = set()
    for box in results[0].boxes:
        class_id = int(box.cls[0])
        detected.add(names[class_id])

    return sorted(detected)
