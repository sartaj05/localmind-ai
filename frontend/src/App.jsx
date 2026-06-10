import { useEffect, useState } from "react";
import {
  createSession,
  getSessionDetail,
  getSessions,
  sendSessionMessage,
  togglePinSession,
  deleteSession,
} from "./api/aiApi";
import { loginUser, registerUser } from "./api/authApi";
import "./App.css";

function App() {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [sessions, setSessions] = useState([]);
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

  const loadSessions = async () => {
    try {
      const res = await getSessions();
      const list = res.data.results || res.data.results?.results || [];
      setSessions(Array.isArray(list) ? list : []);
    } catch {
      showPopup("Failed to load sessions", "error");
    }
  };

  const openSession = async (session) => {
    try {
      setActiveSession(session);
      const res = await getSessionDetail(session.id);
      const detail = res.data.result;
      setMessages(detail?.messages || []);
    } catch {
      showPopup("Failed to open session", "error");
    }
  };

  useEffect(() => {
    if (isLoggedIn) {
      loadSessions();
    }
  }, [isLoggedIn]);

  const handleLogin = async () => {
    try {
      const res = await loginUser({ username, password });

      const access =
        res.data.access ||
        res.data.token ||
        res.data.tokens?.access ||
        res.data.data?.access;

      if (!access) {
        showPopup("Login success but token not found", "error");
        return;
      }

      localStorage.setItem("access_token", access);
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
      const res = await createSession({
        title: "New Chat",
      });

      const session = res.data.result;
      await loadSessions();
      await openSession(session);
      showPopup("New session created", "success");
    } catch {
      showPopup("Failed to create session", "error");
    }
  };

  const handleSendMessage = async () => {
    if (!prompt.trim()) return;

    setLoading(true);

    try {
      let session = activeSession;

      if (!session) {
        const res = await createSession({ title: "New Chat" });
        session = res.data.result;
        setActiveSession(session);
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

      const res = await sendSessionMessage(session.id, {
        message: userText,
      });

      const assistantMessage = res.data.assistant_message;

      setMessages((prev) => [
        ...prev.filter((msg) => !String(msg.id).startsWith("temp-user")),
        {
          id: `user-${Date.now()}`,
          role: "user",
          content: userText,
        },
        assistantMessage,
      ]);

      await loadSessions();
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
      await loadSessions();
      showPopup("Session pin updated", "success");
    } catch {
      showPopup("Pin failed", "error");
    }
  };

  const handleDelete = async (session) => {
    try {
      await deleteSession(session.id);

      if (activeSession?.id === session.id) {
        setActiveSession(null);
        setMessages([]);
      }

      await loadSessions();
      showPopup("Session moved to trash", "success");
    } catch {
      showPopup("Delete failed", "error");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    setIsLoggedIn(false);
    setActiveSession(null);
    setMessages([]);
    showPopup("Logged out successfully", "success");
  };

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

      <div className={`workspace-page ${sidebarOpen ? "with-sidebar" : "no-sidebar"}`}>
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

          <div className="session-list">
            {sessions.map((session) => (
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
                      handleDelete(session);
                    }}
                  >
                    🗑
                  </button>
                </div>
              </div>
            ))}
          </div>
        </aside>

        <main className={sidebarOpen ? "mind-main" : "mind-main expanded"}>
          <header className="mind-header">
            {!sidebarOpen && (
              <button className="session-open-btn" onClick={() => setSidebarOpen(true)}>
                ☰ Sessions
              </button>
            )}

            <div>
              <h1>{activeSession?.title || "LocalMind Workspace"}</h1>
              <p>
                A different AI workspace: session cards, thought stream, and local brain.
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