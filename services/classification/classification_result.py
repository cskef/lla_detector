from dataclasses import dataclass, field


LABELS = {
    0: "Cellule saine (non-blaste)",
    1: "Cellule leucémique (blaste)",
}


@dataclass
class ClassificationResult:
    # Résultat d'une classification binaire de cellule sanguine.

    class_index: int
    confidence: float          
    filename: str = ""
    timestamp: str = ""

    @property
    def label(self) -> str:
        return LABELS.get(self.class_index, "Inconnu")

    def to_dict(self) -> dict:
        return {
            "label":       self.label,
            "confidence":  self.confidence,
            "class_index": self.class_index,
            "filename":    self.filename,
            "timestamp":   self.timestamp,
        }
