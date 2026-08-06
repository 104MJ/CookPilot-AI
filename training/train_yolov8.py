"""
Fine-tune un modele yolov8n sur le dataset d'ingredients telecharge via
download_dataset.py. Prevu pour tourner sur Google Colab (GPU gratuit) ou
toute machine disposant d'un GPU.

Usage :
    python train_yolov8.py --data dataset/data.yaml --epochs 30
"""

import argparse

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
    args = parser.parse_args()

    model = YOLO(args.base_model)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project="runs_ingredients",
        name="yolov8n_ingredients",
    )

    print(
        "Entrainement termine. Poids a recuperer dans : "
        "runs_ingredients/yolov8n_ingredients/weights/best.pt"
    )


if __name__ == "__main__":
    main()
