# Fine-tuning YOLOv8 — detection d'ingredients

Ce dossier contient les scripts pour entrainer le modele de vision utilise par
`detect_ingredients()` (voir `backend/ai_engine/vision.py`, a venir). Ce n'est
**pas** execute par l'application en production — c'est une etape ponctuelle
(realisee une fois, ou de temps en temps pour ameliorer le modele), dont le
resultat (`best.pt`) est ensuite embarque dans le backend.

## Dataset

[Ingredients detection YoloV8](https://universe.roboflow.com/visual-captioning-for-food/ingredients-detection-yolov8-npkkb)
— 112 classes alimentaires (lait, oeuf, fromage, riz, oignon, poivron,
crevette...), 46 674 images, licence **CC BY 4.0** (attribution obligatoire,
a mentionner dans le README principal du projet).

## Etapes

1. Creer un compte Roboflow gratuit et recuperer une cle API :
   https://app.roboflow.com/settings/api

2. Installer les dependances (en local ou sur Google Colab) :

   ```bash
   pip install -r requirements.txt
   ```

3. Telecharger le dataset :

   ```bash
   ROBOFLOW_API_KEY=xxxx python download_dataset.py
   ```

4. Lancer l'entrainement (idealement sur Google Colab avec GPU gratuit —
   environ 30 a 60 minutes pour 30 epochs sur yolov8n) :

   ```bash
   python train_yolov8.py --data dataset/data.yaml --epochs 30
   ```

5. Recuperer le fichier `runs_ingredients/yolov8n_ingredients/weights/best.pt`
   et le copier dans `backend/ai_engine/ml_models/ingredients_yolov8n.pt`
   (dossier a creer ; le fichier fait quelques Mo, acceptable en commit
   direct pour un MVP).

6. Prevenir Membre 1 (backend) une fois le fichier pret, pour finaliser
   `detect_ingredients()`.
