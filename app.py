from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import pandas as pd
import fitz
import os
import re
import json
import hashlib
from collections import Counter
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from redis import Redis
from rq import Queue
from rq.job import Job
from rq.exceptions import NoSuchJobError
# Import enhanced recommender with ASJC-based scoring (v2 with proper dataset integration)
try:
    from recommender_enhanced_v2 import load_venue_database_enhanced, recommend_venues_enhanced
except ImportError:
    from recommender_enhanced import load_venue_database_enhanced, recommend_venues_enhanced
from sklearn.feature_extraction.text import TfidfVectorizer


# Cache TTL defaults (24h for analysis, 24h for recommendations by default)
ANALYSIS_CACHE_TTL_SECONDS = int(os.getenv("ANALYSIS_CACHE_TTL_SECONDS", 24 * 60 * 60))
RECOMMENDATION_CACHE_TTL_SECONDS = int(os.getenv("RECOMMENDATION_CACHE_TTL_SECONDS", 24 * 60 * 60))


app = Flask(__name__)
allowed_origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",") if origin.strip()]
CORS(app, origins=allowed_origins)

# NOTE: ensure the Flask server binds to the configured host/port in Docker
flask_host = os.getenv("FLASK_HOST", "0.0.0.0")
flask_port = int(os.getenv("FLASK_PORT", "5000"))
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_connection = Redis.from_url(redis_url)
analysis_queue = Queue("analysis", connection=redis_connection)
ANALYSIS_CACHE_TTL_SECONDS = int(os.getenv("ANALYSIS_CACHE_TTL_SECONDS", 24 * 60 * 60))
RECOMMENDATION_CACHE_TTL_SECONDS = int(os.getenv("RECOMMENDATION_CACHE_TTL_SECONDS", 24 * 60 * 60))


# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Load model with error handling
try:
    model_path = os.path.join(current_dir, "model.pkl")
    model = pickle.load(open(model_path, "rb"))
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# Load new venue dataset (ext_list_Jan_2026)
try:
    # Try to load preprocessed venues first (from new dataset)
    csv_path = os.path.join(current_dir, "datasets", "ext_venues_active.csv")
    if not os.path.exists(csv_path):
        # Fallback to full dataset if active dataset not found
        csv_path = os.path.join(current_dir, "datasets", "ext_venues_full.csv")
    
    if os.path.exists(csv_path):
        dataset = pd.read_csv(csv_path)
        print(f"[OK] Loaded new venue dataset: {len(dataset)} active venues")
    else:
        # Keep existing behavior for backward compatibility
        csv_path = os.path.join(current_dir, "arxiv_clean.csv")
        dataset = pd.read_csv(csv_path)
        dataset = dataset.dropna().head(100)
except Exception as e:
    print(f"Error loading dataset: {e}")
    dataset = pd.DataFrame()





# Load venue database for recommendations
try:
    venue_db = load_venue_database_enhanced()
    print(f"[OK] Enhanced venue database loaded with {len(venue_db)} venues")
except Exception as e:
    print(f"Warning: Could not load venue database: {e}")
    venue_db = None

# Load TF-IDF vectorizer for recommendation topic matching
global_vectorizer = None

# Domain keywords for paper classification
DOMAIN_KEYWORDS_SIMPLE = {
    "Computer Science & AI": ["machine learning", "ai", "artificial intelligence", "neural network", "deep learning", "algorithm", "database", "software"],
    "Biomedical & Medicine": ["medical", "clinical", "disease", "health", "patient", "treatment", "diagnosis", "drug", "therapy", "biomedical"],
    "Physics & Materials": ["physics", "quantum", "particle", "material", "electromagnetic", "relativity"],
    "Chemistry": ["chemistry", "chemical", "reaction", "molecule", "compound", "synthesis", "organic"],
    "Engineering": ["engineering", "mechanical", "electrical", "civil", "infrastructure", "infrastructure"],
    "Mathematics": ["mathematics", "mathematical", "proof", "theorem", "equation", "calculus"],
    "Economics & Business": ["economics", "economic", "business", "financial", "market", "trade"],
    "Environmental Science": ["environmental", "ecology", "sustainable", "pollution", "climate", "conservation"],
    "Social Sciences": ["social", "sociology", "anthropology", "psychology", "culture", "society"]
}

# Extract text
def extract_text_from_pdf(file):
    if hasattr(file, "read"):
        file_bytes = file.read()
    else:
        file_bytes = file

    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def hash_bytes(value):
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def cache_get_json(key):
    cached_value = redis_connection.get(key)
    if not cached_value:
        return None

    if isinstance(cached_value, bytes):
        cached_value = cached_value.decode("utf-8")

    try:
        return json.loads(cached_value)
    except json.JSONDecodeError:
        return None


def cache_set_json(key, value, ttl_seconds):
    redis_connection.setex(key, ttl_seconds, json.dumps(value))


def process_paper_analysis(file_bytes, file_name="uploaded.pdf"):
    text = extract_text_from_pdf(file_bytes)

    summary = extract_summary(text)
    features = extract_features(text)
    features_df = pd.DataFrame([features])
    domain_stats = get_domain_stats(text)

    if model is None:
        print("Warning: Model not loaded, using default scoring")
        score = 6.5
    else:
        score = model.predict(features_df)[0]

    words = text.split()
    if len(words) > 0:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.4:
            score -= 2

    score = max(0, min(10, score))
    recommendations = generate_recommendations(text, features, score)

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    docs_for_comparison = []
    if not dataset.empty and 'Source Title' in dataset.columns:
        docs_for_comparison = dataset["Source Title"].fillna("").tolist()

    all_docs = docs_for_comparison.copy() if docs_for_comparison else [""]
    all_docs.insert(0, text)

    vectorizer = TfidfVectorizer(max_features=500)
    tfidf = vectorizer.fit_transform(all_docs)

    similarity = cosine_similarity(tfidf)[0]
    top_indices = similarity.argsort()[-6:][::-1][1:]

    similar_papers = []
    for i in top_indices:
        if i - 1 >= 0 and i - 1 < len(dataset):
            title_col = "Source Title" if "Source Title" in dataset.columns else "title"
            similar_papers.append({
                "title": str(dataset.iloc[i - 1][title_col])[:100],
                "score": float(similarity[i])
            })

    return {
        "score": float(score),
        "features": features,
        "similar_papers": similar_papers,
        "summary": summary,
        "recommendations": recommendations,
        "domain_stats": domain_stats,
        "file_name": file_name,
    }

# Extract features
def extract_features(text):
    words = text.split()

    if len(words) == 0:
        return {
            "word_count": 0,
            "sentence_count": 0,
            "avg_word_length": 0,
            "readability": 50
        }

    return {
        "word_count": len(words),
        "sentence_count": text.count("."),
        "avg_word_length": sum(len(word) for word in words) / len(words),
        "readability": 50
    }


def sanitize_text(value, max_length=200000):
    if value is None:
        return ""

    cleaned = str(value).replace("\x00", "").strip()
    return cleaned[:max_length]


@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        file = request.files.get("file")

        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        if file.mimetype != "application/pdf":
            return jsonify({"error": "Only PDF files are allowed"}), 400

        file_bytes = file.read()
        job = analysis_queue.enqueue(process_paper_analysis, file_bytes, file.filename)
        job.meta["file_name"] = file.filename
        job.save_meta()

        return jsonify({
            "job_id": job.id,
            "status": job.get_status(),
            "status_url": f"/status/{job.id}",
        }), 202

    except Exception as e:
        return jsonify({"error": "Failed to enqueue analysis"}), 500

# Detect paper domain and get domain statistics
def get_domain_stats(text):
    """
    Detect paper domain and calculate statistics from venue database
    """
    text_lower = (text or "").lower()

    # Detect domain
    domain_scores = {}
    for domain, keywords in DOMAIN_KEYWORDS_SIMPLE.items():
        score = sum(text_lower.count(keyword) for keyword in keywords)
        if score > 0:
            domain_scores[domain] = score
    
    detected_domain = max(domain_scores, key=domain_scores.get) if domain_scores else "General Research"
    confidence = min((domain_scores.get(detected_domain, 0) / max(1, len(text_lower.split()))) * 100, 100)
    
    # Calculate domain statistics from dataset
    domain_stats = {
        "domain": detected_domain,
        "confidence": confidence,
        "total_venues": len(dataset) if not dataset.empty else 0,
        "matching_venues": 0,
        "oa_count": 0,
        "medline_count": 0,
        "active_count": 0,
        "publishers_count": 0
    }
    
    if not dataset.empty:
        # Count total statistics
        domain_stats["total_venues"] = len(dataset)
        
        # Try to count OA venues
        try:
            domain_stats["oa_count"] = len(dataset[dataset.get("OA Status", pd.Series()).str.contains("OA", case=False, na=False)])
        except:
            domain_stats["oa_count"] = 0
        
        # Try to count Medline venues
        try:
            domain_stats["medline_count"] = len(dataset[dataset.get("Medline Coverage", pd.Series()).str.contains("Yes|Indexed", case=False, na=False)])
        except:
            domain_stats["medline_count"] = 0
        
        # Try to count active venues
        try:
            domain_stats["active_count"] = len(dataset[dataset.get("Status", pd.Series()).str.contains("Active", case=False, na=False)])
        except:
            domain_stats["active_count"] = len(dataset)
        
        # Count publishers
        try:
            domain_stats["publishers_count"] = dataset.get("Publisher", pd.Series()).nunique()
        except:
            domain_stats["publishers_count"] = 0
        
        # For now, set matching_venues as domain percentage (this can be enhanced)
        domain_stats["matching_venues"] = int(len(dataset) * 0.3)  # Estimate ~30% match to domain
    
    return domain_stats

# Extract or generate summary
def extract_summary(text, max_sentences=5):
    """
    Extract abstract if available, otherwise generate extractive summary
    """
    # Try to find abstract section
    abstract_patterns = [
        r'(?i)abstract\s*\n(.*?)(?=introduction|1\.|keywords)',
        r'(?i)abstract\s*\n(.*?)(?=\n\n[A-Z])',
        r'(?i)abstract:(.*?)(?=introduction|1\.|keywords)',
    ]
    
    for pattern in abstract_patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            abstract = match.group(1).strip()
            # Clean up the abstract
            abstract = ' '.join(abstract.split())
            if len(abstract) > 100:  # Only use if substantial
                return abstract[:500] + "..." if len(abstract) > 500 else abstract
    
    # If no abstract found, use extractive summarization
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    
    if len(sentences) == 0:
        return "Unable to extract summary from the paper."
    
    # Score sentences based on word frequency
    words = re.findall(r'\w+', text.lower())
    word_freq = Counter(words)
    
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'have', 'has', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
        'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how'
    }
    
    # Calculate sentence scores
    sentence_scores = {}
    for i, sentence in enumerate(sentences[:50]):  # Consider first 50 sentences
        score = 0
        words_in_sentence = re.findall(r'\w+', sentence.lower())
        for word in words_in_sentence:
            if word not in stop_words:
                score += word_freq.get(word, 0)
        sentence_scores[i] = score
    
    # Get top sentences
    top_sentence_indices = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:max_sentences]
    top_sentence_indices.sort()  # Maintain order
    
    summary_sentences = [sentences[i] for i in top_sentence_indices]
    summary = ' '.join(summary_sentences)
    
    # Limit summary length
    if len(summary) > 500:
        summary = summary[:500] + "..."
    
    return summary

# Generate recommendations based on paper analysis
def generate_recommendations(text, features, score):
    """
    Generate specific recommendations based on paper analysis
    """
    recommendations = []
    word_count = features.get("word_count", 0)
    sentence_count = features.get("sentence_count", 0)
    avg_word_length = features.get("avg_word_length", 0)
    
    # Word count analysis
    if word_count < 2000:
        recommendations.append({
            "title": "Expand Content",
            "description": f"Your paper has {word_count} words. Consider expanding to at least 3,000-5,000 words for a comprehensive research paper. Add more detail to methodology, results, and discussion sections."
        })
    elif word_count > 15000:
        recommendations.append({
            "title": "Optimize Length",
            "description": f"Your paper has {word_count} words, which may be too lengthy. Consider condensing or removing redundant sections while maintaining key information and research quality."
        })
    else:
        recommendations.append({
            "title": "Content Length",
            "description": f"Your paper's word count ({word_count} words) is within a good range for research papers. Focus on maintaining quality over quantity."
        })
    
    # Sentence structure analysis
    if word_count > 0 and sentence_count > 0:
        avg_sentence_length = word_count / sentence_count
        if avg_sentence_length > 30:
            recommendations.append({
                "title": "Simplify Sentence Structure",
                "description": f"Average sentence length is {avg_sentence_length:.1f} words, which may reduce readability. Break down complex sentences into shorter, clearer statements for better comprehension."
            })
        elif avg_sentence_length < 10:
            recommendations.append({
                "title": "Enhance Sentence Variety",
                "description": f"Average sentence length is {avg_sentence_length:.1f} words. Try varying sentence length and structure to improve flow and maintain reader engagement."
            })
    
    # Vocabulary analysis
    if avg_word_length < 4.5:
        recommendations.append({
            "title": "Enhance Academic Vocabulary",
            "description": f"Average word length is {avg_word_length:.1f} characters. Consider using more sophisticated academic terminology to elevate the scholarly tone of your paper."
        })
    elif avg_word_length > 6:
        recommendations.append({
            "title": "Improve Clarity",
            "description": f"Average word length is {avg_word_length:.1f} characters. Some words may be overly complex. Balance technical terminology with clear explanations for accessibility."
        })
    
    # Score-based recommendations
    if score < 5:
        recommendations.append({
            "title": "Critical Improvements Needed",
            "description": "Your paper scored below 5/10. Focus on strengthening the methodology, providing clear research objectives, and improving overall organization and presentation quality."
        })
    elif score < 7:
        recommendations.append({
            "title": "Strengthen Key Sections",
            "description": "Your paper has good potential. Enhance the introduction with clearer thesis statement, expand the literature review, and provide more detailed analysis in the results section."
        })
    elif score < 8.5:
        recommendations.append({
            "title": "Polish for Excellence",
            "description": "Your paper is strong! Focus on minor refinements: enhance abstract clarity, add more citations, review formatting consistency, and ensure all tables/figures are well-labeled."
        })
    else:
        recommendations.append({
            "title": "Excellent Work",
            "description": "Your paper demonstrates high quality. Consider submitting to peer-reviewed venues or academic conferences. Continue maintaining this level of academic rigor."
        })
    
    # Repetition analysis
    words = text.split()
    if len(words) > 0:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.5:
            recommendations.append({
                "title": "Reduce Repetition",
                "description": "Your paper shows significant word repetition. Use synonyms and varied expressions to improve readability and maintain reader interest throughout the paper."
            })
    
    # Check for common issues
    if "conclusion" not in text.lower():
        recommendations.append({
            "title": "Add Conclusion Section",
            "description": "Your paper appears to lack a formal conclusion. Add a strong conclusion section that summarizes findings, implications, and suggests future research directions."
        })
    
    if len(re.findall(r'\[\d+\]|cite|ref', text, re.IGNORECASE)) < 5:
        recommendations.append({
            "title": "Increase Citations",
            "description": "Your paper has minimal citations. Strengthen your research by citing relevant literature and establishing connections to existing work in your field."
        })
    
    return recommendations


@app.route("/predict", methods=["POST"])
def predict():
    try:
        file = request.files.get("file")

        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        if file.mimetype != "application/pdf":
            return jsonify({"error": "Only PDF files are allowed"}), 400

        file_bytes = file.read()
        # Cache key based strictly on uploaded bytes
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        cached_result = cache_get_json(f"analysis:{file_hash}")
        if cached_result:
            cached_result["cached"] = True
            return jsonify(cached_result), 200

        text = extract_text_from_pdf(file_bytes)


        # Extract summary early
        summary = extract_summary(text)

        features = extract_features(text)
        features_df = pd.DataFrame([features])

        # Get domain statistics
        domain_stats = get_domain_stats(text)

        # Check if model is loaded, use default score if not
        if model is None:
            print("Warning: Model not loaded, using default scoring")
            score = 6.5  # Default middle score
        else:
            score = model.predict(features_df)[0]

        # 🔥 repetition penalty
        words = text.split()
        if len(words) > 0:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.4:
                score -= 2

        score = max(0, min(10, score))

        # Generate recommendations based on analysis
        recommendations = generate_recommendations(text, features, score)

        # Similarity matching - use Source Title as the basis for comparison
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        # Get the document titles - use 'Source Title' column from venues dataset
        docs_for_comparison = []
        paper_titles = []
        
        if not dataset.empty and 'Source Title' in dataset.columns:
            docs_for_comparison = dataset["Source Title"].fillna("").tolist()
            paper_titles = docs_for_comparison[:5]
        
        all_docs = docs_for_comparison.copy() if docs_for_comparison else [""]
        all_docs.insert(0, text)

        vectorizer = TfidfVectorizer(max_features=500)
        tfidf = vectorizer.fit_transform(all_docs)

        similarity = cosine_similarity(tfidf)[0]

        top_indices = similarity.argsort()[-6:][::-1][1:]

        similar_papers = []
        for i in top_indices:
            if i-1 >= 0 and i-1 < len(dataset):
                title_col = "Source Title" if "Source Title" in dataset.columns else "title"
                similar_papers.append({
                    "title": str(dataset.iloc[i-1][title_col])[:100],
                    "score": float(similarity[i])
                })

        result = {
            "score": float(score),
            "features": features,
            "similar_papers": similar_papers,
            "summary": summary,
            "recommendations": recommendations,
            "domain_stats": domain_stats,
            "cached": False,
        }

        # TTL: 24 hours
        cache_set_json(f"analysis:{file_hash}", result, 24 * 60 * 60)

        return jsonify(result)
    
    except Exception as e:

        print(f"Error in predict endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": f"Failed to analyze paper: {str(e)}"
        }), 500


@app.route("/status/<job_id>", methods=["GET"])
def status(job_id):
    try:
        job = Job.fetch(job_id, connection=redis_connection)
    except NoSuchJobError:
        return jsonify({"error": "Job not found"}), 404

    payload = {
        "job_id": job_id,
        "status": job.get_status(),
        "file_name": job.meta.get("file_name"),
    }

    if job.is_finished:
        payload["result"] = job.result
        file_hash = job.meta.get("file_hash")
        if file_hash and job.result:
            cache_set_json(f"analysis:{file_hash}", job.result, ANALYSIS_CACHE_TTL_SECONDS)
    elif job.is_failed:
        payload["error"] = "Analysis job failed"

    return jsonify(payload)


@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json(silent=True) or {}

    paper_text = data.get("paper_text", "")
    paper_score = data.get("paper_score", 5.0)
    paper_topic = data.get("paper_topic", "")

    venue_type = data.get("venue_type", "any")
    indexing = data.get("indexing", ["Any"])
    fee_pref = data.get("fee_pref", "Any")
    acceptance = data.get("acceptance", "Any")

    # preferences object for enhanced recommender (keep it simple for now)
    prefs = {
        "venue_type": venue_type,
        "indexing": indexing,
        "fee_pref": fee_pref,
        "acceptance": acceptance,
        "open_access_only": data.get("open_access_only", False),
        "exclude_discontinued": data.get("exclude_discontinued", False),
        "medline_only": data.get("medline_only", False),
        "min_coverage_year": data.get("min_coverage_year", 2000),
        "publisher": data.get("publisher", "any"),
        "selected_subjects": data.get("selected_subjects", []),
    }

    if not paper_text or len(str(paper_text).strip()) < 50:
        return jsonify({"error": "paper_text must be at least 50 characters"}), 400

    cache_payload = {
        "paper_text": paper_text,
        "paper_score": paper_score,
        "paper_topic": paper_topic,
        "preferences": prefs,
    }

    # Stable cache key for recommendation results
    cache_key = f"recommend:{hash_bytes(json.dumps(cache_payload, sort_keys=True, default=str))}"

    cached_result = cache_get_json(cache_key)
    if cached_result:
        cached_result["cached"] = True
        return jsonify(cached_result), 200


    if venue_db is None or getattr(venue_db, "empty", False):
        return jsonify({"error": "Venue database not available. Try again later."}), 503

    try:
        result = recommend_venues_enhanced(
            paper_text=paper_text,
            paper_score=paper_score,
            paper_topic=paper_topic,
            preferences=prefs,
            venue_db=venue_db,
            top_n=10,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    cache_set_json(cache_key, result, RECOMMENDATION_CACHE_TTL_SECONDS)

    return jsonify(result)


if __name__ == "__main__":
    app.run(host=flask_host, port=flask_port)


