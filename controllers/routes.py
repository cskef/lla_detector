
import os
import io
import base64
import json
import uuid
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file,
    session,
)

from services.preprocessing.preprocessing_service import PreprocessingService
from services.classification.classification_service import ClassificationService
from services.explicabilite.grad_cam_service import GradCAMService
from services.export.export_service import ExportService

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024       
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "model", "model.h5")
ETHICAL_WARNING = (
    "Ce résultat est une aide à la décision et NON un diagnostic médical certifié. "
    "Consultez impérativement un professionnel de santé qualifié."
)


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def create_app() -> Flask:

    base_dir = os.path.dirname(__file__)
    template_dir = os.path.abspath(os.path.join(base_dir, "..", "presentation", "templates"))
    static_dir   = os.path.abspath(os.path.join(base_dir, "..", "presentation", "static"))

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.secret_key = os.urandom(24)
    app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

    # ── Chargement unique des services au démarrage ─
    preprocessing_svc   = PreprocessingService()
    classification_svc  = ClassificationService(model_path=MODEL_PATH)
    grad_cam_svc        = GradCAMService(model=classification_svc.model)
    export_svc          = ExportService()

    # ── Stockage de session en mémoire (pas de BDD, exigence BNF06) ──
    _session_results: list = [] 


    # GET  /

    @app.route("/", methods=["GET"])
    def index():
        _session_results.clear()
        return render_template("index.html", warning=ETHICAL_WARNING)


    # POST /upload  — Validation + aperçu base64

    @app.route("/upload", methods=["POST"])
    def upload():
        if "file" not in request.files:
            return jsonify({"error": "Aucun fichier reçu."}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "Nom de fichier vide."}), 400

        if not _allowed_file(file.filename):
            return jsonify({"error": "Format non supporté. Utilisez JPG ou PNG."}), 415

        image_bytes = file.read()
        if len(image_bytes) == 0:
            return jsonify({"error": "Fichier vide ou illisible."}), 400

        # Aperçu encodé en base64 pour affichage immédiat dans le navigateur
        preview_b64 = base64.b64encode(image_bytes).decode("utf-8")
        ext = file.filename.rsplit(".", 1)[1].lower()
        mime = "image/jpeg" if ext in {"jpg", "jpeg"} else "image/png"

        return jsonify({
            "preview": f"data:{mime};base64,{preview_b64}",
            "filename": file.filename,
            "size_kb": round(len(image_bytes) / 1024, 1),
        }), 200

    # ────────────────────────────────────────────────────────────────────────
    # POST /analyze  — Pipeline complet
    # ────────────────────────────────────────────────────────────────────────
    @app.route("/analyze", methods=["POST"])
    def analyze():
        if "file" not in request.files:
            return jsonify({"error": "Aucune image soumise."}), 400

        file = request.files["file"]

        if not _allowed_file(file.filename):
            return jsonify({"error": "Format non supporté."}), 415

        image_bytes = file.read()
        if len(image_bytes) == 0:
            return jsonify({"error": "Fichier vide ou illisible."}), 400

        try:
            # 1. Prétraitement
            tensor = preprocessing_svc.preprocess(image_bytes)

            # 2. Classification
            result = classification_svc.predict(tensor)

            # 3. Grad-CAM
            heatmap_b64 = grad_cam_svc.generate(tensor, class_idx=result.class_index)

            # 4. Mémorisation pour export éventuel
            result.filename  = file.filename
            result.timestamp = datetime.now().isoformat(timespec="seconds")
            _session_results.append(result)

            return jsonify({
                "label":      result.label,
                "confidence": result.confidence,
                "heatmap":    heatmap_b64,
                "warning":    ETHICAL_WARNING,
                "filename":   file.filename,
                "timestamp":  result.timestamp,
            }), 200

        except Exception as exc:         # noqa: BLE001
            return jsonify({"error": f"Erreur interne du pipeline : {exc}"}), 500

    # ────────────────────────────────────────────────────────────────────────
    # GET  /export  — Rapport de synthèse (optionnel, BF06)
    # ────────────────────────────────────────────────────────────────────────
    @app.route("/export", methods=["GET"])
    def export():
        if not _session_results:
            return jsonify({"error": "Aucun résultat à exporter."}), 404

        report_bytes = export_svc.generate_report(
            results=_session_results,
            warning=ETHICAL_WARNING,
        )

        return send_file(
            io.BytesIO(report_bytes),
            mimetype="text/html",
            as_attachment=True,
            download_name=f"rapport_LLA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
        )

    # ────────────────────────────────────────────────────
    # POST /batch  — Traitement par lot (optionnel, BF06) | 
    # ────────────────────────────────────────────────────
    @app.route("/batch", methods=["POST"])
    def batch():
        files = request.files.getlist("files")
        if not files:
            return jsonify({"error": "Aucun fichier reçu."}), 400

        batch_results = []
        errors        = []

        for f in files:
            if not _allowed_file(f.filename):
                errors.append({"filename": f.filename, "error": "Format non supporté."})
                continue

            image_bytes = f.read()
            if len(image_bytes) == 0:
                errors.append({"filename": f.filename, "error": "Fichier vide."})
                continue

            try:
                tensor  = preprocessing_svc.preprocess(image_bytes)
                result  = classification_svc.predict(tensor)
                result.filename  = f.filename
                result.timestamp = datetime.now().isoformat(timespec="seconds")
                _session_results.append(result)
                batch_results.append({
                    "filename":   result.filename,
                    "label":      result.label,
                    "confidence": result.confidence,
                    "timestamp":  result.timestamp,
                })
            except Exception as exc:    # noqa: BLE001
                errors.append({"filename": f.filename, "error": str(exc)})

        return jsonify({
            "processed": len(batch_results),
            "errors":    len(errors),
            "results":   batch_results,
            "error_details": errors,
            "warning":   ETHICAL_WARNING,
        }), 200

    return app
