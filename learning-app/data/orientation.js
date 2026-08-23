window.LFV_ACADEMY.lessons.push(...[
  {
    "id":"project-map","track":"orientation","order":1,"title":"프로젝트 전체 지도","subtitle":"금융 모델에서 proof-carrying evidence까지 한 번에 연결합니다.","difficulty":"입문","minutes":18,
    "covers":["core","game-theory","market","constraints","dynamics","inference","strategy-ecology","supply-chain","backtest","certificate","epistemic","generated"],
    "prerequisites":[],
    "outcomes":["LeanFinance.lean의 umbrella 구조를 설명한다.","금융 모델과 검증 이론의 역할을 분리한다.","외부 계산과 Lean kernel의 신뢰 경계를 구분한다."],
    "concepts":["hidden history","observation map","claim","certificate","generated witness"],
    "why":"이 프로젝트는 수익률을 증명하는 라이브러리가 아니라, 금융 연구가 어떤 증거에 의해 어떤 범위에서 검증 가능한지를 모델링한다.",
    "assurance":{"proves":["각 namespace가 담당하는 계약","Lean이 검사하는 명제와 generated witness의 연결"],"notProves":["전략의 미래 수익성","모든 현실 공격의 완전한 열거"]},
    "sources":["LeanFinance.lean","LeanFinance/Core.lean","README.md"],
    "docs":["README.md","docs/EVIDENCE_SEPARATION_THEORY.md"],"commands":["lake build"],
    "challenge":{"prompt":"어떤 설명이 프로젝트의 중심 질문에 가장 가깝나?","options":["다음 달 수익률을 맞힌다","주장의 최소 검증 증거를 합성한다","모든 금융 모델을 하나로 통합한다"],"answer":1,"explanation":"핵심은 예측이 아니라 claim–evidence 관계와 최소 evidence architecture다."},
    "quiz":[
      {"question":"Generated Lean 파일의 주된 역할은?","choices":["Python 최적화 결과를 무조건 신뢰","외부 산출물을 kernel이 다시 검사할 witness로 연결","UI 렌더링"],"answer":1,"explanation":"Generated witness는 외부 계산을 Lean 의미론에 결박한다."},
      {"question":"프로젝트가 직접 증명하지 않는 것은?","choices":["PIT 데이터 사용 계약","선택된 증거의 bounded sufficiency","미래 수익성"],"answer":2,"explanation":"수익성은 empirical claim이며 이 프레임워크의 보증 대상이 아니다."}
    ]
  },
  {
    "id":"lean-reading","track":"orientation","order":2,"title":"Lean 코드 읽기","subtitle":"정의·구조체·정리·실행 가능한 decide 패턴을 읽습니다.","difficulty":"입문","minutes":22,
    "covers":["core","epistemic","generated"],"prerequisites":["project-map"],
    "outcomes":["structure와 Prop-valued certificate의 차이를 읽는다.","by decide가 가능한 bounded proposition을 구분한다.","정리의 가정이 실제 보증 범위를 어떻게 제한하는지 찾는다."],
    "concepts":["structure","Prop","theorem","Decidable","by decide","soundness"],
    "why":"이 저장소는 작은 일반 정리와 finite executable checker를 조합한다. 코드 읽기의 핵심은 결론보다 가정과 universe/bound를 먼저 보는 것이다.",
    "assurance":{"proves":["정리 문장에 명시된 가정 아래의 결론","finite type에서의 kernel computation"],"notProves":["정리 밖의 운영 가정","Python/OpenSSL 구현 전체의 formal verification"]},
    "sources":["LeanFinance/Epistemic/CutSet.lean","LeanFinance/Epistemic/FiniteSynthesis.lean","LeanFinance/Generated/EvidenceSynthesis.lean"],
    "docs":["docs/EVIDENCE_SEPARATION_THEORY.md","docs/EVIDENCE_SYNTHESIS.md"],"commands":["lake env lean LeanFinance/Epistemic/CutSet.lean"],
    "challenge":{"prompt":"`by decide`가 가장 적절한 경우는?","options":["무한 실수 모델의 통계적 타당성","닫힌 finite proposition","외부 TSA의 정직성"],"answer":1,"explanation":"Decidable 인스턴스가 있는 닫힌 유한 명제는 kernel computation으로 닫을 수 있다."},
    "quiz":[
      {"question":"정리의 실제 보증을 읽을 때 먼저 확인할 것은?","choices":["파일 길이","가정과 quantifier","주석 색상"],"answer":1,"explanation":"가정과 quantifier가 theorem의 범위를 결정한다."},
      {"question":"Prop-valued structure의 필드는 일반적으로 무엇이어야 하나?","choices":["증명","임의의 Prop 값","JSON"],"answer":0,"explanation":"Prop-valued 구조체는 proposition의 proof object를 담는다."}
    ]
  },
  {
    "id":"assurance-boundaries","track":"orientation","order":3,"title":"보증 수준과 위협 모델","subtitle":"L1–L4 보증과 residual assumption을 구분합니다.","difficulty":"입문","minutes":20,
    "covers":["backtest","certificate","epistemic","adapter","external-quorum","ci"],"prerequisites":["project-map"],
    "outcomes":["Lean theorem, bounded computation, external verification, operational assumption을 분류한다.","'signed'와 'true'를 구분한다.","검증 결과를 과장하지 않는 보고 형식을 적용한다."],
    "concepts":["L1 theorem","L2 exact bounded","L3 external crypto","L4 operational assumption","TCB"],
    "why":"형식증명은 모델과 입력 경계를 정직하게 만들지만, vendor honesty·provider independence·instrumentation completeness를 자동으로 창조하지 않는다.",
    "assurance":{"proves":["명시된 모델과 입력에 대한 정확한 보증","외부 검증 결과를 normalized proposition으로 연결"],"notProves":["raw data의 경제적 진실성","provider의 실제 독립성","host compromise 부재"]},
    "sources":["LeanFinance/Backtest/IntegrityCertificate.lean","LeanFinance/Epistemic/ProviderQuorum.lean"],
    "docs":["README.md","docs/COUNTEREXAMPLE_GUIDED_EVIDENCE_SYNTHESIS.md","docs/REFERENCE_ADAPTER.md"],"commands":[],
    "challenge":{"prompt":"두 TSA 이름이 다르면 자동으로 두 trust domain인가?","options":["예","아니오"],"answer":1,"explanation":"독립성은 이름이 아니라 운영·관리·인프라에 대한 외부 가정이다."},
    "quiz":[
      {"question":"서명된 vendor package가 직접 증명하는 것은?","choices":["데이터의 경제적 진실","선택된 키가 해당 bytes/manifest를 인증","미래 성과"],"answer":1,"explanation":"서명은 statement authenticity를 보장하지 statement truth를 보장하지 않는다."},
      {"question":"실행 로그 completeness는 주로 어느 수준인가?","choices":["항상 L1","운영·instrumentation 가정이 포함된 L4 경계","UI 기능"],"answer":1,"explanation":"독립 runner가 서명해도 모든 실제 이벤트가 capture되었다는 가정은 남는다."}
    ]
  }
]);
