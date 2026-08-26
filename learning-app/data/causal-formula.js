window.LFV_ACADEMY.lessons.push(...[
  {
    "id":"temporal-noninterference","track":"backtest","order":8,
    "title":"Temporal Noninterference",
    "subtitle":"미래 확장과 unavailable input이 과거 signal·position을 바꾸지 못하는지 metamorphic하게 검증합니다.",
    "difficulty":"연구","minutes":42,
    "covers":["backtest","temporal-noninterference"],
    "prerequisites":["pit-lineage","evidence-equivalence"],
    "outcomes":["available-prefix equivalence를 정의한다.","future-extension과 availability-projection oracle을 구분한다.","first-divergence witness로 noncausal transform을 찾는다."],
    "concepts":["temporal noninterference","causal transform","future-extension invariance","availability projection","source immutability","first divergence"],
    "why":"최종 데이터에 미래 날짜가 없어 보여도 fill·interpolation·전역 정규화가 미래 값을 과거 판단에 전파할 수 있다. 계산 전체의 causal prefix가 보존돼야 한다.",
    "assurance":{"proves":["prefix-safe feature와 prefix-causal consumer의 composition theorem","controlled finite histories에서 exact temporal and mutation verdict"],"notProves":["임의의 외부 엔진이 adapter 없이 causal함","모델 밖 data transformation 부재","시장 데이터의 진실성"]},
    "sources":["LeanFinance/Backtest/TemporalNoninterference.lean","LeanFinance/Backtest/TemporalNoninterferenceExample.lean","tools/temporal_noninterference/","examples/temporal_noninterference/gs_quant_generic_data_source.json"],
    "docs":["docs/TEMPORAL_NONINTERFERENCE.md","docs/CAUSAL_FINANCIAL_COMPUTATION.md"],
    "commands":["python -m unittest discover -s tools/temporal_noninterference/tests -v","python -m tools.temporal_noninterference analyze --model examples/temporal_noninterference/gs_quant_generic_data_source.json --out /tmp/temporal.json"],
    "challenge":{"prompt":"2018년까지 동일한 두 dataset 중 하나에 2026년 극단값을 추가했더니 2018년 position이 바뀌었다. 깨진 성질은?","options":["temporal noninterference","portfolio permutation","hash collision"],"answer":0,"explanation":"decision cutoff 뒤의 정보가 cutoff 이전 출력에 영향을 주었으므로 future-extension invariance가 깨졌다."},
    "quiz":[{"question":"두 dataset이 cutoff까지 equivalent하다는 뜻은?","choices":["cutoff까지 available했던 모든 input 값이 같음","전체 파일 hash가 같음","미래 row 수도 같음"],"answer":0,"explanation":"미래 부분은 달라도 되지만 당시 이용 가능했던 prefix는 같아야 한다."},{"question":"source mutation을 temporal verdict와 따로 검사하는 이유는?","choices":["한 query 값은 같아도 삽입된 row가 뒤의 feature를 오염시킬 수 있어서","파일 크기를 줄이려고","unit 변환을 위해"],"answer":0,"explanation":"관찰이 원본을 바꾸면 이후 계산의 입력 세계 자체가 달라진다."}]
  },
  {
    "id":"formula-contract","track":"robust","order":14,
    "title":"Proof-Carrying Formula Contract",
    "subtitle":"수식의 대수적 정확성과 실제 금융 적용의 시점·단위·모델·artifact binding을 분리합니다.",
    "difficulty":"연구","minutes":40,
    "covers":["formula-contract","composition"],
    "prerequisites":["temporal-noninterference","certificate-composition"],
    "outcomes":["formula correctness와 application correctness를 구분한다.","hedge scale의 unit·time·model·domain obligation을 검사한다.","exact rational output을 input artifact에 binding한다."],
    "concepts":["formula definition","application contract","unit signature","domain precondition","implementation hash","result binding"],
    "why":"올바른 식으로 올바른 숫자를 계산해도 미래 input, 통화 불일치, 다른 risk-model version, 다른 실행 결과를 사용했다면 금융 claim은 잘못된다.",
    "assurance":{"proves":["registered hedge-scale formula의 complete application obligations","formula와 결과가 맞지만 미래 input 때문에 application이 invalid인 counterexample"],"notProves":["외부 risk model 자체의 정확성","hedge의 경제적 최적성","모든 금융 unit vocabulary의 완전성"]},
    "sources":["LeanFinance/Formula/Contract.lean","LeanFinance/Formula/ContractExample.lean","tools/formula_contract/","examples/formula_contract/hedge_scale.json"],
    "docs":["docs/PROOF_CARRYING_FORMULA_CONTRACTS.md","docs/CAUSAL_FINANCIAL_COMPUTATION.md"],
    "commands":["python -m unittest discover -s tools/formula_contract/tests -v","python -m tools.formula_contract analyze --model examples/formula_contract/hedge_scale.json --out /tmp/formula.json"],
    "challenge":{"prompt":"수식 hash와 결과 3/4가 정확하지만 current risk가 decision 뒤 공개됐다면?","options":["application invalid","formula가 맞으므로 certified","unit만 맞으면 certified"],"answer":0,"explanation":"대수적 correctness와 temporal admissibility는 별도 gate다."},
    "quiz":[{"question":"hedge-scale에서 current risk와 hedge risk가 만족해야 할 조건은?","choices":["같은 risk unit·valuation time·model version","값의 부호가 같음","artifact hash가 동일함"],"answer":0,"explanation":"비율을 의미 있게 만들려면 비교 가능한 위험량이어야 한다."},{"question":"Formula Correct ⇒ Application Correct가 아닌 이유는?","choices":["입력 시점·단위·domain·binding이 별도 명제라서","수학식은 항상 틀려서","SHA-256이 확률적이라서"],"answer":0,"explanation":"정확한 식도 잘못된 객체나 미래 값에 적용될 수 있다."}]
  }
]);
