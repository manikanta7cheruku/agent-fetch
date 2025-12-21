// frontend/src/App.jsx
import React, { useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler);

// Backend API base URL (FastAPI)
const API_BASE = 'http://localhost:8000/api';

// Some suggested cities and coins to show as quick-select chips
const SUGGESTED_CITIES = ['Hyderabad', 'London', 'New York', 'Tokyo', 'Sydney'];
const SUGGESTED_COINS = ['bitcoin', 'ethereum', 'solana', 'dogecoin', 'litecoin'];

function App() {
  // Mode: "weather" or "crypto"
  const [mode, setMode] = useState('weather');

  // User input (city or coin)
  const [inputValue, setInputValue] = useState('');

  // Last API result (parsed response from backend)
  const [result, setResult] = useState(null);

  // Raw JSON (from result.raw)
  const [rawJson, setRawJson] = useState(null);

  // Show/hide raw JSON
  const [showRaw, setShowRaw] = useState(false);

  // Loading state for the "Get Info" button
  const [loading, setLoading] = useState(false);

  // Error message (if any)
  const [error, setError] = useState('');

  // History for charts (session-based, in-memory)
  const [weatherHistory, setWeatherHistory] = useState([]); // { city, timeLabel, temperature }
  const [cryptoHistory, setCryptoHistory] = useState([]);   // { coin, timeLabel, price }

  // Handle "Get Info" click or Enter key
  const handleFetch = async (valueOverride) => {
    setError('');
    setResult(null);
    setRawJson(null);
    setShowRaw(false);

    const trimmed = (valueOverride ?? inputValue).trim();
    if (!trimmed) {
      setError(mode === 'weather' ? 'Please enter a city.' : 'Please enter a coin id.');
      return;
    }

    setLoading(true);
    try {
      const url =
        mode === 'weather'
          ? `${API_BASE}/weather?city=${encodeURIComponent(trimmed)}`
          : `${API_BASE}/crypto?coin=${encodeURIComponent(trimmed.toLowerCase())}`;

      const res = await fetch(url);
      const data = await res.json();

      if (!res.ok) {
        // Backend sends { detail: "error message" } on errors
        setError(data.detail || 'Request failed.');
      } else {
        setResult(data);
        setRawJson(data.raw || data);

        // Record history point for charts
        const timeLabel = new Date().toLocaleTimeString(undefined, {
          hour: '2-digit',
          minute: '2-digit',
        });

        if (mode === 'weather') {
          setWeatherHistory((prev) => [
            ...prev,
            {
              city: data.city,
              timeLabel,
              temperature: data.temperature_c,
            },
          ]);
        } else {
          setCryptoHistory((prev) => [
            ...prev,
            {
              coin: data.coin_id,
              timeLabel,
              price: data.price_usd,
            },
          ]);
        }
      }
    } catch (err) {
      console.error(err);
      setError('Network error. Is the backend running on http://localhost:8000?');
    } finally {
      setLoading(false);
    }
  };

  // Build chart data for the current city/coin based on history
  const buildChartData = () => {
    if (mode === 'weather') {
      if (!result) return null;

      // Filter history for the current city
      const historyForCity = weatherHistory.filter((h) => h.city === result.city);
      if (historyForCity.length === 0) return null;

      const labels = historyForCity.map((h) => h.timeLabel);
      const temps = historyForCity.map((h) => h.temperature);

      return {
        labels,
        datasets: [
          {
            label: `${result.city} temperature (°C)`,
            data: temps,
            fill: true,
            borderColor: '#38bdf8',
            backgroundColor: 'rgba(56, 189, 248, 0.18)',
            tension: 0.35,
            pointRadius: 3,
          },
        ],
      };
    }

    if (mode === 'crypto') {
      if (!result) return null;

      // Filter history for the current coin
      const historyForCoin = cryptoHistory.filter((h) => h.coin === result.coin_id);
      if (historyForCoin.length === 0) return null;

      const labels = historyForCoin.map((h) => h.timeLabel);
      const prices = historyForCoin.map((h) => h.price);

      return {
        labels,
        datasets: [
          {
            label: `${result.coin_id.toUpperCase()} price (USD)`,
            data: prices,
            fill: true,
            borderColor: '#22c55e',
            backgroundColor: 'rgba(34, 197, 94, 0.16)',
            tension: 0.35,
            pointRadius: 3,
          },
        ],
      };
    }

    return null;
  };

  const chartData = buildChartData();

  // Chart options (hide some clutter for a small dashboard-style chart)
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: '#e5e7eb',
          font: { size: 10 },
        },
      },
      tooltip: {
        callbacks: {
          label: (context) => `${context.parsed.y}`,
        },
      },
    },
    scales: {
      x: {
        ticks: {
          color: '#9ca3af',
          maxRotation: 0,
        },
        grid: {
          color: 'rgba(55,65,81,0.4)',
        },
      },
      y: {
        ticks: {
          color: '#9ca3af',
        },
        grid: {
          color: 'rgba(55,65,81,0.4)',
        },
      },
    },
  };

  // Render result summary based on current mode
  const renderResult = () => {
    if (!result) return null;

    if (mode === 'weather') {
      return (
        <div className="result-block">
          <div className="result-title">Current Weather</div>
          <div className="result-main">
            {result.city}, {result.country} — {result.temperature_c.toFixed(1)}°C
          </div>
          <div className="result-sub">
            {result.description} · feels like {result.feels_like_c.toFixed(1)}°C · humidity{' '}
            {result.humidity}%
          </div>
        </div>
      );
    }

    if (mode === 'crypto') {
      return (
        <div className="result-block">
          <div className="result-title">Crypto Price</div>
          <div className="result-main">
            {result.coin_id.toUpperCase()} — $
            {result.price_usd.toLocaleString(undefined, {
              maximumFractionDigits: 2,
            })}
          </div>
          {typeof result.change_24h === 'number' && (
            <div className="result-sub">
              24h change:{' '}
              <span style={{ color: result.change_24h >= 0 ? '#4ade80' : '#f97373' }}>
                {result.change_24h.toFixed(2)}%
              </span>
            </div>
          )}
        </div>
      );
    }

    return null;
  };

  // Suggestions list for current mode
  const renderSuggestions = () => {
    const items = mode === 'weather' ? SUGGESTED_CITIES : SUGGESTED_COINS;
    return (
      <div className="suggestions">
        {items.map((item) => (
          <button
            key={item}
            type="button"
            className="suggestion-chip"
            onClick={() => {
              setInputValue(item);
              // Optionally, immediately trigger fetch:
              // handleFetch(item);
            }}
          >
            {item}
          </button>
        ))}
      </div>
    );
  };

  return (
    <div className="app-root">
      <div className="shell">
        <header className="shell-header">
          <div className="title-stack">
            <h1>Agentic Signals Console</h1>
            <span>Weather & crypto insights, built to evolve into an AI agent.</span>
          </div>
          <div className="badge">Phase 1 · MVP</div>
        </header>

        <div className="main-grid">
          {/* Left: Query + Results */}
          <div className="card">
            <div className="card-title">Query</div>

            {/* Mode toggle */}
            <div className="toggle-group">
              <button
                className={`toggle-btn ${mode === 'weather' ? 'active' : ''}`}
                onClick={() => {
                  setMode('weather');
                  setResult(null);
                  setRawJson(null);
                  setError('');
                  setShowRaw(false);
                }}
              >
                Weather
              </button>
              <button
                className={`toggle-btn ${mode === 'crypto' ? 'active' : ''}`}
                onClick={() => {
                  setMode('crypto');
                  setResult(null);
                  setRawJson(null);
                  setError('');
                  setShowRaw(false);
                }}
              >
                Crypto
              </button>
            </div>

            <div className="form-row">
              {/* Field label & help */}
              <div className="field-label">
                {mode === 'weather' ? 'City' : 'Coin ID'}
              </div>
              <div className="field-help">
                {mode === 'weather'
                  ? 'Example: Hyderabad, London, New York'
                  : 'Example: bitcoin, ethereum, solana'}
              </div>

              {/* Suggestions */}
              {renderSuggestions()}

              {/* Input + button */}
              <div className="field-line">
                <input
                  className="input"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder={mode === 'weather' ? 'Hyderabad' : 'bitcoin'}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleFetch();
                    }
                  }}
                />
                <button
                  className="button"
                  onClick={() => handleFetch()}
                  disabled={loading}
                  type="button"
                >
                  {loading && <span className="pulse-dot" />}
                  <span>{loading ? 'Fetching' : 'Get Info'}</span>
                </button>
              </div>

              {/* Error message */}
              {error && <div className="error">{error}</div>}

              {/* Summary result card */}
              {renderResult()}

              {/* Chart (if we have enough history) */}
              {chartData && (
                <div className="chart-block" style={{ height: 180 }}>
                  <div className="chart-title">
                    {mode === 'weather' ? 'Session Temperature Trace' : 'Session Price Trace'}
                  </div>
                  <Line data={chartData} options={chartOptions} />
                </div>
              )}

              {/* Raw JSON toggle + view */}
              {rawJson && (
                <>
                  <div
                    className="raw-toggle"
                    onClick={() => setShowRaw((prev) => !prev)}
                  >
                    {showRaw ? 'Hide raw JSON (debug)' : 'Show raw JSON (debug)'}
                  </div>
                  {showRaw && (
                    <pre className="raw-json">
                      {JSON.stringify(rawJson, null, 2)}
                    </pre>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Right: System / Future Agent panel */}
          <aside className="card sidebar">
            <div className="card-title">System</div>
            <div className="sidebar-section">
              <strong>Phase 1 · Direct Tools</strong>
              This dashboard calls Python tools:
              <br />
              <code>get_weather(city)</code> and <code>get_crypto_price(coin)</code>.
              <br />
              Raw JSON is saved under:
              <br />
              <code>data/weather_*.json</code> and <code>data/crypto_*.json</code>.
            </div>
            <div className="sidebar-section">
              <strong>Phase 2 · Agent Loop (Reserved)</strong>
              In the next phase, this area will surface:
              <br />• Scheduled checks (e.g. daily reports)
              <br />• Alerts (e.g. BTC below threshold)
              <br />• AI-generated summaries of trends.
            </div>
            <div className="sidebar-section">
              <strong>Debug & Testing</strong>
              You can also:
              <br />• Call the API via Postman:
              <br />
              <code>/api/weather?city=...</code>
              <br />
              <code>/api/crypto?coin=...</code>
              <br />• Use the CLI:
              <br />
              <code>poetry run app weather --city ...</code>
              <br />
              <code>poetry run app crypto --coin ...</code>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}

export default App;