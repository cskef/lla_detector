import io
import unittest
from pathlib import Path
from unittest import mock

from controllers.routes import _allowed_file, create_app
from services.classification.classification_result import ClassificationResult
from services.preprocessing.preprocessing_service import PreprocessingService


class TestClassificationResult(unittest.TestCase):
    def test_label_and_to_dict(self):
        result = ClassificationResult(
            class_index=1,
            confidence=87.5,
            filename="sample.png",
            timestamp="2026-07-01T02:30:00",
        )

        self.assertEqual(result.label, "Cellule leucémique (blaste)")
        self.assertEqual(
            result.to_dict(),
            {
                "label": "Cellule leucémique (blaste)",
                "confidence": 87.5,
                "class_index": 1,
                "filename": "sample.png",
                "timestamp": "2026-07-01T02:30:00",
            },
        )

    def test_unknown_label(self):
        result = ClassificationResult(class_index=99, confidence=12.0)
        self.assertEqual(result.label, "Inconnu")


class TestAllowedFile(unittest.TestCase):
    def test_allowed_extensions(self):
        self.assertTrue(_allowed_file("image.jpg"))
        self.assertTrue(_allowed_file("image.jpeg"))
        self.assertTrue(_allowed_file("image.png"))

    def test_disallowed_extensions(self):
        self.assertFalse(_allowed_file("image.gif"))
        self.assertFalse(_allowed_file("image"))
        self.assertFalse(_allowed_file("image.txt"))


class TestPreprocessingService(unittest.TestCase):
    def setUp(self):
        self.service = PreprocessingService()
        self.sample_image = Path(__file__).with_name("cellule_S.png")

    def test_preprocess_shape_and_range(self):
        image_bytes = self.sample_image.read_bytes()
        tensor = self.service.preprocess(image_bytes)

        self.assertEqual(tensor.shape, (1, 224, 224, 3))
        self.assertEqual(tensor.dtype.name, "float32")
        self.assertGreaterEqual(float(tensor.min()), 0.0)
        self.assertLessEqual(float(tensor.max()), 1.0)

    def test_decode_invalid_bytes_raises(self):
        with self.assertRaises(ValueError):
            self.service.preprocess(b"not-an-image")


class TestFlaskRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class DummyClassificationService:
            def __init__(self, model_path=None):
                self.model = None

            def predict(self, tensor):
                return ClassificationResult(class_index=0, confidence=72.0)

        class DummyGradCAMService:
            def __init__(self, model=None):
                self.model = model

            def generate(self, tensor, class_idx):
                return "data:image/png;base64,dummy"

        class DummyExportService:
            def generate_report(self, results, warning):
                return b"<html><body>dummy</body></html>"

        patches = [
            mock.patch("controllers.routes.ClassificationService", DummyClassificationService),
            mock.patch("controllers.routes.GradCAMService", DummyGradCAMService),
            mock.patch("controllers.routes.ExportService", DummyExportService),
        ]
        cls._patchers = patches
        for patcher in cls._patchers:
            patcher.start()

        cls.app = create_app()
        cls.app.testing = True
        cls.client = cls.app.test_client()
        cls.sample_image = Path(__file__).with_name("cellule_S.png")

    @classmethod
    def tearDownClass(cls):
        for patcher in getattr(cls, "_patchers", []):
            patcher.stop()

    def test_index_route(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"LLA Detector", response.data)

    def test_upload_route_success(self):
        data = {
            "file": (io.BytesIO(self.sample_image.read_bytes()), "cellule_S.png"),
        }
        response = self.client.post("/upload", data=data, content_type="multipart/form-data")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("preview", payload)
        self.assertEqual(payload["filename"], "cellule_S.png")

    def test_upload_route_rejects_invalid_extension(self):
        data = {
            "file": (io.BytesIO(b"fake"), "bad.gif"),
        }
        response = self.client.post("/upload", data=data, content_type="multipart/form-data")

        self.assertEqual(response.status_code, 415)
        payload = response.get_json()
        self.assertEqual(payload["error"], "Format non supporté. Utilisez JPG ou PNG.")

    def test_analyze_route_success(self):
        data = {
            "file": (io.BytesIO(self.sample_image.read_bytes()), "cellule_S.png"),
        }
        response = self.client.post("/analyze", data=data, content_type="multipart/form-data")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn(payload["label"], {"Cellule saine (non-blaste)", "Cellule leucémique (blaste)"})
        self.assertIn("confidence", payload)
        self.assertIn("heatmap", payload)
        self.assertIn("warning", payload)

    def test_analyze_route_requires_file(self):
        response = self.client.post("/analyze", data={}, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertEqual(payload["error"], "Aucune image soumise.")


if __name__ == "__main__":
    unittest.main()
