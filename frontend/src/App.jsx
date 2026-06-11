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
} from "./api/aiApi";
import { loginUser, registerUser } from "./api/authApi";
import "./App.css";

function App() {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [activePanel, setActivePanel] = useState("chat");

  const [sessions, setSessions] = useState([]);
  const [sessionSearch, setSessionSearch] = useState("");
  const [sessionView, setSessionView] = useState("active");
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [prompt, setPrompt] = useState("");

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

  const normalizeList = (res) => {
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

  const handlePanelChange = async (panel) => {
    setActivePanel(panel);

    if (panel === "knowledge") {
      await loadDocuments();
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
        "error"
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
        "error"
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

      await sendSessionMessage(session.id, { message: userText });

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
    console.log("Upload clicked:", selectedFiles);

    if (selectedFiles.length === 0) {
      showPopup("Please select files first", "error");
      return;
    }

    setUploadingDocs(true);

    try {
      for (const file of selectedFiles) {
        console.log("Uploading file:", file.name, file.type, file.size);

        const formData = new FormData();
        formData.append("file", file);
        formData.append("title", file.name);

        const res = await uploadKnowledgeDocument(formData);
        console.log("Upload response:", res.data);
      }

      setSelectedFiles([]);
      await loadDocuments();
      showPopup("Documents uploaded successfully", "success");
    } catch (error) {
      console.error("Upload failed:", error.response?.data || error);

      showPopup(
        error.response?.data?.error?.message ||
          error.response?.data?.error ||
          error.response?.data?.message ||
          "Document upload failed",
        "error"
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
        top_k: 5,
      });

      setRagAnswer(res.data.answer || "");
      setRagSources(res.data.sources || []);

      showPopup("Knowledge answer generated", "success");
    } catch (error) {
      console.error("Knowledge ask failed:", error.response?.data || error);

      showPopup(
        error.response?.data?.error?.message ||
          error.response?.data?.error ||
          error.response?.data?.message ||
          "Knowledge ask failed",
        "error"
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
        top_k: 5,
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

      showPopup("Streaming answer completed", "success");
    } catch (error) {
      console.error("Streaming RAG failed:", error);

      showPopup(
        error.response?.data?.error?.message ||
          error.message ||
          "Streaming RAG failed",
        "error"
      );
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
    session.title?.toLowerCase().includes(sessionSearch.toLowerCase())
  );

  const filteredDocuments = documents.filter((doc) =>
    doc.title?.toLowerCase().includes(documentSearch.toLowerCase())
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
              <p>
                {activePanel === "chat" ? "Session galaxy" : "Knowledge vault"}
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
            <div className="session-empty">
              Upload, ask, and stream answers from the main panel.
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
                  : "Knowledge Base"}
              </h1>
              <p>
                {activePanel === "chat"
                  ? "A different AI workspace: session cards, thought stream, and local brain."
                  : "Upload PDF, DOCX, or TXT files and use them for local RAG answers."}
              </p>
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
          ) : (
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
          )}
        </main>
      </div>
    </>
  );
}

export default App;