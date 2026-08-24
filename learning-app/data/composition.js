window.LFV_ACADEMY.lessons.push(...[
  {
    "id":"certificate-composition",
    "track":"robust",
    "order":13,
    "title":"Certificate Composition Law",
    "subtitle":"모든 local certificate가 green이어도 cross-boundary binding이 없으면 global claim이 깨질 수 있음을 증명합니다.",
    "difficulty":"연구",
    "minutes":38,
    "covers":["epistemic","composition"],
    "prerequisites":["multi-claim"],
    "outcomes":[
      "local claim과 bridge claim을 분리한다.",
      "local-pass summary가 global pipeline을 검증하지 못하는 counterexample를 읽는다.",
      "minimum-cost binding receipt architecture를 exact synthesis한다."
    ],
    "concepts":["local certificate","bridge claim","object identity","cross-boundary substitution","composition theorem","binding receipt"],
    "why":"dataset, decision, result가 각각 유효해도 서로 다른 객체를 가리키면 전역 연구 claim은 거짓일 수 있다. 로컬 증명을 연결하는 causal binding이 별도 의무다.",
    "assurance":{
      "proves":["세 local claim과 두 bridge claim이 각각 verifiable할 때 global conjunction도 verifiable함","controlled world/channel language에서 minimum-cost bridge set과 lower-cost counterexample"],
      "notProves":["local certificate 의미의 현실 완전성","digest가 올바른 causal boundary에서 측정됐음","모델 밖 substitution attack 부재"]
    },
    "sources":[
      "LeanFinance/Epistemic/CertificateComposition.lean",
      "tools/certificate_composition/",
      "examples/certificate_composition/research_bundle.json"
    ],
    "docs":["docs/CERTIFICATE_COMPOSITION_LAW.md"],
    "commands":[
      "python -m unittest discover -s tools/certificate_composition/tests -v",
      "python -m tools.certificate_composition analyze --model examples/certificate_composition/research_bundle.json --out /tmp/certificate-composition.json"
    ],
    "challenge":{
      "prompt":"dataset·decision·result certificate가 모두 valid인데 global claim이 false일 수 있는 가장 직접적인 이유는?",
      "options":["서로 다른 객체에 대한 local certificate를 조합했기 때문","certificate 수가 홀수라서","Lean file이 분리돼 있어서"],
      "answer":0,
      "explanation":"각 local claim의 진실성과 그 certificate들이 같은 causal pipeline을 가리킨다는 binding은 다른 명제다."
    },
    "quiz":[
      {
        "question":"Controlled fixture의 exact minimum architecture는?",
        "choices":["localValiditySummary","두 narrow binding receipts","global bundle과 local summary","아무 evidence도 없음"],
        "answer":1,
        "explanation":"data→decision과 decision→result 경계를 각각 묶는 두 receipt가 cost 4로 모든 global disagreement를 분리한다."
      },
      {
        "question":"Global bundle 하나도 claim을 검증하지만 minimum이 아닌 이유는?",
        "choices":["cost 6으로 두 narrow receipts의 cost 4보다 비싸서","hash가 없어서","local certificate를 무효화해서"],
        "answer":0,
        "explanation":"full bundle은 충분하지만 controlled cost model에서는 더 좁은 boundary receipts가 저렴하다."
      }
    ]
  }
]);
