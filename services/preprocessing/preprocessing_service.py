
import numpy as np
import cv2


class PreprocessingService:
    #Transforme des bytes d'image en tenseur prêt pour l'inférence.

    TARGET_SIZE: tuple[int, int] = (224, 224)

    def __init__(self, apply_clahe: bool = True) -> None:
    
        self._apply_clahe = apply_clahe

        # Pré-instanciation du processeur CLAHE 
        self._clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    # ── API publique ───

    def preprocess(self, image_bytes: bytes) -> np.ndarray:
     
        img = self._decode(image_bytes)
        img = self._resize(img)

        if self._apply_clahe:
            img = self._enhance_contrast(img)

        img = self._normalize(img)
        return img[np.newaxis, ...]          # (H, W, 3) → (1, H, W, 3)

    # ── Méthodes internes ─────

    def _decode(self, image_bytes: bytes) -> np.ndarray:
        """Décode les bytes en tableau NumPy RGB uint8."""
        buf = np.frombuffer(image_bytes, dtype=np.uint8)
        img_bgr = cv2.imdecode(buf, cv2.IMREAD_COLOR)

        if img_bgr is None:
            raise ValueError(
                "Impossible de décoder l'image. "
                "Vérifiez que le fichier est un JPG ou PNG valide et non corrompu."
            )

        # OpenCV charge en BGR → conversion en RGB
        return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    def _resize(self, img: np.ndarray) -> np.ndarray:
        """Redimensionne l'image à TARGET_SIZE avec interpolation bilinéaire."""
        return cv2.resize(img, self.TARGET_SIZE, interpolation=cv2.INTER_LINEAR)

    def _enhance_contrast(self, img: np.ndarray) -> np.ndarray:
        """
        Applique CLAHE sur le canal L de l'espace LAB.
        Améliore la lisibilité des structures cellulaires sans saturer les couleurs.
        """
        lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        l_enhanced = self._clahe.apply(l_channel)
        lab_enhanced = cv2.merge([l_enhanced, a_channel, b_channel])
        return cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2RGB)

    def _normalize(self, img: np.ndarray) -> np.ndarray:
        """Normalise les valeurs uint8 [0, 255] en float32 [0, 1]."""
        return img.astype(np.float32) / 255.0
