import os
import re
import sys

# Ensure repo root is on sys.path so `analysis_tasks.py` can be imported
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import analysis_tasks
from domain_detection import get_domain_stats


# Keep legacy scoring function for backwards comparison. (The debug endpoint isn’t used in production.)




EXCERPT = (
    "Effect of Mechanochemically Synthesized Copper (II) and Silver (I) Complexes with Cefuroxime on Some "
    "Cephalosporin Resistance Bacteria. This study investigates the synthesis and characterization of copper and "
    "silver metal complexes with cefuroxime, a cephalosporin antibiotic. The synthesized complexes were characterized "
    "using spectroscopic techniques including UV-Vis, IR, and elemental analysis. The antibacterial activity of the "
    "synthesized compounds was evaluated against cephalosporin-resistant bacterial strains."
)


def score_exact_phrase_boundaries(text: str):
    """Exact phrase matching using regex word boundaries around the whole keyword phrase."""

    t = (text or "").lower()
    scores = {}

    for domain, keywords in analysis_tasks.DOMAIN_KEYWORDS_SIMPLE.items():
        total = 0
        for kw in keywords:
            kw_l = kw.lower().strip()
            # Whole phrase boundaries: \bkeyword\b
            # Works for multi-word phrases because \b matches word boundary at start/end.
            pattern = r"\b" + re.escape(kw_l) + r"\b"
            total += len(re.findall(pattern, t, flags=re.IGNORECASE))
        if total > 0:
            scores[domain] = total

    return scores


def main():
    scores = score_exact_phrase_boundaries(EXCERPT)
    print("domain_scores(word-boundary exact phrases):")
    print(scores)
    print("\nChemistry:", scores.get("Chemistry", 0))
    print("Biomedical & Medicine:", scores.get("Biomedical & Medicine", 0))


if __name__ == "__main__":
    main()

