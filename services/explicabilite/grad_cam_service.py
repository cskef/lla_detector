import base64
import io
import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)

DENSENET121_LAST_CONV = "conv5_block16_concat"
MOBILENET_LAST_CONV   = "Conv_1"


class GradCAMService:
    #Génère des cartes Grad-CAM superposées à l'image originale.

    def __init__(self, model, last_conv_layer_name: str = DENSENET121_LAST_CONV) -> None:
        
        self.model               = model
        self.last_conv_layer_name = last_conv_layer_name
        self._stub_mode          = model is None

        if not self._stub_mode:
            self._build_grad_model()

    # ── Construction du modèle de gradient ───

    def _build_grad_model(self) -> None:
        
        try:
            import tensorflow as tf
            last_conv_layer = self.model.get_layer(self.last_conv_layer_name)
            self._grad_model = tf.keras.models.Model(
                inputs=self.model.inputs,
                outputs=[last_conv_layer.output, self.model.output],
            )
            logger.info("Grad-CAM : modèle de gradient construit sur la couche '%s'.",
                        self.last_conv_layer_name)
        except Exception as exc:
            logger.error("Impossible de construire le modèle Grad-CAM : %s", exc)
            self._stub_mode = True

    # ── API publique ───

    def generate(self, tensor: np.ndarray, class_idx: int) -> str:
        
        if self._stub_mode:
            return self._stub_heatmap(tensor)

        try:
            return self._compute_gradcam(tensor, class_idx)
        except Exception as exc:
            logger.error("Erreur Grad-CAM : %s — fallback stub.", exc)
            return self._stub_heatmap(tensor)

    # ── Calcul Grad-CAM ───

    def _compute_gradcam(self, tensor: np.ndarray, class_idx: int) -> str:
        import tensorflow as tf

        with tf.GradientTape() as tape:
            conv_outputs, predictions = self._grad_model(tensor)
            loss = predictions[:, class_idx]

        # Gradients du score par rapport aux activations conv
        grads     = tape.gradient(loss, conv_outputs)          # (1, H', W', C)
        pooled    = tf.reduce_mean(grads, axis=(0, 1, 2))      # (C,)  — global avg pool

        conv_outputs = conv_outputs[0]                         # (H', W', C)
        cam = tf.reduce_sum(tf.multiply(pooled, conv_outputs), axis=-1)  # (H', W')

        # ReLU + normalisation
        cam = np.maximum(cam.numpy(), 0)
        cam_max = cam.max()
        if cam_max > 0:
            cam = cam / cam_max

        return self._overlay(tensor, cam)

    # ── Superposition visuelle ──

    def _overlay(self, tensor: np.ndarray, cam: np.ndarray) -> str:
        """Superpose la heatmap colorisée à l'image originale et encode en base64."""
        # Image originale reconstruite depuis le tenseur normalisé
        img_rgb = (tensor[0] * 255).astype(np.uint8)
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

        # Redimensionnement de la CAM à la taille de l'image
        h, w = img_bgr.shape[:2]
        cam_resized = cv2.resize(cam, (w, h), interpolation=cv2.INTER_LINEAR)

        # Colorisation en palette thermique (COLORMAP_JET)
        cam_uint8   = np.uint8(255 * cam_resized)
        heatmap_bgr = cv2.applyColorMap(cam_uint8, cv2.COLORMAP_JET)

        # Superposition pondérée (40 % heatmap, 60 % image)
        overlay = cv2.addWeighted(heatmap_bgr, 0.4, img_bgr, 0.6, 0)

        return self._encode_png_b64(overlay)

    # ── Stub ────

    def _stub_heatmap(self, tensor: np.ndarray) -> str:
        """Retourne l'image originale sans heatmap (mode développement)."""
        img_rgb = (tensor[0] * 255).astype(np.uint8)
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        return self._encode_png_b64(img_bgr)

    # ── Utilitaire ──

    @staticmethod
    def _encode_png_b64(img_bgr: np.ndarray) -> str:
        """Encode une image OpenCV BGR en URI base64 PNG."""
        success, buf = cv2.imencode(".png", img_bgr)
        if not success:
            raise RuntimeError("Échec de l'encodage PNG de la heatmap.")
        b64 = base64.b64encode(buf.tobytes()).decode("utf-8")
        return f"data:image/png;base64,{b64}"
