  function lessonOrderForNavigation() {
    return pathLessons();
  }

  function renderLesson(lesson) {
    const track = trackById.get(lesson.track);
    const navLessons = lessonOrderForNavigation();
    const index = navLessons.findIndex((item) => item.id === lesson.id);
    const previous = index > 0 ? navLessons[index - 1] : null;
    const next = index >= 0 && index < navLessons.length - 1
      ? navLessons[index + 1]
      : null;

    elements.lessonView.innerHTML = `
      <header class="lesson-header">
        <div class="lesson-header-top">
          <div>
            <p class="lesson-kicker">${escapeHtml(track.label)}</p>
            <h2>${escapeHtml(lesson.title)}</h2>
            <p class="lesson-subtitle">${escapeHtml(lesson.subtitle)}</p>
          </div>
          <button id="completeLessonButton" type="button" class="button ${
            isCompleted(lesson.id) ? "button-quiet" : "button-primary"
          }">
            ${isCompleted(lesson.id) ? "✓ 완료 취소" : "레슨 완료"}
          </button>
        </div>
        <div class="chip-row">
          <span class="pill">${escapeHtml(lesson.difficulty)}</span>
          <span class="pill">${lesson.minutes}분</span>
          <span class="pill">${lesson.sources.length} source</span>
          <span class="pill">${lesson.covers.length} coverage area</span>
        </div>
      </header>

      <div class="lesson-grid">
        <div class="lesson-column">
          <section class="lesson-section">
            <p class="eyebrow">Why it matters</p>
            <h3>왜 이 레슨이 필요한가</h3>
            <p>${escapeHtml(lesson.why)}</p>
          </section>

          <section class="lesson-section">
            <h3>학습 목표</h3>
            <ol>
              ${lesson.outcomes
                .map((outcome) => `<li>${escapeHtml(outcome)}</li>`)
                .join("")}
            </ol>
          </section>

          <section class="lesson-section">
            <h3>핵심 개념</h3>
            <div class="chip-row">
              ${lesson.concepts
                .map(
                  (concept) =>
                    `<button type="button" class="chip concept-chip" data-concept="${escapeHtml(
                      concept
                    )}">${escapeHtml(concept)}</button>`
                )
                .join("")}
            </div>
          </section>

          <section class="assurance-grid">
            <article class="assurance-box positive">
              <span>✓</span>
              <div>
                <strong>이 레슨에서 증명·검사하는 것</strong>
                <ul>${lesson.assurance.proves
                  .map((item) => `<li>${escapeHtml(item)}</li>`)
                  .join("")}</ul>
              </div>
            </article>
            <article class="assurance-box negative">
              <span>!</span>
              <div>
                <strong>여전히 증명하지 않는 것</strong>
                <ul>${lesson.assurance.notProves
                  .map((item) => `<li>${escapeHtml(item)}</li>`)
                  .join("")}</ul>
              </div>
            </article>
          </section>

          ${renderChallenge(lesson)}
          ${renderQuiz(lesson)}
        </div>

        <aside class="lesson-column">
          ${
            lesson.prerequisites.length
              ? `<section class="lesson-section">
                  <h3>선행 레슨</h3>
                  <ul class="reference-list">
                    ${lesson.prerequisites
                      .map((id) => {
                        const prerequisite = lessonById.get(id);
                        return prerequisite
                          ? `<li><button type="button" data-open-lesson="${escapeHtml(
                              id
                            )}">${isCompleted(id) ? "✓" : "→"} ${escapeHtml(
                              prerequisite.title
                            )}</button></li>`
                          : "";
                      })
                      .join("")}
                  </ul>
                </section>`
              : ""
          }
          ${referencesHtml("Lean · Python source", lesson.sources)}
          ${referencesHtml("설계 문서", lesson.docs)}
          ${commandsHtml(lesson.commands)}
          <section class="lesson-section">
            <h3>프로젝트 커버리지</h3>
            <div class="chip-row">
              ${lesson.covers
                .map((id) => {
                  const area = coverageById.get(id);
                  return `<button type="button" class="chip" data-coverage-area="${escapeHtml(
                    id
                  )}">${escapeHtml(area ? area.label : id)}</button>`;
                })
                .join("")}
            </div>
          </section>
        </aside>
      </div>

      <footer class="lesson-footer">
        <button class="button button-quiet" type="button" id="backToOverview">← 전체 지도</button>
        <div class="lesson-controls">
          ${
            previous
              ? `<button class="button button-quiet" type="button" data-open-lesson="${escapeHtml(
                  previous.id
                )}">← ${escapeHtml(previous.title)}</button>`
              : ""
          }
          ${
            next
              ? `<button class="button button-primary" type="button" data-open-lesson="${escapeHtml(
                  next.id
                )}">${escapeHtml(next.title)} →</button>`
              : ""
          }
        </div>
      </footer>`;

    $("completeLessonButton").addEventListener("click", () =>
      toggleCompleted(lesson.id)
    );
    $("backToOverview").addEventListener("click", () => {
      state.activeLesson = null;
      setView("overview");
      renderAll();
    });
    elements.lessonView.querySelectorAll("[data-open-lesson]").forEach((button) => {
      button.addEventListener("click", () => openLesson(button.dataset.openLesson));
    });
    elements.lessonView
      .querySelectorAll("[data-coverage-area]")
      .forEach((button) => {
        button.addEventListener("click", () => {
          renderCoverage(button.dataset.coverageArea);
          setView("coverage");
        });
      });
    elements.lessonView.querySelectorAll(".concept-chip").forEach((button) => {
      button.addEventListener("click", () => {
        renderGlossary(button.dataset.concept);
        setView("glossary");
      });
    });
    elements.lessonView.querySelectorAll(".copy-command").forEach((button) => {
      button.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(button.dataset.command);
          const original = button.textContent;
          button.textContent = "복사됨";
          setTimeout(() => {
            button.textContent = original;
          }, 1000);
        } catch {
          button.textContent = "복사 실패";
        }
      });
    });
    elements.lessonView
      .querySelectorAll("[data-challenge-answer]")
      .forEach((button) => {
        button.addEventListener("click", () => {
          progress.challenge[lesson.id] = Number(
            button.dataset.challengeAnswer
          );
          persistProgress();
          renderLesson(lesson);
        });
      });
    elements.lessonView.querySelectorAll(".quiz-question").forEach((question) => {
      question.querySelectorAll("[data-quiz-answer]").forEach((button) => {
        button.addEventListener("click", () => {
          const index = Number(question.dataset.question);
          progress.quiz[lesson.id] = progress.quiz[lesson.id] || {};
          progress.quiz[lesson.id][index] = Number(button.dataset.quizAnswer);
          persistProgress();
          renderLesson(lesson);
        });
      });
    });
  }

  function openLesson(id) {
    const lesson = lessonById.get(id);
    if (!lesson) return;
    state.activeLesson = id;
    setView("lesson");
    renderLesson(lesson);
    renderLessonNav();
  }

  function coverageLessons(areaId) {
    return data.lessons.filter((lesson) => lesson.covers.includes(areaId));
  }

  function renderCoverage(focusId = null) {
    const represented = data.coverageAreas.filter(
      (area) => coverageLessons(area.id).length
    );
    const completedAreas = represented.filter((area) =>
      coverageLessons(area.id).every((lesson) => isCompleted(lesson.id))
    ).length;
    elements.coverageView.innerHTML = `
      <header class="overview-header">
        <div>
          <p class="eyebrow">Repository coverage</p>
          <h2 class="view-title">프로젝트 커버리지 맵</h2>
          <p>각 프로젝트 영역을 어떤 레슨이 다루는지 확인합니다. 형식 이론뿐 아니라 금융 모델, Python 도구, fixture, CI까지 포함합니다.</p>
        </div>
        <button class="button button-quiet" type="button" id="coverageBack">전체 지도로</button>
      </header>
      <section class="coverage-summary">
        <article><strong>${represented.length}/${data.coverageAreas.length}</strong><span>영역에 레슨 연결</span></article>
        <article><strong>${completedAreas}</strong><span>완료된 영역</span></article>
        <article><strong>${new Set(
          data.lessons.flatMap((lesson) => lesson.sources)
        ).size}</strong><span>직접 연결 source</span></article>
      </section>
      <div class="coverage-grid">
        ${data.coverageAreas
          .map((area) => {
            const lessons = coverageLessons(area.id);
            const done = lessons.filter((lesson) => isCompleted(lesson.id)).length;
            return `
              <article class="coverage-card ${
                focusId === area.id ? "focused" : ""
              }" id="coverage-${escapeHtml(area.id)}">
                <div>
                  <span class="pill">${done}/${lessons.length}</span>
                  <h3>${escapeHtml(area.label)}</h3>
                  <p>${escapeHtml(area.description)}</p>
                </div>
                <div class="coverage-lessons">
                  ${lessons
                    .map(
                      (lesson) => `
                        <button type="button" data-open-lesson="${escapeHtml(
                          lesson.id
                        )}">
                          <span>${isCompleted(lesson.id) ? "✓" : "→"}</span>
                          ${escapeHtml(lesson.title)}
                        </button>`
                    )
                    .join("")}
                </div>
              </article>`;
          })
          .join("")}
      </div>`;
    $("coverageBack").addEventListener("click", () => {
      setView("overview");
      renderAll();
    });
    elements.coverageView
      .querySelectorAll("[data-open-lesson]")
      .forEach((button) => {
        button.addEventListener("click", () => openLesson(button.dataset.openLesson));
      });
    if (focusId) {
      requestAnimationFrame(() =>
        $(`coverage-${focusId}`)?.scrollIntoView({
          behavior: "smooth",
          block: "center",
        })
      );
    }
  }

  function glossaryEntries() {
    const map = new Map();
    data.lessons.forEach((lesson) => {
      lesson.concepts.forEach((concept) => {
        if (!map.has(concept)) map.set(concept, []);
        map.get(concept).push(lesson);
      });
    });
    return [...map.entries()].sort(([left], [right]) =>
      left.localeCompare(right, "en")
    );
  }

  function renderGlossary(focusConcept = "") {
    elements.glossaryView.innerHTML = `
      <header class="overview-header">
        <div>
          <p class="eyebrow">Project vocabulary</p>
          <h2 class="view-title">용어집</h2>
          <p>${glossaryEntries().length}개 핵심 용어를 실제 source 레슨으로 역추적합니다.</p>
        </div>
        <button class="button button-quiet" type="button" id="glossaryBack">전체 지도로</button>
      </header>
      <div class="glossary-toolbar">
        <label class="field">
          <span>용어 필터</span>
          <input id="glossarySearch" type="search" value="${escapeHtml(
            focusConcept
          )}" placeholder="예: separator, trust domain">
        </label>
      </div>
      <div id="glossaryGrid" class="glossary-grid"></div>`;
    $("glossaryBack").addEventListener("click", () => {
      setView("overview");
      renderAll();
    });
    const input = $("glossarySearch");
    const grid = $("glossaryGrid");

    const renderEntries = () => {
      const query = input.value.trim().toLowerCase();
      const entries = glossaryEntries().filter(([concept, lessons]) => {
        const text = [
          concept,
          ...lessons.map((lesson) => lesson.title),
        ]
          .join(" ")
          .toLowerCase();
        return !query || text.includes(query);
      });
      grid.innerHTML = entries.length
        ? entries
            .map(
              ([concept, lessons]) => `
                <article class="glossary-item" id="term-${encodeURIComponent(
                  concept
                )}">
                  <span class="pill">${lessons.length} 레슨</span>
                  <h3>${escapeHtml(concept)}</h3>
                  <p>${escapeHtml(
                    lessons
                      .map((lesson) => trackById.get(lesson.track).label)
                      .filter((value, index, array) => array.indexOf(value) === index)
                      .join(" · ")
                  )}</p>
                  <div class="coverage-lessons">
                    ${lessons
                      .map(
                        (lesson) => `
                          <button type="button" data-open-lesson="${escapeHtml(
                            lesson.id
                          )}">→ ${escapeHtml(lesson.title)}</button>`
                      )
                      .join("")}
                  </div>
                </article>`
            )
            .join("")
        : '<p class="empty-state">일치하는 용어가 없습니다.</p>';
      grid.querySelectorAll("[data-open-lesson]").forEach((button) => {
        button.addEventListener("click", () => openLesson(button.dataset.openLesson));
      });
    };
    input.addEventListener("input", renderEntries);
    renderEntries();
    if (focusConcept) {
      requestAnimationFrame(() => input.focus());
    }
  }
