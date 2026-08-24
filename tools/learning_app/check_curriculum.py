from __future__ import annotations

import json
import re
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

META_PREFIX = "window.LFV_ACADEMY = "
TRACK_PREFIX = "window.LFV_ACADEMY.lessons.push(..."
EXPECTED_SCHEMA = "lfv-learning-curriculum-v2"

REQUIRED_APP_FILES = (
    "learning-app/index.html", "learning-app/styles/base.css",
    "learning-app/styles/layout.css", "learning-app/styles/components.css",
    "learning-app/data/meta.js", "learning-app/data/orientation.js",
    "learning-app/data/finance.js", "learning-app/data/alpha.js",
    "learning-app/data/research.js", "learning-app/data/event-study.js",
    "learning-app/data/composition.js",
    "learning-app/data/backtest.js", "learning-app/data/epistemic.js",
    "learning-app/data/robust.js", "learning-app/data/infrastructure.js",
    "learning-app/data/curriculum.js", "learning-app/app/core.js",
    "learning-app/app/render-a.js", "learning-app/app/render-b.js",
    "learning-app/app/main.js", "learning-app/README.md",
)
REQUIRED_COVERAGE_IDS = {
    "core", "game-theory", "market", "constraints", "dynamics", "inference",
    "strategy-ecology", "supply-chain", "backtest", "certificate", "epistemic",
    "generated", "alpha-research", "portfolio-research", "liquidation-research",
    "event-study", "composition", "research-agent", "adapter", "evidence-synth", "workflow-cegis",
    "trace-refinement", "model-family", "robust-evidence", "multiclaim", "taxonomy",
    "symbolic", "pit-study", "pit-vendor", "external-quorum", "selective-receipt",
    "zk-receipt", "schemas", "examples", "ci",
}
REQUIRED_TRACK_IDS = {"orientation", "finance", "backtest", "epistemic", "robust", "infrastructure"}
REQUIRED_TOOL_DIRS = {
    "tools/lfv_adapter", "tools/evidence_synth", "tools/workflow_cegis",
    "tools/trace_refinement", "tools/model_family_synth", "tools/robust_evidence",
    "tools/multiclaim_synth", "tools/evidence_taxonomy", "tools/symbolic_evidence",
    "tools/fake_alpha_benchmark", "tools/certifiable_alpha_interval",
    "tools/evidence_portfolio", "tools/certifiability_crowding",
    "tools/epistemic_liquidation", "tools/epistemic_event_study",
    "tools/certificate_composition", "tools/research_agent", "tools/pit_study", "tools/pit_vendor_import",
    "tools/external_quorum", "tools/selective_receipt", "tools/zk_receipt",
}


class CurriculumValidationError(ValueError):
    pass


def _json_assignment(path: Path, prefix: str, suffix: str) -> Any:
    raw = path.read_text(encoding="utf-8").strip()
    if not raw.startswith(prefix) or not raw.endswith(suffix):
        raise CurriculumValidationError(f"{path.name} has an unexpected data wrapper")
    try:
        return json.loads(raw[len(prefix):len(raw)-len(suffix)])
    except json.JSONDecodeError as exc:
        raise CurriculumValidationError(f"{path.name} contains invalid JSON: {exc}") from exc


def load_curriculum(repository_root: Path) -> dict[str, Any]:
    data_dir = repository_root / "learning-app" / "data"
    result = _json_assignment(data_dir / "meta.js", META_PREFIX, ";")
    if not isinstance(result, dict) or result.get("lessons") != []:
        raise CurriculumValidationError("meta.js must initialize an empty lesson array")
    lessons = result["lessons"]
    for path in sorted(data_dir.glob("*.js")):
        if path.name in {"meta.js", "curriculum.js"}:
            continue
        payload = _json_assignment(path, TRACK_PREFIX, ");")
        if not isinstance(payload, list):
            raise CurriculumValidationError(f"{path.name} must contain a lesson array")
        lessons.extend(payload)
    return result


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CurriculumValidationError(message)


def _require_strings(values: Any, path: str, *, allow_empty: bool = False) -> list[str]:
    _require(isinstance(values, list), f"{path} must be an array")
    _require(allow_empty or bool(values), f"{path} must not be empty")
    _require(all(isinstance(value, str) and value for value in values), f"{path} must contain non-empty strings")
    return values


def _validate_repository_path(root: Path, value: str, label: str) -> None:
    _require(not value.startswith(("http://", "https://", "/", "../")), f"{label} must be repository-relative: {value}")
    candidate = root / value.rstrip("/")
    _require(candidate.exists(), f"{label} points to missing path: {value}")
    if value.endswith("/"):
        _require(candidate.is_dir(), f"{label} must reference a directory: {value}")


def _validate_question(question: Any, label: str, choices_key: str) -> None:
    _require(isinstance(question, dict), f"{label} must be an object")
    choices = _require_strings(question.get(choices_key), f"{label}.{choices_key}")
    answer = question.get("answer")
    _require(isinstance(answer, int) and not isinstance(answer, bool) and 0 <= answer < len(choices), f"{label}.answer is invalid")
    _require(isinstance(question.get("explanation"), str) and question["explanation"], f"{label}.explanation must be non-empty")


def _validate_dag(lesson_by_id: dict[str, dict[str, Any]]) -> None:
    indegree = {lesson_id: 0 for lesson_id in lesson_by_id}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for lesson_id, lesson in lesson_by_id.items():
        for prerequisite in lesson["prerequisites"]:
            _require(prerequisite in lesson_by_id, f"lesson {lesson_id} has unknown prerequisite {prerequisite}")
            _require(prerequisite != lesson_id, f"lesson {lesson_id} cannot depend on itself")
            outgoing[prerequisite].append(lesson_id)
            indegree[lesson_id] += 1
    queue = deque(sorted(key for key, value in indegree.items() if value == 0))
    visited = 0
    while queue:
        current = queue.popleft(); visited += 1
        for successor in outgoing[current]:
            indegree[successor] -= 1
            if indegree[successor] == 0:
                queue.append(successor)
    _require(visited == len(lesson_by_id), "lesson prerequisites contain a cycle")


def validate_curriculum(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    for relative in REQUIRED_APP_FILES:
        _require((root / relative).is_file(), f"missing app file: {relative}")
    curriculum = load_curriculum(root)
    _require(curriculum.get("schemaVersion") == EXPECTED_SCHEMA, f"expected schema {EXPECTED_SCHEMA}")
    _require(curriculum.get("repo") == "dmbs335/lean-finance-verification", "curriculum repo link must target this repository")
    tracks, coverage, paths, lessons = (curriculum.get(key) for key in ("tracks", "coverageAreas", "paths", "lessons"))
    for value, label in ((tracks,"tracks"),(coverage,"coverageAreas"),(paths,"paths"),(lessons,"lessons")):
        _require(isinstance(value, list) and value, f"{label} must be non-empty")
    track_ids = [item.get("id") for item in tracks if isinstance(item, dict)]
    coverage_ids = [item.get("id") for item in coverage if isinstance(item, dict)]
    _require(len(track_ids) == len(tracks) and len(set(track_ids)) == len(track_ids), "track ids invalid")
    _require(REQUIRED_TRACK_IDS.issubset(set(track_ids)), "required tracks missing")
    _require(len(coverage_ids) == len(coverage) and len(set(coverage_ids)) == len(coverage_ids), "coverage ids invalid")
    _require(REQUIRED_COVERAGE_IDS.issubset(set(coverage_ids)), "required coverage areas missing")
    for index, area in enumerate(coverage):
        for path_index, source in enumerate(_require_strings(area.get("paths"), f"coverageAreas[{index}].paths")):
            _validate_repository_path(root, source, f"coverageAreas[{index}].paths[{path_index}]")
    _require(len(lessons) >= 30, "curriculum must contain at least 30 lessons")
    lesson_by_id: dict[str, dict[str, Any]] = {}
    represented_coverage: set[str] = set(); represented_tracks: set[str] = set()
    for index, lesson in enumerate(lessons):
        label = f"lessons[{index}]"; _require(isinstance(lesson, dict), f"{label} must be object")
        lesson_id = lesson.get("id"); _require(isinstance(lesson_id, str) and lesson_id and lesson_id not in lesson_by_id, f"{label}.id invalid")
        lesson_by_id[lesson_id] = lesson
        for field in ("title","subtitle","difficulty","why"):
            _require(isinstance(lesson.get(field), str) and lesson[field], f"{label}.{field} missing")
        _require(isinstance(lesson.get("minutes"), int) and not isinstance(lesson["minutes"], bool) and lesson["minutes"] > 0, f"{label}.minutes invalid")
        _require(isinstance(lesson.get("order"), int) and not isinstance(lesson["order"], bool) and lesson["order"] > 0, f"{label}.order invalid")
        _require(lesson.get("track") in set(track_ids), f"{label}.track unknown"); represented_tracks.add(lesson["track"])
        covers = _require_strings(lesson.get("covers"), f"{label}.covers"); _require(set(covers).issubset(set(coverage_ids)), f"{label}.covers unknown"); represented_coverage.update(covers)
        _require_strings(lesson.get("prerequisites"), f"{label}.prerequisites", allow_empty=True)
        _require_strings(lesson.get("outcomes"), f"{label}.outcomes"); _require_strings(lesson.get("concepts"), f"{label}.concepts")
        assurance = lesson.get("assurance"); _require(isinstance(assurance, dict), f"{label}.assurance invalid")
        _require_strings(assurance.get("proves"), f"{label}.assurance.proves"); _require_strings(assurance.get("notProves"), f"{label}.assurance.notProves")
        sources = _require_strings(lesson.get("sources"), f"{label}.sources"); docs = _require_strings(lesson.get("docs"), f"{label}.docs", allow_empty=True)
        _require_strings(lesson.get("commands"), f"{label}.commands", allow_empty=True)
        for i, source in enumerate(sources): _validate_repository_path(root, source, f"{label}.sources[{i}]")
        for i, doc in enumerate(docs): _validate_repository_path(root, doc, f"{label}.docs[{i}]")
        challenge = lesson.get("challenge"); _require(isinstance(challenge, dict) and isinstance(challenge.get("prompt"), str) and challenge["prompt"], f"{label}.challenge invalid")
        _validate_question(challenge, f"{label}.challenge", "options")
        quiz = lesson.get("quiz"); _require(isinstance(quiz, list) and len(quiz) >= 2, f"{label}.quiz invalid")
        for i, question in enumerate(quiz): _validate_question(question, f"{label}.quiz[{i}]", "choices")
    _require(represented_tracks == set(track_ids), "tracks without lessons")
    _require(REQUIRED_COVERAGE_IDS.issubset(represented_coverage), "coverage areas without lessons")
    _validate_dag(lesson_by_id)
    seen_paths: set[str] = set()
    for index, learning_path in enumerate(paths):
        label = f"paths[{index}]"; _require(isinstance(learning_path, dict), f"{label} invalid")
        path_id = learning_path.get("id"); _require(isinstance(path_id, str) and path_id and path_id not in seen_paths, f"{label}.id invalid"); seen_paths.add(path_id)
        lesson_ids = _require_strings(learning_path.get("lessonIds"), f"{label}.lessonIds")
        _require(len(lesson_ids) == len(set(lesson_ids)) and set(lesson_ids).issubset(lesson_by_id), f"{label}.lessonIds invalid")
        _require(isinstance(learning_path.get("label"), str) and learning_path["label"], f"{label}.label missing")
        _require(isinstance(learning_path.get("description"), str) and learning_path["description"], f"{label}.description missing")
    for tool_dir in REQUIRED_TOOL_DIRS: _require((root / tool_dir).is_dir(), f"missing required tool directory: {tool_dir}")
    html = (root / "learning-app/index.html").read_text(encoding="utf-8")
    assets = ("styles/base.css","styles/layout.css","styles/components.css","data/meta.js","data/orientation.js","data/finance.js","data/alpha.js","data/research.js","data/event-study.js","data/composition.js","data/backtest.js","data/epistemic.js","data/robust.js","data/infrastructure.js","data/curriculum.js","app/core.js","app/render-a.js","app/render-b.js","app/main.js")
    for asset in assets:
        attribute = "href" if asset.endswith(".css") else "src"; _require(f'{attribute}="{asset}"' in html, f"index.html must load {asset}")
    _require(not re.search(r'<(?:script|link)[^>]+https?://', html, re.IGNORECASE), "external scripts/styles forbidden")
    app_js = "\n".join(path.read_text(encoding="utf-8") for path in sorted((root / "learning-app/app").glob("*.js")))
    _require("window.LFV_CURRICULUM" in app_js and "localStorage" in app_js, "browser curriculum/progress contract missing")
    return {"lesson_count":len(lessons),"track_count":len(tracks),"coverage_count":len(coverage),"path_count":len(paths),"source_count":len({source for lesson in lessons for source in lesson.get("sources",[])}),"minutes":sum(lesson["minutes"] for lesson in lessons)}


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    try: summary = validate_curriculum(root)
    except CurriculumValidationError as exc:
        print(f"error: {exc}"); return 2
    print("learning curriculum valid: " + " ".join(f"{key}={value}" for key, value in summary.items()))
    return 0


if __name__ == "__main__": raise SystemExit(main())
