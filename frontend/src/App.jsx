// frontend/src/App.jsx
import React, { useState, useEffect } from 'react';
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
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

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

  // Chat agent state
  const [chatMessage, setChatMessage] = useState('');
  const [chatAnswer, setChatAnswer] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState('');
    // Phase 3 state: toggle + backend history
  const [phase3Open, setPhase3Open] = useState(false);
  const [historyItems, setHistoryItems] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState('');
    // Schedules (Phase 3) UI state
  const [schedulesOpen, setSchedulesOpen] = useState(false);
  const [schedules, setSchedules] = useState([]);
    // Show only the 2 most recently created schedules
  const visibleSchedules = schedules.slice(-2).reverse();
  const [schedulesLoading, setSchedulesLoading] = useState(false);
  const [schedulesError, setSchedulesError] = useState('');

  const [newScheduleName, setNewScheduleName] = useState('Morning Briefing');
  const [newScheduleTime, setNewScheduleTime] = useState('08:00'); // HH:MM UTC
  const [newScheduleCity, setNewScheduleCity] = useState('');
  const [newScheduleCoin, setNewScheduleCoin] = useState('');
  const [creatingSchedule, setCreatingSchedule] = useState(false);

  // Collapsible placeholders for Alerts / Notifications
  const [alertsOpen, setAlertsOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

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
        const msg = data.detail || 'Request failed.';

        // If backend reports a rate-limit issue, show a friendly message
        if (msg.toLowerCase().includes('rate-limited')) {
          setError(
            'Crypto data is temporarily unavailable because the provider rate limit was exceeded. Please try again in a few minutes.'
          );
        } else {
          setError(msg);
        }
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

  // Call the LLM agent endpoint
  const handleChatSubmit = async () => {
    const trimmed = chatMessage.trim();

    if (!trimmed) {
      setChatError('Please enter a question for the agent.');
      setChatAnswer('');
      return;
    }

    setChatError('');
    setChatAnswer('');
    setChatLoading(true);

    try {
      const res = await fetch(`${API_BASE}/agent/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed }),
      });

      const data = await res.json();

      if (!res.ok) {
        // Backend returns { detail: "..." } on errors (e.g. OpenAI quota)
        setChatError(data.detail || 'Agent request failed.');
      } else {
        setChatAnswer(data.answer || '');
      }
    } catch (err) {
      console.error(err);
      setChatError('Network error calling agent. Is the backend running on http://localhost:8000?');
    } finally {
      setChatLoading(false);
    }
  };

     // Load recent history from backend when Phase 3 is opened
  const loadHistory = async () => {
    setHistoryLoading(true);
    setHistoryError('');
    try {
      const res = await fetch(`${API_BASE}/history?limit=20`);
      const data = await res.json();
      if (!res.ok) {
        setHistoryError(data.detail || 'Failed to load history.');
        setHistoryItems([]);
      } else {
        setHistoryItems(data);
      }
    } catch (err) {
      console.error(err);
      setHistoryError('Network error loading history.');
      setHistoryItems([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  // Load schedules from backend
  const loadSchedules = async () => {
    setSchedulesLoading(true);
    setSchedulesError('');
    try {
      const res = await fetch(`${API_BASE}/schedules`);
      const data = await res.json();
      if (!res.ok) {
        setSchedulesError(data.detail || 'Failed to load schedules.');
        setSchedules([]);
      } else {
        setSchedules(data);
      }
    } catch (err) {
      console.error(err);
      setSchedulesError('Network error loading schedules.');
      setSchedules([]);
    } finally {
      setSchedulesLoading(false);
    }
  };

  // Create a new daily schedule
  const handleCreateSchedule = async (e) => {
    e.preventDefault();
    if (!newScheduleCity.trim() && !newScheduleCoin.trim()) {
      setSchedulesError('Please provide at least a city or a coin for the schedule.');
      return;
    }

    setSchedulesError('');
    setCreatingSchedule(true);
    try {
      const body = {
        name: newScheduleName.trim() || 'Daily Check',
        time_of_day: newScheduleTime || '08:00',
        city: newScheduleCity.trim() || null,
        coin: newScheduleCoin.trim().toLowerCase() || null,
      };

      const res = await fetch(`${API_BASE}/schedules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) {
        setSchedulesError(data.detail || 'Failed to create schedule.');
      } else {
        // refresh list
        await loadSchedules();
        // keep form values so user can tweak; or reset city/coin if you prefer
      }
    } catch (err) {
      console.error(err);
      setSchedulesError('Network error creating schedule.');
    } finally {
      setCreatingSchedule(false);
    }
  };

  // Enable/disable a schedule
  const handleToggleSchedule = async (scheduleId, enabled) => {
    try {
      const res = await fetch(`${API_BASE}/schedules/${scheduleId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled }),
      });
      const data = await res.json();
      if (!res.ok) {
        setSchedulesError(data.detail || 'Failed to update schedule.');
      } else {
        await loadSchedules();
      }
    } catch (err) {
      console.error(err);
      setSchedulesError('Network error updating schedule.');
    }
  };


    // Delete a schedule
  const handleDeleteSchedule = async (scheduleId) => {
    try {
      const res = await fetch(`${API_BASE}/schedules/${scheduleId}`, {
        method: 'DELETE',
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setSchedulesError(data.detail || 'Failed to delete schedule.');
      } else {
        await loadSchedules();
      }
    } catch (err) {
      console.error(err);
      setSchedulesError('Network error deleting schedule.');
    }
  };

  // When Phase 3 is opened, load both history and schedules
  useEffect(() => {
    if (phase3Open) {
      loadHistory();
      loadSchedules();
    }
  }, [phase3Open]);


  

  // When Phase 3 is opened, load both history and schedules
  useEffect(() => {
    if (phase3Open) {
      loadHistory();
      loadSchedules();
    }
  }, [phase3Open]);

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
          <div className="badge">Signals · Phase 1 of 3</div>
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

          {/* Right: System / Agent panel */}
                    {/* Right: System / Agent / Phase 3 panel */}
          <aside className="card sidebar">
            <div className="card-title">System</div>

            {/* Phase 1 */}
            <div className="sidebar-section">
              <strong>Phase 1 · Live Tools</strong>
              This dashboard calls Python tools:
              <br />
              <code>get_weather(city)</code> and <code>get_crypto_price(coin)</code>.
              <br />
              Raw JSON is saved under:
              <br />
              <code>data/weather_*.json</code>
              <br />
              <code>data/crypto_*.json</code>.
            </div>

            {/* Phase 2: Chat */}
            <div className="sidebar-section">
              <strong>Phase 2 · Chat + LLM</strong>
              <p>
                Talk to the agent in natural language about weather and crypto.
                It will call the same live tools and combine the answers.
              </p>

              <div className="agent-chat">
                <textarea
                  className="agent-chat-textarea"
                  placeholder="Example: What's the weather in Hyderabad and the price of bitcoin right now?"
                  value={chatMessage}
                  onChange={(e) => {
                    setChatMessage(e.target.value);
                    setChatError('');
                    setChatAnswer('');
                  }}
                  onKeyDown={(e) => {
                    // Enter to send, Shift+Enter for new line
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleChatSubmit();
                    }
                  }}
                />

                <button
                  type="button"
                  className="button"
                  style={{ marginTop: '0.6rem', width: '100%', justifyContent: 'center' }}
                  onClick={handleChatSubmit}
                  disabled={chatLoading}
                >
                  {chatLoading && <span className="pulse-dot" />}
                  <span>{chatLoading ? 'Asking agent...' : 'Ask Agent'}</span>
                </button>

                {chatError && (
                  <div className="error" style={{ marginTop: '0.6rem' }}>
                    {chatError}
                  </div>
                )}

                {chatAnswer && !chatError && (
                  <div className="agent-chat-answer">
                    <div className="result-title">Agent Answer</div>
                    <div className="result-sub" style={{ whiteSpace: 'pre-wrap' }}>
                      {chatAnswer}
                    </div>
                  </div>
                )}

                <div className="agent-chat-tip">
                  Tip: press <code>Enter</code> to send, or <code>Shift+Enter</code> for a new line.
                </div>
              </div>
            </div>

            {/* Phase 3: toggle + panels */}
            <div className="sidebar-section">
              <strong>Phase 3 · Automations & Insights</strong>
              <p>
    Enable background checks and a shared activity feed. Schedules can run daily
    weather/crypto checks even when you are not on the page, with results logged
    into History. Alerts and notifications will be added next.
  </p>

              <button
                type="button"
                className="phase3-toggle"
                onClick={() => setPhase3Open((prev) => !prev)}
              >
                {phase3Open ? 'Collapse Phase 3' : 'Enable Phase 3'}
              </button>

              {phase3Open && (
                <div className="phase3-panel">
                  {/* History */}
                  <div className="phase3-block">
                    <div className="phase3-block-title">History & Insights</div>
                    {historyLoading && <div className="phase3-muted">Loading history...</div>}
                    {historyError && <div className="error">{historyError}</div>}
                    {!historyLoading && !historyError && historyItems.length === 0 && (
                      <div className="phase3-muted">
                        No history yet. Use "Get Info" or "Ask Agent" to generate some data.
                      </div>
                    )}
                    {!historyLoading && historyItems.length > 0 && (
                      <ul className="history-list">
                        {historyItems.map((item, idx) => (
                          <li key={idx} className="history-item">
                            <div className="history-meta">
                              <span className="history-kind">{item.kind}</span>
                              <span className="history-time">
                                {new Date(item.timestamp).toLocaleTimeString()}
                              </span>
                            </div>
                            <div className="history-query">{item.query}
                                  <div className="history-query">
      {item.kind === 'weather' && (
        <>
          <strong>{item.query}</strong>
          {' — '}
          {item.result?.temperature_c != null && (
            <>
              {item.result.temperature_c.toFixed(1)}°C
              {item.result?.description && ` · ${item.result.description}`}
            </>
          )}
        </>
      )}

      {item.kind === 'crypto' && (
        <>
          <strong>{item.query.toUpperCase()}</strong>
          {' — '}
          {item.result?.price_usd != null && (
            <>${item.result.price_usd.toFixed(2)}</>
          )}
          {typeof item.result?.change_24h === 'number' && (
            <> · {item.result.change_24h.toFixed(2)}% 24h</>
          )}
        </>
      )}

      {item.kind === 'agent' && (
        <>
          <strong>Q:</strong> {item.query}
          {item.result?.answer && (
            <>
              <br />
              <span className="history-answer-snippet">
                <strong>A:</strong>{' '}
                {item.result.answer.length > 120
                  ? item.result.answer.slice(0, 120) + '…'
                  : item.result.answer}
              </span>
            </>
          )}
        </>
      )}
    </div>
                            </div>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>

                  {/* Coming Soon blocks */}
                  <div className="phase3-block">
  <div className="phase3-block-title">Schedules</div>
  <div className="phase3-muted" style={{ marginBottom: '0.4rem' }}>
    Create simple daily checks for weather and crypto. Schedules are global.
  </div>

  {/* Create schedule form */}
  <form className="schedule-form" onSubmit={handleCreateSchedule}>
    <div className="schedule-form-row">
      <input
        className="input"
        type="text"
        placeholder="Schedule name (e.g. Morning Briefing)"
        value={newScheduleName}
        onChange={(e) => setNewScheduleName(e.target.value)}
      />
    </div>
    <div className="schedule-form-row">
      <input
        className="input"
        type="text"
        placeholder="Time (HH:MM UTC, e.g. 08:00)"
        value={newScheduleTime}
        onChange={(e) => setNewScheduleTime(e.target.value)}
      />
    </div>
    <div className="schedule-form-row">
      <input
        className="input"
        type="text"
        placeholder="City (optional, e.g. Hyderabad)"
        value={newScheduleCity}
        onChange={(e) => setNewScheduleCity(e.target.value)}
      />
    </div>
    <div className="schedule-form-row">
      <input
        className="input"
        type="text"
        placeholder="Coin id (optional, e.g. bitcoin)"
        value={newScheduleCoin}
        onChange={(e) => setNewScheduleCoin(e.target.value)}
      />
    </div>
    <button
      type="submit"
      className="button"
      style={{ marginTop: '0.5rem', width: '100%', justifyContent: 'center' }}
      disabled={creatingSchedule}
    >
      {creatingSchedule ? 'Creating…' : 'Create Schedule'}
    </button>
  </form>

  {/* Schedules list */}
  {schedulesError && (
    <div className="error" style={{ marginTop: '0.5rem' }}>
      {schedulesError}
    </div>
  )}

  {schedulesLoading && (
    <div className="phase3-muted" style={{ marginTop: '0.5rem' }}>
      Loading schedules…
    </div>
  )}

  {!schedulesLoading && !schedulesError && schedules.length === 0 && (
    <div className="phase3-muted" style={{ marginTop: '0.5rem' }}>
      No schedules yet. Create one above.
    </div>
  )}

 {!schedulesLoading && schedules.length > 0 && (
  <ul className="schedule-list" style={{ marginTop: '0.6rem' }}>
    {visibleSchedules.map((s) => (
      <li key={s.id} className="schedule-item">
        <div className="schedule-main">
          <span className="schedule-name">{s.name}</span>
          <span
            className={`schedule-pill ${
              s.enabled ? 'schedule-pill-on' : 'schedule-pill-off'
            }`}
          >
            {s.enabled ? 'ON' : 'OFF'}
          </span>
        </div>
        <div className="schedule-sub">
          Daily at {s.time_of_day} UTC
          {s.city && ` · City: ${s.city}`}
          {s.coin && ` · Coin: ${s.coin.toUpperCase()}`}
        </div>
        {s.last_status && (
          <div className="schedule-status">
            Last: {s.last_status}
          </div>
        )}
        <div style={{ marginTop: '0.3rem', fontSize: '0.75rem', display: 'flex', gap: '0.4rem' }}>
          <button
            type="button"
            className="phase3-inner-toggle"
            onClick={() => handleToggleSchedule(s.id, !s.enabled)}
          >
            {s.enabled ? 'Disable' : 'Enable'}
          </button>
          <button
            type="button"
            className="phase3-inner-toggle"
            onClick={() => handleDeleteSchedule(s.id)}
          >
            Delete
          </button>
        </div>
      </li>
    ))}
  </ul>
)}
</div>

                  <div className="phase3-block">
                    <div className="phase3-block-title">Alerts (Coming Soon)</div>
                    <div className="phase3-muted">
                      Configure alerts when prices move sharply or weather crosses thresholds.
                    </div>
                  </div>

                  <div className="phase3-block">
                    <div className="phase3-block-title">Notifications (Coming Soon)</div>
                    <div className="phase3-muted">
                      Connect channels like Telegram to receive summaries and alerts even when the
                      dashboard is closed.
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Debug */}
            <div className="sidebar-section">
              <strong>Debug & Testing</strong>
              You can also:
              <br />• Call the API via Postman:
              <br />
              <code>/api/weather?city=...</code>
              <br />
              <code>/api/crypto?coin=...</code>
              <br />
              <code>/api/agent/chat</code>
              <br />• Use the CLI:
              <br />
              <code>python -m cli.main weather --city ...</code>
              <br />
              <code>python -m cli.main crypto --coin ...</code>
              <br />
              <code>python -m cli.main chat -m "your question"</code>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}

export default App;