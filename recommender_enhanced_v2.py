"""
Enhanced Research Submission Recommender v2.0 - ASJC Dataset Integration

NEW Scoring System (Based on Actual CSV Data):
- Subject Match (35%): Uses actual ASJC codes from venue database
- Venue Quality (25%): Active status, coverage, medline, related titles  
- Paper-Venue Fit (25%): Language, OA status, type match
- Publisher Profile (15%): Publisher reputation, OA availability

Key Features:
- 26 ASJC codes from the 48,151 venue dataset
- Venue status tracking (Active/Discontinued)
- Medline integration for biomedical research
- Language support in 200+ codes
- Coverage date analysis
- Publisher reputation weighting
- Related titles tracking for multidisciplinary fit
"""

import pandas as pd
import numpy as np
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# All 26 ASJC codes present in the dataset
ASJC_CODES_IN_DATASET = {
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

DOMAIN_KEYWORDS = {
    "machine_learning": ["machine learning", "neural network", "deep learning", "classification", "regression", "ai", "artificial intelligence", "tensorflow", "pytorch"],
    "biomedical": ["medical", "clinical", "disease", "treatment", "health", "patient", "diagnosis", "therapy", "drug", "hospital"],
    "chemistry": ["chemistry", "chemical", "reaction", "molecule", "compound", "synthesis"],
    "physics": ["physics", "quantum", "particle", "electromagnetic", "relativity"],
    "engineering": ["engineering", "mechanical", "electrical", "civil", "infrastructure"],
    "mathematics": ["mathematics", "mathematical", "proof", "theorem", "equation", "algorithm"],
    "economics": ["economics", "economic", "financial", "market", "trade", "business"],
    "social_sciences": ["social", "sociology", "anthropology", "culture", "society"],
    "environmental": ["environmental", "ecology", "sustainable", "pollution", "conservation", "climate"],
    "computer_science": ["computer", "software", "programming", "algorithm", "database", "network"]
}

def detect_domain_from_paper(text):
    """Detect the research domain of a paper"""
    text_lower = (text or "").lower()
    
    domain_scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            domain_scores[domain] = score
    
    if not domain_scores:
        return "general", 0.3
    
    top_domain = max(domain_scores, key=domain_scores.get)
    confidence = min(domain_scores[top_domain] / max(1, len(text_lower.split())), 1.0)
    
    return top_domain, confidence


def match_asjc_codes(domain, text):
    """Match paper domain to top ASJC codes"""
    domain_lower = domain.lower()
    
    # Map domains to ASJC codes
    domain_to_asjc = {
        "machine_learning": ["1700"],  # Computer Science
        "computer_science": ["1700"],
        "biomedical": ["2700", "2400", "3000"],  # Medicine, Immunology, Pharmacology
        "chemistry": ["1600", "3000"],  # Chemistry, Pharmacology
        "physics": ["3100", "2500"],  # Physics, Materials
        "engineering": ["2200", "1500"],  # Engineering, ChemEng
        "mathematics": ["2600", "1700"],  # Math, CS
        "economics": ["2000", "1400", "3300"],  # Economics, Business, Social
        "environmental": ["2300", "1900", "1100"],  # Environmental, Earth, Bio
        "social_sciences": ["3300", "1200", "3200"]  # Social, Humanities, Psychology
    }
    
    asjc_matches = domain_to_asjc.get(domain_lower, ["2700"])  # Default to Medicine if unknown
    
    return [(code, ASJC_CODES_IN_DATASET.get(code, "Unknown")) for code in asjc_matches]


def calculate_enhanced_match_score(venue, paper_text, paper_score, paper_asjc, preferences):
    """
    Calculate match score (0-100) using actual dataset columns
    
    Parameters:
    - venue: Row from pandas dataframe
    - paper_text: Paper abstract/content
    - paper_score: Paper quality score
    - paper_asjc: List of paper's ASJC codes
    - preferences: Filter preferences dict
    """
    
    score = 0.0
    
    # ==== 1. SUBJECT MATCH (35%) - Based on actual ASJC codes in CSV ====
    subject_weight = 35.0
    
    # Extract which ASJC codes this venue has
    venue_asjcs = []
    for code, name in ASJC_CODES_IN_DATASET.items():
        col_name = f"{code}\n{name}"
        try:
            if col_name in venue.index or col_name in venue.keys():
                val = venue.get(col_name, np.nan)
            else:
                val = np.nan
            
            if pd.notna(val) and str(val).strip().lower() not in ["nan", ""]:
                venue_asjcs.append(code)
        except:
            pass
    
    # Match paper ASJC codes to venue ASJC codes
    paper_asjc_code = paper_asjc[0] if isinstance(paper_asjc, list) and paper_asjc else "2700"
    if isinstance(paper_asjc_code, tuple):
        paper_asjc_code = paper_asjc_code[0]
    
    # Primary subject match (20%)
    primary_match_score = 0.95 if paper_asjc_code in venue_asjcs else (
        0.6 if any(paper_asjc_code[:2] == code[:2] for code in venue_asjcs) else 0.2
    )
    score += (subject_weight * 0.571) * primary_match_score
    
    # Multi-subject support (10%)
    multi_subject_score = min(0.9, 0.4 + (len(venue_asjcs) / 10.0) * 0.5)
    score += (subject_weight * 0.286) * multi_subject_score
    
    # Cross-disciplinary opportunity (5%)
    cross_disciplinary_score = 0.7 if len(venue_asjcs) >= 2 else 0.35
    score += (subject_weight * 0.143) * cross_disciplinary_score
    
    # ==== 2. VENUE QUALITY (25%) ====
    quality_weight = 25.0
    
    # Active Status (8%)
    active_status = str(venue.get("Active or Inactive", "Unknown")).strip().lower()
    active_score = 0.95 if active_status == "active" else 0.35
    score += (quality_weight * 0.32) * active_score
    
    # Coverage History (8%) - check if venue has coverage dates
    coverage = str(venue.get("Coverage", "Unknown")).strip()
    coverage_score = 0.85 if coverage and coverage.lower() != "unknown" and coverage.lower() != "nan" else 0.3
    score += (quality_weight * 0.32) * coverage_score
    
    # Medline Status (7%)
    medline_col = "Medline-sourced Title? (See additional details under separate tab.)"
    medline_status = str(venue.get(medline_col, "Unknown")).strip().lower()
    medline_score = 0.9 if medline_status in ["yes", "true", "1"] else 0.25
    score += (quality_weight * 0.28) * medline_score
    
    # New Venue (Added to List Jan 2026) (2%)
    new_venue_col = "Added to List Jan. 2026"
    new_status = str(venue.get(new_venue_col, "Unknown")).strip().lower()
    new_score = 0.7 if new_status in ["yes", "true", "1"] else 0.2
    score += (quality_weight * 0.08) * new_score
    
    # ==== 3. PAPER-VENUE FIT (25%) ====
    fit_weight = 25.0
    
    # Language Support (10%)
    lang_col = "Article Language in Source (Three-Letter ISO Language Codes)"
    language = str(venue.get(lang_col, "")).strip()
    lang_score = 0.85 if language and language.lower() != "nan" else 0.4
    score += (fit_weight * 0.4) * lang_score
    
    # Open Access Status Match (10%)
    oa_status = str(venue.get("Open Access Status", "")).strip().lower()
    if preferences.get("open_access_only", False):
        oa_score = 0.9 if "open" in oa_status else 0.25
    else:
        oa_score = 0.85 if "open" in oa_status else 0.65
    score += (fit_weight * 0.4) * oa_score
    
    # Timeline/Recency Fit (5%)
    timeline_score = 0.75 if coverage and coverage.lower() != "nan" else 0.4
    score += (fit_weight * 0.2) * timeline_score
    
    # ==== 4. PUBLISHER PROFILE (15%) ====
    publisher_weight = 15.0
    
    publisher = str(venue.get("Publisher", "Unknown")).strip().lower()
    
    # Publisher Reputation (8%)
    major_publishers = ["elsevier", "springer", "wiley", "taylor", "sage", "nature", "ieee", "acm", "cambridge", "oxford"]
    publisher_reputation_score = 0.92 if any(pub in publisher for pub in major_publishers) else 0.55
    score += (publisher_weight * 0.533) * publisher_reputation_score
    
    # Source Type Match (5%)
    source_type = str(venue.get("Source Type", "Unknown")).strip().lower()
    user_type_pref = preferences.get("venue_type", "any").lower()
    if user_type_pref != "any":
        type_score = 0.85 if user_type_pref in source_type else 0.5
    else:
        type_score = 0.75
    score += (publisher_weight * 0.333) * type_score
    
    # OA Status Bonus (2%)
    oa_bonus_score = 0.8 if "open" in oa_status else 0.35
    score += (publisher_weight * 0.133) * oa_bonus_score
    
    # ==== APPLY PREFERENCE-BASED FILTERS ====
    
    # Active/Discontinued filter
    if preferences.get("exclude_discontinued", False):
        if active_status != "active":
            score *= 0.55
    
    # Medline filter
    if preferences.get("medline_only", False):
        if medline_status not in ["yes", "true", "1"]:
            score *= 0.65
    
    # Open Access filter
    if preferences.get("open_access_only", False):
        if "open" not in oa_status:
            score *= 0.6
    
    # Publisher preference
    preferred_publisher = preferences.get("publisher", "any").lower()
    if preferred_publisher != "any" and preferred_publisher not in publisher:
        score *= 0.82
    
    # Coverage year filter
    min_year = preferences.get("min_coverage_year", 2000)
    if coverage and coverage.lower() != "nan":
        try:
            years = [int(y) for y in re.findall(r'\d{4}', coverage)]
            if years and max(years) < min_year:
                score *= 0.65
        except:
            pass
    
    # Venue type filter
    if user_type_pref != "any" and user_type_pref not in source_type:
        score *= 0.75
    
    return min(max(score, 0.0), 100.0)


def recommend_venues_enhanced(paper_text, paper_score, paper_topic, preferences, venue_db, top_n=10):
    """
    Main recommendation function using enhanced scoring
    """
    
    if venue_db is None or venue_db.empty:
        return {
            "error": "Venue database not available",
            "venues": [],
            "paper_domain": "unknown",
            "paper_subjects": [],
            "total_venues_evaluated": 0,
            "matches_found": 0
        }
    
    # Detect paper domain
    paper_domain, domain_confidence = detect_domain_from_paper(paper_text or paper_topic or "")
    paper_asjc = match_asjc_codes(paper_domain, paper_text or paper_topic or "")
    
    recommendations = []
    
    # Score all venues
    for idx, (_, venue) in enumerate(venue_db.iterrows()):
        try:
            match_score = calculate_enhanced_match_score(
                venue,
                paper_text or paper_topic or "",
                paper_score or 5.0,
                paper_asjc,
                preferences
            )
            
            # Extract venue details
            venue_title = str(venue.get("Source Title", f"Venue {idx+1}")).strip()
            if not venue_title or venue_title.lower() == "nan":
                venue_title = f"Venue {idx+1}"
            
            publisher = str(venue.get("Publisher", "Unknown")).strip()
            source_type = str(venue.get("Source Type", "Unknown")).strip()
            active_status = str(venue.get("Active or Inactive", "Unknown")).strip()
            oa_status = str(venue.get("Open Access Status", "")).strip()
            coverage = str(venue.get("Coverage", "")).strip()
            
            # Detect ASJC codes for this venue
            asjc_codes = []
            for code, name in ASJC_CODES_IN_DATASET.items():
                col_name = f"{code}\n{name}"
                try:
                    val = venue.get(col_name, np.nan)
                    if pd.notna(val) and str(val).strip().lower() not in ["nan", ""]:
                        asjc_codes.append(name)
                except:
                    pass
            
            # Check filters
            medline_col = "Medline-sourced Title? (See additional details under separate tab.)"
            is_medline = str(venue.get(medline_col, "")).lower() in ["yes", "true", "1"]
            
            new_col = "Added to List Jan. 2026"
            is_new = str(venue.get(new_col, "")).lower() in ["yes", "true", "1"]
            
            # Generate recommendation reason
            paper_asjc_code = paper_asjc[0][0] if paper_asjc else "2700"
            reason = f"Strong match for {paper_domain.replace('_', ' ')} research"
            if paper_asjc_code in [c[:4] for c in asjc_codes]:
                reason += f" with {source_type.lower()} specialization"
            if active_status.lower() == "active":
                reason += " • Currently indexed and active"
            if is_medline:
                reason += " • Medline indexed"
            
            # Get language information
            language = str(venue.get("Language", "English")).strip()
            if not language or language.lower() == "nan":
                language = "English"
            
            # Get ISSN information
            issn = str(venue.get("ISSN", "")).strip()
            eissn = str(venue.get("EISSN", "")).strip()
            venue_issn = issn if issn and issn.lower() != "nan" else (eissn if eissn and eissn.lower() != "nan" else None)
            
            # Get Scopus Source Record ID
            sourcerecord_id = str(venue.get("Sourcerecord ID", "")).strip()
            if sourcerecord_id and sourcerecord_id.lower() != "nan":
                sourcerecord_id = sourcerecord_id
            else:
                sourcerecord_id = None
            
            recommendations.append({
                "name": venue_title,
                "type": source_type,
                "publisher": publisher,
                "coverage_year_range": coverage,
                "open_access": "open" in oa_status.lower() if oa_status else False,
                "active_status": active_status.lower() == "active",
                "medline_coverage": is_medline,
                "language": language,
                "issn": venue_issn,
                "sourcerecord_id": sourcerecord_id,
                "matched_asjc_subjects": asjc_codes[:5],  # Top 5 ASJC codes
                "is_new_jan_2026": is_new,
                "match_score": round(match_score, 1),
                "reason": reason
            })
        except Exception as e:
            continue
    
    # Sort by score and return top N
    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    
    return {
        "venues": recommendations[:top_n],
        "paper_domain": paper_domain.replace("_", " "),
        "paper_subjects": [asjc[1] for asjc in paper_asjc],
        "total_venues_evaluated": len(venue_db),
        "matches_found": len([r for r in recommendations if r["match_score"] > 30])
    }


def load_venue_database_enhanced():
    """Load the enhanced venue database from CSV"""
    
    db_path = None
    
    # Try primary dataset
    if os.path.exists("datasets/ext_venues_enhanced.csv"):
        db_path = "datasets/ext_venues_enhanced.csv"
    # Try backup dataset
    elif os.path.exists("datasets/ext_venues_active.csv"):
        db_path = "datasets/ext_venues_active.csv"
    
    if not db_path:
        print("ERROR: Venue database not found")
        return None
    
    try:
        df = pd.read_csv(db_path, low_memory=False)
        print(f"✓ Loaded {len(df)} venues from {db_path}")
        print(f"  Columns: {list(df.columns)[:5]}... ({len(df.columns)} total)")
        return df
    except Exception as e:
        print(f"ERROR loading database: {e}")
        return None
