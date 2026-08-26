window.LFV_ACADEMY.lessons.push(...[
  {
    "id":"temporal-noninterference",
    "track":"epistemic",
    "order":14,
    "title":"Temporal Noninterference",
    "subtitle":"미래-only 데이터 확장이 과거 signal·order·fill·PnL을 바꾸지 못하게 하는 인과적 안전 성질을 검증합니다.",
    "difficulty":"연구",
    "minutes":42,
    "covers":["temporal-noninterference","epistemic"],
    "prerequisites":["pit-lineage","trace-refinement"],
    "outcomes":[
      "decision cutoff까지 동일한 두 history의 prefix equivalence를 정의한다.",
      "causal transform의 composition theorem을 설명한다.",
      "future-extension metamorphic test와 first-divergence witness를 해석한다."
    ],
    "concepts":["prefix equivalence","temporal noninterference","causal transform","future extension","first divergence","metamorphic oracle"],
    "why":"정답 PnL을 몰라도 미래 row 하나를 추가한 뒤 과거 출력이 바뀌는지 검사하면 future-information contamination을 발견할 수 있다.",
    "assurance":{
      "proves":["동일한 available prefix를 causal transform이 보존하며 causal transforms가 composition됨","controlled fixture에서 future-only extension에 대한 exact output equality 또는 최소 divergence witness"],
      "notProves":["production source의 publication time이 진실임","모든 timezone·calendar·revision semantics가 모델에 포함됨","finite corpus 통과가 모든 입력에서 universal causality를 보장함"]
    },
    "sources":[
      "LeanFinance/Epistemic/TemporalNoninterference.lean",
      "tools/temporal_noninterference/",
      "examples/temporal_noninterference/future_extension.json"
    ],
    "docs":["docs/TEMPORAL_NONINTERFERENCE.md"],
    "commands":[
      "python -m unittest discover -s tools/temporal_noninterference/tests -v",
      "python -m tools.temporal_noninterference analyze --model examples/temporal_noninterference/future_extension.json --out /tmp/temporal-noninterference.json"
    ],
    "challenge":{
      "prompt":"2018년까지 동일한 두 데이터셋 중 하나에 2026년 극단값을 추가했더니 2018년 fill이 바뀌었다. 가장 정확한 판정은?",
      "options":["temporal noninterference 위반","단순 수익률 차이","미래 데이터가 많아져 정상"],
      "answer":0,
      "explanation":"cutoff까지 available prefix가 동일하므로 과거-visible output은 동일해야 한다."
    },
    "quiz":[
      {
        "question":"Causal forward fill이 선택할 수 있는 값은?",
        "choices":["query 시점까지 observation과 availability가 모두 충족된 가장 최근 값","전체 시계열의 마지막 값","가장 가까운 미래 값"],
        "answer":0,
        "explanation":"관측일뿐 아니라 실제 이용 가능 시각도 query cutoff 이전이어야 한다."
      },
      {
        "question":"First-divergence witness의 주된 목적은?",
        "choices":["처음 오염된 출력 시각과 원인을 국소화","최종 Sharpe만 다시 계산","미래 row를 자동 삭제"],
        "answer":0,
        "explanation":"최초 divergence는 최소 재현 trace와 repair 위치를 제공한다."
      }
    ]
  },
  {
    "id":"formula-application-contract",
    "track":"robust",
    "order":14,
    "title":"Proof-Carrying Formula Contract",
    "subtitle":"수식이 맞다는 사실과 그 수식이 올바른 단위·시점·정의역·구현·입출력에 적용됐다는 사실을 분리합니다.",
    "difficulty":"연구",
    "minutes":44,
    "covers":["formula-contract","composition"],
    "prerequisites":["temporal-noninterference","certificate-composition"],
    "outcomes":[
      "formula correctness와 application correctness를 구분한다.",
      "unit·availability·domain·implementation·input·output receipt를 설명한다.",
      "minimum-cost formula application evidence를 exact synthesis한다."
    ],
    "concepts":["unit signature","domain precondition","availability receipt","implementation hash","artifact binding","formula application composition"],
    "why":"같은 올바른 hedge 수식도 percent/decimal 혼동, 미래 risk input, 0 denominator, 구현 drift, artifact substitution 때문에 잘못 적용될 수 있다.",
    "assurance":{
      "proves":["일곱 local application claim이 각각 verifiable할 때 global formula application도 verifiable함","7개 controlled world와 8개 channel에서 exact minimum-cost evidence set"],
      "notProves":["수식이 경제 문제에 적합함","deployed binary hash가 정직하게 측정됨","모든 수치 불안정성과 domain failure가 모델에 포함됨"]
    },
    "sources":[
      "LeanFinance/Formula/Contract.lean",
      "tools/formula_contract/",
      "examples/formula_contract/hedge_scale.json"
    ],
    "docs":["docs/PROOF_CARRYING_FORMULA_CONTRACT.md","docs/CERTIFICATE_COMPOSITION_LAW.md"],
    "commands":[
      "python -m unittest discover -s tools/formula_contract/tests -v",
      "python -m tools.formula_contract analyze --model examples/formula_contract/hedge_scale.json --out /tmp/formula-contract.json"
    ],
    "challenge":{
      "prompt":"수식 theorem과 expression hash가 valid인데 riskPercentage를 0.5 decimal로 넣었고 contract는 50 percent를 요구한다. 무엇이 부족한가?",
      "options":["unitSignatureReceipt","formula theorem 하나 더","result timestamp만"],
      "answer":0,
      "explanation":"같은 숫자 primitive라도 decimal과 percent는 다른 unit contract다."
    },
    "quiz":[
      {
        "question":"Controlled exact minimum architecture의 receipt 수는?",
        "choices":["6개 narrow application receipts","formula summary 1개","global bundle과 formula summary 2개"],
        "answer":0,
        "explanation":"unit, availability, domain, implementation, input, output 여섯 경계를 모두 분리해야 한다."
      },
      {
        "question":"Formula correctness만으로 application correctness가 성립하지 않는 이유는?",
        "choices":["정확한 식도 잘못된 단위·미래 입력·다른 artifact에 적용될 수 있어서","수식은 항상 거짓이라서","SHA-256이 숫자를 계산하지 못해서"],
        "answer":0,
        "explanation":"표현식의 정당성과 특정 invocation의 causal·semantic 정당성은 다른 claim이다."
      }
    ]
  }
]);
