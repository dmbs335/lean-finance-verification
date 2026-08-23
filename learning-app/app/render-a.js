  function setView(name) {
    state.view = name;
    for (const [viewName, element] of [
      ["overview", elements.overviewView],
      ["lesson", elements.lessonView],
      ["coverage", elements.coverageView],
      ["glossary", elements.glossaryView],
    ]) {
      element.classList.toggle("hidden", viewName !== name);
    }
    elements.coverageButton.setAttribute(
      "aria-pressed",
      String(name === "coverage")
    );
    elements.glossaryButton.setAttribute(
      "aria-pressed",
      String(name === "glossary")
    );
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function renderStats() {
    const totalMinutes = data.lessons.reduce(
      (sum, lesson) => sum + lesson.minutes,
      0
    );
    elements.lessonCount.textContent = data.lessons.length;
    elements.totalMinutes.textContent = totalMinutes.toLocaleString("ko-KR");
    elements.coverageCount.textContent = data.coverageAreas.length;
    elements.completionPercent.textContent = `${completionFor(data.lessons)}%`;
  }

  function renderPathSelect() {
    elements.pathSelect.innerHTML = data.paths
      .map(
        (path) =>
          `<option value="${escapeHtml(path.id)}">${escapeHtml(
            path.label
          )}</option>`
      )
      .join("");
    elements.pathSelect.value = state.selectedPath;
  }

  function renderTrackFilters() {
    const buttons = [
      { id: "all", label: "전체" },
      ...data.tracks.map((track) => ({ id: track.id, label: track.label })),
    ];
    elements.trackFilters.innerHTML = buttons
      .map(
        (item) => `
          <button type="button" class="chip ${
            item.id === state.selectedTrack ? "active" : ""
          }" data-track="${escapeHtml(item.id)}" aria-pressed="${
          item.id === state.selectedTrack
        }">${escapeHtml(item.label)}</button>`
      )
      .join("");
    elements.trackFilters.querySelectorAll("[data-track]").forEach((button) => {
      button.addEventListener("click", () => {
        state.selectedTrack = button.dataset.track;
        renderAll();
      });
    });
  }

  function renderPathProgress() {
    const lessons = pathLessons();
    const completed = lessons.filter((lesson) => isCompleted(lesson.id)).length;
    const percent = lessons.length
      ? Math.round((completed / lessons.length) * 100)
      : 0;
    elements.pathProgressText.textContent = `${completed} / ${lessons.length}`;
    elements.pathProgressBar.style.width = `${percent}%`;
  }

  function renderLessonNav() {
    const lessons = visibleLessons();
    elements.lessonNav.innerHTML = "";
    if (!lessons.length) {
      elements.lessonNav.innerHTML =
        '<p class="empty-state">검색 조건에 맞는 레슨이 없습니다.</p>';
      return;
    }

    lessons.forEach((lesson, index) => {
      const card = elements.cardTemplate.content.firstElementChild.cloneNode(true);
      card.dataset.lessonId = lesson.id;
      card.classList.toggle("active", state.activeLesson === lesson.id);
      card.querySelector(".lesson-card-index").textContent = String(
        index + 1
      ).padStart(2, "0");
      card.querySelector("strong").textContent = lesson.title;
      card.querySelector("small").textContent = `${
        trackById.get(lesson.track).label
      } · ${lesson.minutes}분`;
      card.querySelector(".lesson-card-status").textContent = isCompleted(
        lesson.id
      )
        ? "✓"
        : "→";
      card.setAttribute(
        "aria-label",
        `${lesson.title}${isCompleted(lesson.id) ? ", 완료" : ""}`
      );
      card.addEventListener("click", () => openLesson(lesson.id));
      elements.lessonNav.appendChild(card);
    });
  }

  function trackProgress(trackId) {
    const lessons = data.lessons.filter((lesson) => lesson.track === trackId);
    const completed = lessons.filter((lesson) => isCompleted(lesson.id)).length;
    return {
      lessons,
      completed,
      percent: lessons.length
        ? Math.round((completed / lessons.length) * 100)
        : 0,
    };
  }

  function renderOverview() {
    const path = currentPath();
    const recommended = pathLessons().find((lesson) => !isCompleted(lesson.id));
    const completedCount = data.lessons.filter((lesson) =>
      isCompleted(lesson.id)
    ).length;
    const sourceCount = new Set(data.lessons.flatMap((lesson) => lesson.sources))
      .size;
    const toolCount = new Set(
      data.lessons
        .flatMap((lesson) => lesson.sources)
        .filter((path) => path.startsWith("tools/"))
        .map((path) => path.split("/").slice(0, 2).join("/"))
    ).size;

    elements.overviewView.innerHTML = `
      <header class="overview-header">
        <div>
          <p class="eyebrow">Current learning path</p>
          <h2 class="view-title">${escapeHtml(path.label)}</h2>
          <p>${escapeHtml(path.description)}</p>
        </div>
        ${
          recommended
            ? `<button class="button button-primary" id="continueButton" type="button">
                 ${completedCount ? "이어서 학습" : "학습 시작"} · ${escapeHtml(
                recommended.title
              )}
               </button>`
            : `<button class="button button-primary" id="continueButton" type="button">경로 복습</button>`
        }
      </header>

      <section class="dashboard-grid" aria-label="프로젝트 학습 대시보드">
        <article class="dashboard-card">
          <span>전체 완료</span>
          <strong>${completedCount} / ${data.lessons.length}</strong>
          <small>${completionFor(data.lessons)}%</small>
        </article>
        <article class="dashboard-card">
          <span>직접 연결된 source</span>
          <strong>${sourceCount}</strong>
          <small>Lean · Python · fixture</small>
        </article>
        <article class="dashboard-card">
          <span>실행 도구</span>
          <strong>${toolCount}</strong>
          <small>합성 · 검증 · 인프라</small>
        </article>
        <article class="dashboard-card">
          <span>보증 질문</span>
          <strong>2 × 28</strong>
          <small>증명함 / 증명하지 않음</small>
        </article>
      </section>

      <section class="panel">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Six connected tracks</p>
            <h3>프로젝트 전체를 층별로 읽기</h3>
          </div>
        </div>
        <div class="track-overview">
          ${data.tracks
            .map((track) => {
              const result = trackProgress(track.id);
              return `
                <button type="button" class="track-row" data-overview-track="${escapeHtml(
                  track.id
                )}">
                  <span>
                    <strong>${escapeHtml(track.label)}</strong>
                    <small>${escapeHtml(track.description)}</small>
                  </span>
                  <span class="track-meter">
                    <span><i style="width:${result.percent}%"></i></span>
                    <b>${result.completed}/${result.lessons.length}</b>
                  </span>
                </button>`;
            })
            .join("")}
        </div>
      </section>

      <section class="panel">
        <div class="section-heading">
          <div>
            <p class="eyebrow">Choose another route</p>
            <h3>목표별 학습 경로</h3>
          </div>
        </div>
        <div class="path-grid">
          ${data.paths
            .map((item) => {
              const lessons = item.lessonIds
                .map((id) => lessonById.get(id))
                .filter(Boolean);
              return `
                <button type="button" class="path-card ${
                  item.id === state.selectedPath ? "active" : ""
                }" data-path-card="${escapeHtml(item.id)}">
                  <span class="pill">${lessons.length} 레슨 · ${lessons.reduce(
                (sum, lesson) => sum + lesson.minutes,
                0
              )}분</span>
                  <strong>${escapeHtml(item.label)}</strong>
                  <small>${escapeHtml(item.description)}</small>
                  <span class="progress-label">
                    <span>완료</span>
                    <b>${completionFor(lessons)}%</b>
                  </span>
                </button>`;
            })
            .join("")}
        </div>
      </section>

      <section class="panel">
        <div class="section-heading">
          <div>
            <p class="eyebrow">End-to-end mental model</p>
            <h3>한 레슨씩 연결되는 검증 파이프라인</h3>
          </div>
        </div>
        <div class="concept-list">
          ${[
            ["금융·연구 상태", "무엇이 실제로 일어날 수 있는가"],
            ["Claim", "무엇을 참이라고 주장하는가"],
            ["Observation", "어떤 증거가 어떤 차이를 보존하는가"],
            ["Counterexample", "같은 증거지만 claim이 다른 두 history"],
            ["Synthesis", "모든 disagreement를 가르는 최소 채널"],
            ["Proof-carrying handoff", "외부 계산을 Lean kernel 검사로 연결"],
          ]
            .map(
              ([term, explanation], index) => `
                <article>
                  <span>${index + 1}</span>
                  <div><strong>${escapeHtml(term)}</strong><small>${escapeHtml(
                explanation
              )}</small></div>
                </article>`
            )
            .join("")}
        </div>
      </section>`;

    const continueButton = $("continueButton");
    if (continueButton) {
      continueButton.addEventListener("click", () => {
        const target = recommended || pathLessons()[0];
        if (target) openLesson(target.id);
      });
    }
    elements.overviewView
      .querySelectorAll("[data-overview-track]")
      .forEach((button) => {
        button.addEventListener("click", () => {
          state.selectedTrack = button.dataset.overviewTrack;
          renderAll();
          elements.lessonNav.querySelector(".lesson-card")?.focus();
        });
      });
    elements.overviewView.querySelectorAll("[data-path-card]").forEach((button) => {
      button.addEventListener("click", () => {
        state.selectedPath = button.dataset.pathCard;
        state.selectedTrack = "all";
        persistSettings();
        renderAll();
      });
    });
  }

  function referencesHtml(title, paths) {
    if (!paths.length) return "";
    return `
      <section class="lesson-section">
        <h3>${escapeHtml(title)}</h3>
        <ul class="reference-list">
          ${paths
            .map(
              (path) => `
                <li>
                  <a href="${gitHubUrl(path)}" target="_blank" rel="noreferrer">
                    <code>${escapeHtml(path)}</code>
                    <span aria-hidden="true">↗</span>
                  </a>
                </li>`
            )
            .join("")}
        </ul>
      </section>`;
  }

  function commandsHtml(commands) {
    if (!commands.length) return "";
    return `
      <section class="lesson-section">
        <h3>직접 실행</h3>
        ${commands
          .map(
            (command) => `
              <div class="command">
                <code>${escapeHtml(command)}</code>
                <button type="button" class="copy-command" data-command="${escapeHtml(
                  command
                )}">복사</button>
              </div>`
          )
          .join("")}
      </section>`;
  }

  function renderChallenge(lesson) {
    const challenge = lesson.challenge;
    if (!challenge) return "";
    const answered = progress.challenge[lesson.id];
    return `
      <section class="lesson-section">
        <p class="eyebrow">Checkpoint</p>
        <h3>개념 판단</h3>
        <p>${escapeHtml(challenge.prompt)}</p>
        <div class="challenge-options" data-challenge="${escapeHtml(lesson.id)}">
          ${challenge.options
            .map((option, index) => {
              const selected = answered === index;
              const correct = index === challenge.answer;
              const stateClass =
                answered === undefined
                  ? ""
                  : selected && correct
                  ? "correct"
                  : selected
                  ? "incorrect"
                  : correct
                  ? "correct muted-choice"
                  : "";
              return `<button type="button" class="answer-option ${stateClass}" data-challenge-answer="${index}">
                <span>${String.fromCharCode(65 + index)}</span>${escapeHtml(
                option
              )}</button>`;
            })
            .join("")}
        </div>
        ${
          answered === undefined
            ? ""
            : `<p class="feedback ${
                answered === challenge.answer ? "success" : "error"
              }">${escapeHtml(challenge.explanation)}</p>`
        }
      </section>`;
  }

  function renderQuiz(lesson) {
    const quizState = progress.quiz[lesson.id] || {};
    return `
      <section class="lesson-section">
        <p class="eyebrow">Knowledge check</p>
        <h3>레슨 퀴즈</h3>
        ${lesson.quiz
          .map((item, questionIndex) => {
            const answered = quizState[questionIndex];
            return `
              <article class="quiz-question" data-question="${questionIndex}">
                <strong>${questionIndex + 1}. ${escapeHtml(item.question)}</strong>
                <div class="quiz-options">
                  ${item.choices
                    .map((choice, choiceIndex) => {
                      const selected = answered === choiceIndex;
                      const correct = choiceIndex === item.answer;
                      const className =
                        answered === undefined
                          ? ""
                          : selected && correct
                          ? "correct"
                          : selected
                          ? "incorrect"
                          : correct
                          ? "correct muted-choice"
                          : "";
                      return `<button type="button" class="answer-option ${className}" data-quiz-answer="${choiceIndex}">
                        <span>${String.fromCharCode(65 + choiceIndex)}</span>${escapeHtml(
                        choice
                      )}</button>`;
                    })
                    .join("")}
                </div>
                ${
                  answered === undefined
                    ? ""
                    : `<p class="feedback ${
                        answered === item.answer ? "success" : "error"
                      }">${escapeHtml(item.explanation)}</p>`
                }
              </article>`;
          })
          .join("")}
      </section>`;
  }
