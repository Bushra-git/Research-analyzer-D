import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


# Centralized domain keyword mapping.
DOMAIN_KEYWORDS_SIMPLE: Dict[str, List[str]] = {
    "Computer Science & AI": [
        "machine learning",
        "ai",
        "artificial intelligence",
        "neural network",
        "deep learning",
        "algorithm",
        "database",
        "software",
        "blockchain",
        "cryptocurrency",
        "distributed ledger",
        "smart contract",
        "internet of things",
        "iot",
    ],
    "Biomedical & Medicine": [
        "medical",
        "clinical",
        "disease",
        "health",
        "patient",
        "treatment",
        "diagnosis",
        "drug",
        "therapy",
        "biomedical",
    ],
    "Physics & Materials": [
        "physics",
        "quantum",
        "particle",
        "material",
        "electromagnetic",
        "relativity",
    ],
    "Chemistry": [
        "chemistry",
        "chemical",
        "reaction",
        "molecule",
        "compound",
        "synthesis",
        "organic",
    ],
    "Engineering": [
        "engineering",
        "mechanical",
        "electrical",
        "civil",
        "infrastructure",
        "infrastructure",
    ],
    "Mathematics": [
        "mathematics",
        "mathematical",
        "proof",
        "theorem",
        "equation",
        "calculus",
    ],
    "Economics & Business": [
        "economics",
        "economic",
        "business",
        "financial",
        "market",
        "trade",
    ],
    "Environmental Science": [
        "environmental",
        "ecology",
        "sustainable",
        "pollution",
        "climate",
        "conservation",
    ],
    "Social Sciences": [
        "social",
        "sociology",
        "anthropology",
        "psychology",
        "culture",
        "society",
    ],
}


def _count_domain_keyword_hits(text_lower: str) -> Dict[str, int]:
    """Count keyword hits using exact word-boundary regex.


    NOTE: This intentionally matches the previous app.py/analysis_tasks behavior
    (exact word boundary matching) to minimize risk. Any future stemming/
    suffix-tolerance should be implemented here once.
    """
    domain_scores: Dict[str, int] = {}

    for domain, keywords in DOMAIN_KEYWORDS_SIMPLE.items():
        total = 0
        for keyword in keywords:
            kw = (keyword or "").lower().strip()
            if not kw:
                continue

            # Use regex word-boundary (single backslash), not a literal backslash-b.
            pattern = r"\b" + re.escape(kw) + r"\b"
            total += len(re.findall(pattern, text_lower, flags=re.IGNORECASE))

        if total > 0:
            domain_scores[domain] = total

    return domain_scores


def get_domain_stats(text: str, dataset: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """Compute domain + confidence + dataset-derived stats.

    dataset is optional to support environments/tests; when absent/empty,
    dataset-derived fields default to 0.
    """

    text_lower = (text or "").lower()


    # 1) domain + confidence
    domain_scores = _count_domain_keyword_hits(text_lower)
    detected_domain = max(domain_scores, key=domain_scores.get) if domain_scores else "General Research"

    # Confidence: normalize against ALL domain keyword hit counts.
    # If all domains have 0 hits, confidence is 0.
    winning_domain_score = float(domain_scores.get(detected_domain, 0))
    sum_of_all_domain_scores = float(sum(domain_scores.values()))
    confidence = (winning_domain_score / sum_of_all_domain_scores) * 100 if sum_of_all_domain_scores > 0 else 0.0


    # 2) dataset stats
    dataset_is_empty = dataset is None or getattr(dataset, "empty", True)

    domain_stats: Dict[str, Any] = {
        "domain": detected_domain,
        "confidence": confidence,
        "total_venues": int(len(dataset)) if not dataset_is_empty else 0,
        "matching_venues": 0,
        "oa_count": 0,
        "medline_count": 0,
        "active_count": 0,
        "publishers_count": 0,
    }

    if dataset_is_empty:
        return domain_stats

    ds = dataset

    # OA
    try:
        if "Is_Open_Access" in ds.columns:
            domain_stats["oa_count"] = int(ds["Is_Open_Access"].fillna(False).astype(bool).sum())
        else:
            oa_series = ds.get("Open Access Status", pd.Series(dtype=object))
            domain_stats["oa_count"] = len(oa_series.astype(str).str.contains("OA|open access", case=False, na=False))
    except Exception:
        domain_stats["oa_count"] = 0

    # Medline
    try:
        med_col = "Medline-sourced Title? (See additional details under separate tab.)"
        if med_col in ds.columns:
            s = ds[med_col]
            if s.dtype == bool:
                domain_stats["medline_count"] = int(s.sum())
            else:
                # Real dataset values are typically: "Medline" / "Medline-unique" (with many NaNs).
                lower = s.fillna("").astype(str).str.lower()
                domain_stats["medline_count"] = int(lower.isin(["medline", "medline-unique"]).sum())

        else:
            med_series = ds.get("Medline Coverage", pd.Series(dtype=object))
            domain_stats["medline_count"] = len(med_series.astype(str).str.contains("Yes|Indexed", case=False, na=False))
    except Exception:
        domain_stats["medline_count"] = 0

    # Active
    try:
        if "Is_Active" in ds.columns:
            domain_stats["active_count"] = int(ds["Is_Active"].fillna(False).astype(bool).sum())
        else:
            status_series = ds.get("Active or Inactive", pd.Series(dtype=object))
            domain_stats["active_count"] = len(status_series.astype(str).str.contains("active", case=False, na=False))
    except Exception:
        domain_stats["active_count"] = 0

    # Publishers
    try:
        if "Publisher" in ds.columns:
            domain_stats["publishers_count"] = int(ds["Publisher"].nunique())
        else:
            domain_stats["publishers_count"] = 0
    except Exception:
        domain_stats["publishers_count"] = 0

    # matching venues: dataset-derived topical matching with an is_estimate flag.
    # This mirrors the richer logic that used to live in analysis_tasks.py.

    def _safe_count_non_null(col_name: str) -> int:
        if ds is None or ds.empty:
            return 0
        if col_name not in ds.columns:
            return 0
        return int(ds[col_name].notna().sum())

    def _safe_count_subject_tags_contains(substr: str) -> int:
        if ds is None or ds.empty:
            return 0
        if "Subject_Tags" not in ds.columns:
            return 0
        series = ds["Subject_Tags"].fillna("").astype(str)
        return int(series.str.contains(substr, case=False, regex=False).sum())

    def _safe_count_subject_tags_equals(val: str) -> int:
        if ds is None or ds.empty:
            return 0
        if "Subject_Tags" not in ds.columns:
            return 0
        series = ds["Subject_Tags"].fillna("").astype(str)
        return int((series == val).sum())

    # Default: estimate until proven precise.
    domain_stats["is_estimate"] = True

    precise_map = {
        "Computer Science & AI": "1700\nComputer Science",
        "Biomedical & Medicine": "2700\nMedicine",
        "Engineering": "2200\nEngineering",
        "Environmental Science": "2300\nEnvironmental Science",
        "Social Sciences": "3300\nSocial Sciences",
    }

    if detected_domain in precise_map:
        domain_stats["matching_venues"] = _safe_count_non_null(precise_map[detected_domain])
        domain_stats["is_estimate"] = False
    elif detected_domain == "General Research":
        domain_stats["matching_venues"] = _safe_count_subject_tags_equals("General")
        domain_stats["is_estimate"] = True
    elif detected_domain == "Chemistry":
        # Chemistry tag root is not reliably present in this dataset; conservative estimate.
        domain_stats["matching_venues"] = _safe_count_subject_tags_contains(
            "1300\nBiochemistry, Genetics and Molecular Biology"
        )
        domain_stats["is_estimate"] = True
    else:
        # Physics & Materials / Mathematics / Economics & Business
        domain_stats["matching_venues"] = 0
        domain_stats["is_estimate"] = True

    return domain_stats


