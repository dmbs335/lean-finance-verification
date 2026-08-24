window.LFV_ACADEMY.lessons.push(...[
  {
    "id":"alpha-uncertainty","track":"finance","order":12,
    "title":"Alpha Uncertainty After Attack Removal",
    "subtitle":"공격 편향을 제거한 뒤에도 남는 모델·통계·배포비용 불확실성을 구간으로 합성합니다.",
    "difficulty":"연구","minutes":36,
    "covers":["alpha-research"],
    "prerequisites":["certifiable-alpha","fake-alpha"],
    "outcomes":[
      "공격 불확실성과 모델·배포비용 불확실성을 분리한다.",
      "증거 선택에 따라 certifiable deployable-alpha interval이 어떻게 좁아지는지 계산한다.",
      "모든 선언 공격을 제거해도 alpha가 한 점이 되지 않는 이유를 설명한다."
    ],
    "concepts":["model envelope","unresolved inflation","deployment cost range","interval width","positive lower bound"],
    "why":"공격 탐지는 편향을 줄이지만 표본·위험모델·시장충격 불확실성을 없애지 않는다. 따라서 정직한 결과는 정확한 숫자보다 방어 가능한 구간이다.",
    "assurance":{
      "proves":["선언된 model interval, distortion upper bound, deployment-cost range에서 최소비용 evidence와 결과 구간을 exact하게 계산함"],
      "notProves":["현실 model interval의 통계적 타당성","미래 alpha의 확정값","모든 현실 공격의 완전성"]
    },
    "sources":[
      "LeanFinance/Alpha/Uncertainty.lean",
      "LeanFinance/Alpha/UncertaintyExample.lean",
      "tools/certifiable_alpha_interval/",
      "examples/certifiable_alpha/uncertainty.json"
    ],
    "docs":["docs/CERTIFIABLE_ALPHA_UNCERTAINTY.md"],
    "commands":[
      "python -m unittest discover -s tools/certifiable_alpha_interval/tests -v",
      "python -m tools.certifiable_alpha_interval analyze --model examples/certifiable_alpha/uncertainty.json --out /tmp/alpha-interval.json"
    ],
    "challenge":{
      "prompt":"선언된 공격 650 bps를 모두 제거했는데도 interval이 [30, 550]인 이유는?",
      "options":["모델 envelope와 deployment-cost range가 남아서","증거가 아무 공격도 찾지 못해서","Lean이 정수만 사용해서"],
      "answer":0,
      "explanation":"공격 불확실성과 모델·배포 불확실성은 서로 다른 층이다."
    },
    "quiz":[
      {"question":"더 강한 증거가 직접 개선하는 endpoint는?","choices":["미검출 upward distortion을 줄여 lower bound를 높임","시장 upper return을 확정함","모든 cost를 0으로 만듦"],"answer":0,"explanation":"검출 evidence는 선언된 조작 가능성을 제거하지만 다른 불확실성은 남긴다."},
      {"question":"공격 식별 후 interval이 한 점이 되려면 추가로 필요한 것은?","choices":["모델과 deployment endpoint도 일치한다는 근거","더 긴 strategy name","provider ID 하나"],"answer":0,"explanation":"point identification에는 남은 모든 uncertainty endpoint의 일치가 필요하다."}
    ]
  },
  {
    "id":"research-agent-gates","track":"robust","order":12,
    "title":"Proof-Carrying Research Agent Gates",
    "subtitle":"등록된 여섯 분석을 fail-closed 순서로 실행하고 모든 gate가 통과할 때만 bounded certificate를 냅니다.",
    "difficulty":"연구","minutes":44,
    "covers":["research-agent","portfolio-research","liquidation-research"],
    "prerequisites":["alpha-uncertainty","evidence-adjusted-portfolio","certifiability-crowding","epistemic-liquidation","epistemic-event-study"],
    "outcomes":[
      "alpha audit와 alpha interval gate를 구분한다.",
      "event-study 자체의 preregistered gate와 agent-level DID gate를 구분한다.",
      "등록 plan과 여섯 analysis report digest가 certificate에 어떻게 결합되는지 설명한다.",
      "gate 하나의 실패가 최종 certificate 발급을 막는 fail-closed 의미를 이해한다."
    ],
    "concepts":["registered plan","analysis gate","alphaBounded","eventStudied","artifact digest","fail closed","bounded certificate"],
    "why":"개별 분석이 모두 존재해도 실행 순서·입력·통과 기준이 사전에 고정되지 않으면 유리한 결과만 골라 보고할 수 있다.",
    "assurance":{
      "proves":["등록된 finite fixture와 threshold에서 여섯 분석을 정확히 재실행하고 모든 gate 통과 시에만 certificate를 발급함"],
      "notProves":["agent가 새로운 전략이나 과학적 가설을 올바르게 생성함","실제 시장 인과효과","외부 데이터 진실성"]
    },
    "sources":[
      "LeanFinance/ResearchAgent/Workflow.lean",
      "LeanFinance/ResearchAgent/Example.lean",
      "tools/research_agent/",
      "examples/research_agent/plan.json"
    ],
    "docs":["docs/PROOF_CARRYING_RESEARCH_AGENT.md"],
    "commands":[
      "python -m unittest discover -s tools/research_agent/tests -v",
      "python -m tools.research_agent --repository-root . run --plan examples/research_agent/plan.json --out /tmp/research-agent.json"
    ],
    "challenge":{
      "prompt":"event-study 자체 기준 700 bps는 통과했지만 agent plan의 최소 DID 900 bps는 못 넘으면?",
      "options":["rejected이며 certificate 없음","event-study가 accepted이므로 무조건 certified","agent threshold를 사후 700으로 내림"],
      "answer":0,
      "explanation":"분석 contract와 certificate 발급 contract는 둘 다 사전 고정되고 모두 통과해야 한다."
    },
    "quiz":[
      {"question":"v3 certificate가 bind하는 분석 report 수는?","choices":["6개","1개","무제한"],"answer":0,"explanation":"fake alpha, alpha interval, portfolio, crowding, liquidation, event study를 각각 digest로 묶는다."},
      {"question":"이 harness가 autonomous scientist가 아닌 이유는?","choices":["가설 중요성·실제 데이터 타당성·인과 calibration을 판단하지 않아서","Python을 사용해서","stage가 여러 개라서"],"answer":0,"explanation":"기계적 gate 통과와 과학적 발견의 타당성은 별개다."}
    ]
  }
]);
