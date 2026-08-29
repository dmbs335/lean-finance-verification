window.LFV_ACADEMY.lessons.push(...[
  {
    "id":"pnl-explain-closure",
    "track":"finance",
    "order":15,
    "title":"Proof-Carrying PnL Explain Closure",
    "subtitle":"1·2차 risk attribution, non-market PnL, residual과 same-pipeline binding을 하나의 closure certificate로 묶습니다.",
    "difficulty":"연구",
    "minutes":42,
    "covers":["pnl-explain","formula-contract","composition","backtest"],
    "prerequisites":["formula-contract","certificate-composition","temporal-noninterference"],
    "outcomes":[
      "GS Quant-style 1·2차 attribution을 local quadratic formula로 해석한다.",
      "다중 포지션의 유지·부분 청산 경로를 실제 공개 메서드와 exact checker로 대조한다.",
      "accounting identity와 bounded explanatory closure를 구분한다.",
      "동일 portfolio·market snapshot·model version binding이 왜 별도 의무인지 설명한다.",
      "CLOSED, PARTIAL, OPEN 상태를 exact checker로 재현한다."
    ],
    "concepts":["Taylor attribution","first order","second order","partial exit","portfolio transition","residual bound","PnL closure","model revision","same-pipeline binding"],
    "why":"각 risk term의 산술이 맞아도 서로 다른 portfolio나 model snapshot에서 가져오면 전체 PnL 설명은 거짓일 수 있다. 작은 residual만으로 cross-object substitution을 정당화할 수 없다.",
    "assurance":{
      "proves":["선언된 local quadratic integer model의 exact closure","controlled cases의 formula·time·binding·residual gate와 CLOSED certificate consequences"],
      "notProves":["실제 pricing function의 전역 quadratic성","higher-order Taylor remainder의 실증 상한","production portfolio 객체와 Goldman Sachs 내부 서비스의 의미론"]
    },
    "sources":[
      "LeanFinance/PnL/Closure.lean",
      "LeanFinance/PnL/ClosureExample.lean",
      "tools/pnl_explain_closure/",
      "examples/pnl_explain_closure/controlled.json",
      "examples/pnl_explain_closure/gs_quant_conformance.json",
      "examples/pnl_explain_closure/generated/gs-quant-conformance.canonical.json"
    ],
    "docs":["docs/PNL_EXPLAIN_CLOSURE.md"],
    "commands":[
      "python -m unittest discover -s tools/pnl_explain_closure/tests -v",
      "python -m tools.pnl_explain_closure analyze --model examples/pnl_explain_closure/controlled.json --out /tmp/pnl-explain-closure.json",
      "python -m tools.pnl_explain_closure gs-quant-conformance --model examples/pnl_explain_closure/gs_quant_conformance.json --out /tmp/gs-quant-pnl-conformance.json"
    ],
    "challenge":{
      "prompt":"모든 1·2차 attribution 산술이 맞고 residual도 0이지만 한 factor가 다른 portfolio hash를 가리킨다. 상태는?",
      "options":["OPEN","CLOSED","PARTIAL"],
      "answer":0,
      "explanation":"formula correctness와 same-pipeline binding은 별도 claim이며 binding 실패는 residual 크기와 무관하게 OPEN이다."
    },
    "quiz":[
      {
        "question":"Residual = realized - reconstructed는 왜 그 자체로 설명의 타당성을 증명하지 못하나?",
        "choices":["정의상 항상 계산 가능하며 residual bound와 binding이 별도로 필요해서","음수 PnL을 허용하지 않아서","Taylor 식에 cash가 없어서"],
        "answer":0,
        "explanation":"accounting difference를 계산하는 것과 선택한 basis가 충분하고 같은 객체를 설명하는 것은 다른 문제다."
      },
      {
        "question":"Controlled local quadratic theorem이 직접 증명하지 않는 것은?",
        "choices":["실제 가격함수의 higher-order remainder가 작음","등록된 정수 expression의 exact arithmetic","CLOSED certificate가 tolerance를 만족함"],
        "answer":0,
        "explanation":"실제 pricing surface의 smoothness와 3차 이상 미분 상한은 외부 이론·실증 의무다."
      }
    ]
  }
]);
