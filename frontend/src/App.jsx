import { useEffect, useState } from "react";
import {
  createSession,
  getSessionDetail,
  getSessions,
  getArchivedSessions,
  getTrashSessions,
  sendSessionMessage,
  togglePinSession,
  toggleArchiveSession,
  deleteSession,
  restoreSession,
  permanentDeleteSession,
  emptyTrashSessions,
  renameSession,
} from "./api/aiApi";
import { loginUser, registerUser } from "./api/authApi";
import "./App.css";

function App() {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [sessions, setSessions] = useState([]);
  const [sessionSearch, setSessionSearch] = useState("");
  const [sessionView, setSessionView] = useState("active");

  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [prompt, setPrompt] = useState("");

  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const [popup, setPopup] = useState({
    show: false,
    type: "success",
    message: "",
  });

  const [isLoggedIn, setIsLoggedIn] = useState(
    Boolean(localStorage.getItem("access_token"))
  );

  const showPopup = (message, type = "success") => {
    setPopup({ show: true, type, message });

    setTimeout(() => {
      setPopup({ show: false, type: "success", message: "" });
    }, 2600);
  };

  const normalizeSessions = (res) => {
    const data = res.data;

    if (Array.isArray(data?.results)) return data.results;
    if (Array.isArray(data?.results?.results)) return data.results.results;
    if (Array.isArray(data?.data?.results)) return data.data.results;

    return [];
  };

  const loadSessions = async (view = sessionView) => {
    try {
      let res;

      if (view === "archive") {
        res = await getArchivedSessions();
      } else if (view === "trash") {
        res = await getTrashSessions();
      } else {
        res = await getSessions();
      }

      const list = normalizeSessions(res);
      setSessions(list);
      return list;
    } catch {
      showPopup("Failed to load sessions", "error");
      return [];
    }
  };

  const openSession = async (session) => {
    if (sessionView === "trash") {
      showPopup("Restore session first to open it", "error");
      return;
    }

    try {
      setActiveSession(session);
      localStorage.setItem("active_session_id", String(session.id));

      const res = await getSessionDetail(session.id);
      const detail = res.data.result;

      setActiveSession(detail || session);
      setMessages(detail?.messages || []);
    } catch {
      showPopup("Failed to open session", "error");
    }
  };

  useEffect(() => {
    const restoreSession = async () => {
      if (!isLoggedIn) return;

      try {
        const list = await loadSessions("active");
        const savedSessionId = localStorage.getItem("active_session_id");

        if (!savedSessionId) return;

        const foundSession = list.find(
          (session) => String(session.id) === String(savedSessionId)
        );

        if (foundSession) {
          await openSession(foundSession);
        } else {
          localStorage.removeItem("active_session_id");
        }
      } catch {
        showPopup("Failed to restore session", "error");
      }
    };

    restoreSession();
  }, [isLoggedIn]);

  const handleLogin = async () => {
    try {
      const res = await loginUser({ username, password });

      const access =
        res.data.access ||
        res.data.token ||
        res.data.tokens?.access ||
        res.data.data?.access;

      const refresh =
        res.data.refresh ||
        res.data.tokens?.refresh ||
        res.data.data?.refresh;

      if (!access) {
        showPopup("Login success but token not found", "error");
        return;
      }

      localStorage.setItem("access_token", access);

      if (refresh) {
        localStorage.setItem("refresh_token", refresh);
      }

      setIsLoggedIn(true);
      showPopup("Login successful", "success");
    } catch (error) {
      showPopup(error.response?.data?.error?.message || "Login failed", "error");
    }
  };

  const handleRegister = async () => {
    try {
      await registerUser({ username, email, password });
      showPopup("Register successful. Now login.", "success");
      setMode("login");
      setPassword("");
    } catch (error) {
      showPopup(error.response?.data?.error?.message || "Register failed", "error");
    }
  };

  const handleNewSession = async () => {
    try {
      if (sessionView !== "active") {
        setSessionView("active");
      }

      const res = await createSession({ title: "New Chat" });
      const session = res.data.result;

      await loadSessions("active");
      await openSession(session);
      showPopup("New session created", "success");
    } catch {
      showPopup("Failed to create session", "error");
    }
  };

  const handleChangeSessionView = async (view) => {
    setSessionView(view);
    setActiveSession(null);
    setMessages([]);
    localStorage.removeItem("active_session_id");
    await loadSessions(view);
  };

  const handleSendMessage = async () => {
    if (!prompt.trim()) return;

    if (sessionView !== "active") {
      showPopup("Switch to Active sessions to send messages", "error");
      return;
    }

    setLoading(true);

    try {
      let session = activeSession;

      if (!session) {
        const res = await createSession({ title: "New Chat" });
        session = res.data.result;
        setActiveSession(session);
        localStorage.setItem("active_session_id", String(session.id));
      }

      const userText = prompt;
      setPrompt("");

      setMessages((prev) => [
        ...prev,
        {
          id: `temp-user-${Date.now()}`,
          role: "user",
          content: userText,
        },
      ]);

      await sendSessionMessage(session.id, {
        message: userText,
      });

      await loadSessions("active");

      const detailRes = await getSessionDetail(session.id);
      const detail = detailRes.data.result;

      setActiveSession(detail || session);
      setMessages(detail?.messages || []);
      localStorage.setItem("active_session_id", String(session.id));
    } catch (error) {
      showPopup(
        error.response?.data?.error?.message || "Message failed",
        "error"
      );
    } finally {
      setLoading(false);
    }
  };

  const handlePin = async (session) => {
    try {
      await togglePinSession(session.id);
      const list = await loadSessions(sessionView);

      if (activeSession?.id === session.id) {
        const updated = list.find((item) => item.id === session.id);
        if (updated) setActiveSession(updated);
      }

      showPopup("Session pin updated", "success");
    } catch {
      showPopup("Pin failed", "error");
    }
  };

  const handleArchive = async (session) => {
    try {
      await toggleArchiveSession(session.id);

      if (activeSession?.id === session.id) {
        setActiveSession(null);
        setMessages([]);
        localStorage.removeItem("active_session_id");
      }

      await loadSessions(sessionView);
      showPopup(
        sessionView === "archive" ? "Session unarchived" : "Session archived",
        "success"
      );
    } catch {
      showPopup("Archive failed", "error");
    }
  };

  const handleDelete = async (session) => {
    try {
      await deleteSession(session.id);

      if (activeSession?.id === session.id) {
        setActiveSession(null);
        setMessages([]);
        localStorage.removeItem("active_session_id");
      }

      await loadSessions(sessionView);
      showPopup("Session moved to trash", "success");
    } catch {
      showPopup("Delete failed", "error");
    }
  };

  const handleRestore = async (session) => {
    try {
      await restoreSession(session.id);
      await loadSessions("trash");
      showPopup("Session restored", "success");
    } catch {
      showPopup("Restore failed", "error");
    }
  };

  const handlePermanentDelete = async (session) => {
    const ok = window.confirm("Permanently delete this session?");
    if (!ok) return;

    try {
      await permanentDeleteSession(session.id);
      await loadSessions("trash");
      showPopup("Session permanently deleted", "success");
    } catch {
      showPopup("Permanent delete failed", "error");
    }
  };

  const handleEmptyTrash = async () => {
    const ok = window.confirm("Empty trash permanently?");
    if (!ok) return;

    try {
      await emptyTrashSessions();
      setActiveSession(null);
      setMessages([]);
      localStorage.removeItem("active_session_id");
      await loadSessions("trash");
      showPopup("Trash emptied", "success");
    } catch {
      showPopup("Empty trash failed", "error");
    }
  };

  const handleRename = async (session) => {
    const newTitle = window.prompt("Enter new session title", session.title);

    if (!newTitle || !newTitle.trim()) return;

    try {
      await renameSession(session.id, {
        title: newTitle.trim(),
      });

      await loadSessions(sessionView);

      if (activeSession?.id === session.id) {
        const detailRes = await getSessionDetail(session.id);
        setActiveSession(detailRes.data.result);
      }

      showPopup("Session renamed successfully", "success");
    } catch {
      showPopup("Rename failed", "error");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("active_session_id");
    setIsLoggedIn(false);
    setActiveSession(null);
    setMessages([]);
    showPopup("Logged out successfully", "success");
  };

  const filteredSessions = sessions.filter((session) =>
    session.title?.toLowerCase().includes(sessionSearch.toLowerCase())
  );

  if (!isLoggedIn) {
    return (
      <>
        {popup.show && (
          <div className={`popup-toast ${popup.type}`}>
            <span>{popup.message}</span>
          </div>
        )}

        <div className="auth-page">
          <div className="auth-shell">
            <div className="brand-panel">
              <div className="logo-badge">LM</div>
              <h1>LocalMind AI</h1>
              <p>Your private local AI workspace powered by Django + Ollama.</p>
            </div>

            <div className="auth-card">
              <h2>{mode === "login" ? "Welcome back" : "Create account"}</h2>
              <p className="muted">
                {mode === "login"
                  ? "Login using username and password."
                  : "Register using username, email, and password."}
              </p>

              <input
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />

              {mode === "register" && (
                <input
                  type="email"
                  placeholder="Email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              )}

              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />

              <button onClick={mode === "login" ? handleLogin : handleRegister}>
                {mode === "login" ? "Login" : "Register"}
              </button>

              <p className="switch-text">
                {mode === "login" ? "No account?" : "Already registered?"}
                <span
                  onClick={() => {
                    setMode(mode === "login" ? "register" : "login");
                    setPassword("");
                  }}
                >
                  {mode === "login" ? " Register" : " Login"}
                </span>
              </p>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      {popup.show && (
        <div className={`popup-toast ${popup.type}`}>
          <span>{popup.message}</span>
        </div>
      )}

      <div
        className={`workspace-page ${sidebarOpen ? "with-sidebar" : "no-sidebar"}`}
      >
        <aside className={`session-sidebar ${sidebarOpen ? "" : "closed"}`}>
          <div className="side-head">
            <div>
              <h2>MindSpace</h2>
              <p>Session galaxy</p>
            </div>
            <button className="icon-btn" onClick={() => setSidebarOpen(false)}>
              ×
            </button>
          </div>

          <button className="new-chat-btn" onClick={handleNewSession}>
            + New Thought
          </button>

          <input
            className="session-search"
            placeholder="Search sessions..."
            value={sessionSearch}
            onChange={(e) => setSessionSearch(e.target.value)}
          />

          <div className="session-tabs">
            <button
              className={sessionView === "active" ? "active" : ""}
              onClick={() => handleChangeSessionView("active")}
            >
              Active
            </button>

            <button
              className={sessionView === "archive" ? "active" : ""}
              onClick={() => handleChangeSessionView("archive")}
            >
              Archive
            </button>

            <button
              className={sessionView === "trash" ? "active" : ""}
              onClick={() => handleChangeSessionView("trash")}
            >
              Trash
            </button>
          </div>

          {sessionView === "trash" && (
            <button className="empty-trash-btn" onClick={handleEmptyTrash}>
              Empty Trash
            </button>
          )}

          <div className="session-list">
            {filteredSessions.length === 0 ? (
              <div className="session-empty">No sessions found</div>
            ) : (
              filteredSessions.map((session) => (
                <div
                  key={session.id}
                  className={`session-item ${
                    activeSession?.id === session.id ? "active" : ""
                  }`}
                  onClick={() => openSession(session)}
                >
                  <div>
                    <strong>
                      {session.is_pinned ? "📌 " : ""}
                      {session.title}
                    </strong>
                    <span>{session.message_count || 0} messages</span>
                  </div>

                  <div className="session-actions">
                    {sessionView !== "trash" && (
                      <>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRename(session);
                          }}
                        >
                          ✏️
                        </button>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handlePin(session);
                          }}
                        >
                          📌
                        </button>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleArchive(session);
                          }}
                        >
                          📦
                        </button>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(session);
                          }}
                        >
                          🗑
                        </button>
                      </>
                    )}

                    {sessionView === "trash" && (
                      <>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRestore(session);
                          }}
                        >
                          ♻️
                        </button>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handlePermanentDelete(session);
                          }}
                        >
                          ❌
                        </button>
                      </>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </aside>

        <main className={sidebarOpen ? "mind-main" : "mind-main expanded"}>
          <header className="mind-header">
            {!sidebarOpen && (
              <button
                className="session-open-btn"
                onClick={() => setSidebarOpen(true)}
              >
                ☰ Sessions
              </button>
            )}

            <div>
              <h1>{activeSession?.title || "LocalMind Workspace"}</h1>
              <p>
                A different AI workspace: session cards, thought stream, and
                local brain.
              </p>
            </div>

            <button className="secondary" onClick={handleLogout}>
              Logout
            </button>
          </header>

          <section className="thought-board">
            {messages.length === 0 ? (
              <div className="empty-state">
                <div className="orb">AI</div>
                <h2>Start a focused thought session</h2>
                <p>
                  Create a session or ask directly. Your local model will answer
                  and the conversation will be saved.
                </p>
              </div>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className={`message-card ${msg.role}`}>
                  <span>{msg.role === "user" ? "You" : "LocalMind"}</span>
                  <p>{msg.content}</p>
                </div>
              ))
            )}
          </section>

          <footer className="prompt-dock">
            <textarea
              placeholder="Type your thought here..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
            />

            <button onClick={handleSendMessage} disabled={loading}>
              {loading ? "Thinking..." : "Send"}
            </button>
          </footer>
        </main>
      </div>
    </>
  );
}

export default App;