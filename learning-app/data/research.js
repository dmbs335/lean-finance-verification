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
    "subtitle":"등록된 일곱 분석과 cross-certificate binding을 fail-closed 순서로 실행합니다.",
    "difficulty":"연구","minutes":46,
    "covers":["research-agent","portfolio-research","liquidation-research","composition"],
    "prerequisites":["alpha-uncertainty","evidence-adjusted-portfolio","certifiability-crowding","epistemic-liquidation","epistemic-event-study","certificate-composition"],
    "outcomes":[
      "여섯 local analysis gate와 composition gate를 구분한다.",
      "local report digest를 나열하는 것과 같은 causal pipeline으로 binding하는 것의 차이를 설명한다.",
      "등록 plan과 일곱 analysis report digest가 certificate에 어떻게 결합되는지 설명한다.",
      "실패한 gate 이전까지만 completed stage로 기록되는 prefix semantics를 이해한다."
    ],
    "concepts":["registered plan","analysis gate","eventStudied","pipelineComposed","bridge receipt","stage prefix","fail closed","bounded certificate"],
    "why":"모든 local analysis가 green이어도 서로 다른 dataset·decision·result를 가리키면 global research claim은 거짓일 수 있다. 최종 인증에는 분석 통과와 cross-boundary composition이 모두 필요하다.",
    "assurance":{
      "proves":["등록된 finite fixture와 threshold에서 일곱 분석을 재실행하고 global binding gate까지 통과할 때만 certificate를 발급함","composition cost 초과 시 local gate가 green이어도 pipelineComposed와 certified stage를 발급하지 않음"],
      "notProves":["bridge digest가 현실의 올바른 causal boundary에서 측정됐음","agent가 과학적으로 중요한 가설을 생성함","실제 시장 인과효과"]
    },
    "sources":[
      "LeanFinance/ResearchAgent/Workflow.lean",
      "LeanFinance/ResearchAgent/Example.lean",
      "tools/research_agent/",
      "examples/research_agent/plan.json",
      "tools/certificate_composition/"
    ],
    "docs":["docs/PROOF_CARRYING_RESEARCH_AGENT.md","docs/CERTIFICATE_COMPOSITION_LAW.md"],
    "commands":[
      "python -m unittest discover -s tools/research_agent/tests -v",
      "python -m tools.research_agent --repository-root . run --plan examples/research_agent/plan.json --out /tmp/research-agent.json"
    ],
    "challenge":{
      "prompt":"여섯 local analysis가 모두 green이지만 binding receipt 최소비용 4가 등록 budget 3을 넘으면?",
      "options":["rejected이며 eventStudied까지만 완료","local gate가 green이므로 자동 certified","global bundle을 사후 무료로 추가"],
      "answer":0,
      "explanation":"composition gate는 별도 등록 의무다. 실패하면 pipelineComposed와 certified stage는 완료되지 않는다."
    },
    "quiz":[
      {"question":"v4 certificate가 bind하는 analysis report 수는?","choices":["7개","6개","1개"],"answer":0,"explanation":"기존 여섯 분석에 certificate-composition report가 추가된다."},
      {"question":"local report digest를 certificate에 나열하는 것만으로 부족한 이유는?","choices":["각 report가 같은 dataset→decision→result pipeline을 가리킨다는 cross-object identity를 보장하지 않아서","SHA-256 길이가 짧아서","report 수가 홀수라서"],"answer":0,"explanation":"local validity와 cross-boundary binding은 서로 다른 claim이다."}
    ]
  }
]);
