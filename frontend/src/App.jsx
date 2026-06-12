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
  getKnowledgeDocuments,
  uploadKnowledgeDocument,
  deleteKnowledgeDocument,
  rebuildKnowledgeDocument,
  getDocumentChunks,
  askRAG,
  streamRAGAsk,
  getModels,
  getAIPreferences,
  updateAIPreferences,
  getDailyUsage,
  getDashboardSummary,
  getKnowledgeHistory,
  deleteKnowledgeHistory,
  exportKnowledgeHistoryTXT,
  exportKnowledgeHistoryJSON,
  exportChatSessionTXT,
  exportChatSessionJSON,
} from "./api/aiApi";
import {
  exportAllChatSessionsTXT,
  exportAllChatSessionsJSON,
  clearKnowledgeHistory,
  exportAllKnowledgeHistoryTXT,
  exportAllKnowledgeHistoryJSON,
} from "./api/exportApi";

import { loginUser, registerUser } from "./api/authApi";
import "./App.css";

function App() {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [activePanel, setActivePanel] = useState(
    localStorage.getItem("active_panel") || "chat",
  );

  const [sessions, setSessions] = useState([]);
  const [sessionSearch, setSessionSearch] = useState("");
  const [sessionView, setSessionView] = useState("active");
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [prompt, setPrompt] = useState("");

  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(
    localStorage.getItem("selected_model") || "",
  );

  const [aiPreferences, setAiPreferences] = useState(null);
  const [savingPreferences, setSavingPreferences] = useState(false);

  const [documents, setDocuments] = useState([]);
  const [documentSearch, setDocumentSearch] = useState("");
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadingDocs, setUploadingDocs] = useState(false);
  const [documentChunks, setDocumentChunks] = useState([]);
  const [ragQuestion, setRagQuestion] = useState("");
  const [ragAnswer, setRagAnswer] = useState("");
  const [ragSources, setRagSources] = useState([]);
  const [askingRag, setAskingRag] = useState(false);
  const [streamingRag, setStreamingRag] = useState(false);
  const [previewDocument, setPreviewDocument] = useState(null);
  const [dailyUsage, setDailyUsage] = useState(null);
  const [dashboardSummary, setDashboardSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [knowledgeHistory, setKnowledgeHistory] = useState([]);
  const [clearModalOpen, setClearModalOpen] = useState(false);
  const [clearPassword, setClearPassword] = useState("");
  const [clearingHistory, setClearingHistory] = useState(false);
  const [popup, setPopup] = useState({
    show: false,
    type: "success",
    message: "",
  });

  const [isLoggedIn, setIsLoggedIn] = useState(
    Boolean(localStorage.getItem("access_token")),
  );

  const showPopup = (message, type = "success") => {
    setPopup({ show: true, type, message });

    setTimeout(() => {
      setPopup({ show: false, type: "success", message: "" });
    }, 2600);
  };

  const normalizeList = (res) => {
    const data = res.data;

    if (Array.isArray(data?.results)) return data.results;
    if (Array.isArray(data?.results?.results)) return data.results.results;
    if (Array.isArray(data?.data?.results)) return data.data.results;

    return [];
  };

  const loadModels = async () => {
    try {
      const res = await getModels();
      const list = res.data.results || [];

      setModels(list);

      if (!selectedModel && list.length > 0) {
        const defaultModel = res.data.default_model || list[0].name;
        setSelectedModel(defaultModel);
        localStorage.setItem("selected_model", defaultModel);
      }
    } catch {
      showPopup("Failed to load models", "error");
    }
  };

  const loadAIPreferences = async () => {
    try {
      const res = await getAIPreferences();
      const pref = res.data.result;

      setAiPreferences(pref);

      if (pref?.default_model) {
        setSelectedModel(pref.default_model);
        localStorage.setItem("selected_model", pref.default_model);
      }
    } catch {
      showPopup("Failed to load AI preferences", "error");
    }
  };

  const loadSessions = async (view = sessionView) => {
    try {
      let res;

      if (view === "archive") res = await getArchivedSessions();
      else if (view === "trash") res = await getTrashSessions();
      else res = await getSessions();

      const list = normalizeList(res);
      setSessions(list);
      return list;
    } catch {
      showPopup("Failed to load sessions", "error");
      return [];
    }
  };

  const loadDocuments = async () => {
    try {
      const res = await getKnowledgeDocuments();
      setDocuments(normalizeList(res));
    } catch {
      showPopup("Failed to load documents", "error");
    }
  };
  const loadKnowledgeHistory = async () => {
    try {
      const res = await getKnowledgeHistory();
      setKnowledgeHistory(res.data.results || []);
    } catch {
      showPopup("Failed to load knowledge history", "error");
    }
  };

  const handleDeleteKnowledgeHistory = async (item) => {
    const ok = window.confirm("Delete this knowledge history?");
    if (!ok) return;

    try {
      await deleteKnowledgeHistory(item.id);
      await loadKnowledgeHistory();

      if (ragQuestion === item.question) {
        setRagQuestion("");
        setRagAnswer("");
        setRagSources([]);
      }

      showPopup("Knowledge history deleted", "success");
    } catch {
      showPopup("Delete knowledge history failed", "error");
    }
  };
  const downloadBlobFile = (response, filename) => {
    const blob = new Blob([response.data]);
    const url = window.URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();

    link.remove();
    window.URL.revokeObjectURL(url);
  };

  const handleExportAllChatTXT = async () => {
    try {
      const res = await exportAllChatSessionsTXT();
      downloadBlobFile(res, "all_chat_sessions.txt");
      showPopup("All chat sessions TXT exported", "success");
    } catch {
      showPopup("All chat sessions TXT export failed", "error");
    }
  };

  const handleExportAllChatJSON = async () => {
    try {
      const res = await exportAllChatSessionsJSON();
      downloadBlobFile(res, "all_chat_sessions.json");
      showPopup("All chat sessions JSON exported", "success");
    } catch {
      showPopup("All chat sessions JSON export failed", "error");
    }
  };

  const handleClearKnowledgeHistory = () => {
    console.log("Clear Knowledge History clicked");
    setClearPassword("");
    setClearModalOpen(true);
  };

  const confirmClearKnowledgeHistory = async () => {
    if (!clearPassword.trim()) {
      showPopup("Password is required", "error");
      return;
    }

    setClearingHistory(true);

    try {
      await clearKnowledgeHistory(clearPassword);

      setKnowledgeHistory([]);
      setRagQuestion("");
      setRagAnswer("");
      setRagSources([]);
      setClearPassword("");
      setClearModalOpen(false);

      showPopup("Knowledge history cleared", "success");
    } catch (error) {
      showPopup(
        error.response?.data?.error ||
          error.response?.data?.error?.message ||
          "Clear knowledge history failed",
        "error",
      );
    } finally {
      setClearingHistory(false);
    }
  };
  const handleExportKnowledgeTXT = async (item) => {
    try {
      const res = await exportKnowledgeHistoryTXT(item.id);
      downloadBlobFile(res, `knowledge_history_${item.id}.txt`);
      showPopup("Knowledge TXT exported", "success");
    } catch {
      showPopup("Knowledge TXT export failed", "error");
    }
  };

  const handleExportKnowledgeJSON = async (item) => {
    try {
      const res = await exportKnowledgeHistoryJSON(item.id);
      downloadBlobFile(res, `knowledge_history_${item.id}.json`);
      showPopup("Knowledge JSON exported", "success");
    } catch {
      showPopup("Knowledge JSON export failed", "error");
    }
  };

  const handleExportChatTXT = async (session) => {
    try {
      const res = await exportChatSessionTXT(session.id);
      downloadBlobFile(res, `chat_session_${session.id}.txt`);
      showPopup("Chat TXT exported", "success");
    } catch {
      showPopup("Chat TXT export failed", "error");
    }
  };

  const handleExportChatJSON = async (session) => {
    try {
      const res = await exportChatSessionJSON(session.id);
      downloadBlobFile(res, `chat_session_${session.id}.json`);
      showPopup("Chat JSON exported", "success");
    } catch {
      showPopup("Chat JSON export failed", "error");
    }
  };
  const handleExportAllKnowledgeTXT = async () => {
    try {
      const res = await exportAllKnowledgeHistoryTXT();
      downloadBlobFile(res, "all_knowledge_history.txt");
      showPopup("All knowledge TXT exported", "success");
    } catch {
      showPopup("All knowledge TXT export failed", "error");
    }
  };

  const handleExportAllKnowledgeJSON = async () => {
    try {
      const res = await exportAllKnowledgeHistoryJSON();
      downloadBlobFile(res, "all_knowledge_history.json");
      showPopup("All knowledge JSON exported", "success");
    } catch {
      showPopup("All knowledge JSON export failed", "error");
    }
  };
  const loadDashboardData = async () => {
    try {
      const [dailyRes, summaryRes] = await Promise.all([
        getDailyUsage(),
        getDashboardSummary(),
      ]);

      setDailyUsage(dailyRes.data);
      setDashboardSummary(summaryRes.data.summary);
    } catch {
      showPopup("Failed to load dashboard", "error");
    }
  };

  const handleModelChange = (event) => {
    const model = event.target.value;
    setSelectedModel(model);
    localStorage.setItem("selected_model", model);

    if (aiPreferences) {
      setAiPreferences((prev) => ({
        ...prev,
        default_model: model,
      }));
    }
  };

  const handlePreferenceChange = (field, value) => {
    setAiPreferences((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSavePreferences = async () => {
    if (!aiPreferences) return;

    setSavingPreferences(true);

    try {
      const payload = {
        default_model: aiPreferences.default_model || selectedModel,
        rag_top_k: Number(aiPreferences.rag_top_k || 3),
        show_sources: Boolean(aiPreferences.show_sources),
        auto_generate_title: Boolean(aiPreferences.auto_generate_title),
        stream_format: aiPreferences.stream_format || "plain",
        daily_request_limit: Number(aiPreferences.daily_request_limit || 100),
        max_prompt_characters: Number(
          aiPreferences.max_prompt_characters || 8000,
        ),
      };

      const res = await updateAIPreferences(payload);
      const updated = res.data.result;

      setAiPreferences(updated);

      if (updated?.default_model) {
        setSelectedModel(updated.default_model);
        localStorage.setItem("selected_model", updated.default_model);
      }

      showPopup("AI preferences saved", "success");
    } catch (error) {
      showPopup(
        error.response?.data?.error?.message || "Failed to save preferences",
        "error",
      );
    } finally {
      setSavingPreferences(false);
    }
  };

  const handleResetPreferenceDraft = () => {
    loadAIPreferences();
  };

  const handlePanelChange = async (panel) => {
    setActivePanel(panel);
    localStorage.setItem("active_panel", panel);

    if (panel === "knowledge") {
      await loadDocuments();
      await loadKnowledgeHistory();
    }

    if (panel === "settings") {
      await loadModels();
      await loadAIPreferences();
    }

    if (panel === "dashboard") {
      await loadDashboardData();
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

      await loadModels();
      await loadAIPreferences();

      const savedPanel = localStorage.getItem("active_panel") || "chat";

      if (savedPanel === "knowledge") {
        await loadDocuments();
        await loadKnowledgeHistory();
      }

      if (savedPanel === "dashboard") {
        await loadDashboardData();
      }

      const list = await loadSessions("active");
      const savedSessionId = localStorage.getItem("active_session_id");

      if (!savedSessionId) return;

      const foundSession = list.find(
        (session) => String(session.id) === String(savedSessionId),
      );

      if (foundSession) await openSession(foundSession);
      else localStorage.removeItem("active_session_id");
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
        res.data.refresh || res.data.tokens?.refresh || res.data.data?.refresh;

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
      showPopup(
        error.response?.data?.error?.message || "Login failed",
        "error",
      );
    }
  };

  const handleRegister = async () => {
    try {
      await registerUser({ username, email, password });
      showPopup("Register successful. Now login.", "success");
      setMode("login");
      setPassword("");
    } catch (error) {
      showPopup(
        error.response?.data?.error?.message || "Register failed",
        "error",
      );
    }
  };

  const handleNewSession = async () => {
    try {
      setActivePanel("chat");
      setSessionView("active");

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

    if (activePanel !== "chat") {
      showPopup("Switch to Chat panel to send messages", "error");
      return;
    }

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
        model: selectedModel,
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
        "error",
      );
    } finally {
      setLoading(false);
    }
  };

  const handlePin = async (session) => {
    try {
      await togglePinSession(session.id);
      await loadSessions(sessionView);
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
        "success",
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
      await renameSession(session.id, { title: newTitle.trim() });
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

  const handleFileChange = (event) => {
    setSelectedFiles(Array.from(event.target.files || []));
  };

  const uploadSelectedFilesIfAny = async () => {
    if (selectedFiles.length === 0) return;

    for (const file of selectedFiles) {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("title", file.name);

      await uploadKnowledgeDocument(formData);
    }

    setSelectedFiles([]);
    await loadDocuments();
  };

  const handleUploadDocuments = async () => {
    if (selectedFiles.length === 0) {
      showPopup("Please select files first", "error");
      return;
    }

    setUploadingDocs(true);

    try {
      await uploadSelectedFilesIfAny();
      showPopup("Documents uploaded successfully", "success");
    } catch (error) {
      showPopup(
        error.response?.data?.error?.message ||
          error.response?.data?.error ||
          error.response?.data?.message ||
          "Document upload failed",
        "error",
      );
    } finally {
      setUploadingDocs(false);
    }
  };

  const handleDeleteDocument = async (document) => {
    const ok = window.confirm(`Delete ${document.title}?`);
    if (!ok) return;

    try {
      await deleteKnowledgeDocument(document.id);
      await loadDocuments();
      setPreviewDocument(null);
      showPopup("Document deleted", "success");
    } catch {
      showPopup("Delete document failed", "error");
    }
  };

  const handleRebuildDocument = async (document) => {
    try {
      await rebuildKnowledgeDocument(document.id);
      await loadDocuments();
      showPopup("Document rebuilt successfully", "success");
    } catch {
      showPopup("Rebuild failed", "error");
    }
  };

  const handlePreviewChunks = async (document) => {
    try {
      const res = await getDocumentChunks(document.id);
      setPreviewDocument(document);
      setDocumentChunks(res.data.chunks || []);
    } catch {
      showPopup("Chunk preview failed", "error");
    }
  };

  const handleAskKnowledge = async () => {
    if (!ragQuestion.trim()) {
      showPopup("Please enter a knowledge question", "error");
      return;
    }

    setAskingRag(true);
    setRagAnswer("");
    setRagSources([]);

    try {
      await uploadSelectedFilesIfAny();

      const res = await askRAG({
        question: ragQuestion,
        model: selectedModel,
        top_k: aiPreferences?.rag_top_k || 5,
      });

      setRagAnswer(res.data.answer || "");
      setRagSources(res.data.sources || []);

      await loadKnowledgeHistory();

      showPopup("Knowledge answer generated", "success");
    } catch (error) {
      showPopup(
        error.response?.data?.error?.message ||
          error.response?.data?.error ||
          error.response?.data?.message ||
          "Knowledge ask failed",
        "error",
      );
    } finally {
      setAskingRag(false);
    }
  };
  const handleStreamAskKnowledge = async () => {
    if (!ragQuestion.trim()) {
      showPopup("Please enter a knowledge question", "error");
      return;
    }

    setStreamingRag(true);
    setRagAnswer("");
    setRagSources([]);

    try {
      let session = activeSession;

      if (!session || sessionView !== "active") {
        const sessionRes = await createSession({ title: "Knowledge Chat" });
        session = sessionRes.data.result;
        setActiveSession(session);
        localStorage.setItem("active_session_id", String(session.id));
        await loadSessions("active");
      }

      await uploadSelectedFilesIfAny();

      const response = await streamRAGAsk(session.id, {
        message: ragQuestion,
        model: selectedModel,
        top_k: aiPreferences?.rag_top_k || 5,
      });

      if (!response.ok) {
        throw new Error("RAG streaming request failed");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let finalText = "";

      while (true) {
        const { value, done } = await reader.read();

        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        finalText += chunk;
        setRagAnswer(finalText);
      }

      await openSession(session);
      await loadSessions("active");
      await loadKnowledgeHistory();

      showPopup("Streaming answer completed", "success");
    } catch (error) {
      showPopup(error.message || "Streaming RAG failed", "error");
    } finally {
      setStreamingRag(false);
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
    session.title?.toLowerCase().includes(sessionSearch.toLowerCase()),
  );

  const filteredDocuments = documents.filter((doc) =>
    doc.title?.toLowerCase().includes(documentSearch.toLowerCase()),
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

      {clearModalOpen && (
        <div className="app-modal-backdrop">
          <div className="app-modal-card">
            <h2>Clear Knowledge History?</h2>

            <p>
              This will permanently delete all knowledge history. Enter your
              password to confirm.
            </p>

            <input
              type="password"
              placeholder="Enter password"
              value={clearPassword}
              onChange={(e) => setClearPassword(e.target.value)}
              autoFocus
            />

            <div className="app-modal-actions">
              <button
                type="button"
                className="modal-cancel-btn"
                onClick={() => {
                  setClearPassword("");
                  setClearModalOpen(false);
                }}
                disabled={clearingHistory}
              >
                Cancel
              </button>

              <button
                type="button"
                className="modal-danger-btn"
                onClick={confirmClearKnowledgeHistory}
                disabled={clearingHistory}
              >
                {clearingHistory ? "Clearing..." : "Clear History"}
              </button>
            </div>
          </div>
        </div>
      )}

      <div
        className={`workspace-page ${sidebarOpen ? "with-sidebar" : "no-sidebar"}`}
      >
        <aside className={`session-sidebar ${sidebarOpen ? "" : "closed"}`}>
          <div className="side-head">
            <div>
              <h2>MindSpace</h2>
              <p>
                {activePanel === "chat"
                  ? "Session galaxy"
                  : activePanel === "knowledge"
                    ? "Knowledge vault"
                    : activePanel === "settings"
                      ? "AI control room"
                      : "Usage dashboard"}
              </p>
            </div>

            <button className="icon-btn" onClick={() => setSidebarOpen(false)}>
              ×
            </button>
          </div>

          <button className="new-chat-btn" onClick={handleNewSession}>
            + New Thought
          </button>

          <div className="panel-tabs">
            <button
              className={activePanel === "chat" ? "active" : ""}
              onClick={() => handlePanelChange("chat")}
            >
              Chat
            </button>

            <button
              className={activePanel === "knowledge" ? "active" : ""}
              onClick={() => handlePanelChange("knowledge")}
            >
              Knowledge
            </button>

            <button
              className={activePanel === "settings" ? "active" : ""}
              onClick={() => handlePanelChange("settings")}
            >
              Settings
            </button>
            <button
              className={activePanel === "dashboard" ? "active" : ""}
              onClick={() => handlePanelChange("dashboard")}
            >
              Dashboard
            </button>
          </div>

          {activePanel === "chat" && (
            <>
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
                        {sessionView !== "trash" ? (
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
                                handleExportChatTXT(session);
                              }}
                            >
                              TXT
                            </button>

                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleExportChatJSON(session);
                              }}
                            >
                              JSON
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
                        ) : (
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
            </>
          )}

          {activePanel === "knowledge" && (
            <>
              <div className="session-search-title">Knowledge History</div>
              <div className="export-all-row">
                <button onClick={handleExportAllKnowledgeTXT}>
                  Export All TXT
                </button>
                <button onClick={handleExportAllKnowledgeJSON}>
                  Export All JSON
                </button>
              </div>
              <button
                type="button"
                className="clear-history-btn"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  handleClearKnowledgeHistory();
                }}
              >
                Clear Knowledge History
              </button>
              <div className="session-list">
                {knowledgeHistory.length === 0 ? (
                  <div className="session-empty">
                    No knowledge questions yet
                  </div>
                ) : (
                  knowledgeHistory.map((item) => (
                    <div
                      key={item.id}
                      className="session-item"
                      onClick={() => {
                        setRagQuestion(item.question);
                        setRagAnswer(item.answer);
                      }}
                    >
                      <div>
                        <strong>{item.question}</strong>
                        <span>{item.model_name}</span>
                      </div>

                      <div className="session-actions">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteKnowledgeHistory(item);
                          }}
                        >
                          🗑
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleExportKnowledgeTXT(item);
                          }}
                        >
                          TXT
                        </button>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleExportKnowledgeJSON(item);
                          }}
                        >
                          JSON
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </>
          )}
          {activePanel === "dashboard" && (
            <>
              <div className="session-search-title">Dashboard</div>

              <div className="session-empty">
                AI usage statistics, quota tracking, recent activity and
                performance metrics.
              </div>
            </>
          )}
          {activePanel === "settings" && (
            <>
              <div className="session-search-title">Settings</div>

              <div className="session-empty">
                Configure models, quotas, source visibility and streaming
                preferences.
              </div>
            </>
          )}
          {activePanel === "settings" && (
            <div className="side-info-list">
              <div className="side-info-card">
                <strong>🤖 Default Model</strong>
                <span>
                  {aiPreferences?.default_model || selectedModel || "Default"}
                </span>
              </div>

              <div className="side-info-card">
                <strong>📚 RAG Top K</strong>
                <span>{aiPreferences?.rag_top_k || 3} chunks</span>
              </div>

              <div className="side-info-card">
                <strong>🔎 Sources</strong>
                <span>
                  {aiPreferences?.show_sources ? "Enabled" : "Disabled"}
                </span>
              </div>

              <div className="side-info-card">
                <strong>⚡ Stream</strong>
                <span>{aiPreferences?.stream_format || "plain"}</span>
              </div>

              <div className="side-info-card">
                <strong>🧾 Daily Limit</strong>
                <span>
                  {aiPreferences?.daily_request_limit || 100} requests
                </span>
              </div>
            </div>
          )}
          {activePanel === "dashboard" && (
            <div className="side-info-list">
              <div className="side-info-card">
                <strong>📊 Today</strong>
                <span>{dailyUsage?.usage?.request_count ?? 0} requests</span>
              </div>

              <div className="side-info-card">
                <strong>🟢 Remaining</strong>
                <span>{dailyUsage?.remaining_requests ?? "-"} left</span>
              </div>

              <div className="side-info-card">
                <strong>💬 Sessions</strong>
                <span>{dashboardSummary?.total_sessions ?? 0}</span>
              </div>

              <div className="side-info-card">
                <strong>📄 Documents</strong>
                <span>{dashboardSummary?.total_documents ?? 0}</span>
              </div>

              <div className="side-info-card">
                <strong>⚙️ AI Requests</strong>
                <span>{dashboardSummary?.total_ai_requests ?? 0}</span>
              </div>
            </div>
          )}
        </aside>

        <main className={sidebarOpen ? "mind-main" : "mind-main expanded"}>
          <header className="mind-header">
            {!sidebarOpen && (
              <button
                className="session-open-btn"
                onClick={() => setSidebarOpen(true)}
              >
                ☰ Menu
              </button>
            )}

            <div>
              <h1>
                {activePanel === "chat"
                  ? activeSession?.title || "LocalMind Workspace"
                  : activePanel === "knowledge"
                    ? "Knowledge Base"
                    : activePanel === "settings"
                      ? "AI Preferences"
                      : "Usage Dashboard"}
              </h1>
              <p>
                {activePanel === "chat"
                  ? "A different AI workspace: session cards, thought stream, and local brain."
                  : activePanel === "knowledge"
                    ? "Upload PDF, DOCX, or TXT files and use them for local RAG answers."
                    : activePanel === "settings"
                      ? "Control model defaults, RAG behavior, sources, and usage limits."
                      : "Track daily quota, requests, documents, sessions, and response health."}
              </p>
            </div>

            <div className="model-switcher">
              <span>Model</span>

              <select value={selectedModel} onChange={handleModelChange}>
                {models.length === 0 ? (
                  <option value="">Default</option>
                ) : (
                  models.map((model) => (
                    <option key={model.name} value={model.name}>
                      {model.name}
                    </option>
                  ))
                )}
              </select>
            </div>

            <button className="secondary" onClick={handleLogout}>
              Logout
            </button>
          </header>

          {activePanel === "chat" ? (
            <>
              <section className="thought-board">
                {messages.length === 0 ? (
                  <div className="empty-state">
                    <div className="orb">AI</div>
                    <h2>Start a focused thought session</h2>
                    <p>
                      Create a session or ask directly. Your local model will
                      answer and the conversation will be saved.
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
            </>
          ) : activePanel === "knowledge" ? (
            <section className="knowledge-board">
              <div className="knowledge-upload-card">
                <h2>Knowledge Base</h2>
                <p>
                  Upload PDF, DOCX, or TXT files for document-aware AI answers.
                </p>

                <input
                  type="file"
                  multiple
                  accept=".pdf,.docx,.txt"
                  onChange={handleFileChange}
                />

                <button
                  onClick={handleUploadDocuments}
                  disabled={uploadingDocs}
                >
                  {uploadingDocs ? "Uploading..." : "Upload Files"}
                </button>

                {selectedFiles.length > 0 && (
                  <div className="selected-files">
                    {selectedFiles.map((file) => (
                      <span key={file.name}>{file.name}</span>
                    ))}
                  </div>
                )}
              </div>

              <div className="rag-ask-card">
                <h2>Ask Knowledge</h2>
                <p>Ask questions using your uploaded documents.</p>

                <textarea
                  placeholder="Ask from uploaded documents..."
                  value={ragQuestion}
                  onChange={(e) => setRagQuestion(e.target.value)}
                />

                <div className="rag-button-row">
                  <button onClick={handleAskKnowledge} disabled={askingRag}>
                    {askingRag ? "Searching knowledge..." : "Ask Knowledge"}
                  </button>

                  <button
                    className="stream-btn"
                    onClick={handleStreamAskKnowledge}
                    disabled={streamingRag}
                  >
                    {streamingRag ? "Streaming..." : "Stream Answer"}
                  </button>
                </div>

                {ragAnswer && (
                  <div className="rag-answer-card">
                    <h3>{streamingRag ? "Streaming Answer" : "Answer"}</h3>
                    <p>{ragAnswer}</p>
                  </div>
                )}

                {ragSources.length > 0 && (
                  <div className="rag-sources">
                    <h3>Sources</h3>

                    {ragSources.map((source, index) => (
                      <div
                        className="rag-source-card"
                        key={`${source.document_id || "source"}-${index}`}
                      >
                        <strong>
                          {source.source ||
                            source.file_name ||
                            "Unknown source"}
                        </strong>
                        <p>{source.chunk_preview || "No preview available"}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="documents-header">
                <h2>Documents</h2>

                <input
                  placeholder="Search documents..."
                  value={documentSearch}
                  onChange={(e) => setDocumentSearch(e.target.value)}
                />
              </div>

              <div className="documents-grid">
                {filteredDocuments.length === 0 ? (
                  <div className="session-empty">No documents found</div>
                ) : (
                  filteredDocuments.map((doc) => (
                    <div className="document-card" key={doc.id}>
                      <div>
                        <h3>{doc.title}</h3>
                        <p>
                          Uploaded:{" "}
                          {doc.uploaded_at
                            ? new Date(doc.uploaded_at).toLocaleDateString()
                            : "Unknown"}
                        </p>
                      </div>

                      <div className="document-actions">
                        <button onClick={() => handlePreviewChunks(doc)}>
                          Preview
                        </button>
                        <button onClick={() => handleRebuildDocument(doc)}>
                          Rebuild
                        </button>
                        <button
                          className="danger"
                          onClick={() => handleDeleteDocument(doc)}
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {previewDocument && (
                <div className="chunk-preview">
                  <div className="chunk-head">
                    <h2>Chunks: {previewDocument.title}</h2>
                    <button onClick={() => setPreviewDocument(null)}>
                      Close
                    </button>
                  </div>

                  {documentChunks.length === 0 ? (
                    <p>No chunks found.</p>
                  ) : (
                    documentChunks.map((chunk) => (
                      <div className="chunk-card" key={chunk.chunk_id}>
                        <strong>{chunk.source || previewDocument.title}</strong>
                        <p>{chunk.preview || chunk.content}</p>
                      </div>
                    ))
                  )}
                </div>
              )}
            </section>
          ) : activePanel === "settings" ? (
            <section className="settings-board">
              <div className="settings-card">
                <div className="settings-head">
                  <div>
                    <h2>AI Preferences</h2>
                    <p>
                      Manage your default AI behavior for chat and document
                      answers.
                    </p>
                  </div>

                  <button onClick={handleResetPreferenceDraft}>
                    Reset Draft
                  </button>
                </div>

                {!aiPreferences ? (
                  <div className="session-empty">Loading preferences...</div>
                ) : (
                  <>
                    <div className="settings-grid">
                      <label className="setting-field">
                        <span>Default Model</span>
                        <select
                          value={aiPreferences.default_model || selectedModel}
                          onChange={(e) =>
                            handlePreferenceChange(
                              "default_model",
                              e.target.value,
                            )
                          }
                        >
                          {models.length === 0 ? (
                            <option value={aiPreferences.default_model || ""}>
                              {aiPreferences.default_model || "Default"}
                            </option>
                          ) : (
                            models.map((model) => (
                              <option key={model.name} value={model.name}>
                                {model.name}
                              </option>
                            ))
                          )}
                        </select>
                      </label>

                      <label className="setting-field">
                        <span>RAG Top K</span>
                        <input
                          type="number"
                          min="1"
                          max="20"
                          value={aiPreferences.rag_top_k || 3}
                          onChange={(e) =>
                            handlePreferenceChange("rag_top_k", e.target.value)
                          }
                        />
                      </label>

                      <label className="setting-field">
                        <span>Stream Format</span>
                        <select
                          value={aiPreferences.stream_format || "plain"}
                          onChange={(e) =>
                            handlePreferenceChange(
                              "stream_format",
                              e.target.value,
                            )
                          }
                        >
                          <option value="plain">Plain Text</option>
                          <option value="sse">Server Sent Events</option>
                        </select>
                      </label>

                      <label className="setting-field">
                        <span>Daily Request Limit</span>
                        <input
                          type="number"
                          min="1"
                          max="10000"
                          value={aiPreferences.daily_request_limit || 100}
                          onChange={(e) =>
                            handlePreferenceChange(
                              "daily_request_limit",
                              e.target.value,
                            )
                          }
                        />
                      </label>

                      <label className="setting-field">
                        <span>Max Prompt Characters</span>
                        <input
                          type="number"
                          min="100"
                          max="100000"
                          value={aiPreferences.max_prompt_characters || 8000}
                          onChange={(e) =>
                            handlePreferenceChange(
                              "max_prompt_characters",
                              e.target.value,
                            )
                          }
                        />
                      </label>
                    </div>

                    <div className="settings-toggles">
                      <label className="toggle-row">
                        <input
                          type="checkbox"
                          checked={Boolean(aiPreferences.show_sources)}
                          onChange={(e) =>
                            handlePreferenceChange(
                              "show_sources",
                              e.target.checked,
                            )
                          }
                        />
                        <div>
                          <strong>Show Sources</strong>
                          <p>Display document chunks used in RAG answers.</p>
                        </div>
                      </label>

                      <label className="toggle-row">
                        <input
                          type="checkbox"
                          checked={Boolean(aiPreferences.auto_generate_title)}
                          onChange={(e) =>
                            handlePreferenceChange(
                              "auto_generate_title",
                              e.target.checked,
                            )
                          }
                        />
                        <div>
                          <strong>Auto Generate Chat Titles</strong>
                          <p>
                            Create titles automatically from the first user
                            message.
                          </p>
                        </div>
                      </label>
                    </div>

                    <button
                      className="save-settings-btn"
                      onClick={handleSavePreferences}
                      disabled={savingPreferences}
                    >
                      {savingPreferences ? "Saving..." : "Save Preferences"}
                    </button>
                  </>
                )}
              </div>
            </section>
          ) : (
            <section className="dashboard-board">
              <div className="dashboard-head-card">
                <div>
                  <h2>Usage Quota Dashboard</h2>
                  <p>
                    Monitor daily usage, quota, documents, sessions, and request
                    health.
                  </p>
                </div>

                <button onClick={loadDashboardData}>Refresh</button>
              </div>

              <div className="dashboard-grid">
                <div className="dashboard-card">
                  <span>Today Requests</span>
                  <strong>{dailyUsage?.usage?.request_count ?? 0}</strong>
                </div>

                <div className="dashboard-card">
                  <span>Daily Limit</span>
                  <strong>
                    {dailyUsage?.preference?.daily_request_limit ?? "-"}
                  </strong>
                </div>

                <div className="dashboard-card">
                  <span>Remaining</span>
                  <strong>{dailyUsage?.remaining_requests ?? "-"}</strong>
                </div>

                <div className="dashboard-card">
                  <span>Characters Used</span>
                  <strong>{dailyUsage?.usage?.character_count ?? 0}</strong>
                </div>

                <div className="dashboard-card">
                  <span>Total Sessions</span>
                  <strong>{dashboardSummary?.total_sessions ?? 0}</strong>
                </div>

                <div className="dashboard-card">
                  <span>Total Documents</span>
                  <strong>{dashboardSummary?.total_documents ?? 0}</strong>
                </div>

                <div className="dashboard-card">
                  <span>Total AI Requests</span>
                  <strong>{dashboardSummary?.total_ai_requests ?? 0}</strong>
                </div>

                <div className="dashboard-card">
                  <span>Avg Response Time</span>
                  <strong>
                    {dashboardSummary?.average_response_time_ms ?? 0} ms
                  </strong>
                </div>
              </div>
            </section>
          )}
        </main>
      </div>
    </>
  );
}

export default App;
