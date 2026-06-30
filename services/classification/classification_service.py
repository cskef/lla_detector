import os
import logging
import numpy as np

from services.classification.classification_result import ClassificationResult

logger = logging.getLogger(__name__)


class ClassificationService:
    #Charge le modèle CNN et effectue l'inférence binaire.

    CLASS_NAMES = ["Cellule saine (non-blaste)", "Cellule leucémique (blaste)"]

    def __init__(self, model_path: str) -> None:
       
        self.model_path = model_path
        self.model      = None
        self._stub_mode = False

        self._load_model()

    # ── Chargement ───

    def _load_model(self) -> None:
        
        if not os.path.exists(self.model_path):
            logger.warning(
                "Fichier de poids introuvable : %s — Mode STUB activé.",
                self.model_path,
            )
            self._stub_mode = True
            return

        try:
            import tensorflow as tf
            self.model = tf.keras.models.load_model(self.model_path)
            logger.info("Modèle chargé avec succès depuis %s", self.model_path)
        except Exception as exc:
            logger.error("Échec du chargement du modèle : %s", exc)
            self._stub_mode = True

    # ── Inférence ────

    def predict(self, tensor: np.ndarray) -> ClassificationResult:
        
        if self._stub_mode:
            return self._stub_predict()

        # Passe avant — sortie softmax de forme (1, 2)
        predictions = self.model.predict(tensor, verbose=0)    # shape: (1, 2)
        probs       = predictions[0]                           # shape: (2,)

        class_idx  = int(np.argmax(probs))
        confidence = round(float(probs[class_idx]) * 100, 2)

        return ClassificationResult(
            class_index=class_idx,
            confidence=confidence,
        )

    def _stub_predict(self) -> ClassificationResult:
        """
        Retourne un résultat simulé déterministe pour le développement.
        Toujours index=0 (saine) avec 72.00 % de confiance.
        """
        logger.debug("Mode STUB — résultat simulé retourné.")
        return ClassificationResult(class_index=0, confidence=72.00)
