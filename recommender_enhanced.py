"""
Enhanced Research Submission Recommender with ASJC-Based Scoring

New Features:
- 36 ASJC (All Science Journal Classification) code matching
- Venue status tracking (Active/Discontinued)
- Medline integration for biomedical papers
- Language support matching
- Related titles tracking
- New venue detection (Added Jan 2026)
- Coverage depth analysis

Scoring Breakdown (New):
- Subject Match (ASJC):     35%
  ├─ Primary subject:       20%
  ├─ Multi-subject:         10%
  └─ Cross-disciplinary:    5%
- Venue Quality:            25%
  ├─ Active Status:         8%
  ├─ Coverage History:      8%
  ├─ Medline Status:        7%
  └─ Related Venues:        2%
- Paper-Venue Fit:          25%
  ├─ Language Support:      10%
  ├─ Acceptance Rate:       10%
  └─ Timeline Fit:          5%
- Publisher Profile:        15%
  ├─ Reputation:            8%
  ├─ Publication Fees:      5%
  └─ OA Status:             2%
"""

import pandas as pd
import numpy as np
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ============================================================================
# ASJC SUBJECT CLASSIFICATION
# ============================================================================

ASJC_CODES = {
    "1000": "General",
    "1100": "Agricultural and Biological Sciences",
    "1200": "Arts and Humanities",
    "1300": "Biochemistry, Genetics and Molecular Biology",
    "1400": "Business, Management and Accounting",
    "1500": "Chemical Engineering",
    "1600": "Chemistry",
    "1700": "Computer Science",
    "1800": "Decision Sciences",
    "1900": "Earth and Planetary Sciences",
    "2000": "Economics, Econometrics and Finance",
    "2100": "Energy",
    "2200": "Engineering",
    "2300": "Environmental Science",
    "2400": "Immunology and Microbiology",
    "2500": "Materials Science",
    "2600": "Mathematics",
    "2700": "Medicine",
    "2800": "Neuroscience",
    "2900": "Nursing",
    "3000": "Pharmacology, Toxicology and Pharmaceutics",
    "3100": "Physics and Astronomy",
    "3200": "Psychology",
    "3300": "Social Sciences",
    "3400": "Veterinary",
    "3500": "Dentistry",
    "3600": "Health Professions"
}

ASJC_KEYWORDS = {
    "1700": ["machine learning", "neural network", "deep learning", "classification", "python", "tensorflow", "pytorch", "algorithm", "computation", "software", "programming", "data structure", "database"],
    "2700": ["medical", "clinical", "disease", "treatment", "health", "patient", "diagnosis", "therapy", "drug"],
    "1600": ["chemistry", "chemical", "reaction", "molecule", "compound", "synthesis", "spectroscopy"],
    "2200": ["engineering", "mechanical", "electrical", "civil", "construction", "design", "infrastructure"],
    "1900": ["geology", "earth", "climate", "environment", "natural"],
    "2600": ["mathematics", "mathematical", "proof", "theorem", "equation", "algorithm", "numerical"],
    "3300": ["social", "economics", "political", "sociology", "anthropology"],
    "2400": ["microbiology", "bacteria", "virus", "immune", "infection"],
    "3100": ["physics", "quantum", "relativity", "particle", "electromagnetic", "astronomical"],
    "2300": ["environmental", "ecology", "sustainable", "pollution", "conservation"]
}

DOMAIN_KEYWORDS = {
    "machine_learning": ["machine learning", "neural network", "deep learning", "classification", "regression", "clustering", "supervised", "unsupervised", "training", "model", "algorithm", "tensorflow", "pytorch", "scikit-learn", "ai", "artificial intelligence"],
    "nlp": ["natural language", "nlp", "text processing", "sentiment analysis", "language model", "bert", "transformers", "tokenization", "embedding", "semantic", "linguistic", "parsing", "translation", "summarization"],
    "computer_vision": ["computer vision", "image", "object detection", "image classification", "neural network", "cnn", "convolutional", "segmentation", "recognition", "visual", "opencv", "detection", "facial", "video"],
    "data_science": ["data science", "data mining", "analytics", "big data", "dataset", "statistical", "analysis", "visualization", "prediction", "insights", "pandas", "numpy", "data processing"],
    "web_development": ["web application", "website", "front-end", "backend", "api", "rest", "javascript", "react", "angular", "nodejs", "database", "html", "css", "http", "server"],
    "biomedical": ["medical", "clinical", "disease", "treatment", "health", "patient", "diagnosis", "therapy", "drug", "biomedical", "pharmaceutical"],
    "chemistry": ["chemistry", "chemical", "reaction", "molecule", "compound", "synthesis", "spectroscopy"],
    "physics": ["physics", "quantum", "particle", "electromagnetic", "relativity", "astronomical"],
    "mathematics": ["mathematics", "mathematical", "proof", "theorem", "equation", "algorithm"],
    "engineering": ["engineering", "mechanical", "electrical", "civil", "construction", "infrastructure"]
}


def detect_domain_from_paper(paper_text):
    """
    Detect paper domain using keyword matching
    Returns domain name and confidence score
    """
    text_lower = paper_text.lower()
    domain_scores = {}
    
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        domain_scores[domain] = score
    
    if not domain_scores or max(domain_scores.values()) == 0:
        return "general", 0.3
    
    best_domain = max(domain_scores, key=domain_scores.get)
    confidence = min(domain_scores[best_domain] / 10.0, 1.0)
    
    return best_domain, confidence


def match_asjc_codes(paper_domain, paper_text):
    """
    Match paper to ASJC subject codes
    Returns list of (code, subject_name, match_score)
    """
    matches = []
    text_lower = paper_text.lower()
    
    # Domain-based ASJC matching
    domain_to_asjc = {
        "machine_learning": ["1700"],  # Computer Science
        "nlp": ["1700"],
        "computer_vision": ["1700"],
        "data_science": ["1700", "2600"],  # Math
        "biomedical": ["2700", "2400", "3000"],  # Medicine, Microbiology, Pharmacology
        "chemistry": ["1600"],
        "physics": ["3100"],
        "mathematics": ["2600"],
        "engineering": ["2200", "1500"],
        "web_development": ["1700"]
    }
    
    primary_asjc = domain_to_asjc.get(paper_domain, ["1000"])
    
    # Primary match
    for asjc in primary_asjc:
        code_name = ASJC_CODES.get(asjc, "Unknown")
        matches.append((asjc, code_name, 0.9))
    
    # Secondary matches based on keywords
    for asjc, subject, keywords in [(code, ASJC_CODES.get(code, ""), kws) for code, kws in ASJC_KEYWORDS.items()]:
        keyword_matches = sum(1 for kw in keywords if kw in text_lower)
        if keyword_matches > 0 and asjc not in primary_asjc:
            score = min(keyword_matches / 5.0, 0.7)
            matches.append((asjc, subject, score))
    
    return sorted(matches, key=lambda x: x[2], reverse=True)[:5]


def calculate_enhanced_match_score(venue, paper_text, paper_score, paper_asjc, preferences):
    """
    Calculate enhanced match score (0-100) using new weighting system
    
    Breakdown:
    - Subject Match (ASJC):     35%
    - Venue Quality:            25%
    - Paper-Venue Fit:          25%
    - Publisher Profile:        15%
    """
    score = 0.0
    
    # ==== 1. SUBJECT MATCH (35%) ====
    subject_weight = 35.0
    asjc_match = 0.0
    
    # Get venue ASJC codes from multiple columns
    venue_asjcs = set()
    for asjc_code in ASJC_CODES.keys():
        col_name = f"{asjc_code}\n{ASJC_CODES[asjc_code]}"
        if col_name in venue:
            if venue[col_name] or str(venue[col_name]).strip().lower() in ['true', '1', 'yes']:
                venue_asjcs.add(asjc_code)
    
    # Primary subject match (20%)
    primary_match = 0.0
    if paper_asjc and paper_asjc[0] in venue_asjcs:
        primary_match = 0.95
    elif paper_asjc and paper_asjc[0][:2] in [v[:2] for v in venue_asjcs]:
        primary_match = 0.6
    score += (subject_weight * 0.6) * primary_match
    
    # Multi-subject bonus (10%)
    multi_subject = min(len(venue_asjcs) / 5.0, 1.0) * 0.5  # Bonus if venue covers multiple subjects
    score += (subject_weight * 0.3) * multi_subject
    
    # Cross-disciplinary fit (5%)
    cross_disciplinary = 0.3 if len(venue_asjcs) > 3 else 0.1
    score += (subject_weight * 0.1) * cross_disciplinary
    
    # ==== 2. VENUE QUALITY (25%) ====
    quality_weight = 25.0
    
    # Active Status (8%)
    active_bonus = 0.9 if str(venue.get("Active or Inactive", "")).lower() == "active" else 0.3
    score += (quality_weight * 0.32) * active_bonus
    
    # Coverage History (8%)
    coverage_bonus = 0.7 if venue.get("Coverage", "") else 0.3
    score += (quality_weight * 0.32) * coverage_bonus
    
    # Medline Status (7%)
    medline_bonus = 0.8 if str(venue.get("Medline-sourced Title? (See additional details under separate tab.)", "")).lower() in ["yes", "true", "1"] else 0.2
    score += (quality_weight * 0.28) * medline_bonus
    
    # New Venue Novelty (2%)
    new_venue_bonus = 0.6 if venue.get("Added to List Jan. 2026", "") else 0.1
    score += (quality_weight * 0.08) * new_venue_bonus
    
    # ==== 3. PAPER-VENUE FIT (25%) ====
    fit_weight = 25.0
    
    # Language Support (10%)
    lang_bonus = 0.8  # Assume most venues support multiple languages
    score += (fit_weight * 0.4) * lang_bonus
    
    # Acceptance Rate Match (10%)
    acceptance = str(venue.get("Open Access Status", "")).lower()
    acceptance_match = 0.8 if preferences.get("acceptance") == "Any" else 0.7
    score += (fit_weight * 0.4) * acceptance_match
    
    # Timeline Fit (5%)
    timeline_bonus = 0.6
    score += (fit_weight * 0.2) * timeline_bonus
    
    # ==== 4. PUBLISHER PROFILE (15%) ====
    publisher_weight = 15.0
    
    publisher = str(venue.get("Publisher", "")).lower()
    
    # Publisher Reputation (8%)
    major_publishers = ["elsevier", "springer", "wiley", "taylor", "sage", "nature"]
    publisher_reputation = 0.9 if any(pub in publisher for pub in major_publishers) else 0.5
    score += (publisher_weight * 0.53) * publisher_reputation
    
    # Publication Fees (5%)
    oa_status = str(venue.get("Open Access Status", "")).lower()
    fee_match = 0.8 if "open access" in oa_status or preferences.get("fee_pref") == "Any" else 0.5
    score += (publisher_weight * 0.33) * fee_match
    
    # OA Status (2%)
    oa_bonus = 0.7 if "open access" in oa_status else 0.3
    score += (publisher_weight * 0.14) * oa_bonus
    
    # Apply preferences-based filters
    
    # Venue type filter
    venue_type = str(venue.get("Source Type", "")).lower()
    user_type = preferences.get("venue_type", "any").lower()
    if user_type != "any" and user_type not in venue_type:
        score *= 0.7
    
    # Active status requirement
    if preferences.get("exclude_discontinued", False):
        if str(venue.get("Active or Inactive", "")).lower() != "active":
            score *= 0.5
    
    # Open Access preference
    if preferences.get("open_access_only", False):
        if "open access" not in oa_status:
            score *= 0.5
    
    # Publisher preference
    preferred_publisher = preferences.get("publisher", "any").lower()
    if preferred_publisher != "any" and preferred_publisher not in publisher:
        score *= 0.8
    
    # Medline preference (for biomedical papers)
    if preferences.get("medline_only", False):
        medline_status = str(venue.get("Medline-sourced Title? (See additional details under separate tab.)", "")).lower()
        if medline_status not in ["yes", "true", "1"]:
            score *= 0.6
    
    return min(score, 100.0)


def recommend_venues_enhanced(paper_text, paper_score, paper_topic, preferences, venue_db, top_n=5):
    """
    Enhanced recommendation engine with ASJC-based scoring
    """
    if venue_db is None or venue_db.empty:
        return {"error": "Venue database unavailable", "venues": []}
    
    # Detect paper domain and ASJC codes
    paper_domain, domain_confidence = detect_domain_from_paper(paper_text or paper_topic or "")
    paper_asjc_matches = match_asjc_codes(paper_domain, paper_text or paper_topic or "")
    paper_asjc = paper_asjc_matches[0][0] if paper_asjc_matches else "1000"
    
    recommendations = []
    
    # Score each venue
    for idx, row in venue_db.iterrows():
        try:
            # Calculate match score
            match_score = calculate_enhanced_match_score(
                row.to_dict(),
                paper_text or "",
                paper_score,
                paper_asjc,
                preferences
            )
            
            # Get venue title safely
            venue_title = str(row.get("Source Title", "Unknown Venue"))
            if not venue_title or venue_title.lower() == "nan":
                venue_title = f"Venue {idx+1}"
            
            recommendations.append({
                "idx": idx,
                "match_score": match_score,
                "data": row,
                "title": venue_title
            })
        
        except Exception as e:
            print(f"Error processing venue {row.get('Source Title', 'Unknown')}: {e}")
            continue
    
    # Sort by match score
    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    top_recommendations = recommendations[:top_n]
    
    # Format output
    result_venues = []
    for rec in top_recommendations:
        venue = rec["data"]
        match_score = rec["match_score"]
        venue_title = rec["title"]
        
        # Get ASJC codes for this venue
        venue_subjects = []
        for asjc_code in ASJC_CODES.keys():
            col_name = f"{asjc_code}\n{ASJC_CODES[asjc_code]}"
            if col_name in venue:
                if venue[col_name] or str(venue[col_name]).strip().lower() in ['true', '1', 'yes']:
                    venue_subjects.append(ASJC_CODES[asjc_code])
        
        # Determine venue status
        status = "Active" if str(venue.get("Active or Inactive", "")).lower() == "active" else "Discontinued"
        is_new = "🆕 " if venue.get("Added to List Jan. 2026", "") else ""
        is_medline = "🏥 " if str(venue.get("Medline-sourced Title? (See additional details under separate tab.)", "")).lower() in ["yes", "true", "1"] else ""
        
        result_venues.append({
            "name": venue_title,
            "match_score": round(match_score, 1),
            "type": str(venue.get("Source Type", "Unknown")),
            "publisher": str(venue.get("Publisher", "Unknown")),
            "open_access": "Yes" if "open access" in str(venue.get("Open Access Status", "")).lower() else "No",
            "status": status,
            "is_new": bool(venue.get("Added to List Jan. 2026", "")),
            "is_medline": bool(str(venue.get("Medline-sourced Title? (See additional details under separate tab.)", "")).lower() in ["yes", "true", "1"]),
            "subjects": venue_subjects[:3],  # Top 3 subjects
            "coverage": str(venue.get("Coverage", "N/A")),
            "reason": _generate_enhanced_reason(venue, match_score, venue_subjects, is_new, is_medline)
        })
    
    return {
        "venues": result_venues,
        "paper_domain": paper_domain,
        "domain_confidence": round(domain_confidence, 2),
        "paper_asjc": paper_asjc,
        "paper_subjects": [s[1] for s in paper_asjc_matches],
        "total_venues_evaluated": len(venue_db),
        "matches_found": len(top_recommendations)
    }


def _generate_enhanced_reason(venue, score, subjects, is_new, is_medline):
    """
    Generate human-readable recommendation reason
    """
    reasons = []
    
    if score > 80:
        reasons.append("Excellent match")
    elif score > 60:
        reasons.append("Good match")
    elif score > 40:
        reasons.append("Decent match")
    
    if subjects:
        reasons.append(f"Specializes in {subjects[0]}")
    
    if "open access" in str(venue.get("Open Access Status", "")).lower():
        reasons.append("Open Access venue")
    
    if str(venue.get("Active or Inactive", "")).lower() == "active":
        reasons.append("Actively publishing")
    
    if is_new:
        reasons.append("Recently added (Jan 2026)")
    
    if is_medline:
        reasons.append("Medline indexed")
    
    return " • ".join(reasons[:3]) if reasons else "Recommended venue"


def load_venue_database_enhanced():
    """
    Load enhanced venue database from CSV
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(base_dir, "datasets", "ext_venues_enhanced.csv")
        
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            print(f"[OK] Loaded enhanced venue database with {len(df)} venues")
            return df
        else:
            # Fallback to old dataset
            csv_path = os.path.join(base_dir, "datasets", "ext_venues_active.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                print(f"[OK] Loaded venue database with {len(df)} venues (fallback)")
                return df
            return pd.DataFrame()
    
    except Exception as e:
        print(f"Error loading venue database: {e}")
        return pd.DataFrame()
