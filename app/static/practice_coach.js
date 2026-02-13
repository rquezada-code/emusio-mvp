
// Emusio AI Practice Coach – Vanilla JS (Phase 0)
console.log("Practice Coach JS loaded");

// Elements
const notesEl = document.getElementById("notes");
const outputEl = document.getElementById("output");
const btnGenerate = document.getElementById("btn-generate");
const btnClear = document.getElementById("btn-clear");
const inputCard = document.getElementById("input-card");

// Utils
function getLessonIdFromURL() {
  const params = new URLSearchParams(window.location.search);
  return params.get("lesson_id");
}

function setLoading(isLoading) {
  if (!btnGenerate) return;
  btnGenerate.disabled = isLoading;
  btnGenerate.textContent = isLoading
    ? "Generating…"
    : "Generate practice";
}

function setOutput(text, state = "ready") {
  outputEl.innerHTML = marked.parse(text);
  outputEl.className = `output is-${state}`;
}

// Clear button
if (btnClear) {
  btnClear.addEventListener("click", () => {
    if (notesEl) notesEl.value = "";
    setOutput("Your AI-generated practice plan will appear here.", "empty");
    notesEl?.focus();
  });
}

// Manual generate
if (btnGenerate) {
  btnGenerate.addEventListener("click", async () => {
    const notes = (notesEl?.value || "").trim();

    if (!notes) {
      setOutput("Please paste your lesson notes 🙂", "empty");
      notesEl?.focus();
      return;
    }

    setLoading(true);
    setOutput("Preparing your practice plan…", "loading");

    try {
      const res = await fetch("/practice-coach", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ teacher_notes: notes })
      });

      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`HTTP ${res.status}: ${txt}`);
      }

      const data = await res.json();
      setOutput(data.practice_plan || "No practice generated.", "ready");
    } catch (err) {
      setOutput(`Oops 😅 ${err.message}`, "empty");
    } finally {
      setLoading(false);
    }
  });
}

// AUTO MODE (Emusio redirect)
document.addEventListener("DOMContentLoaded", async () => {
  const lessonId = getLessonIdFromURL();
  if (!lessonId) return;

  if (inputCard) inputCard.style.display = "none";

  setLoading(true);
  setOutput("Preparing your practice plan…", "loading");

  try {
    const res = await fetch("/practice-coach", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        lesson_id: lessonId   // 🔥 AHORA SÍ ENVIAMOS EL ID REAL
      })
    });

    const data = await res.json();
    setOutput(data.practice_plan || "No practice generated.", "ready");
  } catch (err) {
    setOutput(`Oops 😅 ${err.message}`, "empty");
  } finally {
    setLoading(false);
  }
});

