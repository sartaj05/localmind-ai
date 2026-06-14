import { useEffect, useState } from "react";
import {
  createPrompt,
  deletePrompt,
  getPrompts,
  togglePinPrompt,
  updatePrompt,
} from "../api/promptApi";

const categories = [
  { value: "", label: "All" },
  { value: "study", label: "Study" },
  { value: "coding", label: "Coding" },
  { value: "writing", label: "Writing" },
  { value: "assistant", label: "AI Assistant" },
  { value: "other", label: "Other" },
];

const emptyForm = {
  title: "",
  category: "other",
  prompt: "",
  is_pinned: false,
};

function PromptLibrary({ onUsePrompt, showPopup }) {
  const [prompts, setPrompts] = useState([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [saving, setSaving] = useState(false);

  const loadPrompts = async () => {
    try {
      const res = await getPrompts({
        search,
        category,
      });

      setPrompts(res.data.results || []);
    } catch {
      showPopup("Failed to load prompts", "error");
    }
  };

  useEffect(() => {
    loadPrompts();
  }, [search, category]);

  const resetForm = () => {
    setForm(emptyForm);
    setEditingId(null);
  };

  const handleSubmit = async () => {
    if (!form.title.trim()) {
      showPopup("Prompt title is required", "error");
      return;
    }

    if (!form.prompt.trim()) {
      showPopup("Prompt text is required", "error");
      return;
    }

    setSaving(true);

    try {
      if (editingId) {
        await updatePrompt(editingId, form);
        showPopup("Prompt updated", "success");
      } else {
        await createPrompt(form);
        showPopup("Prompt created", "success");
      }

      resetForm();
      await loadPrompts();
    } catch {
      showPopup("Prompt save failed", "error");
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (prompt) => {
    setEditingId(prompt.id);
    setForm({
      title: prompt.title || "",
      category: prompt.category || "other",
      prompt: prompt.prompt || "",
      is_pinned: Boolean(prompt.is_pinned),
    });
  };

  const handleDelete = async (prompt) => {
    const ok = window.confirm(`Delete prompt "${prompt.title}"?`);
    if (!ok) return;

    try {
      await deletePrompt(prompt.id);
      await loadPrompts();
      showPopup("Prompt deleted", "success");
    } catch {
      showPopup("Delete prompt failed", "error");
    }
  };

  const handleTogglePin = async (prompt) => {
    try {
      await togglePinPrompt(prompt.id);
      await loadPrompts();
      showPopup("Prompt pin updated", "success");
    } catch {
      showPopup("Pin prompt failed", "error");
    }
  };

  return (
    <section className="prompt-library-board">
      <div className="prompt-library-head">
        <div>
          <h2>Prompt Library</h2>
          <p>Save reusable prompts and send them to chat instantly.</p>
        </div>

        <button onClick={resetForm}>+ New Prompt</button>
      </div>

      <div className="prompt-library-layout">
        <div className="prompt-form-card">
          <h3>{editingId ? "Edit Prompt" : "Create Prompt"}</h3>

          <input
            placeholder="Prompt title"
            value={form.title}
            onChange={(e) =>
              setForm((prev) => ({
                ...prev,
                title: e.target.value,
              }))
            }
          />

          <select
            value={form.category}
            onChange={(e) =>
              setForm((prev) => ({
                ...prev,
                category: e.target.value,
              }))
            }
          >
            {categories
              .filter((item) => item.value)
              .map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
          </select>

          <textarea
            placeholder="Write reusable prompt..."
            value={form.prompt}
            onChange={(e) =>
              setForm((prev) => ({
                ...prev,
                prompt: e.target.value,
              }))
            }
          />

          <label className="prompt-pin-row">
            <input
              type="checkbox"
              checked={form.is_pinned}
              onChange={(e) =>
                setForm((prev) => ({
                  ...prev,
                  is_pinned: e.target.checked,
                }))
              }
            />
            Pin this prompt
          </label>

          <div className="prompt-form-actions">
            <button onClick={handleSubmit} disabled={saving}>
              {saving ? "Saving..." : editingId ? "Update Prompt" : "Save Prompt"}
            </button>

            {editingId && (
              <button className="secondary-prompt-btn" onClick={resetForm}>
                Cancel Edit
              </button>
            )}
          </div>
        </div>

        <div className="prompt-list-panel">
          <div className="prompt-filters">
            <input
              placeholder="Search prompts..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />

            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {categories.map((item) => (
                <option key={item.label} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>

          <div className="prompt-card-grid">
            {prompts.length === 0 ? (
              <div className="session-empty">No prompts found</div>
            ) : (
              prompts.map((item) => (
                <div className="prompt-template-card" key={item.id}>
                  <div className="prompt-template-head">
                    <div>
                      <h3>
                        {item.is_pinned ? "⭐ " : ""}
                        {item.title}
                      </h3>
                      <span>{item.category}</span>
                    </div>

                    <button onClick={() => handleTogglePin(item)}>
                      {item.is_pinned ? "Unpin" : "Pin"}
                    </button>
                  </div>

                  <p>{item.prompt}</p>

                  <div className="prompt-template-actions">
                    <button onClick={() => onUsePrompt(item.prompt)}>Use</button>
                    <button onClick={() => handleEdit(item)}>Edit</button>
                    <button
                      className="danger"
                      onClick={() => handleDelete(item)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

export default PromptLibrary;