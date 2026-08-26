window.LFV_ACADEMY.lessons.push(...[
  {
    "id":"formula-contract","track":"robust","order":15,
    "title":"Proof-Carrying Formula Contract",
    "subtitle":"수식의 대수적 정확성과 실제 금융 적용의 시점·단위·모델·artifact binding을 분리합니다.",
    "difficulty":"연구","minutes":40,
    "covers":["backtest","composition"],
    "prerequisites":["temporal-noninterference","certificate-composition"],
    "outcomes":["formula correctness와 application correctness를 구분한다.","hedge scale의 preregistration·unit·time·model·domain obligation을 검사한다.","exact rational output을 input/output artifact에 binding한다."],
    "concepts":["formula definition","application contract","unit signature","domain precondition","implementation hash","result binding"],
    "why":"올바른 식으로 올바른 숫자를 계산해도 미래 input, 통화 불일치, 다른 risk-model version, 늦게 등록된 formula, 다른 result artifact를 사용했다면 금융 claim은 잘못된다.",
    "assurance":{"proves":["registered hedge-scale formula의 complete application obligations","formula와 결과가 맞지만 미래 input 때문에 application이 invalid인 Lean counterexample","canonical JSON corpus의 exact deterministic verdict"],"notProves":["외부 risk model 자체의 정확성","hedge의 경제적 최적성","모든 금융 unit vocabulary의 완전성"]},
    "sources":["LeanFinance/Formula/Contract.lean","LeanFinance/Formula/ContractExample.lean","tools/formula_contract/","examples/formula_contract/hedge_scale.json"],
    "docs":["docs/PROOF_CARRYING_FORMULA_CONTRACTS.md","docs/CAUSAL_FINANCIAL_COMPUTATION.md"],
    "commands":["python -m unittest discover -s tools/formula_contract/tests -v","python -m tools.formula_contract analyze --model examples/formula_contract/hedge_scale.json --out /tmp/formula.json"],
    "challenge":{"prompt":"수식 hash와 결과 3/4가 정확하지만 current risk가 decision 뒤 공개됐다면?","options":["application invalid","formula가 맞으므로 certified","unit만 맞으면 certified"],"answer":0,"explanation":"대수적 correctness와 temporal admissibility는 별도 gate다."},
    "quiz":[{"question":"hedge-scale에서 current risk와 hedge risk가 만족해야 할 조건은?","choices":["같은 risk unit·valuation time·model version","값의 부호가 같음","artifact hash가 동일함"],"answer":0,"explanation":"비율을 의미 있게 만들려면 비교 가능한 위험량이어야 한다."},{"question":"Formula Correct ⇒ Application Correct가 아닌 이유는?","choices":["입력 시점·단위·domain·binding이 별도 명제라서","수학식은 항상 틀려서","SHA-256이 확률적이라서"],"answer":0,"explanation":"정확한 식도 잘못된 객체나 미래 값에 적용될 수 있다."}]
  }
]);
