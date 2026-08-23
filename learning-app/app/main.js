  function applyTheme() {
    document.documentElement.dataset.theme = state.theme;
    elements.themeButton.textContent = state.theme === "dark" ? "☀" : "◐";
    elements.themeButton.setAttribute(
      "aria-label",
      state.theme === "dark" ? "라이트 테마" : "다크 테마"
    );
  }

  function exportProgress() {
    const output = {
      schemaVersion: "lfv-learning-progress-v2",
      exportedAt: new Date().toISOString(),
      curriculumVersion: data.schemaVersion,
      selectedPath: state.selectedPath,
      completed: progress.completed,
      quiz: progress.quiz,
      challenge: progress.challenge,
      summary: {
        lessonCount: data.lessons.length,
        completedCount: progress.completed.length,
        completionPercent: completionFor(data.lessons),
      },
    };
    const blob = new Blob([JSON.stringify(output, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "lfv-learning-progress.json";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  function renderAll() {
    renderStats();
    renderPathSelect();
    renderTrackFilters();
    renderPathProgress();
    renderLessonNav();
    renderOverview();
    if (state.view === "lesson" && state.activeLesson) {
      renderLesson(lessonById.get(state.activeLesson));
    } else if (state.view === "coverage") {
      renderCoverage();
    } else if (state.view === "glossary") {
      renderGlossary();
    }
    applyTheme();
  }

  elements.pathSelect.addEventListener("change", () => {
    state.selectedPath = elements.pathSelect.value;
    state.selectedTrack = "all";
    state.activeLesson = null;
    persistSettings();
    setView("overview");
    renderAll();
  });

  elements.searchInput.addEventListener("input", () => {
    state.search = elements.searchInput.value;
    renderLessonNav();
  });

  elements.coverageButton.addEventListener("click", () => {
    renderCoverage();
    setView("coverage");
  });

  elements.glossaryButton.addEventListener("click", () => {
    renderGlossary();
    setView("glossary");
  });

  elements.themeButton.addEventListener("click", () => {
    state.theme = state.theme === "dark" ? "light" : "dark";
    persistSettings();
    applyTheme();
  });

  elements.exportButton.addEventListener("click", exportProgress);

  elements.resetButton.addEventListener("click", () => {
    const confirmed = window.confirm(
      "완료 표시와 퀴즈 기록을 모두 초기화할까요?"
    );
    if (!confirmed) return;
    progress.completed = [];
    progress.quiz = {};
    progress.challenge = {};
    persistProgress();
    state.activeLesson = null;
    setView("overview");
    renderAll();
  });

  document.addEventListener("keydown", (event) => {
    if (
      event.key === "/" &&
      document.activeElement?.tagName !== "INPUT" &&
      document.activeElement?.tagName !== "TEXTAREA"
    ) {
      event.preventDefault();
      elements.searchInput.focus();
    }
    if (event.key === "Escape" && document.activeElement === elements.searchInput) {
      elements.searchInput.value = "";
      state.search = "";
      elements.searchInput.blur();
      renderLessonNav();
    }
  });

  applyTheme();
  renderAll();
  setView("overview");
