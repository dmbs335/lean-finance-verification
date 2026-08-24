window.LFV_ACADEMY.lessons.push(...[
  {
    "id":"epistemic-event-study","track":"finance","order":13,
    "title":"Preregistered Epistemic-Crowding Event Study",
    "subtitle":"공통 evidence-domain 충격의 추가 설명력을 matched pretrend/DID gate로 검정합니다.",
    "difficulty":"연구","minutes":40,
    "covers":["event-study"],
    "prerequisites":["epistemic-liquidation","research-agent-gates"],
    "outcomes":[
      "실패 domain 노출군과 비노출 대조군을 conventional dimensions로 사전 매칭한다.",
      "pretrend DID와 event DID를 분리하고 gate 실패 시 certificate를 거부한다.",
      "controlled benchmark와 real-market causal inference의 차이를 설명한다."
    ],
    "concepts":["preregistration","matched pairs","parallel trend","difference-in-differences","evidence exposure","event window"],
    "why":"Epistemic liquidation이 단지 기존 factor·holdings·liquidity crowding을 다시 이름 붙인 것인지 구분하려면 사전 등록된 비교 설계가 필요하다.",
    "assurance":{
      "proves":["등록 시각, failed-domain exposure, matching tolerance, pretrend tolerance, aggregate DID threshold를 controlled fixture에서 exact하게 검사함"],
      "notProves":["현실 vendor shock의 인과효과","unobserved confounding 부재","실제 strategy dependency metadata의 진실성"]
    },
    "sources":[
      "LeanFinance/Market/EpistemicEventStudy.lean",
      "tools/epistemic_event_study/",
      "examples/epistemic_event_study/vendor_shock.json"
    ],
    "docs":["docs/EPISTEMIC_CROWDING_EVENT_STUDY.md"],
    "commands":[
      "python -m unittest discover -s tools/epistemic_event_study/tests -v",
      "python -m tools.epistemic_event_study analyze --plan examples/epistemic_event_study/vendor_shock.json --out /tmp/event-study.json"
    ],
    "challenge":{
      "prompt":"노출 전략의 post-event outflow가 더 커도 바로 epistemic effect라고 부를 수 없는 이유는?",
      "options":["기존 factor·holdings·liquidity 차이와 pretrend가 설명할 수 있어서","outflow는 정수가 아니어서","vendor 이름이 짧아서"],
      "answer":0,
      "explanation":"매칭과 parallel-trend gate가 없으면 기존 차이와 event effect를 분리하기 어렵다."
    },
    "quiz":[
      {"question":"이 protocol에서 treated와 control의 핵심 차이는?","choices":["failed evidence domain 노출 여부","모든 수익률이 동일함","같은 strategy ID"],"answer":0,"explanation":"conventional dimensions는 가깝게 맞추고 evidence exposure를 핵심 처리 차이로 둔다."},
      {"question":"pretrend DID가 tolerance를 넘으면?","choices":["rejected이며 certificate 없음","event DID가 크면 무시","자동으로 0으로 수정"],"answer":0,"explanation":"사전 추세 불균형은 registered identification gate 실패다."}
    ]
  }
]);
