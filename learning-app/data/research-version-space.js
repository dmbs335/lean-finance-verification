window.LFV_ACADEMY.lessons.push(...[
  {
    "id":"research-version-space",
    "track":"robust",
    "order":16,
    "title":"Unified Research Version Space",
    "subtitle":"데이터·모델·탐색·실행·universe 불확실성을 하나의 admissible-world calculus로 합칩니다.",
    "difficulty":"연구",
    "minutes":44,
    "covers":["epistemic","model-family","alpha-research","backtest","research-version-space"],
    "prerequisites":["version-space","alpha-uncertainty","temporal-noninterference","formula-contract"],
    "outcomes":[
      "research world를 D-M-S-X-U 다섯 좌표로 표현한다.",
      "증거 refinement가 exact certifiable range를 중첩시키는 정리를 설명한다.",
      "32개 world와 64개 evidence subset을 exact enumeration한다.",
      "interaction을 포함한 Shapley revision attribution을 해석한다."
    ],
    "concepts":["admissible world","research version space","greatest lower bound","least upper bound","range refinement","Shapley attribution","evidence-width optimization"],
    "why":"PIT data, model revision, hidden search, optimistic execution과 survivorship를 별도 벌점으로 단순 합산하면 상호작용과 공통 evidence requirement를 놓친다. 가능한 전체 연구세계의 집합으로 다뤄야 한다.",
    "assurance":{
      "proves":["강한 evidence가 admissible world를 줄이면 exact lower bound는 하락하지 않고 upper bound는 상승하지 않음","controlled 5차원 world와 channel language의 exact interval·최소비용 evidence·Shapley attribution"],
      "notProves":["각 controlled effect의 실제 시장 크기","다섯 좌표가 현실 uncertainty를 완전히 포괄함","외부 adapter와 timestamp의 진실성"]
    },
    "sources":["LeanFinance/Epistemic/ResearchVersionSpace.lean","LeanFinance/Epistemic/ResearchVersionSpaceExample.lean","tools/research_version_space/","examples/research_version_space/five_dimensions.json"],
    "docs":["docs/UNIFIED_RESEARCH_VERSION_SPACE.md"],
    "commands":["python -m unittest discover -s tools/research_version_space/tests -v","python -m tools.research_version_space analyze --model examples/research_version_space/five_dimensions.json --out /tmp/research-version-space.json"],
    "challenge":{"prompt":"PIT receipt와 search ledger를 추가해 range가 [20,150]에서 [20,55]로 줄었다. 무엇이 직접 증명된 것인가?","options":["선언된 world family에서 latest-data와 hidden-search worlds가 배제됨","미래 수익 20 이상 보장","모든 현실 모델이 정확함"],"answer":0,"explanation":"range 축소는 선언된 admissibility와 metric에 상대적이며 미래 성과의 보장이 아니다."},
    "quiz":[
      {"question":"강한 evidence E2가 E1을 refine한다는 뜻은?","choices":["V(E2)가 V(E1)의 부분집합","모든 metric이 증가","evidence cost가 항상 낮음"],"answer":0,"explanation":"강한 evidence에서 살아남는 모든 world가 약한 evidence에서도 admissible해야 한다."},
      {"question":"Shapley attribution을 쓰는 주된 이유는?","choices":["revision 적용 순서에 독립적으로 interaction을 분배","world enumeration을 생략","Lean proof를 확률적으로 대체"],"answer":0,"explanation":"각 dimension의 marginal effect를 모든 순서에 평균해 interaction contribution을 공정하게 나눈다."}
    ]
  }
]);
