import { useState } from "react";
import axios from "axios";

function VenueRecommenderEnhanced({ paperText, paperScore, paperTopic }) {
  const API_BASE_URL = process.env.REACT_APP_API_URL || "";
  // Form state
  const [venueType, setVenueType] = useState("any");
  const [openAccessOnly, setOpenAccessOnly] = useState(false);
  const [medlineOnly, setMedlineOnly] = useState(false);
  const [excludeDiscontinued, setExcludeDiscontinued] = useState(true);
  const [paperDescription, setPaperDescription] = useState("");
  const [minCoverageYear, setMinCoverageYear] = useState(2010);

  // Results state
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getScoreColor = (score) => {
    if (score > 75) return "#10b981";
    if (score > 50) return "#f59e0b";
    return "#ef4444";
  };

  const getScoreLabel = (score) => {
    if (score > 75) return "Excellent Match";
    if (score > 50) return "Good Match";
    return "Fair Match";
  };

  const handleRecommend = async () => {
    if (!paperText || !paperText.trim()) {
      setError("Please upload and analyze a research paper first");
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/recommend`,
        {
          paper_text: paperText || paperDescription,
          paper_score: paperScore || 5.0,
          paper_topic: paperTopic || paperDescription,
          venue_type: venueType,
          open_access_only: openAccessOnly,
          exclude_discontinued: excludeDiscontinued,
          medline_only: medlineOnly,
          min_coverage_year: minCoverageYear,
          selected_subjects: []
        }
      );

      setResults(response.data);
    } catch (err) {
      console.error("Recommendation error:", err);
      setError(
        err.response?.data?.error ||
        "Failed to get recommendations. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const styles = {
    container: {
      maxWidth: "1200px",
      margin: "0 auto",
      padding: "30px 20px",
      fontFamily: "system-ui, -apple-system, sans-serif"
    },
    sectionTitle: {
      fontSize: "28px",
      fontWeight: "700",
      marginBottom: "10px",
      color: "#1f2937"
    },
    sectionDescription: {
      fontSize: "14px",
      color: "#6b7280",
      marginBottom: "25px"
    },
    formCard: {
      background: "#ffffff",
      border: "1px solid #e5e7eb",
      borderRadius: "12px",
      padding: "24px",
      marginBottom: "30px",
      boxShadow: "0 1px 3px rgba(0,0,0,0.1)"
    },
    formSection: {
      marginBottom: "20px"
    },
    label: {
      display: "block",
      marginBottom: "8px"
    },
    labelText: {
      fontSize: "14px",
      fontWeight: "600",
      color: "#374151"
    },
    textarea: {
      width: "100%",
      height: "80px",
      padding: "10px",
      border: "1px solid #d1d5db",
      borderRadius: "6px",
      fontSize: "13px",
      fontFamily: "inherit",
      resize: "vertical"
    },
    hint: {
      fontSize: "12px",
      color: "#9ca3af",
      marginTop: "6px"
    },
    preferencesGrid: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
      gap: "16px",
      marginBottom: "20px"
    },
    formGroup: {
      display: "flex",
      flexDirection: "column"
    },
    select: {
      padding: "10px",
      border: "1px solid #d1d5db",
      borderRadius: "6px",
      fontSize: "13px",
      fontFamily: "inherit",
      backgroundColor: "#ffffff"
    },
    checkboxGroup: {
      display: "flex",
      alignItems: "center",
      gap: "8px",
      paddingTop: "8px"
    },
    checkbox: {
      width: "18px",
      height: "18px",
      cursor: "pointer"
    },
    checkboxLabel: {
      fontSize: "14px",
      color: "#374151",
      cursor: "pointer"
    },
    slider: {
      width: "100%",
      height: "6px",
      borderRadius: "3px",
      outline: "none",
      marginTop: "8px"
    },
    errorAlert: {
      background: "#fee2e2",
      border: "1px solid #fecaca",
      color: "#991b1b",
      padding: "12px",
      borderRadius: "6px",
      marginBottom: "16px",
      fontSize: "13px"
    },
    submitButton: {
      width: "100%",
      padding: "12px 16px",
      background: "#3b82f6",
      color: "white",
      border: "none",
      borderRadius: "6px",
      fontSize: "14px",
      fontWeight: "600",
      cursor: "pointer",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      gap: "8px",
      transition: "background 0.2s"
    },
    spinner: {
      width: "16px",
      height: "16px",
      border: "2px solid rgba(255,255,255,0.3)",
      borderTopColor: "white",
      borderRadius: "50%",
      animation: "spin 1s linear infinite"
    },
    resultsContainer: {
      marginTop: "30px"
    },
    summaryBox: {
      background: "#f0f9ff",
      border: "1px solid #bfdbfe",
      borderRadius: "8px",
      padding: "16px",
      marginBottom: "20px",
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
      gap: "16px"
    },
    summaryItem: {
      display: "flex",
      flexDirection: "column"
    },
    summaryLabel: {
      fontSize: "12px",
      color: "#6b7280",
      fontWeight: "600"
    },
    summaryValue: {
      fontSize: "16px",
      fontWeight: "700",
      color: "#1f2937",
      marginTop: "4px"
    },
    venuesList: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fill, minmax(350px, 1fr))",
      gap: "20px"
    },
    venueCard: {
      background: "white",
      border: "1px solid #e5e7eb",
      borderRadius: "12px",
      padding: "20px",
      boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
      transition: "transform 0.2s, box-shadow 0.2s"
    },
    venueHeader: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "flex-start",
      marginBottom: "12px"
    },
    venueTitleArea: {
      flex: 1
    },
    venueName: {
      fontSize: "16px",
      fontWeight: "700",
      margin: "0 0 8px 0",
      color: "#1f2937",
      wordBreak: "break-word"
    },
    venueMeta: {
      display: "flex",
      gap: "8px",
      flexWrap: "wrap"
    },
    typeTag: {
      display: "inline-block",
      background: "#dbeafe",
      color: "#1e40af",
      padding: "4px 8px",
      borderRadius: "4px",
      fontSize: "11px",
      fontWeight: "600"
    },
    domainTag: {
      display: "inline-block",
      background: "#e0e7ff",
      color: "#3730a3",
      padding: "4px 8px",
      borderRadius: "4px",
      fontSize: "11px",
      fontWeight: "600"
    },
    asjcTag: {
      display: "inline-block",
      background: "#d1e7dd",
      color: "#0f5132",
      padding: "4px 8px",
      borderRadius: "4px",
      fontSize: "11px",
      fontWeight: "600",
      marginRight: "4px"
    },
    scoreBadge: {
      borderRadius: "8px",
      padding: "12px 16px",
      color: "white",
      textAlign: "center",
      minWidth: "80px"
    },
    scoreValue: {
      fontSize: "24px",
      fontWeight: "700"
    },
    scoreLabel: {
      fontSize: "11px",
      marginTop: "2px"
    },
    scoreBarContainer: {
      width: "100%",
      height: "6px",
      background: "#e5e7eb",
      borderRadius: "3px",
      overflow: "hidden",
      marginBottom: "12px"
    },
    scoreBarFill: {
      height: "100%",
      transition: "width 0.3s ease"
    },
    venueDetails: {
      display: "grid",
      gridTemplateColumns: "repeat(2, 1fr)",
      gap: "12px",
      marginBottom: "16px",
      fontSize: "13px"
    },
    detailRow: {
      display: "flex",
      flexDirection: "column"
    },
    detailLabel: {
      color: "#6b7280",
      fontWeight: "600",
      fontSize: "11px"
    },
    detailValue: {
      color: "#1f2937",
      fontWeight: "500",
      marginTop: "2px"
    },
    reasonBox: {
      background: "#fef3c7",
      border: "1px solid #fde68a",
      borderRadius: "6px",
      padding: "12px",
      marginBottom: "12px",
      fontSize: "13px"
    },
    reasonText: {
      color: "#78350f",
      margin: "6px 0 0 0",
      fontSize: "12px"
    },
    venueLink: {
      display: "inline-block",
      background: "#3b82f6",
      color: "white",
      padding: "8px 12px",
      borderRadius: "6px",
      textDecoration: "none",
      fontSize: "12px",
      fontWeight: "600",
      transition: "background 0.2s"
    },
    viewVenueButton: {
      display: "inline-block",
      background: "#3b82f6",
      color: "white",
      padding: "10px 16px",
      borderRadius: "6px",
      border: "none",
      fontSize: "13px",
      fontWeight: "600",
      cursor: "pointer",
      transition: "background 0.2s",
      marginTop: "12px",
      width: "100%",
      textAlign: "center"
    },
    noResults: {
      textAlign: "center",
      padding: "40px",
      color: "#6b7280",
      fontSize: "14px"
    }
  };

  return (
    <div style={styles.container}>
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        a:hover { opacity: 0.9; }
        button:hover:not(:disabled) { background-color: #2563eb !important; }
      `}</style>

      <h2 style={styles.sectionTitle}>Find Suitable Venues for Submission</h2>
      <p style={styles.sectionDescription}>
        Get personalized recommendations for journals and conferences based on your research topic, quality metrics, and preferences.
      </p>

      <div style={styles.formCard}>
        {/* Additional Keywords */}
        <div style={styles.formSection}>
          <label style={styles.label}>
            <span style={styles.labelText}>Additional Keywords (Optional)</span>
          </label>
          <textarea
            value={paperDescription}
            onChange={(e) => setPaperDescription(e.target.value)}
            placeholder="Optional: Add related keywords to refine results (e.g., 'machine learning, neural networks')"
            style={styles.textarea}
            disabled={loading}
          />
          <p style={styles.hint}>
            The research domain will be automatically detected from your paper content. Add keywords to improve matching.
          </p>
        </div>

        {/* Preferences Grid */}
        <div style={styles.preferencesGrid}>
          {/* Venue Type */}
          <div style={styles.formGroup}>
            <label style={styles.label}>
              <span style={styles.labelText}>Venue Type</span>
            </label>
            <select
              value={venueType}
              onChange={(e) => setVenueType(e.target.value)}
              style={styles.select}
              disabled={loading}
            >
              <option value="any">Any</option>
              <option value="journal">Journal</option>
              <option value="conference">Conference</option>
              <option value="book">Book / Chapter</option>
            </select>
          </div>

          {/* Minimum Coverage Year */}
          <div style={styles.formGroup}>
            <label style={styles.label}>
              <span style={styles.labelText}>Coverage Since: {minCoverageYear}</span>
            </label>
            <input
              type="range"
              min="1980"
              max="2026"
              value={minCoverageYear}
              onChange={(e) => setMinCoverageYear(Number(e.target.value))}
              style={styles.slider}
              disabled={loading}
            />
            <p style={styles.hint}>Venues with coverage from {minCoverageYear} onwards</p>
          </div>
        </div>

        {/* Checkboxes Section */}
        <div style={styles.preferencesGrid}>
          <div style={styles.formGroup}>
            <div style={styles.checkboxGroup}>
              <input
                type="checkbox"
                id="openAccess"
                checked={openAccessOnly}
                onChange={(e) => setOpenAccessOnly(e.target.checked)}
                style={styles.checkbox}
                disabled={loading}
              />
              <label htmlFor="openAccess" style={styles.checkboxLabel}>
                Open Access Only
              </label>
            </div>
            <p style={styles.hint}>Show only venues with open access publications</p>
          </div>

          <div style={styles.formGroup}>
            <div style={styles.checkboxGroup}>
              <input
                type="checkbox"
                id="medline"
                checked={medlineOnly}
                onChange={(e) => setMedlineOnly(e.target.checked)}
                style={styles.checkbox}
                disabled={loading}
              />
              <label htmlFor="medline" style={styles.checkboxLabel}>
                Medline Indexed Only
              </label>
            </div>
            <p style={styles.hint}>Show only Medline-indexed journals (biomedical)</p>
          </div>

          <div style={styles.formGroup}>
            <div style={styles.checkboxGroup}>
              <input
                type="checkbox"
                id="active"
                checked={excludeDiscontinued}
                onChange={(e) => setExcludeDiscontinued(e.target.checked)}
                style={styles.checkbox}
                disabled={loading}
              />
              <label htmlFor="active" style={styles.checkboxLabel}>
                Active Venues Only
              </label>
            </div>
            <p style={styles.hint}>Exclude discontinued and inactive venues</p>
          </div>
        </div>

        {/* Error Message */}
        {error && <div style={styles.errorAlert}>{error}</div>}

        {/* Submit Button */}
        <button
          onClick={handleRecommend}
          disabled={loading}
          style={{
            ...styles.submitButton,
            opacity: loading ? 0.7 : 1,
            cursor: loading ? "not-allowed" : "pointer"
          }}
        >
          {loading ? (
            <>
              <span style={styles.spinner}></span>
              Finding Venues...
            </>
          ) : (
            "Get Recommendations"
          )}
        </button>
      </div>

      {/* Results */}
      {results && (
        <div style={styles.resultsContainer}>
          {/* Summary Info */}
          {results.paper_domain && (
            <div style={styles.summaryBox}>
              <div style={styles.summaryItem}>
                <span style={styles.summaryLabel}>Detected Domain:</span>
                <span style={styles.summaryValue}>
                  {(results.paper_domain || "Unknown").replace(/_/g, " ").toUpperCase()}
                </span>
              </div>
              <div style={styles.summaryItem}>
                <span style={styles.summaryLabel}>Paper Quality:</span>
                <span style={styles.summaryValue}>{paperScore || 5.0}/10.0</span>
              </div>
              <div style={styles.summaryItem}>
                <span style={styles.summaryLabel}>Matches Found:</span>
                <span style={styles.summaryValue}>
                  {(results.matches_found || 0)} / {(results.total_venues_evaluated || 0)}
                </span>
              </div>
              <div style={styles.summaryItem}>
                <span style={styles.summaryLabel}>Search Filters:</span>
                <span style={styles.summaryValue}>
                  {[
                    openAccessOnly && "OA",
                    medlineOnly && "Medline",
                    excludeDiscontinued && "Active"
                  ]
                    .filter(Boolean)
                    .join(", ") || "None"}
                </span>
              </div>
            </div>
          )}

          {/* Recommendations List */}
          {results.venues && results.venues.length > 0 ? (
            <div style={styles.venuesList}>
              {results.venues.map((venue, index) => (
                <div key={index} style={styles.venueCard}>
                  {/* Venue Header */}
                  <div style={styles.venueHeader}>
                    <div style={styles.venueTitleArea}>
                      <h3 style={styles.venueName}>{venue.name}</h3>
                      <div style={styles.venueMeta}>
                        <span style={styles.typeTag}>
                          {(venue.type || "Unknown").toUpperCase()}
                        </span>
                        {venue.is_new_jan_2026 && (
                          <span style={{ ...styles.typeTag, background: "#fce7f3", color: "#831843" }}>
                            🆕 NEW 2026
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Match Score Badge */}
                    <div style={{ ...styles.scoreBadge, backgroundColor: getScoreColor(venue.match_score) }}>
                      <div style={styles.scoreValue}>{Math.round(venue.match_score)}%</div>
                      <div style={styles.scoreLabel}>{getScoreLabel(venue.match_score)}</div>
                    </div>
                  </div>

                  {/* Score Bar */}
                  <div style={styles.scoreBarContainer}>
                    <div
                      style={{
                        ...styles.scoreBarFill,
                        width: `${Math.min(venue.match_score, 100)}%`,
                        backgroundColor: getScoreColor(venue.match_score)
                      }}
                    />
                  </div>

                  {/* ASJC Subjects */}
                  {venue.matched_asjc_subjects && venue.matched_asjc_subjects.length > 0 && (
                    <div style={{ marginBottom: "12px" }}>
                      <div style={{ fontSize: "11px", fontWeight: "600", color: "#6b7280", marginBottom: "4px" }}>
                        Subject Areas:
                      </div>
                      <div>
                        {venue.matched_asjc_subjects.slice(0, 3).map((subject, idx) => (
                          <span key={idx} style={styles.asjcTag}>
                            {subject}
                          </span>
                        ))}
                        {venue.matched_asjc_subjects.length > 3 && (
                          <span style={{ fontSize: "11px", color: "#6b7280" }}>
                            +{venue.matched_asjc_subjects.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Venue Details */}
                  <div style={styles.venueDetails}>
                    <div style={styles.detailRow}>
                      <span style={styles.detailLabel}>Publisher:</span>
                      <span style={styles.detailValue}>{venue.publisher || "N/A"}</span>
                    </div>
                    <div style={styles.detailRow}>
                      <span style={styles.detailLabel}>Status:</span>
                      <span style={styles.detailValue}>
                        {venue.active_status ? "✓ Active" : "⊘ Discontinued"}
                      </span>
                    </div>
                    <div style={styles.detailRow}>
                      <span style={styles.detailLabel}>Coverage:</span>
                      <span style={styles.detailValue}>{venue.coverage_year_range || "N/A"}</span>
                    </div>
                    <div style={styles.detailRow}>
                      <span style={styles.detailLabel}>OA Status:</span>
                      <span style={styles.detailValue}>
                        {venue.open_access ? "✓ Yes" : "✗ No"}
                      </span>
                    </div>
                    <div style={styles.detailRow}>
                      <span style={styles.detailLabel}>Medline:</span>
                      <span style={styles.detailValue}>
                        {venue.medline_coverage ? "✓ Yes" : "✗ No"}
                      </span>
                    </div>
                    <div style={styles.detailRow}>
                      <span style={styles.detailLabel}>Language:</span>
                      <span style={styles.detailValue}>{venue.language || "N/A"}</span>
                    </div>
                  </div>

                  {/* Recommendation Reason */}
                  <div style={styles.reasonBox}>
                    <strong>Why recommended:</strong>
                    <p style={styles.reasonText}>{venue.reason || "Good match for your research"}</p>
                  </div>

                  {/* View Venue Button */}
                  <button
                    onClick={() => {
                      // Open Scopus journal profile directly using Source Record ID
                      if (venue.sourcerecord_id) {
                        const scopusUrl = `https://www.scopus.com/sourceid/${venue.sourcerecord_id}`;
                        window.open(scopusUrl, '_blank');
                      } else {
                        // Fallback to search if no sourcerecord_id
                        const scopusUrl = `https://www.scopus.com/sources/search?q=${encodeURIComponent(venue.name)}`;
                        window.open(scopusUrl, '_blank');
                      }
                    }}
                    style={styles.viewVenueButton}
                    onMouseEnter={(e) => e.target.style.backgroundColor = "#2563eb"}
                    onMouseLeave={(e) => e.target.style.backgroundColor = "#3b82f6"}
                  >
                    👁️ View Venue
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div style={styles.noResults}>
              <p>No venues found matching your criteria. Try adjusting your filters.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default VenueRecommenderEnhanced;
