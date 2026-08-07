"""
Fine-tune un modele yolov8n sur le dataset d'ingredients telecharge via
download_dataset.py. Prevu pour tourner sur Google Colab (GPU gratuit) ou
toute machine disposant d'un GPU.

Usage :
    python train_yolov8.py --data dataset/data.yaml --epochs 30
"""

import argparse

import torch
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data", default="dataset/data.yaml", help="Chemin vers data.yaml"
    )
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument(
        "--base-model", default="yolov8n.pt", help="Checkpoint de depart (COCO)"
    )
    parser.add_argument(
        "--device",
        default=None,
        help="0 pour GPU, cpu pour CPU. Par defaut : GPU si disponible, sinon CPU.",
    )
    args = parser.parse_args()

    device = args.device
    if device is None:
        device = 0 if torch.cuda.is_available() else "cpu"
    print(f"Utilisation du device : {device} (CUDA disponible : {torch.cuda.is_available()})")

    model = YOLO(args.base_model)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project="runs_ingredients",
        name="yolov8n_ingredients",
        device=device,
    )

    print(
        "Entrainement termine. Poids a recuperer dans : "
        "runs_ingredients/yolov8n_ingredients/weights/best.pt"
    )


if __name__ == "__main__":
    main()
