import { useState } from "react";
import { askAI } from "./api/aiApi";
import { loginUser, registerUser } from "./api/authApi";
import "./App.css";

function App() {
  const [mode, setMode] = useState("login");

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [prompt, setPrompt] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  const [popup, setPopup] = useState({
    show: false,
    type: "success",
    message: "",
  });

  const [isLoggedIn, setIsLoggedIn] = useState(
    Boolean(localStorage.getItem("access_token"))
  );

  const showPopup = (message, type = "success") => {
    setPopup({
      show: true,
      type,
      message,
    });

    setTimeout(() => {
      setPopup({
        show: false,
        type: "success",
        message: "",
      });
    }, 3000);
  };

  const handleLogin = async () => {
    try {
      const res = await loginUser({
        username,
        password,
      });

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
      showPopup(
        error.response?.data?.error?.message || "Login failed",
        "error"
      );
    }
  };

  const handleRegister = async () => {
    try {
      await registerUser({
        username,
        email,
        password,
      });

      showPopup("Register successful. Now login.", "success");
      setMode("login");
      setPassword("");
    } catch (error) {
      showPopup(
        error.response?.data?.error?.message || "Register failed",
        "error"
      );
    }
  };

  const handleAsk = async () => {
    if (!prompt.trim()) return;

    setLoading(true);
    setAnswer("");

    try {
      const res = await askAI({ prompt });
      setAnswer(res.data.answer || res.data.result?.answer || "");
    } catch (error) {
      setAnswer(error.response?.data?.error?.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    setIsLoggedIn(false);
    showPopup("Logged out successfully", "success");
  };

  return (
    <>
      {popup.show && (
        <div className={`popup-toast ${popup.type}`}>
          <span>{popup.message}</span>
        </div>
      )}

      {!isLoggedIn ? (
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
      ) : (
        <div className="dashboard-page">
          <div className="chat-card">
            <div className="topbar">
              <div>
                <h1>LocalMind AI</h1>
                <p>Ask your local model anything.</p>
              </div>

              <button className="secondary" onClick={handleLogout}>
                Logout
              </button>
            </div>

            <textarea
              placeholder="Ask your local AI..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />

            <button onClick={handleAsk} disabled={loading}>
              {loading ? "Thinking..." : "Ask AI"}
            </button>

            {answer && (
              <div className="answer">
                <h3>Answer</h3>
                <p>{answer}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

export default App;