const API_BASE = "http://127.0.0.1:8000";
const COLUMNS = ["Backlog", "In Progress", "Review", "Done"];

function TaskCard({ task, onDragStart, onDelete }) {
  const blockedStyle = task.is_blocked
    ? { borderLeft: "4px solid #e74c3c" }
    : { borderLeft: "4px solid #2ecc71" };
  const criticalStyle = task.is_critical ? { background: "#fff3f0" } : {};

  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, task.id)}
      style={{
        background: "#fff",
        padding: "10px 12px",
        marginBottom: "8px",
        borderRadius: "6px",
        boxShadow: "0 1px 3px rgba(0,0,0,0.15)",
        cursor: "grab",
        position: "relative",
        ...blockedStyle,
        ...criticalStyle,
      }}
    >
      <button
        onClick={() => onDelete(task.id)}
        title="Delete task"
        style={{
          position: "absolute",
          top: "6px",
          right: "6px",
          border: "none",
          background: "transparent",
          cursor: "pointer",
          color: "#999",
          fontSize: "14px",
        }}
      >
        ✕
      </button>
      <strong>{task.title}</strong>
      <div style={{ fontSize: "12px", color: "#666", marginTop: "4px" }}>
        {task.is_blocked ? "Blocked" : "Ready"}
        {task.is_critical ? " · Critical Path" : ""}
        {" · "}
        {task.duration}d · start {task.earliest_start} → finish {task.earliest_finish}
      </div>
    </div>
  );
}

function Column({ name, tasks, onDrop, onDragOver, onDragStart, onDelete }) {
  return (
    <div
      onDrop={(e) => onDrop(e, name)}
      onDragOver={onDragOver}
      style={{
        background: "#f4f5f7",
        borderRadius: "8px",
        padding: "12px",
        width: "260px",
        minHeight: "400px",
      }}
    >
      <h3 style={{ fontSize: "14px", textTransform: "uppercase", color: "#555" }}>
        {name} ({tasks.length})
      </h3>
      {tasks.map((t) => (
        <TaskCard key={t.id} task={t} onDragStart={onDragStart} onDelete={onDelete} />
      ))}
    </div>
  );
}

function AddTaskForm({ onAdd }) {
  const [title, setTitle] = React.useState("");
  const [duration, setDuration] = React.useState(1);

  const submit = (e) => {
    e.preventDefault();
    if (!title.trim()) return;
    onAdd({ title, duration: Number(duration), description: "", column: "Backlog" });
    setTitle("");
    setDuration(1);
  };

  return (
    <form onSubmit={submit} style={{ marginBottom: "20px", display: "flex", gap: "8px" }}>
      <input
        placeholder="New task title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        style={{ padding: "6px 10px" }}
      />
      <input
        type="number"
        min="0.5"
        step="0.5"
        value={duration}
        onChange={(e) => setDuration(e.target.value)}
        style={{ width: "70px", padding: "6px" }}
      />
      <button type="submit">+ Add Task (with AI suggestions)</button>
    </form>
  );
}

function AddDependencyForm({ tasks, onAdd }) {
  const [pred, setPred] = React.useState("");
  const [succ, setSucc] = React.useState("");
  const [error, setError] = React.useState("");

  const submit = async (e) => {
    e.preventDefault();
    if (!pred || !succ) return;
    setError("");
    const err = await onAdd(pred, succ);
    if (err) setError(err);
    else {
      setPred("");
      setSucc("");
    }
  };

  return (
    <form onSubmit={submit} style={{ marginBottom: "20px", display: "flex", gap: "8px", alignItems: "center" }}>
      <select value={pred} onChange={(e) => setPred(e.target.value)}>
        <option value="">Prerequisite task</option>
        {tasks.map((t) => (
          <option key={t.id} value={t.id}>
            {t.title}
          </option>
        ))}
      </select>
      <span>→ must finish before →</span>
      <select value={succ} onChange={(e) => setSucc(e.target.value)}>
        <option value="">Dependent task</option>
        {tasks.map((t) => (
          <option key={t.id} value={t.id}>
            {t.title}
          </option>
        ))}
      </select>
      <button type="submit">Link</button>
      {error && <span style={{ color: "#e74c3c", fontSize: "13px" }}>{error}</span>}
    </form>
  );
}

function SuggestionPanel({ suggestions, tasks, onAccept, onDismiss }) {
  if (suggestions.length === 0) return null;

  const taskTitle = (id) => tasks.find((t) => t.id === id)?.title || id;

  return (
    <div
      style={{
        marginBottom: "20px",
        padding: "12px",
        background: "#eef6ff",
        borderRadius: "8px",
        border: "1px solid #b3d7ff",
      }}
    >
      <strong style={{ fontSize: "13px", color: "#333" }}>AI Suggested Dependencies</strong>
      {suggestions.map((s) => (
        <div
          key={s.id}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginTop: "8px",
            padding: "8px",
            background: "#fff",
            borderRadius: "6px",
          }}
        >
          <div style={{ fontSize: "13px" }}>
            <strong>{taskTitle(s.predecessor_id)}</strong> → <strong>{taskTitle(s.successor_id)}</strong>
            <div style={{ color: "#666", fontSize: "12px" }}>
              {s.reason} · confidence {(s.confidence * 100).toFixed(0)}%
            </div>
          </div>
          <div style={{ display: "flex", gap: "6px" }}>
            <button
              onClick={() => onAccept(s.id)}
              style={{
                background: "#2ecc71",
                color: "#fff",
                border: "none",
                padding: "4px 10px",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              Accept
            </button>
            <button
              onClick={() => onDismiss(s.id)}
              style={{
                background: "#eee",
                border: "none",
                padding: "4px 10px",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              Dismiss
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

function App() {
  const [tasks, setTasks] = React.useState([]);
  const [suggestions, setSuggestions] = React.useState([]);
  const [loading, setLoading] = React.useState(true);

  const fetchWorkflow = async () => {
    const res = await fetch(`${API_BASE}/workflow`);
    const data = await res.json();
    setTasks(data.tasks);
    setLoading(false);
  };

  React.useEffect(() => {
    fetchWorkflow();
  }, []);

  const addTask = async (payload) => {
    const res = await fetch(`${API_BASE}/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const newTask = await res.json();
    await fetchWorkflow();

    try {
      const sugRes = await fetch(`${API_BASE}/suggestions/generate/${newTask.id}`, { method: "POST" });
      const sugData = await sugRes.json();
      setSuggestions((prev) => [...prev, ...sugData]);
    } catch {
      // AI failure should never break task creation
    }
  };

  const addDependency = async (predecessor_id, successor_id) => {
    const res = await fetch(`${API_BASE}/dependencies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ predecessor_id, successor_id }),
    });
    if (!res.ok) {
      const err = await res.json();
      return err.detail || "Failed to add dependency";
    }
    fetchWorkflow();
    return null;
  };

  const deleteTask = async (taskId) => {
    if (!confirm("Delete this task?")) return;
    await fetch(`${API_BASE}/tasks/${taskId}`, { method: "DELETE" });
    fetchWorkflow();
  };

  const acceptSuggestion = async (suggestionId) => {
    const res = await fetch(`${API_BASE}/suggestions/${suggestionId}/accept`, { method: "POST" });
    if (res.ok) {
      setSuggestions((prev) => prev.filter((s) => s.id !== suggestionId));
      fetchWorkflow();
    } else {
      const err = await res.json();
      alert(err.detail || "Could not accept suggestion");
      setSuggestions((prev) => prev.filter((s) => s.id !== suggestionId));
    }
  };

  const dismissSuggestion = async (suggestionId) => {
    await fetch(`${API_BASE}/suggestions/${suggestionId}/dismiss`, { method: "POST" });
    setSuggestions((prev) => prev.filter((s) => s.id !== suggestionId));
  };

  const onDragStart = (e, taskId) => {
    e.dataTransfer.setData("taskId", taskId);
  };

  const onDragOver = (e) => e.preventDefault();

  const onDrop = async (e, newColumn) => {
    const taskId = e.dataTransfer.getData("taskId");
    await fetch(`${API_BASE}/tasks/${taskId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ column: newColumn }),
    });
    fetchWorkflow();
  };

  if (loading) return <div style={{ padding: "20px" }}>Loading...</div>;

  return (
    <div style={{ fontFamily: "sans-serif", padding: "20px" }}>
      <h1>TaskFlow Pro</h1>
      <AddTaskForm onAdd={addTask} />
      <AddDependencyForm tasks={tasks} onAdd={addDependency} />
      <SuggestionPanel
        suggestions={suggestions}
        tasks={tasks}
        onAccept={acceptSuggestion}
        onDismiss={dismissSuggestion}
      />
      <div style={{ display: "flex", gap: "16px" }}>
        {COLUMNS.map((col) => (
          <Column
            key={col}
            name={col}
            tasks={tasks.filter((t) => t.column === col)}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onDragStart={onDragStart}
            onDelete={deleteTask}
          />
        ))}
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
