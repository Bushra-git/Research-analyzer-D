"""Similarity matching helpers used by both:
- analysis_tasks.py (RQ async /analyze path)
- app.py (sync /predict path)

Goal: isolate TF-IDF + cosine similarity logic so it can be tested and reused.

The core improvements over the previous implementation:
- Use a richer TF-IDF corpus per venue: Source Title + Subject_Tags
- Pre-filter candidates by the paper's detected domain before ranking
- Fallback to full-set ranking if the filtered candidate set is too small

No Flask/IO side effects: pure functions only.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# NOTE: sklearn imports can fail in some binary-incompatible environments.
# Callers expect compute_similar_papers() to be best-effort (they already wrap
# in try/except). We keep this module simple and let ImportError surface.


from domain_detection import DOMAIN_KEYWORDS_SIMPLE


_PRECISION_MAP: Dict[str, str] = {
    "Computer Science & AI": "1700\nComputer Science",
    "Biomedical & Medicine": "2700\nMedicine",
    "Engineering": "2200\nEngineering",
    "Environmental Science": "2300\nEnvironmental Science",
    "Social Sciences": "3300\nSocial Sciences",
}


def _count_domain_keyword_hits(text_lower: str) -> Dict[str, int]:
    domain_scores: Dict[str, int] = {}
    for domain, keywords in DOMAIN_KEYWORDS_SIMPLE.items():
        total = 0
        for keyword in keywords:
            kw = (keyword or "").lower().strip()
            if not kw:
                continue
            # Word-boundary match; mirrors domain_detection behavior.
            pattern = r"\b" + re.escape(kw) + r"\b"
            total += len(re.findall(pattern, text_lower, flags=re.IGNORECASE))
        if total > 0:
            domain_scores[domain] = total
    return domain_scores


def detect_domain_for_filtering(text: str) -> str:
    """Detect domain label using keyword hits (same family as domain_detection)."""
    text_lower = (text or "").lower()
    domain_scores = _count_domain_keyword_hits(text_lower)
    return max(domain_scores, key=domain_scores.get) if domain_scores else "General Research"


def _candidate_indices_for_domain(dataset: pd.DataFrame, detected_domain: str) -> List[int]:
    """Return indices (into dataset) to consider before similarity ranking."""
    if dataset is None or getattr(dataset, "empty", True):
        return []

    if detected_domain in _PRECISION_MAP:
        col = _PRECISION_MAP[detected_domain]
        if col in dataset.columns:
            # Domain indicator columns are sparse; non-null means presence.
            return dataset.index[dataset[col].notna()].tolist()
        return []

    if detected_domain == "General Research":
        if "Subject_Tags" in dataset.columns:
            s = dataset["Subject_Tags"].fillna("").astype(str)
            return dataset.index[s.eq("General")].tolist()
        return []

    if detected_domain == "Chemistry":
        # Chemistry tag root isn't present as a clean indicator; reuse conservative estimate
        # from prior logic: search for the biochemistry subject indicator root.
        if "Subject_Tags" in dataset.columns:
            s = dataset["Subject_Tags"].fillna("").astype(str)
            needle = "1300\nBiochemistry, Genetics and Molecular Biology"
            return dataset.index[s.str.contains(needle, case=False, regex=False)].tolist()
        return []

    # Physics/Materials, Mathematics, Economics & Business: no supported root indicator => no prefilter
    return []


def _build_venue_corpus(dataset: pd.DataFrame, venue_indices: Optional[Sequence[int]] = None) -> List[str]:
    if dataset is None or getattr(dataset, "empty", True):
        return []

    if venue_indices is None:
        df = dataset
    else:
        df = dataset.loc[list(venue_indices)]

    title_col = "Source Title" if "Source Title" in df.columns else "title"

    titles = df.get(title_col, pd.Series(dtype=object)).fillna("").astype(str)
    subject_tags = df.get("Subject_Tags", pd.Series(dtype=object)).fillna("").astype(str)

    # Key change: concatenate topical vocabulary from Subject_Tags.
    return (titles + " " + subject_tags).tolist()


# --- Import-time precomputation (vectorizer + tfidf_matrix) ---
# This is intentionally best-effort: in binary-incompatible environments,
# compute_similar_papers() will fall back to returning an empty list.

_VECTORIZER = None
_TFIDF_MATRIX = None
_VENUE_INDEX = None  # list of dataset indices aligned to tfidf_matrix rows
_TITLE_COL_FALLBACK = "Source Title"


def _safe_build_precomputed(dataset: pd.DataFrame) -> None:
    global _VECTORIZER, _TFIDF_MATRIX, _VENUE_INDEX

    if dataset is None or getattr(dataset, "empty", True):
        _VECTORIZER = None
        _TFIDF_MATRIX = None
        _VENUE_INDEX = None
        return

    # Use full venue corpus (Source Title + Subject_Tags) once.
    _V = dataset
    title_col = "Source Title" if "Source Title" in _V.columns else "title"
    venue_corpus = _build_venue_corpus(_V, venue_indices=None)

    if not venue_corpus:
        _VECTORIZER = None
        _TFIDF_MATRIX = None
        _VENUE_INDEX = None
        return

    _VENUE_INDEX = _V.index.tolist()

    # Fit once.
    _VECTORIZER = TfidfVectorizer(max_features=500)
    _TFIDF_MATRIX = _VECTORIZER.fit_transform(venue_corpus)


# Module-level precompute happens on import. The dataset rows are loaded by
# callers; here we only know how to build corpus once we receive a dataset.
# We therefore precompute lazily on first successful call to compute_similar_papers.


def compute_similar_papers(
    paper_text: str,
    dataset: pd.DataFrame,
    detected_domain: Optional[str] = None,
    top_k: int = 5,
    prefilter_threshold: int = 20,
) -> List[Dict[str, Any]]:

    """Compute top-K similar venues/papers using TF-IDF + cosine similarity.
    Returns list of dicts: {title, score}
    """
    
    if dataset is None or getattr(dataset, "empty", True):
        return []
    if not paper_text:
        return []

    if detected_domain is None:
        detected_domain = detect_domain_for_filtering(paper_text)

    # Candidate prefilter
    candidate_indices = _candidate_indices_for_domain(dataset, detected_domain)
    used_full_set = False

    if len(candidate_indices) >= prefilter_threshold:
        venue_df = dataset.loc[candidate_indices]
        candidate_indices = venue_df.index.tolist()
    else:
        venue_df = dataset
        used_full_set = True
        candidate_indices = venue_df.index.tolist()

    # --- Precomputed similarity (NO per-request refit) ---
    # Ensure precomputed structures exist for this dataset.
    global _VECTORIZER, _TFIDF_MATRIX, _VENUE_INDEX
    if _VECTORIZER is None or _TFIDF_MATRIX is None or _VENUE_INDEX is None:
        _safe_build_precomputed(dataset)

    if _VECTORIZER is None or _TFIDF_MATRIX is None or _VENUE_INDEX is None:
        return []

    title_col = "Source Title" if "Source Title" in dataset.columns else "title"

    # Domain filtering as post-hoc mask on already-computed similarity scores.
    # Build mask aligned to _VENUE_INDEX rows.
    candidate_set = set(candidate_indices)
    mask = [idx in candidate_set for idx in _VENUE_INDEX]
    if not any(mask):
        return []

    # Transform only the query/paper.
    query_vec = _VECTORIZER.transform([paper_text])

    # Similarities against full venue matrix.
    # cosine_similarity(query_vec, tfidf_matrix) returns shape (1, n_venues)
    scores_vec = cosine_similarity(query_vec, _TFIDF_MATRIX)[0]

    # Apply mask by setting disallowed scores to -inf.
    import math
    for i, allowed in enumerate(mask):
        if not allowed:
            scores_vec[i] = -math.inf

    ranked_positions = scores_vec.argsort()[-top_k:][::-1]

    results: List[Dict[str, Any]] = []
    for pos in ranked_positions:
        if not math.isfinite(scores_vec[pos]):
            continue
        venue_idx = _VENUE_INDEX[pos]
        title = str(dataset.loc[venue_idx][title_col])
        results.append({"title": title[:100], "score": float(scores_vec[pos])})
        if len(results) >= top_k:
            break

    for r in results:
        r["_used_full_set"] = used_full_set

    return results


