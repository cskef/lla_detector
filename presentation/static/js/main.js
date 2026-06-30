"use strict";

/* ── Références DOM ── */
const fileInput       = document.getElementById("fileInput");
const dropZone        = document.getElementById("dropZone");
const previewBlock    = document.getElementById("previewBlock");
const previewImg      = document.getElementById("previewImg");
const previewMeta     = document.getElementById("previewMeta");
const analyzeBtn      = document.getElementById("analyzeBtn");
const analyzeSpinner  = document.getElementById("analyzeSpinner");
const resetBtn        = document.getElementById("resetBtn");
const newAnalysisBtn  = document.getElementById("newAnalysisBtn");

const resultCard      = document.getElementById("resultCard");
const resultBadge     = document.getElementById("resultBadge");
const confidenceFill  = document.getElementById("confidenceFill");
const confidenceValue = document.getElementById("confidenceValue");
const resultMeta      = document.getElementById("resultMeta");
const exportBtn       = document.getElementById("exportBtn");

const gradcamPlaceholder = document.getElementById("gradcamPlaceholder");
const gradcamResult      = document.getElementById("gradcamResult");
const gradcamImg         = document.getElementById("gradcamImg");

const batchInput       = document.getElementById("batchInput");
const batchCount       = document.getElementById("batchCount");
const batchAnalyzeBtn  = document.getElementById("batchAnalyzeBtn");
const batchSpinner     = document.getElementById("batchSpinner");
const batchResults     = document.getElementById("batchResults");
const batchSummary     = document.getElementById("batchSummary");
const batchTableBody   = document.getElementById("batchTableBody");
const batchExportBtn   = document.getElementById("batchExportBtn");

const toast            = document.getElementById("toast");

/* ── État interne ─── */
let currentFile  = null;   // File sélectionné pour l'analyse individuelle
let toastTimeout = null;

/* ═════════════
   UTILITAIRES
   ═════════════ */

function showToast(message, isError = false) {
  clearTimeout(toastTimeout);
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("show");
  toastTimeout = setTimeout(() => toast.classList.remove("show"), 3500);
}

function formatBytes(bytes) {
  if (bytes < 1024)        return `${bytes} o`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
}

function setLoading(btn, spinner, loading) {
  btn.disabled = loading;
  spinner.hidden = !loading;
}

/* ════════════════════════════════════════
   IMPORT D'IMAGE — clic + glisser-déposer
   ════════════════════════════════════════ */

dropZone.addEventListener("click", () => fileInput.click());

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("drag-over");
});

["dragleave", "dragend"].forEach((ev) =>
  dropZone.addEventListener(ev, () => dropZone.classList.remove("drag-over"))
);

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) handleFileSelection(file);
});

fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) handleFileSelection(fileInput.files[0]);
});

async function handleFileSelection(file) {
  const allowed = ["image/jpeg", "image/png"];
  if (!allowed.includes(file.type)) {
    showToast("Format non supporté. Utilisez JPG ou PNG.", true);
    return;
  }

  currentFile = file;

  // Aperçu local immédiat (pas besoin d'attendre /upload)
  const objectUrl = URL.createObjectURL(file);
  previewImg.src = objectUrl;
  previewImg.onload = () => URL.revokeObjectURL(objectUrl);

  previewMeta.textContent = `${file.name} · ${formatBytes(file.size)}`;
  dropZone.hidden   = true;
  previewBlock.hidden = false;
  analyzeBtn.disabled = false;

  // Réinitialiser les résultats précédents
  resetResults();
}

/* ═════════════════════
   ANALYSE INDIVIDUELLE
   ═════════════════════ */

analyzeBtn.addEventListener("click", () => runAnalysis());

async function runAnalysis() {
  if (!currentFile) return;

  setLoading(analyzeBtn, analyzeSpinner, true);

  const fd = new FormData();
  fd.append("file", currentFile);

  try {
    const res  = await fetch("/analyze", { method: "POST", body: fd });
    const data = await res.json();

    if (!res.ok) {
      showToast(data.error || "Erreur serveur.", true);
      return;
    }

    displayResult(data);

  } catch (err) {
    showToast("Impossible de contacter le serveur.", true);
    console.error(err);
  } finally {
    setLoading(analyzeBtn, analyzeSpinner, false);
  }
}

function displayResult(data) {
  /* Badge de classification */
  const isBlaste = data.label.toLowerCase().includes("blaste") &&
                   !data.label.toLowerCase().includes("non");

  resultBadge.textContent = data.label;
  resultBadge.className   = "result-badge " + (isBlaste ? "blaste" : "saine");

  /* Barre de confiance */
  confidenceFill.style.width = `${data.confidence}%`;
  confidenceValue.textContent = `${data.confidence.toFixed(1)} %`;

  /* Méta-données */
  resultMeta.innerHTML = `
    <dt>Fichier analysé</dt><dd>${data.filename}</dd>
    <dt>Horodatage</dt><dd>${data.timestamp}</dd>
  `;

  /* Grad-CAM */
  if (data.heatmap) {
    gradcamImg.src = data.heatmap;
    gradcamPlaceholder.hidden = true;
    gradcamResult.hidden      = false;
  }

  /* Afficher la carte résultat */
  resultCard.hidden = false;
  resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });

  showToast("✓ Analyse terminée.");
}

/* ═════════════════════════
   EXPORT RAPPORT INDIVIDUEL
   ═════════════════════════ */

exportBtn.addEventListener("click", () => {
  window.location.href = "/export";
});

/* ═════════════════
   RÉINITIALISATION
   ════════════════ */

resetBtn.addEventListener("click", resetAll);
newAnalysisBtn.addEventListener("click", resetAll);

function resetAll() {
  currentFile = null;
  fileInput.value = "";

  dropZone.hidden     = false;
  previewBlock.hidden = true;
  analyzeBtn.disabled = true;

  resetResults();
}

function resetResults() {
  resultCard.hidden   = true;
  resultBadge.textContent = "—";
  resultBadge.className   = "result-badge";
  confidenceFill.style.width = "0%";
  confidenceValue.textContent = "0 %";
  resultMeta.innerHTML = "";

  gradcamPlaceholder.hidden = false;
  gradcamResult.hidden      = true;
  gradcamImg.src = "";
}

/* ═══════════════════
   TRAITEMENT PAR LOT
   ═══════════════════ */

batchInput.addEventListener("change", () => {
  const n = batchInput.files.length;
  if (n === 0) {
    batchCount.textContent = "";
    batchAnalyzeBtn.disabled = true;
    return;
  }
  batchCount.textContent   = `${n} fichier${n > 1 ? "s" : ""} sélectionné${n > 1 ? "s" : ""}`;
  batchAnalyzeBtn.disabled = false;
});

batchAnalyzeBtn.addEventListener("click", runBatchAnalysis);

async function runBatchAnalysis() {
  const files = batchInput.files;
  if (!files.length) return;

  setLoading(batchAnalyzeBtn, batchSpinner, true);
  batchResults.hidden = true;

  const fd = new FormData();
  for (const f of files) fd.append("files", f);

  try {
    const res  = await fetch("/batch", { method: "POST", body: fd });
    const data = await res.json();

    if (!res.ok) {
      showToast(data.error || "Erreur lors du lot.", true);
      return;
    }

    displayBatchResults(data);

  } catch (err) {
    showToast("Impossible de contacter le serveur.", true);
    console.error(err);
  } finally {
    setLoading(batchAnalyzeBtn, batchSpinner, false);
  }
}

function displayBatchResults(data) {
  const { processed, errors, results } = data;

  const nBlastes = results.filter(r =>
    r.label.toLowerCase().includes("blaste") &&
    !r.label.toLowerCase().includes("non")
  ).length;
  const nSaines = processed - nBlastes;

  batchSummary.textContent =
    `${processed} image${processed > 1 ? "s" : ""} analysée${processed > 1 ? "s" : ""} · ` +
    `${nSaines} saine${nSaines > 1 ? "s" : ""} · ${nBlastes} blaste${nBlastes > 1 ? "s" : ""} détecté${nBlastes > 1 ? "s" : ""}` +
    (errors ? ` · ${errors} erreur${errors > 1 ? "s" : ""}` : "");

  batchTableBody.innerHTML = results.map((r, i) => {
    const isB = r.label.toLowerCase().includes("blaste") && !r.label.toLowerCase().includes("non");
    return `<tr>
      <td>${i + 1}</td>
      <td>${r.filename}</td>
      <td><span class="${isB ? "badge-b" : "badge-s"}">${r.label}</span></td>
      <td>${r.confidence.toFixed(1)} %</td>
    </tr>`;
  }).join("");

  batchResults.hidden = false;
  showToast(`✓ Lot de ${processed} image${processed > 1 ? "s" : ""} analysé.`);
}

batchExportBtn.addEventListener("click", () => {
  window.location.href = "/export";
});
