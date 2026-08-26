window.LFV_ACADEMY.lessons.push(...[
  {
    "id":"unified-research-version-space",
    "track":"epistemic",
    "order":16,
    "title":"Unified Research Version Space",
    "subtitle":"데이터·모델·탐색·실행·universe의 가능한 world를 하나의 evidence-conditioned 공간으로 통합합니다.",
    "difficulty":"연구",
    "minutes":44,
    "covers":["epistemic","alpha-research","research-version-space"],
    "prerequisites":["temporal-noninterference","alpha-uncertainty","proof-carrying-formula"],
    "outcomes":[
      "research world를 data, model, search, execution, universe 좌표로 표현한다.",
      "evidence refinement를 admissible-world inclusion으로 정의한다.",
      "exact lower/upper witness를 가진 certifiable range를 읽는다.",
      "강한 evidence가 alpha와 risk interval을 넓히지 못하는 contraction law를 설명한다.",
      "integrity uncertainty와 legitimate model uncertainty를 분리한다."
    ],
    "concepts":["research world","version space","admissibility","exact endpoint witness","range contraction","residual model uncertainty","interval evidence debt"],
    "why":"data revision, risk-model version, hidden search, optimistic execution, survivorship를 독립 bias 항으로 가정하면 상호작용을 놓친다. 완전한 가능한 world 집합을 직접 줄이는 편이 더 근본적이다.",
    "assurance":{
      "proves":["strong evidence의 admissible world가 weak evidence의 부분집합이면 exact lower bound는 상승하고 upper bound와 width는 감소함","finite fixture의 모든 evidence-refinement pair에서 alpha/risk range contraction","target interval을 만족하는 minimum-cost evidence set"],
      "notProves":["declared world family의 현실 완전성","각 world의 alpha/risk calibration","좁은 interval의 미래 수익성"]
    },
    "sources":[
      "LeanFinance/Epistemic/ResearchVersionSpace.lean",
      "tools/research_version_space/",
      "examples/research_version_space/integrity_and_model_uncertainty.json"
    ],
    "docs":["docs/UNIFIED_RESEARCH_VERSION_SPACE.md"],
    "commands":[
      "python -m unittest discover -s tools/research_version_space/tests -v",
      "python -m tools.research_version_space analyze --model examples/research_version_space/integrity_and_model_uncertainty.json --out /tmp/research-version-space.json"
    ],
    "challenge":{
      "prompt":"모든 integrity-distortion world를 제거했는데도 alpha interval이 [30, 50]으로 남는 이유는?",
      "options":["세 legitimate risk-model world가 여전히 evidence와 일치해서","solver가 일부 attack을 놓쳐서","alpha가 정수가 아니라서"],
      "answer":0,
      "explanation":"무결성 evidence는 조작 world를 제거하지만 정당한 model-family uncertainty를 자동으로 없애지 않는다."
    },
    "quiz":[
      {
        "question":"강한 evidence가 weak evidence를 refine한다는 뜻은?",
        "choices":["strong에서 가능한 모든 world가 weak에서도 가능","strong이 항상 더 높은 alpha를 보장","channel cost가 더 큼"],
        "answer":0,
        "explanation":"admissible world inclusion이 refinement의 의미다."
      },
      {
        "question":"Controlled exact minimum evidence cost는?",
        "choices":["12","14","5"],
        "answer":0,
        "explanation":"PIT data, model vintage, search ledger, execution receipt, universe snapshot의 합계가 12다."
      }
    ]
  }
]);
