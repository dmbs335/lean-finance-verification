window.LFV_ACADEMY.lessons.push(...[
  {
    "id":"temporal-noninterference",
    "track":"backtest",
    "order":5,
    "title":"Temporal Noninterference",
    "subtitle":"미래 데이터·미래 수정·표현 변경이 과거 signal·order·PnL prefix를 바꾸지 못하게 합니다.",
    "difficulty":"연구",
    "minutes":42,
    "covers":["backtest","pit-study"],
    "prerequisites":["pit-lineage","proof-carrying-certificate"],
    "outcomes":[
      "causal-prefix equivalence와 output-prefix invariance를 정의한다.",
      "causal factorization이 temporal noninterference를 함의하는 Lean 정리를 읽는다.",
      "future extension, future revision, reorder, representation mutation을 이용해 semantic backtest bug를 찾는다.",
      "first-divergence와 minimized mutation witness를 해석한다."
    ],
    "concepts":["causal prefix","temporal noninterference","future-extension invariance","strict availability","metamorphic testing","first divergence","source immutability"],
    "why":"백테스트가 예외 없이 그럴듯한 숫자를 내더라도 미래 행 추가나 데이터 표현만으로 과거 결과가 바뀐다면 인과적 연구 결과가 아니다.",
    "assurance":{
      "proves":["선언된 causal factorization이 past-output temporal noninterference를 함의함","controlled finite engine·mutation corpus에서 exact violation, first divergence와 최소 operation witness를 계산함"],
      "notProves":["외부 library adapter의 정확성","실제 vendor availability timestamp의 진실성","모든 미래정보·동시성·부동소수점 오류의 완전한 탐지"]
    },
    "sources":["LeanFinance/Backtest/TemporalNoninterference.lean","LeanFinance/Backtest/TemporalNoninterferenceExample.lean","tools/temporal_noninterference/","examples/temporal_noninterference/gs_quant_style.json"],
    "docs":["docs/TEMPORAL_NONINTERFERENCE.md"],
    "commands":["python -m unittest discover -s tools/temporal_noninterference/tests -v","python -m tools.temporal_noninterference analyze --model examples/temporal_noninterference/gs_quant_style.json --out /tmp/temporal.json"],
    "challenge":{"prompt":"2026년 극단값 행을 추가했는데 2018년 holiday mark가 달라졌다. causal prefix는 동일하다면 무엇을 의미하나?","options":["temporal noninterference 위반","정상적인 새 정보 반영","portfolio diversification"],"answer":0,"explanation":"결정 당시 이용 가능했던 정보가 동일한데 과거 출력이 달라졌으므로 미래 정보가 past output에 간섭했다."},
    "quiz":[
      {"question":"두 데이터셋의 과거 출력이 같아야 한다는 전제가 성립하려면?","choices":["전체 파일 bytes가 같아야 함","각 audited decision의 causal prefix가 같아야 함","마지막 row만 같아야 함"],"answer":1,"explanation":"미래 부분은 달라도 되지만 각 의사결정까지 실제 이용 가능한 논리 정보는 같아야 한다."},
      {"question":"observation_time이 decision_time과 같지만 available_time이 이후라면?","choices":["strict PIT 입력","결정에 사용할 수 없는 late release","representation-only difference"],"answer":1,"explanation":"사건 시각과 공개·수신 시각은 별개이며 실제 available time이 의사결정 뒤면 미래정보다."}
    ]
  }
]);
