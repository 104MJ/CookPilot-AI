"""
Telecharge le dataset "Ingredients detection YoloV8" (Roboflow Universe,
licence CC BY 4.0) au format YOLOv8, en vue de fine-tuner un yolov8n local
pour detect_ingredients() (backend/ai_engine/vision.py).

Usage :
    ROBOFLOW_API_KEY=xxxx python download_dataset.py

Cle API gratuite (compte personnel) : https://app.roboflow.com/settings/api
Dataset source : https://universe.roboflow.com/visual-captioning-for-food/ingredients-detection-yolov8-npkkb
"""

import os
import sys

from roboflow import Roboflow

WORKSPACE = "visual-captioning-for-food"
PROJECT = "ingredients-detection-yolov8-npkkb"
VERSION = 5
OUTPUT_DIR = "dataset"


def main():
    api_key = os.environ.get("ROBOFLOW_API_KEY")
    if not api_key:
        sys.exit(
            "Erreur : variable d'environnement ROBOFLOW_API_KEY manquante.\n"
            "Recupere une cle gratuite sur https://app.roboflow.com/settings/api"
        )

    rf = Roboflow(api_key=api_key)
    project = rf.workspace(WORKSPACE).project(PROJECT)
    dataset = project.version(VERSION).download("yolov8", location=OUTPUT_DIR)

    print(f"Dataset telecharge dans : {dataset.location}")
    print(
        "Fichier de config pour l'entrainement : "
        f"{os.path.join(dataset.location, 'data.yaml')}"
    )


if __name__ == "__main__":
    main()
