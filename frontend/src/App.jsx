import { useEffect, useState } from "react";
import { getAIHealth, askAI } from "./api/aiApi";
import "./App.css";

function App() {
  const [health, setHealth] = useState(null);
  const [prompt, setPrompt] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getAIHealth()
      .then((res) => setHealth(res.data))
      .catch(() => setHealth({ success: false }));
  }, []);

  const handleAsk = async () => {
    if (!prompt.trim()) return;

    setLoading(true);
    setAnswer("");

    try {
      const res = await askAI({
        prompt,
      });

      setAnswer(res.data.answer || "");
    } catch (error) {
      setAnswer(error.response?.data?.error?.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <div className="card">
        <h1>LocalMind AI</h1>

        <p>
          Backend:{" "}
          <b>{health?.success ? "Connected" : "Not Connected"}</b>
        </p>

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
  );
}

export default App;