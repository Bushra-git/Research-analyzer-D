"""Analysis-only RQ tasks.

Goal:
- Prevent RQ analysis workers from importing the full Flask app module (`app.py`).
- Keep heavy analysis resources (ML model + analysis dataset) localized here.

This module is intentionally safe to import in an RQ worker process.
"""

from __future__ import annotations

import os
import pickle
import re
import json
import hashlib
from collections import Counter
from typing import Any, Dict

import pandas as pd
import fitz

# sklearn is used in the similarity computation
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _current_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


# -----------------------------
# Load analysis resources once
# -----------------------------

_MODEL = None
_DATASET = pd.DataFrame()

# Domain keywords for paper classification (mirrors app.py)
DOMAIN_KEYWORDS_SIMPLE = {
    "Computer Science & AI": [
        "machine learning",
        "ai",
        "artificial intelligence",
        "neural network",
        "deep learning",
        "algorithm",
        "database",
        "software",
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


def _load_model_and_dataset() -> None:
    global _MODEL, _DATASET

    current_dir = _current_dir()

    # Load model
    try:
        model_path = os.path.join(current_dir, "model.pkl")
        _MODEL = pickle.load(open(model_path, "rb"))
    except Exception as e:
        print(f"Error loading model: {e}")
        _MODEL = None

    # Load analysis dataset
    try:
        csv_path = os.path.join(current_dir, "datasets", "ext_venues_active.csv")

        if not os.path.exists(csv_path):
            csv_path = os.path.join(current_dir, "datasets", "ext_venues_full.csv")

        if os.path.exists(csv_path):
            _DATASET = pd.read_csv(csv_path)
            print(f"[OK] Loaded new venue dataset: {len(_DATASET)} active venues")
        else:
            # Backward compatibility
            csv_path = os.path.join(current_dir, "arxiv_clean.csv")
            df = pd.read_csv(csv_path)
            _DATASET = df.dropna().head(100)
    except Exception as e:
        print(f"Error loading dataset: {e}")
        _DATASET = pd.DataFrame()


_load_model_and_dataset()


# -----------------------------
# Text processing helpers
# -----------------------------

def extract_text_from_pdf(file: Any) -> str:
    if hasattr(file, "read"):
        file_bytes = file.read()
    else:
        file_bytes = file

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def extract_features(text: str) -> Dict[str, Any]:
    words = text.split()

    if len(words) == 0:
        return {
            "word_count": 0,
            "sentence_count": 0,
            "avg_word_length": 0,
            "readability": 50,
        }

    return {
        "word_count": len(words),
        "sentence_count": text.count("."),
        "avg_word_length": sum(len(word) for word in words) / len(words),
        "readability": 50,
    }


def extract_summary(text: str, max_sentences: int = 5) -> str:
    abstract_patterns = [
        r"(?i)abstract\s*\n(.*?)(?=introduction|1\.|keywords)",
        r"(?i)abstract\s*\n(.*?)(?=\n\n[A-Z])",
        r"(?i)abstract:(.*?)(?=introduction|1\.|keywords)",
    ]

    for pattern in abstract_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            abstract = match.group(1).strip()
            abstract = " ".join(abstract.split())
            if len(abstract) > 100:
                return abstract[:500] + "..." if len(abstract) > 500 else abstract

    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    if len(sentences) == 0:
        return "Unable to extract summary from the paper."

    words = re.findall(r"\w+", text.lower())
    word_freq = Counter(words)

    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "have",
        "has",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "this",
        "that",
        "these",
        "those",
        "i",
        "you",
        "he",
        "she",
        "it",
        "we",
        "they",
        "what",
        "which",
        "who",
        "when",
        "where",
        "why",
        "how",
    }

    sentence_scores: Dict[int, int] = {}
    for i, sentence in enumerate(sentences[:50]):
        score = 0
        words_in_sentence = re.findall(r"\w+", sentence.lower())
        for word in words_in_sentence:
            if word not in stop_words:
                score += word_freq.get(word, 0)
        sentence_scores[i] = score

    top_sentence_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:max_sentences]
    top_sentence_indices.sort()

    summary_sentences = [sentences[i] for i in top_sentence_indices]
    summary = " ".join(summary_sentences)

    if len(summary) > 500:
        summary = summary[:500] + "..."

    return summary


def get_domain_stats(text: str) -> Dict[str, Any]:
    text_lower = (text or "").lower()

    domain_scores: Dict[str, int] = {}
    for domain, keywords in DOMAIN_KEYWORDS_SIMPLE.items():
        score = sum(text_lower.count(keyword) for keyword in keywords)
        if score > 0:
            domain_scores[domain] = score

    detected_domain = max(domain_scores, key=domain_scores.get) if domain_scores else "General Research"
    confidence = min((domain_scores.get(detected_domain, 0) / max(1, len(text_lower.split()))) * 100, 100)

    domain_stats: Dict[str, Any] = {
        "domain": detected_domain,
        "confidence": confidence,
        "total_venues": len(_DATASET) if not _DATASET.empty else 0,
        "matching_venues": 0,
        "oa_count": 0,
        "medline_count": 0,
        "active_count": 0,
        "publishers_count": 0,
    }

    if not _DATASET.empty:
        domain_stats["total_venues"] = len(_DATASET)

        # Try to count OA venues (prefer boolean Is_Open_Access)
        try:
            if "Is_Open_Access" in _DATASET.columns:
                domain_stats["oa_count"] = int(_DATASET["Is_Open_Access"].fillna(False).astype(bool).sum())
            else:
                oa_series = _DATASET.get("Open Access Status", pd.Series(dtype=object))
                domain_stats["oa_count"] = len(
                    oa_series.astype(str).str.contains("OA|open access", case=False, na=False)
                )

        except Exception as e:
            print(f"[WARN] oa_count computation failed: {e}")
            domain_stats["oa_count"] = 0

        # Try to count Medline venues (use real Medline column)
        try:
            med_col = "Medline-sourced Title? (See additional details under separate tab.)"
            if med_col in _DATASET.columns:
                # Real dataset values are exactly:
                # - NaN (missing) / 26339 rows
                # - "Medline" / 4862 rows
                # - "Medline-unique" / 53 rows
                # There are NO "Yes" / "Indexed" strings.
                med_series = _DATASET[med_col]
                domain_stats["medline_count"] = int(
                    med_series.notna().values.sum()
                    - med_series.isna().values.sum()
                )

                # More robust: count only the two expected string categories.
                domain_stats["medline_count"] = int(
                    med_series.fillna("").astype(str).isin(["Medline", "Medline-unique"]).sum()
                )
            else:
                # Fallback to older schema if present.
                med_series = _DATASET.get("Medline Coverage", pd.Series(dtype=object))
                domain_stats["medline_count"] = len(
                    med_series.astype(str).str.contains("Yes|Indexed", case=False, na=False)
                )
        except Exception as e:
            print(f"[WARN] medline_count computation failed: {e}")
            domain_stats["medline_count"] = 0


        # Try to count active venues (prefer boolean Is_Active)
        try:
            if "Is_Active" in _DATASET.columns:
                domain_stats["active_count"] = int(_DATASET["Is_Active"].fillna(False).astype(bool).sum())
            else:
                status_series = _DATASET.get("Active or Inactive", pd.Series(dtype=object))
                domain_stats["active_count"] = len(
                    status_series.astype(str).str.contains("active", case=False, na=False)
                )
        except Exception as e:
            print(f"[WARN] active_count computation failed: {e}")
            domain_stats["active_count"] = 0

        # Count publishers
        try:
            if "Publisher" in _DATASET.columns:
                domain_stats["publishers_count"] = int(_DATASET["Publisher"].nunique())
            else:
                domain_stats["publishers_count"] = 0
        except Exception as e:
            print(f"[WARN] publishers_count computation failed: {e}")
            domain_stats["publishers_count"] = 0


        domain_stats["matching_venues"] = int(len(_DATASET) * 0.3)

    return domain_stats


def generate_recommendations(text: str, features: Dict[str, Any], score: float) -> Any:
    recommendations = []
    word_count = features.get("word_count", 0)
    sentence_count = features.get("sentence_count", 0)
    avg_word_length = features.get("avg_word_length", 0)

    if word_count < 2000:
        recommendations.append(
            {
                "title": "Expand Content",
                "description": (
                    f"Your paper has {word_count} words. Consider expanding to at least 3,000-5,000 words "
                    "for a comprehensive research paper. Add more detail to methodology, results, and "
                    "discussion sections."
                ),
            }
        )
    elif word_count > 15000:
        recommendations.append(
            {
                "title": "Optimize Length",
                "description": (
                    f"Your paper has {word_count} words, which may be too lengthy. Consider condensing or "
                    "removing redundant sections while maintaining key information and research quality."
                ),
            }
        )
    else:
        recommendations.append(
            {
                "title": "Content Length",
                "description": (
                    f"Your paper's word count ({word_count} words) is within a good range for research papers. "
                    "Focus on maintaining quality over quantity."
                ),
            }
        )

    if word_count > 0 and sentence_count > 0:
        avg_sentence_length = word_count / sentence_count
        if avg_sentence_length > 30:
            recommendations.append(
                {
                    "title": "Simplify Sentence Structure",
                    "description": (
                        f"Average sentence length is {avg_sentence_length:.1f} words, which may reduce readability. "
                        "Break down complex sentences into shorter, clearer statements for better comprehension."
                    ),
                }
            )
        elif avg_sentence_length < 10:
            recommendations.append(
                {
                    "title": "Enhance Sentence Variety",
                    "description": (
                        f"Average sentence length is {avg_sentence_length:.1f} words. Try varying sentence length and "
                        "structure to improve flow and maintain reader engagement."
                    ),
                }
            )

    if avg_word_length < 4.5:
        recommendations.append(
            {
                "title": "Enhance Academic Vocabulary",
                "description": (
                    f"Average word length is {avg_word_length:.1f} characters. Consider using more sophisticated "
                    "academic terminology to elevate the scholarly tone of your paper."
                ),
            }
        )
    elif avg_word_length > 6:
        recommendations.append(
            {
                "title": "Improve Clarity",
                "description": (
                    f"Average word length is {avg_word_length:.1f} characters. Some words may be overly complex. "
                    "Balance technical terminology with clear explanations for accessibility."
                ),
            }
        )

    if score < 5:
        recommendations.append(
            {
                "title": "Critical Improvements Needed",
                "description": (
                    "Your paper scored below 5/10. Focus on strengthening the methodology, providing clear research "
                    "objectives, and improving overall organization and presentation quality."
                ),
            }
        )
    elif score < 7:
        recommendations.append(
            {
                "title": "Strengthen Key Sections",
                "description": (
                    "Your paper has good potential. Enhance the introduction with clearer thesis statement, expand the "
                    "literature review, and provide more detailed analysis in the results section."
                ),
            }
        )
    elif score < 8.5:
        recommendations.append(
            {
                "title": "Polish for Excellence",
                "description": (
                    "Your paper is strong! Focus on minor refinements: enhance abstract clarity, add more citations, "
                    "review formatting consistency, and ensure all tables/figures are well-labeled."
                ),
            }
        )
    else:
        recommendations.append(
            {
                "title": "Excellent Work",
                "description": (
                    "Your paper demonstrates high quality. Consider submitting to peer-reviewed venues or academic conferences. "
                    "Continue maintaining this level of academic rigor."
                ),
            }
        )

    words = text.split()
    if len(words) > 0:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.5:
            recommendations.append(
                {
                    "title": "Reduce Repetition",
                    "description": (
                        "Your paper shows significant word repetition. Use synonyms and varied expressions to improve "
                        "readability and maintain reader interest throughout the paper."
                    ),
                }
            )

    if "conclusion" not in text.lower():
        recommendations.append(
            {
                "title": "Add Conclusion Section",
                "description": (
                    "Your paper appears to lack a formal conclusion. Add a strong conclusion section that summarizes findings, "
                    "implications, and suggests future research directions."
                ),
            }
        )

    if len(re.findall(r"\[\d+\]|cite|ref", text, re.IGNORECASE)) < 5:
        recommendations.append(
            {
                "title": "Increase Citations",
                "description": (
                    "Your paper has minimal citations. Strengthen your research by citing relevant literature and establishing "
                    "connections to existing work in your field."
                ),
            }
        )

    return recommendations


# -----------------------------
# Main RQ task
# -----------------------------

def process_paper_analysis(file_bytes: bytes, file_name: str = "uploaded.pdf") -> Dict[str, Any]:
    text = extract_text_from_pdf(file_bytes)

    # Guard: scanned/corrupted PDFs may yield empty/near-empty text.
    # In that case, stop early and return a clear error payload.
    if len((text or "").split()) < 50:
        return {
            "error": "Could not extract readable text from this PDF. It may be a scanned image without OCR text, corrupted, or empty.",
            "file_name": file_name,
        }

    summary = extract_summary(text)
    features = extract_features(text)
    domain_stats = get_domain_stats(text)


    # Model scoring
    if _MODEL is None:
        print("Warning: Model not loaded, using default scoring")
        score = 6.5
    else:
        features_df = pd.DataFrame([features])
        score = _MODEL.predict(features_df)[0]

    words = text.split()
    if len(words) > 0:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.4:
            score -= 2

    score = max(0, min(10, score))
    recommendations = generate_recommendations(text, features, score)

    # Similarity matching (kept equivalent to existing logic)
    docs_for_comparison = []
    if not _DATASET.empty and "Source Title" in _DATASET.columns:
        docs_for_comparison = _DATASET["Source Title"].fillna("").tolist()

    all_docs = docs_for_comparison.copy() if docs_for_comparison else [""]
    all_docs.insert(0, text)

    vectorizer = TfidfVectorizer(max_features=500)
    tfidf = vectorizer.fit_transform(all_docs)

    similarity = cosine_similarity(tfidf)[0]
    top_indices = similarity.argsort()[-6:][::-1][1:]

    similar_papers = []
    for i in top_indices:
        if i - 1 >= 0 and i - 1 < len(_DATASET):
            title_col = "Source Title" if "Source Title" in _DATASET.columns else "title"
            similar_papers.append(
                {
                    "title": str(_DATASET.iloc[i - 1][title_col])[:100],
                    "score": float(similarity[i]),
                }
            )

    return {
        "score": float(score),
        "features": features,
        "similar_papers": similar_papers,
        "summary": summary,
        "recommendations": recommendations,
        "domain_stats": domain_stats,
        "file_name": file_name,
    }

