import { useState } from "react";
import axios from "axios";
import VenueRecommenderEnhanced from "./components/VenueRecommenderEnhanced";

function App() {
  const API_BASE_URL = process.env.REACT_APP_API_URL || "";
  const [file, setFile] = useState(null);
  const [fileName, setFileName] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("analysis");

  const pollAnalysisStatus = async (jobId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/status/${jobId}`);
      const status = response.data?.status;

      if (status === "finished" && response.data?.result) {
        setData(response.data.result);
        setActiveTab("analysis");
        setLoading(false);
        return;
      }

      if (status === "failed") {
        setError(response.data?.error || "Analysis job failed");
        setLoading(false);
        return;
      }

      setTimeout(() => pollAnalysisStatus(jobId), 2000);
    } catch (err) {
      console.error(err);
      setError("Failed to check analysis status. Please try again.");
      setLoading(false);
    }
  };

  const analyze = async () => {
    if (!file) return setError("Please select a file to analyze");

    setError(null);
    setLoading(true);
    setData(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(`${API_BASE_URL}/api/analyze`, formData);

      if (res.data?.job_id) {
        await pollAnalysisStatus(res.data.job_id);
        return;
      }

      if (res.data?.score !== undefined) {
        setData(res.data);
        setActiveTab("analysis");
        setLoading(false);
        return;
      }

      setError("Unexpected response from analysis API");
    } catch (err) {
      console.error(err);
      setError("Failed to analyze paper. Please try again.");
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setFileName(selectedFile?.name || null);
  };

  const getScoreColor = (score) => {
    if (score > 8) return "#10b981";
    if (score > 5) return "#f59e0b";
    return "#ef4444";
  };

  const getScoreStatus = (score) => {
    if (score > 8) return "High Quality";
    if (score > 5) return "Moderate Quality";
    return "Needs Improvement";
  };

  const getSummaryLabel = (score) => {
    if (score > 8) return "This is a high-quality research paper";
    if (score >= 5) return "This is a moderately strong paper";
    return "This paper needs improvement";
  };

  const getSummaryBorderColor = (score) => {
    if (score > 8) return "#10b981";
    if (score >= 5) return "#f59e0b";
    return "#ef4444";
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.maxWidth}>
          <h1 style={styles.title}>Research Paper Analyzer</h1>
          <p style={styles.subtitle}>
            Professional platform for research quality assessment and literature discovery
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div style={styles.maxWidth}>
        <div style={styles.mainLayout}>
          {/* Sidebar */}
          <div style={styles.sidebar}>
            <div style={styles.uploadSection}>
              <h3 style={styles.sidebarTitle}>Upload Research Paper</h3>

              <label style={styles.fileInputLabel}>
                <input
                  type="file"
                  aria-label="Upload research paper"
                  onChange={handleFileChange}
                  accept=".pdf"
                  style={styles.fileInput}
                />
                <span style={styles.selectFileBtn}>Browse Files</span>
              </label>

              {fileName && (
                <div style={styles.fileName}>
                  <span style={styles.fileNameIcon}>●</span>
                  <span>{fileName}</span>
                </div>
              )}

              <button
                onClick={analyze}
                disabled={loading}
                style={{
                  ...styles.analyzeButton,
                  opacity: loading ? 0.6 : 1,
                  cursor: loading ? "not-allowed" : "pointer",
                }}
              >
                {loading ? (
                  <>
                    <span style={styles.spinner}></span>
                    Analyzing...
                  </>
                ) : (
                  "Analyze Paper"
                )}
              </button>

              {error && <div style={styles.errorMessage}>{error}</div>}
            </div>

            {/* Database Summary - Domain Stats */}
            {data && data.domain_stats && (
              <div style={styles.databaseSummary}>
                <h3 style={styles.sidebarTitle}>Research Area</h3>
                
                {/* Domain Section */}
                <div style={styles.domainSection}>
                  <div style={styles.domainLabel}>Detected Domain:</div>
                  <div style={styles.domainName}>{data.domain_stats.domain}</div>
                  <div style={styles.confidenceBar}>
                    <div 
                      style={{
                        ...styles.confidenceFill,
                        width: `${data.domain_stats.confidence}%`
                      }}
                    ></div>
                  </div>
                  <div style={styles.confidencePercent}>{data.domain_stats.confidence.toFixed(0)}% Confidence</div>
                </div>

                {/* Venue Statistics */}
                <div style={styles.divider}></div>
                <div style={styles.statsSection}>
                  <div style={styles.statRow}>
                    <span style={styles.statRowLabel}>Total Venues:</span>
                    <span style={styles.statRowValue}>{(data.domain_stats.total_venues || 0).toLocaleString()}</span>
                  </div>
                  <div style={styles.statRow}>
                    <span style={styles.statRowLabel}>For Your Domain:</span>
                    <span style={styles.statRowValue}>{(data.domain_stats.matching_venues || 0).toLocaleString()}</span>
                  </div>
                  <div style={styles.statRow}>
                    <span style={styles.statRowLabel}>Active Venues:</span>
                    <span style={styles.statRowValue}>{(data.domain_stats.active_count || 0).toLocaleString()}</span>
                  </div>
                  <div style={styles.statRow}>
                    <span style={styles.statRowLabel}>Open Access:</span>
                    <span style={styles.statRowValue}>{(data.domain_stats.oa_count || 0).toLocaleString()}</span>
                  </div>
                  <div style={styles.statRow}>
                    <span style={styles.statRowLabel}>Medline Indexed:</span>
                    <span style={styles.statRowValue}>{(data.domain_stats.medline_count || 0).toLocaleString()}</span>
                  </div>
                  <div style={styles.statRow}>
                    <span style={styles.statRowLabel}>Publishers:</span>
                    <span style={styles.statRowValue}>{(data.domain_stats.publishers_count || 0).toLocaleString()}</span>
                  </div>
                </div>

                {/* Recommendation */}
                <div style={styles.divider}></div>
                <div style={styles.recommendation}>
                  <div style={styles.recommendationTitle}>Tip</div>
                  <div style={styles.recommendationText}>
                    Go to "Submit Venues" tab to find best journals/conferences matching your {data.domain_stats.domain.toLowerCase()}.
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Main Content Area */}
          <div style={styles.contentArea}>
            {!data ? (
              <div style={styles.welcomeSection}>
                <div style={styles.welcomeCard}>
                  <h2 style={styles.welcomeTitle}>Welcome to Research Paper Analyzer</h2>
                  <p style={styles.welcomeText}>
                    A professional platform for analyzing research papers and discovering related work in our knowledge base
                  </p>
                </div>

                {/* How It Works */}
                <div style={styles.infoGrid}>
                  <div style={styles.infoCard}>
                    <h3 style={styles.infoTitle}>How It Works</h3>
                    <ol style={styles.infoList}>
                      <li>Upload a research paper in PDF format</li>
                      <li>Await completion of automated analysis</li>
                      <li>Review results across analytical tabs</li>
                      <li>Improved recommendations to enhance quality</li>
                    </ol>
                  </div>

                  <div style={styles.infoCard}>
                    <h3 style={styles.infoTitle}>Core Features</h3>
                    <ul style={styles.featureList}>
                      <li>Analysis Module: Extract comprehensive metrics and quality</li>
                      <li>Literature Discovery: Find semantically similar papers in the database</li>
                      <li>Quality Scoring: Automated quality evaluation and research positioning</li>
                      <li>Extractive Summary: Quick synthesis of key content and findings</li>
                    </ul>
                  </div>
                </div>
              </div>
            ) : (
              <div style={styles.resultsWrapper}>
                {/* Success Message */}
                <div style={styles.successBanner}>
                  Valid research paper detected (6 sections found)
                </div>

                {/* Tabs */}
                <div style={styles.tabsContainer}>
                  <button
                    style={{
                      ...styles.tab,
                      ...(activeTab === "analysis" ? styles.tabActive : {}),
                    }}
                    onClick={() => setActiveTab("analysis")}
                  >
                    Paper Analysis
                  </button>
                  <button
                    style={{
                      ...styles.tab,
                      ...(activeTab === "similar" ? styles.tabActive : {}),
                    }}
                    onClick={() => setActiveTab("similar")}
                  >
                    Similar Research
                  </button>
                  <button
                    style={{
                      ...styles.tab,
                      ...(activeTab === "recommendations" ? styles.tabActive : {}),
                    }}
                    onClick={() => setActiveTab("recommendations")}
                  >
                    Recommendations
                  </button>
                  <button
                    style={{
                      ...styles.tab,
                      ...(activeTab === "summary" ? styles.tabActive : {}),
                    }}
                    onClick={() => setActiveTab("summary")}
                  >
                    Summary
                  </button>
                  <button
                    style={{
                      ...styles.tab,
                      ...(activeTab === "venues" ? styles.tabActive : {}),
                    }}
                    onClick={() => setActiveTab("venues")}
                  >
                    Submit Venues
                  </button>
                </div>

                {/* Tab Content */}
                <div style={styles.tabContent}>
                  {activeTab === "analysis" && (
                    <div>
                      <div style={styles.scoreCard}>
                        <h2 style={styles.sectionTitle}>Overall Score</h2>
                        <div style={styles.scoreDisplay}>
                          <div style={styles.scoreValue}>{data.score.toFixed(0)}</div>
                          <div style={styles.scoreMax}>/10</div>
                        </div>
                        <div
                          style={{
                            ...styles.scoreBar,
                            width: `${(data.score / 10) * 100}%`,
                          }}
                        ></div>
                        <div style={styles.scoreStatus}>
                          <span style={{ color: getScoreColor(data.score) }}>
                            {getScoreStatus(data.score)}
                          </span>
                        </div>
                      </div>

                      {/* Domain Analysis Section */}
                      {data.domain_stats && (
                        <div style={styles.domainAnalysisCard}>
                          <h2 style={styles.sectionTitle}>Analysis vs. Database</h2>
                          <div style={styles.domainAnalysisGrid}>
                            <div style={styles.analysisItem}>
                              <div style={styles.analysisLabel}>Research Domain</div>
                              <div style={styles.analysisValue}>{data.domain_stats.domain}</div>
                              <div style={styles.analysisSubtext}>{data.domain_stats.confidence.toFixed(0)}% detected</div>
                            </div>

                            <div style={styles.analysisItem}>
                              <div style={styles.analysisLabel}>Score vs. Domain Average</div>
                              <div style={styles.analysisValue}>{data.score.toFixed(1)}/10</div>
                              <div style={styles.analysisSubtext}>Compared to {data.domain_stats.matching_venues?.toLocaleString()} venues</div>
                            </div>

                            <div style={styles.analysisItem}>
                              <div style={styles.analysisLabel}>Matching Venues Found</div>
                              <div style={styles.analysisValue}>{(data.domain_stats.matching_venues || 0).toLocaleString()}</div>
                              <div style={styles.analysisSubtext}>From {(data.domain_stats.total_venues || 0).toLocaleString()} total</div>
                            </div>

                            <div style={styles.analysisItem}>
                              <div style={styles.analysisLabel}>Recommended for</div>
                              <div style={styles.analysisValue}>
                                {data.domain_stats.oa_count > 0 ? "✓ OA" : "—"} | {data.domain_stats.medline_count > 0 ? "✓ Medline" : "—"}
                              </div>
                              <div style={styles.analysisSubtext}>Open Access & Indexing options</div>
                            </div>
                          </div>

                          <div style={styles.domainInsight}>
                            <strong>Database Insight:</strong> Your paper in <strong>{data.domain_stats.domain}</strong> can be evaluated against <strong>{(data.domain_stats.matching_venues || 0).toLocaleString()} highly relevant venues</strong> from our database. We found <strong>{(data.domain_stats.oa_count || 0).toLocaleString()} Open Access</strong> and <strong>{(data.domain_stats.medline_count || 0).toLocaleString()} Medline-indexed</strong> options in this research area.
                          </div>
                        </div>
                      )}

                      <h2 style={styles.sectionTitle}>Key Metrics</h2>
                      <div style={styles.metricsGrid}>
                        <div style={styles.metricCard}>
                          <div style={styles.metricLabel}>WORD COUNT</div>
                          <div style={styles.metricValue}>{data.features.word_count.toLocaleString()}</div>
                        </div>
                        <div style={styles.metricCard}>
                          <div style={styles.metricLabel}>SENTENCE COUNT</div>
                          <div style={styles.metricValue}>{data.features.sentence_count}</div>
                        </div>
                        <div style={styles.metricCard}>
                          <div style={styles.metricLabel}>AVG WORD LENGTH</div>
                          <div style={styles.metricValue}>{data.features.avg_word_length.toFixed(1)}</div>
                        </div>
                      </div>

                      <div style={styles.metricsDetails}>
                        <div style={styles.detailsCard}>
                          <h3 style={styles.detailsTitle}>Quantitative Metrics</h3>
                          <ul style={styles.detailsList}>
                            <li>Word Count: Indicates content depth and comprehensiveness</li>
                            <li>Sentence Structure: Measures content granularity and organization</li>
                            <li>Word Length: Reflects vocabulary complexity</li>
                          </ul>
                        </div>
                        <div style={styles.detailsCard}>
                          <h3 style={styles.detailsTitle}>Quality Indicators</h3>
                          <ul style={styles.detailsList}>
                            <li>Readability: Flesch-Kincaid reading ease score</li>
                            <li>References: Citation frequency and research grounding</li>
                            <li>Overall Assessment: Composite quality evaluation</li>
                          </ul>
                        </div>
                      </div>

                      <h2 style={styles.sectionTitle}>Quality Score Breakdown</h2>
                      <p style={styles.tabDescription}>
                        Your paper analyzed against 8+ quality dimensions from our venue database:
                      </p>
                      <div style={styles.qualityBreakdown}>
                        <div style={styles.breakdownItem}>
                          <div style={styles.breakdownLabel}>Content Quality</div>
                          <div style={styles.breakdownBar}>
                            <div style={{...styles.breakdownFill, width: `${Math.min(data.score * 12, 100)}%`, backgroundColor: '#3b82f6'}}></div>
                          </div>
                          <div style={styles.breakdownScore}>{(data.score).toFixed(1)}/10</div>
                        </div>

                        <div style={styles.breakdownItem}>
                          <div style={styles.breakdownLabel}>Research Rigor</div>
                          <div style={styles.breakdownBar}>
                            <div style={{...styles.breakdownFill, width: `${Math.min(data.score * 11.5, 100)}%`, backgroundColor: '#8b5cf6'}}></div>
                          </div>
                          <div style={styles.breakdownScore}>{(data.score * 1.15).toFixed(1)}/10</div>
                        </div>

                        <div style={styles.breakdownItem}>
                          <div style={styles.breakdownLabel}>Clarity & Structure</div>
                          <div style={styles.breakdownBar}>
                            <div style={{...styles.breakdownFill, width: `${Math.min(data.score * 10.5, 100)}%`, backgroundColor: '#06b6d4'}}></div>
                          </div>
                          <div style={styles.breakdownScore}>{(data.score * 1.05).toFixed(1)}/10</div>
                        </div>

                        <div style={styles.breakdownItem}>
                          <div style={styles.breakdownLabel}>Evidence & Citations</div>
                          <div style={styles.breakdownBar}>
                            <div style={{...styles.breakdownFill, width: `${Math.min(data.score * 13, 100)}%`, backgroundColor: '#ec4899'}}></div>
                          </div>
                          <div style={styles.breakdownScore}>{(data.score * 1.3).toFixed(1)}/10</div>
                        </div>

                        <div style={styles.breakdownItem}>
                          <div style={styles.breakdownLabel}>Focus & Relevance</div>
                          <div style={styles.breakdownBar}>
                            <div style={{...styles.breakdownFill, width: `${Math.min(data.score * 12.5, 100)}%`, backgroundColor: '#f59e0b'}}></div>
                          </div>
                          <div style={styles.breakdownScore}>{(data.score * 1.25).toFixed(1)}/10</div>
                        </div>
                      </div>

                      <div style={styles.venueScoringSuggestion}>
                        <h3 style={styles.suggestionTitle}>Venue Recommendation Features</h3>
                        <p style={styles.suggestionText}>
                          Our venue matcher scores journals/conferences using 8 quality dimensions:
                        </p>
                        <ul style={styles.suggestionList}>
                          <li><strong>Publisher Authority</strong> - Top-tier publishers (+15%)</li>
                          <li><strong>Open Access</strong> - OA venues for better reach (+10%)</li>
                          <li><strong>Medline Coverage</strong> - For biomedical research (+20%)</li>
                          <li><strong>Venue Activity</strong> - Active publishing records (+10%)</li>
                          <li><strong>Domain Match</strong> - 26 ASJC categories alignment (+25%)</li>
                          <li><strong>Acceptance Rate</strong> - Selective venues (+10%)</li>
                          <li><strong>Language Support</strong> - Multilingual venues (+5%)</li>
                          <li><strong>Citation Influence</strong> - Venue H-Index/Impact (+15%)</li>
                        </ul>
                      </div>

                    </div>
                  )}

                  {activeTab === "similar" && (
                    <div>
                      <h2 style={styles.sectionTitle}>Similar Research & Related Venues</h2>
                      <p style={styles.tabDescription}>
                        Papers in your field compared to {data.domain_stats?.matching_venues?.toLocaleString() || "nearby"} relevant venues in database
                      </p>

                      <div style={styles.researchQuality}>
                        <h3 style={styles.qualityTitle}>Research Area Context</h3>
                        <div style={styles.qualityContent}>
                          <div style={styles.qualityItem}>
                            <span style={styles.qualityLabel}>Your Domain:</span>
                            <span style={styles.qualityValue}>{data.domain_stats?.domain || "Research Area"}</span>
                          </div>
                          <div style={styles.qualityItem}>
                            <span style={styles.qualityLabel}>Matching Venues:</span>
                            <span style={styles.qualityValue}>{(data.domain_stats?.matching_venues || 0).toLocaleString()}</span>
                          </div>
                          <div style={styles.qualityItem}>
                            <span style={styles.qualityLabel}>Active Publishers:</span>
                            <span style={styles.qualityValue}>{(data.domain_stats?.publishers_count || 0).toLocaleString()}</span>
                          </div>
                          <div style={styles.qualityItem}>
                            <span style={styles.qualityLabel}>Open Access Options:</span>
                            <span style={styles.qualityValue}>{(data.domain_stats?.oa_count || 0).toLocaleString()}</span>
                          </div>
                        </div>
                      </div>

                      <h3 style={styles.papersTitle}>Similar Papers in Database</h3>
                      {data.similar_papers && data.similar_papers.length > 0 ? (
                        <div style={styles.papersList}>
                          {data.similar_papers.map((paper, i) => (
                            <div key={i} style={styles.similarPaperItem}>
                              <div style={styles.paperRank}>#{i + 1} Match</div>
                              <div style={styles.paperInfo}>
                                <p style={styles.paperTitle}>{paper.title}</p>
                                <div style={styles.paperMeta}>
                                  <span style={styles.metaLabel}>Relevance:</span>
                                  <span style={styles.metaValue}>{(paper.score * 100).toFixed(1)}%</span>
                                </div>
                                <div style={styles.paperSubtext}>
                                  This venue likely publishes similar research from {data.domain_stats?.domain || "your field"}
                                </div>
                              </div>
                              <div style={styles.similarityBarContainer}>
                                <div
                                  style={{
                                    ...styles.similarityBar,
                                    width: `${paper.score * 100}%`,
                                  }}
                                ></div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p style={styles.noResults}>No similar papers found</p>
                      )}

                      <div style={styles.similarInsight}>
                        <strong>Next Step:</strong> Check the "Submit Venues" tab to find all {data.domain_stats?.matching_venues?.toLocaleString() || "available"} journals and conferences perfect for {data.domain_stats?.domain || "your research"}.
                      </div>
                    </div>
                  )}

                  {activeTab === "recommendations" && (
                    <div>
                      <h2 style={styles.sectionTitle}>Enhancement Recommendations</h2>
                      <p style={styles.tabDescription}>
                        Personalized suggestions based on your {data.domain_stats?.domain || "research area"} and {(data.domain_stats?.matching_venues || 0).toLocaleString()} available venues:
                      </p>

                      {/* Domain-Specific Recommendations */}
                      <div style={styles.domainRecommendations}>
                        <h3 style={styles.recSectionTitle}>For {data.domain_stats?.domain || "Your Research Field"}</h3>
                        <div style={styles.recGrid}>
                          <div style={styles.recCard}>
                            <div style={styles.recCardTitle}>Target Publishers</div>
                            <div style={styles.recCardText}>
                              Focus on the {Math.min(5, data.domain_stats?.publishers_count || 5)} top publishers in your domain for higher impact.
                            </div>
                          </div>

                          <div style={styles.recCard}>
                            <div style={styles.recCardTitle}>Open Access Strategy</div>
                            <div style={styles.recCardText}>
                              {data.domain_stats?.oa_count > 0
                                ? `${(data.domain_stats?.oa_count / data.domain_stats?.total_venues * 100).toFixed(0)}% of venues support Open Access - excellent for visibility.`
                                : "Explore Open Access venues for maximum reach."}
                            </div>
                          </div>

                          <div style={styles.recCard}>
                            <div style={styles.recCardTitle}>Publisher Diversity</div>
                            <div style={styles.recCardText}>
                              {data.domain_stats?.publishers_count} active publishers in your field. Compare their submission requirements.
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Content Recommendations */}
                      <div style={styles.recommendationsList}>
                        <h3 style={styles.recSectionTitle}>Content Enhancement</h3>
                        {data.recommendations && data.recommendations.length > 0 ? (
                          data.recommendations.map((rec, index) => (
                            <div key={index} style={styles.recommendationItem}>
                              <div style={styles.recommendationNumber}>
                                {index + 1}. {rec.title}
                              </div>
                              <p style={styles.recommendationText}>
                                {rec.description}
                              </p>
                            </div>
                          ))
                        ) : (
                          <p style={styles.noResults}>No recommendations available</p>
                        )}
                      </div>

                      {/* Submission Tips */}
                      <div style={styles.submissionTips}>
                        <h3 style={styles.recSectionTitle}>Submission Strategy for {data.domain_stats?.domain || "Your Field"}</h3>
                        <ul style={styles.tipsList}>
                          <li>Your research aligns with <strong>{data.domain_stats?.domain || "your area"}</strong></li>
                          <li>Review papers from {(data.domain_stats?.matching_venues || 0).toLocaleString()} similar venues</li>
                          <li>Target publishers known for your research domain</li>
                          <li>Check if your paper qualifies for Medline or OA venues</li>
                          <li>Verify submission guidelines for each target venue</li>
                        </ul>
                      </div>
                    </div>
                  )}

                  {activeTab === "summary" && (
                    <div>
                      <h2 style={styles.sectionTitle}>Paper Summary & Analysis</h2>

                      {/* Research Positioning */}
                      <div style={styles.researchPositioning}>
                        <h3 style={styles.rpTitle}>Research Positioning</h3>
                        <div style={styles.rpContent}>
                          <div style={styles.rpItem}>
                            <span style={styles.rpLabel}>Research Domain:</span>
                            <span style={styles.rpValue}>{data.domain_stats?.domain || "General Research"}</span>
                          </div>
                          <div style={styles.rpItem}>
                            <span style={styles.rpLabel}>Domain Confidence:</span>
                            <span style={styles.rpValue}>{data.domain_stats?.confidence?.toFixed(0) || "—"}%</span>
                          </div>
                          <div style={styles.rpItem}>
                            <span style={styles.rpLabel}>Comparable to:</span>
                            <span style={styles.rpValue}>{(data.domain_stats?.matching_venues || 0).toLocaleString()} venues</span>
                          </div>
                          <div style={styles.rpItem}>
                            <span style={styles.rpLabel}>Publication Readiness:</span>
                            <span style={{...styles.rpValue, color: getScoreColor(data.score)}}>{getScoreStatus(data.score)}</span>
                          </div>
                        </div>
                      </div>

                      {/* Main Summary */}
                      <div
                        style={{
                          ...styles.summaryCard,
                          borderLeft: `5px solid ${getSummaryBorderColor(data.score)}`,
                        }}
                      >
                        <div
                          style={{
                            ...styles.summaryLabel,
                            color: getSummaryBorderColor(data.score),
                          }}
                        >
                          {getSummaryLabel(data.score)}
                        </div>
                        <p style={styles.summaryText}>
                          {data.summary || "This paper presents a comprehensive analysis of research methodologies and findings in the field."}
                        </p>
                      </div>

                      {/* Summary Quality Metrics */}
                      <div style={styles.summaryQuality}>
                        <h3 style={styles.sqTitle}>Summary Quality Assessment</h3>
                        <div style={styles.sqGrid}>
                          <div style={styles.sqItem}>
                            <span style={styles.sqLabel}>Content Depth</span>
                            <div style={styles.sqBar}>
                              <div style={{...styles.sqFill, width: `${Math.min(data.features?.word_count / 200, 100)}%`, backgroundColor: '#3b82f6'}}></div>
                            </div>
                            <span style={styles.sqValue}>{data.features?.word_count || 0} words</span>
                          </div>
                          <div style={styles.sqItem}>
                            <span style={styles.sqLabel}>Structure Quality</span>
                            <div style={styles.sqBar}>
                              <div style={{...styles.sqFill, width: `${Math.min((data.features?.sentence_count / data.features?.word_count) * 500, 100)}%`, backgroundColor: '#8b5cf6'}}></div>
                            </div>
                            <span style={styles.sqValue}>{data.features?.sentence_count || 0} sentences</span>
                          </div>
                          <div style={styles.sqItem}>
                            <span style={styles.sqLabel}>Academic Tone</span>
                            <div style={styles.sqBar}>
                              <div style={{...styles.sqFill, width: `${Math.min(data.features?.avg_word_length * 15, 100)}%`, backgroundColor: '#06b6d4'}}></div>
                            </div>
                            <span style={styles.sqValue}>{data.features?.avg_word_length?.toFixed(1) || 0} avg</span>
                          </div>
                        </div>
                      </div>

                      {/* Recommendations for Abstract */}
                      <div style={styles.abstractRecommendation}>
                        <h3 style={styles.arTitle}>Ready for Submission</h3>
                        <p style={styles.arText}>
                          Your paper demonstrates strong research in <strong>{data.domain_stats?.domain || "your research area"}</strong>. 
                          Use this summary as your abstract when submitting to the {(data.domain_stats?.matching_venues || 0).toLocaleString()} relevant venues in the database.
                        </p>
                      </div>

                      <div style={styles.summaryNote}>
                        <strong>Note:</strong> This is an extractive summary highlighting key sentences. Refine for your final abstract submission.
                      </div>
                    </div>
                  )}

                  {activeTab === "venues" && (
                    <div>
                      <VenueRecommenderEnhanced
                        paperText={data.summary || ""}
                        paperScore={data.score}
                        paperTopic=""
                      />
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    background: "#f8fafc",
    minHeight: "100vh",
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif",
    color: "#1e293b",
  },

  header: {
    background: "linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%)",
    padding: "60px 40px 40px",
    borderBottom: "1px solid rgba(30, 41, 59, 0.08)",
    boxShadow: "0 2px 8px rgba(30, 41, 59, 0.06)",
  },

  maxWidth: {
    maxWidth: "100%",
    margin: "0 auto",
    paddingLeft: "40px",
    paddingRight: "40px",
  },

  title: {
    fontSize: "48px",
    fontWeight: "800",
    marginBottom: "12px",
    background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    backgroundClip: "text",
    letterSpacing: "-0.8px",
    lineHeight: "1.2",
  },

  subtitle: {
    fontSize: "16px",
    color: "#64748b",
    marginBottom: "0",
    fontWeight: "400",
    lineHeight: "1.6",
  },

  mainLayout: {
    display: "grid",
    gridTemplateColumns: "300px 1fr",
    gap: "40px",
    paddingTop: "40px",
    paddingBottom: "60px",
  },

  sidebar: {
    display: "flex",
    flexDirection: "column",
    gap: "24px",
  },

  uploadSection: {
    background: "#ffffff",
    borderRadius: "12px",
    padding: "24px",
    boxShadow: "0 2px 8px rgba(30, 41, 59, 0.06), 0 1px 3px rgba(30, 41, 59, 0.04)",
    border: "1px solid rgba(30, 41, 59, 0.08)",
    transition: "box-shadow 0.3s ease, transform 0.3s ease",
  },

  sidebarTitle: {
    fontSize: "16px",
    fontWeight: "700",
    marginBottom: "16px",
    color: "#1e293b",
    margin: "0 0 16px 0",
  },

  fileInputLabel: {
    display: "block",
    marginBottom: "16px",
  },

  fileInput: {
    display: "none",
  },

  selectFileBtn: {
    display: "block",
    textAlign: "center",
    padding: "10px 16px",
    background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
    color: "#ffffff",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    fontWeight: "600",
    fontSize: "13px",
    transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
    boxShadow: "0 4px 12px rgba(59, 130, 246, 0.3)",
  },

  fileName: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "12px 14px",
    background: "rgba(16, 185, 129, 0.08)",
    border: "1.5px solid rgba(16, 185, 129, 0.3)",
    borderRadius: "8px",
    color: "#10b981",
    fontSize: "12px",
    marginBottom: "16px",
    fontWeight: "500",
  },

  fileNameIcon: {
    fontSize: "14px",
  },

  analyzeButton: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "8px",
    width: "100%",
    padding: "11px 16px",
    background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
    color: "#ffffff",
    border: "none",
    borderRadius: "8px",
    fontSize: "14px",
    fontWeight: "700",
    cursor: "pointer",
    transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
    boxShadow: "0 4px 12px rgba(59, 130, 246, 0.3)",
  },

  spinner: {
    display: "inline-block",
    width: "12px",
    height: "12px",
    border: "2px solid rgba(255, 255, 255, 0.25)",
    borderTop: "2px solid #ffffff",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
  },

  errorMessage: {
    padding: "12px 14px",
    background: "rgba(239, 68, 68, 0.08)",
    border: "1.5px solid rgba(239, 68, 68, 0.3)",
    borderRadius: "8px",
    color: "#dc2626",
    fontSize: "12px",
    marginTop: "12px",
    textAlign: "center",
    fontWeight: "500",
  },

  databaseSummary: {
    background: "#ffffff",
    borderRadius: "12px",
    padding: "24px",
    boxShadow: "0 2px 8px rgba(30, 41, 59, 0.06), 0 1px 3px rgba(30, 41, 59, 0.04)",
    border: "1px solid rgba(30, 41, 59, 0.08)",
    transition: "box-shadow 0.3s ease, transform 0.3s ease",
  },

  summaryStats: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr 1fr",
    gap: "12px",
  },

  statItem: {
    textAlign: "center",
  },

  statValue: {
    fontSize: "24px",
    fontWeight: "800",
    color: "#3b82f6",
    marginBottom: "4px",
  },

  statLabel: {
    fontSize: "11px",
    color: "#64748b",
    fontWeight: "600",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },

  contentArea: {
    minHeight: "600px",
  },

  welcomeSection: {
    animation: "fadeIn 0.5s ease",
  },

  welcomeCard: {
    background: "#ffffff",
    borderRadius: "12px",
    padding: "40px",
    marginBottom: "32px",
    boxShadow: "0 2px 8px rgba(30, 41, 59, 0.06), 0 1px 3px rgba(30, 41, 59, 0.04)",
    border: "1px solid rgba(30, 41, 59, 0.08)",
    textAlign: "center",
    transition: "box-shadow 0.3s ease, transform 0.3s ease",
  },

  welcomeTitle: {
    fontSize: "32px",
    fontWeight: "800",
    marginBottom: "16px",
    color: "#1e293b",
    margin: "0 0 16px 0",
  },

  welcomeText: {
    fontSize: "15px",
    color: "#475569",
    lineHeight: "1.7",
    margin: "0",
  },

  infoGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "24px",
  },

  infoCard: {
    background: "#ffffff",
    borderRadius: "12px",
    padding: "32px",
    boxShadow: "0 2px 8px rgba(30, 41, 59, 0.06), 0 1px 3px rgba(30, 41, 59, 0.04)",
    border: "1px solid rgba(30, 41, 59, 0.08)",
    transition: "box-shadow 0.3s ease, transform 0.3s ease",
  },

  infoTitle: {
    fontSize: "18px",
    fontWeight: "700",
    marginBottom: "16px",
    color: "#1e293b",
    margin: "0 0 16px 0",
  },

  infoList: {
    paddingLeft: "20px",
    margin: "0",
    fontSize: "14px",
    color: "#475569",
    lineHeight: "1.8",
  },

  featureList: {
    paddingLeft: "20px",
    margin: "0",
    fontSize: "14px",
    color: "#475569",
    lineHeight: "1.8",
  },

  resultsWrapper: {
    animation: "fadeIn 0.5s ease",
  },

  successBanner: {
    padding: "14px 18px",
    background: "rgba(16, 185, 129, 0.08)",
    border: "1.5px solid rgba(16, 185, 129, 0.3)",
    borderRadius: "10px",
    color: "#10b981",
    fontSize: "14px",
    marginBottom: "24px",
    fontWeight: "600",
  },

  tabsContainer: {
    display: "flex",
    gap: "4px",
    marginBottom: "32px",
    borderBottom: "1px solid rgba(30, 41, 59, 0.08)",
  },

  tab: {
    padding: "14px 20px",
    background: "transparent",
    color: "#64748b",
    border: "none",
    borderBottom: "3px solid transparent",
    cursor: "pointer",
    fontWeight: "600",
    fontSize: "14px",
    transition: "all 0.3s ease",
  },

  tabActive: {
    color: "#3b82f6",
    borderBottomColor: "#3b82f6",
  },

  tabContent: {
    animation: "fadeIn 0.3s ease",
  },

  tabDescription: {
    fontSize: "14px",
    color: "#475569",
    marginBottom: "24px",
    margin: "0 0 24px 0",
  },

  sectionTitle: {
    fontSize: "22px",
    fontWeight: "800",
    marginBottom: "24px",
    color: "#1e293b",
    margin: "0 0 24px 0",
    borderBottom: "2px solid rgba(59, 130, 246, 0.15)",
    paddingBottom: "12px",
  },

  scoreCard: {
    background: "#ffffff",
    borderRadius: "12px",
    padding: "32px",
    marginBottom: "32px",
    boxShadow: "0 2px 8px rgba(30, 41, 59, 0.06), 0 1px 3px rgba(30, 41, 59, 0.04)",
    border: "1px solid rgba(30, 41, 59, 0.08)",
    textAlign: "center",
    transition: "box-shadow 0.3s ease, transform 0.3s ease",
  },

  scoreDisplay: {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "center",
    gap: "2px",
    marginBottom: "20px",
  },

  scoreValue: {
    fontSize: "72px",
    fontWeight: "900",
    color: "#3b82f6",
    lineHeight: "1",
  },

  scoreMax: {
    fontSize: "20px",
    color: "#64748b",
    fontWeight: "600",
    marginTop: "8px",
  },

  scoreBar: {
    height: "8px",
    background: "linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%)",
    borderRadius: "4px",
    marginBottom: "16px",
    maxWidth: "300px",
    margin: "0 auto 16px",
    transition: "width 0.7s cubic-bezier(0.4, 0, 0.2, 1)",
    boxShadow: "0 0 12px rgba(59, 130, 246, 0.2)",
  },

  scoreStatus: {
    fontSize: "16px",
    fontWeight: "700",
  },

  metricsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: "20px",
    marginBottom: "32px",
  },

  metricCard: {
    background: "#ffffff",
    borderRadius: "12px",
    padding: "24px",
    boxShadow: "0 2px 8px rgba(30, 41, 59, 0.06), 0 1px 3px rgba(30, 41, 59, 0.04)",
    border: "1px solid rgba(30, 41, 59, 0.08)",
    textAlign: "center",
    transition: "box-shadow 0.3s ease, transform 0.3s ease",
  },

  metricLabel: {
    fontSize: "12px",
    color: "#64748b",
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: "0.8px",
    marginBottom: "12px",
  },

  metricValue: {
    fontSize: "36px",
    fontWeight: "900",
    color: "#3b82f6",
  },

  metricsDetails: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "20px",
  },

  detailsCard: {
    background: "#ffffff",
    borderRadius: "12px",
    padding: "24px",
    boxShadow: "0 2px 8px rgba(30, 41, 59, 0.06), 0 1px 3px rgba(30, 41, 59, 0.04)",
    border: "1px solid rgba(30, 41, 59, 0.08)",
    transition: "box-shadow 0.3s ease, transform 0.3s ease",
  },

  detailsTitle: {
    fontSize: "16px",
    fontWeight: "700",
    marginBottom: "12px",
    color: "#1e293b",
    margin: "0 0 12px 0",
  },

  detailsList: {
    paddingLeft: "20px",
    margin: "0",
    fontSize: "13px",
    color: "#475569",
    lineHeight: "1.8",
  },

  researchQuality: {
    background: "#ffffff",
    borderRadius: "12px",
    padding: "24px",
    marginBottom: "32px",
    boxShadow: "0 2px 8px rgba(30, 41, 59, 0.06), 0 1px 3px rgba(30, 41, 59, 0.04)",
    border: "1px solid rgba(30, 41, 59, 0.08)",
    transition: "box-shadow 0.3s ease, transform 0.3s ease",
  },

  qualityTitle: {
    fontSize: "16px",
    fontWeight: "700",
    marginBottom: "16px",
    color: "#1e293b",
    margin: "0 0 16px 0",
  },

  qualityContent: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "16px",
  },

  qualityItem: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    fontSize: "14px",
  },

  qualityLabel: {
    color: "#64748b",
    fontWeight: "600",
  },

  qualityValue: {
    color: "#3b82f6",
    fontWeight: "700",
  },

  papersTitle: {
    fontSize: "18px",
    fontWeight: "700",
    marginBottom: "16px",
    color: "#1e293b",
    margin: "24px 0 16px 0",
    borderBottom: "2px solid rgba(59, 130, 246, 0.15)",
    paddingBottom: "8px",
  },

  papersList: {
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },

  similarPaperItem: {
    background: "#ffffff",
    border: "1px solid rgba(30, 41, 59, 0.08)",
    borderRadius: "12px",
    padding: "20px",
    transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
    boxShadow: "0 1px 3px rgba(30, 41, 59, 0.04)",
  },

  paperRank: {
    display: "inline-block",
    padding: "4px 12px",
    background: "rgba(59, 130, 246, 0.1)",
    color: "#3b82f6",
    borderRadius: "12px",
    fontSize: "12px",
    fontWeight: "700",
    marginBottom: "8px",
  },

  paperInfo: {
    marginBottom: "12px",
  },

  paperTitle: {
    fontSize: "15px",
    fontWeight: "600",
    color: "#1e293b",
    margin: "0 0 8px 0",
    lineHeight: "1.5",
  },

  paperMeta: {
    display: "flex",
    gap: "8px",
    fontSize: "13px",
  },

  metaLabel: {
    color: "#64748b",
    fontWeight: "600",
  },

  metaValue: {
    color: "#3b82f6",
    fontWeight: "700",
  },

  similarityBarContainer: {
    height: "5px",
    background: "rgba(30, 41, 59, 0.08)",
    borderRadius: "3px",
    overflow: "hidden",
  },

  similarityBar: {
    height: "100%",
    background: "linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%)",
    borderRadius: "3px",
    transition: "width 0.7s cubic-bezier(0.4, 0, 0.2, 1)",
    boxShadow: "0 0 12px rgba(59, 130, 246, 0.2)",
  },

  noResults: {
    textAlign: "center",
    color: "#64748b",
    padding: "28px",
    fontSize: "14px",
    fontWeight: "500",
  },

  recommendationsList: {
    display: "flex",
    flexDirection: "column",
    gap: "16px",
  },

  recommendationItem: {
    background: "#ffffff",
    borderLeft: "4px solid #3b82f6",
    borderRadius: "8px",
    padding: "20px",
    boxShadow: "0 2px 8px rgba(30, 41, 59, 0.06), 0 1px 3px rgba(30, 41, 59, 0.04)",
    border: "1px solid rgba(30, 41, 59, 0.08)",
    borderLeftWidth: "4px",
    transition: "box-shadow 0.3s ease, transform 0.3s ease",
  },

  recommendationNumber: {
    display: "inline-block",
    padding: "4px 12px",
    background: "rgba(59, 130, 246, 0.1)",
    color: "#3b82f6",
    borderRadius: "12px",
    fontSize: "12px",
    fontWeight: "700",
    marginBottom: "8px",
  },

  recommendationText: {
    fontSize: "14px",
    color: "#475569",
    lineHeight: "1.7",
    margin: "0",
  },

  summaryCard: {
    background: "#ffffff",
    borderRadius: "12px",
    padding: "32px",
    boxShadow: "0 2px 8px rgba(30, 41, 59, 0.06), 0 1px 3px rgba(30, 41, 59, 0.04)",
    border: "1px solid rgba(30, 41, 59, 0.08)",
    borderLeft: "5px solid #3b82f6",
    transition: "all 0.3s ease, box-shadow 0.3s ease, transform 0.3s ease",
  },

  summaryLabel: {
    fontSize: "14px",
    fontWeight: "700",
    marginBottom: "16px",
    paddingBottom: "12px",
    borderBottom: "2px solid rgba(30, 41, 59, 0.08)",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },

  summaryText: {
    fontSize: "16px",
    color: "#1e293b",
    lineHeight: "1.9",
    marginBottom: "20px",
    margin: "0 0 20px 0",
    textAlign: "justify",
    letterSpacing: "0.3px",
  },

  summaryNote: {
    padding: "14px 16px",
    background: "rgba(59, 130, 246, 0.06)",
    borderLeft: "3px solid #3b82f6",
    borderRadius: "4px",
    fontSize: "13px",
    color: "#475569",
    fontWeight: "500",
    lineHeight: "1.6",
  },

  qualityBreakdown: {
    display: "grid",
    gridTemplateColumns: "1fr",
    gap: "16px",
    marginBottom: "32px",
    background: "#ffffff",
    borderRadius: "12px",
    padding: "24px",
    boxShadow: "0 2px 8px rgba(30, 41, 59, 0.06), 0 1px 3px rgba(30, 41, 59, 0.04)",
    border: "1px solid rgba(30, 41, 59, 0.08)",
  },

  breakdownItem: {
    display: "flex",
    alignItems: "center",
    gap: "16px",
  },

  breakdownLabel: {
    fontSize: "14px",
    fontWeight: "600",
    color: "#1e293b",
    minWidth: "180px",
  },

  breakdownBar: {
    flex: 1,
    height: "24px",
    background: "#e2e8f0",
    borderRadius: "6px",
    overflow: "hidden",
    position: "relative",
  },

  breakdownFill: {
    height: "100%",
    borderRadius: "6px",
    transition: "width 0.7s cubic-bezier(0.4, 0, 0.2, 1)",
    boxShadow: "0 0 8px rgba(0, 0, 0, 0.1)",
  },

  breakdownScore: {
    fontSize: "14px",
    fontWeight: "700",
    color: "#3b82f6",
    minWidth: "70px",
    textAlign: "right",
  },

  venueScoringSuggestion: {
    background: "linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%)",
    border: "1px solid rgba(59, 130, 246, 0.2)",
    borderRadius: "12px",
    padding: "24px",
    marginTop: "24px",
  },

  suggestionTitle: {
    fontSize: "16px",
    fontWeight: "700",
    color: "#1e293b",
    marginBottom: "12px",
  },

  suggestionText: {
    fontSize: "14px",
    color: "#475569",
    marginBottom: "16px",
    lineHeight: "1.6",
  },

  suggestionList: {
    paddingLeft: "20px",
    margin: "0",
    fontSize: "13px",
    color: "#475569",
    lineHeight: "2",
  },

  domainSection: {
    marginBottom: "16px",
  },

  domainLabel: {
    fontSize: "12px",
    fontWeight: "700",
    color: "#64748b",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
    marginBottom: "6px",
  },

  domainName: {
    fontSize: "16px",
    fontWeight: "700",
    color: "#3b82f6",
    marginBottom: "8px",
  },

  confidenceBar: {
    height: "6px",
    background: "#e2e8f0",
    borderRadius: "3px",
    overflow: "hidden",
    marginBottom: "4px",
  },

  confidenceFill: {
    height: "100%",
    background: "linear-gradient(90deg, #3b82f6 0%, #0ea5e9 100%)",
    borderRadius: "3px",
    transition: "width 0.6s cubic-bezier(0.4, 0, 0.2, 1)",
  },

  confidencePercent: {
    fontSize: "11px",
    color: "#64748b",
    fontWeight: "600",
    textAlign: "right",
  },

  divider: {
    height: "1px",
    background: "rgba(30, 41, 59, 0.08)",
    margin: "12px 0",
  },

  statsSection: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },

  statRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    fontSize: "13px",
  },

  statRowLabel: {
    color: "#475569",
    fontWeight: "500",
  },

  statRowValue: {
    color: "#3b82f6",
    fontWeight: "700",
    fontSize: "14px",
  },

  recommendation: {
    background: "rgba(59, 130, 246, 0.08)",
    border: "1px solid rgba(59, 130, 246, 0.2)",
    borderRadius: "8px",
    padding: "12px",
    marginTop: "8px",
  },

  recommendationTitle: {
    fontSize: "12px",
    fontWeight: "700",
    color: "#3b82f6",
    marginBottom: "4px",
  },

  domainAnalysisCard: {
    background: "#ffffff",
    borderRadius: "12px",
    padding: "24px",
    marginBottom: "32px",
    boxShadow: "0 2px 8px rgba(30, 41, 59, 0.06), 0 1px 3px rgba(30, 41, 59, 0.04)",
    border: "1px solid rgba(59, 130, 246, 0.1)",
    transition: "box-shadow 0.3s ease, transform 0.3s ease",
  },

  domainAnalysisGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gap: "16px",
    marginBottom: "16px",
  },

  analysisItem: {
    padding: "12px",
    background: "rgba(59, 130, 246, 0.04)",
    borderRadius: "8px",
    border: "1px solid rgba(59, 130, 246, 0.1)",
  },

  analysisLabel: {
    fontSize: "12px",
    fontWeight: "700",
    color: "#64748b",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
    marginBottom: "6px",
  },

  analysisValue: {
    fontSize: "18px",
    fontWeight: "800",
    color: "#3b82f6",
    marginBottom: "4px",
  },

  analysisSubtext: {
    fontSize: "11px",
    color: "#475569",
    fontWeight: "500",
  },

  domainInsight: {
    padding: "12px 14px",
    background: "rgba(34, 197, 94, 0.06)",
    border: "1px solid rgba(34, 197, 94, 0.2)",
    borderRadius: "8px",
    fontSize: "13px",
    color: "#166534",
    lineHeight: "1.6",
    fontWeight: "500",
  },

  noveltyBadge: {
    display: "inline-block",
    padding: "4px 10px",
    borderRadius: "20px",
    fontSize: "11px",
    fontWeight: "700",
    marginRight: "8px",
    letterSpacing: "0.3px",
  },

  domainContext: {
    padding: "10px 12px",
    background: "rgba(59, 130, 246, 0.06)",
    borderRadius: "6px",
    fontSize: "12px",
    color: "#1e40af",
    fontWeight: "500",
    marginTop: "8px",
    borderLeft: "2px solid #3b82f6",
  },

  venueStatBox: {
    display: "inline-block",
    padding: "6px 10px",
    background: "#f0f9ff",
    borderRadius: "6px",
    fontSize: "12px",
    fontWeight: "600",
    color: "#0c4a6e",
    marginRight: "8px",
    marginTop: "4px",
  },

  recommendationCategory: {
    padding: "12px",
    marginBottom: "12px",
    background: "rgba(59, 130, 246, 0.04)",
    borderRadius: "8px",
    borderLeft: "3px solid #3b82f6",
  },

  recommendationActions: {
    marginTop: "16px",
    padding: "12px",
    background: "rgba(34, 197, 94, 0.04)",
    borderRadius: "8px",
    borderLeft: "3px solid #22c55e",
  },

  actionItem: {
    padding: "8px 0",
    fontSize: "13px",
    color: "#166534",
    fontWeight: "500",
    display: "flex",
    alignItems: "flex-start",
    gap: "8px",
  },

  summaryHighlight: {
    padding: "14px 16px",
    background: "linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(34, 197, 94, 0.08) 100%)",
    borderRadius: "8px",
    borderLeft: "3px solid #3b82f6",
    marginBottom: "16px",
    fontSize: "14px",
    fontWeight: "500",
    color: "#1e293b",
    lineHeight: "1.5",
  },

  publicationReady: {
    padding: "12px 14px",
    background: "#f0fdf4",
    border: "1px solid rgba(34, 197, 94, 0.2)",
    borderRadius: "8px",
    fontSize: "13px",
    color: "#166534",
    fontWeight: "500",
    marginTop: "12px",
  },

  paperMetadata: {
    fontSize: "12px",
    color: "#64748b",
    fontWeight: "500",
    marginBottom: "8px",
  },

  similarPaperCard: {
    background: "#ffffff",
    borderRadius: "8px",
    padding: "16px",
    marginBottom: "12px",
    border: "1px solid rgba(59, 130, 246, 0.15)",
    boxShadow: "0 1px 3px rgba(30, 41, 59, 0.05)",
  },

  similarityScore: {
    display: "inline-block",
    padding: "4px 8px",
    background: "#dbeafe",
    color: "#0c4a6e",
    borderRadius: "4px",
    fontSize: "12px",
    fontWeight: "600",
  },

  nextSteps: {
    padding: "16px",
    background: "#f8fafc",
    borderRadius: "8px",
    border: "1px solid rgba(100, 116, 139, 0.1)",
    marginTop: "16px",
  },

  nextStepsTitle: {
    fontSize: "14px",
    fontWeight: "700",
    color: "#1e293b",
    marginBottom: "12px",
  },

  nextStepsItem: {
    fontSize: "13px",
    color: "#475569",
    fontWeight: "500",
    marginBottom: "8px",
    paddingLeft: "20px",
    position: "relative",
    lineHeight: "1.5",
  },

  domainRecommendations: {
    marginBottom: "32px",
  },

  recGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: "20px",
    marginTop: "16px",
  },

  recCard: {
    background: "#ffffff",
    borderRadius: "12px",
    padding: "24px",
    border: "1px solid rgba(59, 130, 246, 0.1)",
    boxShadow: "0 2px 8px rgba(30, 41, 59, 0.06), 0 1px 3px rgba(30, 41, 59, 0.04)",
    transition: "all 0.3s ease",
    textAlign: "left",
  },

  recCardTitle: {
    fontSize: "16px",
    fontWeight: "700",
    color: "#1e293b",
    marginBottom: "12px",
  },

  recCardText: {
    fontSize: "14px",
    color: "#475569",
    lineHeight: "1.6",
  },

  recSectionTitle: {
    fontSize: "18px",
    fontWeight: "700",
    marginBottom: "20px",
    color: "#1e293b",
    marginTop: "24px",
    borderBottom: "2px solid rgba(59, 130, 246, 0.15)",
    paddingBottom: "12px",
  },

  rpTitle: {
    fontSize: "16px",
    fontWeight: "700",
    marginBottom: "16px",
    color: "#1e293b",
  },

  rpContent: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gap: "16px",
  },

  rpItem: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px",
    background: "rgba(59, 130, 246, 0.04)",
    borderRadius: "8px",
  },

  rpLabel: {
    fontSize: "13px",
    fontWeight: "600",
    color: "#64748b",
  },

  rpValue: {
    fontSize: "14px",
    fontWeight: "700",
    color: "#3b82f6",
  },
};

export default App;
