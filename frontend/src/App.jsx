import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './App.css';
import BriefingQuestionnaire from './components/BriefingQuestionnaire';

function App() {
  const [inputMode, setInputMode] = useState('url'); // 'url' or 'search'
  const [input, setInput] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  // Questionnaire state
  const [showQuestionnaire, setShowQuestionnaire] = useState(false);
  const [pendingVideoId, setPendingVideoId] = useState(null);

  const API_BASE = 'http://localhost:8000/api';

  // Search YouTube
  const handleSearch = async () => {
    if (!input.trim()) return;

    setLoading(true);
    setError(null);
    setSearchResults([]);

    try {
      const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(input)}&limit=5`);
      const data = await response.json();

      if (response.ok) {
        setSearchResults(data.results);
      } else {
        setError(data.detail || 'Search failed');
      }
    } catch (err) {
      setError('Failed to search. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  // Show questionnaire before summarizing
  const handleSummarizeClick = (videoIdOrUrl) => {
    setPendingVideoId(videoIdOrUrl);
    setShowQuestionnaire(true);
  };

  // Generate briefing with context from questionnaire
  const handleGenerateBriefing = async (context) => {
    setShowQuestionnaire(false);
    setLoading(true);
    setError(null);
    setSummary(null);

    try {
      const body = pendingVideoId.includes('youtube.com') || pendingVideoId.includes('youtu.be')
        ? { video_url: pendingVideoId, context }
        : { video_id: pendingVideoId, context };

      const response = await fetch(`${API_BASE}/summarize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      const data = await response.json();

      if (response.ok) {
        setSummary(data);
        setSearchResults([]); // Clear search results
      } else {
        setError(data.detail || 'Briefing generation failed');
      }
    } catch (err) {
      setError('Failed to generate briefing. Check your ANTHROPIC_API_KEY in .env');
    } finally {
      setLoading(false);
      setPendingVideoId(null);
    }
  };

  // Cancel questionnaire
  const handleCancelQuestionnaire = () => {
    setShowQuestionnaire(false);
    setPendingVideoId(null);
  };

  const formatDuration = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  // Smart handler - detects if input is URL or search keyword
  const handleSubmit = async () => {
    if (!input.trim()) return;

    const isUrl = input.includes('youtube.com') || input.includes('youtu.be');

    if (isUrl) {
      // Direct to questionnaire for URL
      handleSummarizeClick(input);
    } else {
      // Search for keywords
      handleSearch();
    }
  };

  return (
    <div className="app">
      <header>
        <h1>🎙️ Podcast Intelligent Brief</h1>
      </header>

      <main>
        {/* Single Input Box */}
        <div className="input-section">
          <input
            type="text"
            placeholder="What podcasts are you interested in?"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleSubmit();
              }
            }}
            disabled={loading}
          />
          <button
            onClick={handleSubmit}
            disabled={loading || !input.trim()}
            className="primary-btn"
          >
            {loading ? '⏳ Loading...' : '🎯 Generate Briefing'}
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="error-box">
            ❌ {error}
          </div>
        )}

        {/* Loading State */}
        {loading && !summary && (
          <div className="loading-box">
            <div className="spinner"></div>
            <p>
              {searchResults.length === 0 && input.includes('youtube')
                ? 'Generating intelligent briefing (60 seconds)...'
                : 'Searching YouTube...'
              }
            </p>
            {searchResults.length === 0 && input.includes('youtube') && (
              <p className="sub-text">Downloading captions → Researching speakers → Generating briefing</p>
            )}
          </div>
        )}

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div className="search-results">
            <h2>Search Results:</h2>
            {searchResults.map((result) => (
              <div key={result.video_id} className="result-card">
                <img src={result.thumbnail_url} alt={result.title} />
                <div className="result-info">
                  <h3>{result.title}</h3>
                  <p className="channel">{result.channel_name}</p>
                  <p className="meta">{formatDuration(result.duration)}</p>
                  <button
                    onClick={() => handleSummarizeClick(result.video_id)}
                    className="summarize-btn"
                  >
                    🎯 Generate Briefing (60s)
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Summary Display */}
        {summary && (
          <div className="summary-box">
            {summary.briefing.cached && (
              <div className="cache-badge">
                ⚡ Loaded from cache (instant!)
              </div>
            )}

            <div className="episode-header">
              <img src={summary.episode.thumbnail_url} alt={summary.episode.title} />
              <div>
                <h2>{summary.episode.title}</h2>
                <p className="channel">{summary.episode.channel_name}</p>
                <p className="meta">{formatDuration(summary.episode.duration)}</p>
              </div>
            </div>

            {/* Briefing Text */}
            <div className="summary-content">
              <ReactMarkdown>{summary.briefing.briefing_text}</ReactMarkdown>
            </div>

            {/* Cost Info */}
            <div className="cost-info">
              💰 Tokens: {summary.cost.tokens_used.toLocaleString()} •
              Cost: ${summary.cost.estimated_cost_usd.toFixed(4)} •
              {summary.cost.note}
            </div>
          </div>
        )}

        {/* Questionnaire Modal */}
        {showQuestionnaire && (
          <BriefingQuestionnaire
            onGenerate={handleGenerateBriefing}
            onCancel={handleCancelQuestionnaire}
          />
        )}
      </main>
    </div>
  );
}

export default App;
