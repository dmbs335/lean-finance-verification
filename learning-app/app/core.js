"use strict";
  const data = window.LFV_CURRICULUM;
  if (!data) {
    document.body.innerHTML = "<p>커리큘럼 데이터를 불러오지 못했습니다.</p>";
    return;
  }

  const REPO_BASE = `https://github.com/${data.repo}/`;
  const STORAGE_KEY = "lfv-academy-progress-v2";
  const SETTINGS_KEY = "lfv-academy-settings-v2";

  const $ = (id) => document.getElementById(id);
  const elements = {
    lessonCount: $("lessonCount"),
    totalMinutes: $("totalMinutes"),
    coverageCount: $("coverageCount"),
    completionPercent: $("completionPercent"),
    pathSelect: $("pathSelect"),
    searchInput: $("searchInput"),
    trackFilters: $("trackFilters"),
    pathProgressText: $("pathProgressText"),
    pathProgressBar: $("pathProgressBar"),
    lessonNav: $("lessonNav"),
    overviewView: $("overviewView"),
    lessonView: $("lessonView"),
    coverageView: $("coverageView"),
    glossaryView: $("glossaryView"),
    coverageButton: $("coverageButton"),
    glossaryButton: $("glossaryButton"),
    themeButton: $("themeButton"),
    exportButton: $("exportButton"),
    resetButton: $("resetButton"),
    cardTemplate: $("lessonCardTemplate"),
  };

  const lessonById = new Map(data.lessons.map((lesson) => [lesson.id, lesson]));
  const trackById = new Map(data.tracks.map((track) => [track.id, track]));
  const pathById = new Map(data.paths.map((path) => [path.id, path]));
  const coverageById = new Map(
    data.coverageAreas.map((area) => [area.id, area])
  );

  const loadJson = (key, fallback) => {
    try {
      const value = localStorage.getItem(key);
      return value ? JSON.parse(value) : fallback;
    } catch {
      return fallback;
    }
  };

  const progress = loadJson(STORAGE_KEY, {
    completed: [],
    quiz: {},
    challenge: {},
  });
  progress.completed = Array.isArray(progress.completed)
    ? progress.completed.filter((id) => lessonById.has(id))
    : [];
  progress.quiz =
    progress.quiz && typeof progress.quiz === "object" ? progress.quiz : {};
  progress.challenge =
    progress.challenge && typeof progress.challenge === "object"
      ? progress.challenge
      : {};

  const savedSettings = loadJson(SETTINGS_KEY, {});
  const state = {
    view: "overview",
    selectedPath:
      pathById.has(savedSettings.path) ? savedSettings.path : data.paths[0].id,
    selectedTrack: "all",
    search: "",
    activeLesson: null,
    theme:
      savedSettings.theme ||
      (window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light"),
  };

  function persistProgress() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
  }

  function persistSettings() {
    localStorage.setItem(
      SETTINGS_KEY,
      JSON.stringify({ path: state.selectedPath, theme: state.theme })
    );
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function isCompleted(id) {
    return progress.completed.includes(id);
  }

  function toggleCompleted(id) {
    if (isCompleted(id)) {
      progress.completed = progress.completed.filter((item) => item !== id);
    } else {
      progress.completed.push(id);
    }
    persistProgress();
    renderAll();
  }

  function currentPath() {
    return pathById.get(state.selectedPath);
  }

  function pathLessons() {
    return currentPath().lessonIds
      .map((id) => lessonById.get(id))
      .filter(Boolean);
  }

  function visibleLessons() {
    const query = state.search.trim().toLowerCase();
    const pathIds = new Set(currentPath().lessonIds);
    return data.lessons
      .filter((lesson) => pathIds.has(lesson.id))
      .filter(
        (lesson) =>
          state.selectedTrack === "all" ||
          lesson.track === state.selectedTrack
      )
      .filter((lesson) => {
        if (!query) return true;
        const searchable = [
          lesson.title,
          lesson.subtitle,
          lesson.difficulty,
          lesson.track,
          lesson.why,
          ...lesson.concepts,
          ...lesson.outcomes,
          ...lesson.covers,
          ...lesson.sources,
          ...lesson.docs,
        ]
          .join(" ")
          .toLowerCase();
        return searchable.includes(query);
      });
  }

  function completionFor(lessons) {
    if (!lessons.length) return 0;
    const done = lessons.filter((lesson) => isCompleted(lesson.id)).length;
    return Math.round((done / lessons.length) * 100);
  }

  function gitHubUrl(path) {
    const encoded = path
      .split("/")
      .map((segment) => encodeURIComponent(segment))
      .join("/");
    const isDirectory = path.endsWith("/");
    return `${REPO_BASE}${isDirectory ? "tree" : "blob"}/main/${encoded.replace(
      /%2F/g,
      "/"
    )}`;
  }
