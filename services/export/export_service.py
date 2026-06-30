from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.classification.classification_result import ClassificationResult


class ExportService:

    def generate_report(
        self,
        results: list["ClassificationResult"],
        warning: str = "",
    ) -> bytes:
        
        n_total  = len(results)
        n_blaste = sum(1 for r in results if r.class_index == 1)
        n_saine  = n_total - n_blaste

        rows_html = "\n".join(self._build_row(i + 1, r) for i, r in enumerate(results))

        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Rapport LLA — {datetime.now().strftime('%d/%m/%Y %H:%M')}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', sans-serif; background: #f0f4f8; color: #1a1a2e; padding: 2rem; }}
    .header {{ background: #0f3460; color: white; padding: 2rem; border-radius: 12px; margin-bottom: 2rem; }}
    .header h1 {{ font-size: 1.6rem; font-weight: 700; }}
    .header p  {{ font-size: 0.9rem; opacity: 0.8; margin-top: 0.4rem; }}
    .warning-box {{
      background: #fff3cd; border-left: 5px solid #e67e22;
      padding: 1rem 1.5rem; border-radius: 8px; margin-bottom: 2rem;
      font-size: 0.88rem; font-weight: 600; color: #7d4e00;
    }}
    .stats {{ display: flex; gap: 1rem; margin-bottom: 2rem; }}
    .stat-card {{
      flex: 1; background: white; padding: 1.2rem; border-radius: 10px;
      box-shadow: 0 2px 8px rgba(0,0,0,.08); text-align: center;
    }}
    .stat-card .num {{ font-size: 2.2rem; font-weight: 800; }}
    .stat-card .lbl {{ font-size: 0.8rem; color: #666; text-transform: uppercase; letter-spacing: .05em; }}
    .num-total  {{ color: #0f3460; }}
    .num-saine  {{ color: #27ae60; }}
    .num-blaste {{ color: #e74c3c; }}
    table {{ width: 100%; border-collapse: collapse; background: white;
             border-radius: 10px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,.08); }}
    th {{ background: #0f3460; color: white; padding: .9rem 1rem; text-align: left;
          font-size: .82rem; text-transform: uppercase; letter-spacing: .06em; }}
    td {{ padding: .8rem 1rem; border-bottom: 1px solid #eef0f4; font-size: .88rem; }}
    tr:last-child td {{ border-bottom: none; }}
    .badge-saine  {{ background: #d5f5e3; color: #1e8449; padding: .2rem .7rem;
                     border-radius: 20px; font-weight: 600; font-size: .8rem; }}
    .badge-blaste {{ background: #fde8e8; color: #c0392b; padding: .2rem .7rem;
                     border-radius: 20px; font-weight: 600; font-size: .8rem; }}
    .footer {{ margin-top: 2rem; font-size: 0.78rem; color: #999; text-align: center; }}
    @media print {{ body {{ background: white; }} }}
  </style>
</head>
<body>
  <div class="header">
    <h1> Rapport de Synthèse — Détection LLA</h1>
    <p>Généré le {datetime.now().strftime('%d %B %Y à %H:%M:%S')} · ENSPY AIA4 — Génie Logiciel</p>
  </div>

  <div class="warning-box"> {warning}</div>

  <div class="stats">
    <div class="stat-card">
      <div class="num num-total">{n_total}</div>
      <div class="lbl">Images analysées</div>
    </div>
    <div class="stat-card">
      <div class="num num-saine">{n_saine}</div>
      <div class="lbl">Cellules saines</div>
    </div>
    <div class="stat-card">
      <div class="num num-blaste">{n_blaste}</div>
      <div class="lbl">Blastes détectés</div>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th>#</th>
        <th>Fichier</th>
        <th>Résultat</th>
        <th>Confiance</th>
        <th>Horodatage</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>

  <div class="footer">
    Application développée à des fins académiques — ENSPY Yaoundé · Filière AIA4<br>
    Ce rapport ne constitue pas un diagnostic médical certifié.
  </div>
</body>
</html>"""

        return html.encode("utf-8")

    # ── Helpers ────

    @staticmethod
    def _build_row(idx: int, result: "ClassificationResult") -> str:
        badge_class = "badge-blaste" if result.class_index == 1 else "badge-saine"
        return (
            f"<tr>"
            f"<td>{idx}</td>"
            f"<td>{result.filename or '—'}</td>"
            f"<td><span class='{badge_class}'>{result.label}</span></td>"
            f"<td>{result.confidence:.1f} %</td>"
            f"<td>{result.timestamp or '—'}</td>"
            f"</tr>"
        )
