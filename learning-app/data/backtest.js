window.LFV_ACADEMY.lessons.push(...[
  {
    "id":"artifact-identity","track":"backtest","order":1,"title":"Artifact identity와 canonicalization","subtitle":"코드·데이터·파라미터·환경·결과를 서로 다른 도메인으로 묶습니다.","difficulty":"중급","minutes":26,
    "covers":["backtest","certificate","schemas","adapter"],"prerequisites":["assurance-boundaries"],
    "outcomes":["ArtifactKind와 domain separation의 필요성을 설명한다.","canonical bytes와 logical meaning을 구분한다.","digest가 증명하는 것과 못하는 것을 말한다."],
    "concepts":["ArtifactRef","ArtifactKind","schemaId","canonical JSON","domain separation","digest"],
    "why":"같은 hash 문자열만 저장하면 code/data/result 간 type confusion과 schema confusion이 생길 수 있다.",
    "assurance":{"proves":["선택된 canonical bytes와 artifact kind의 동일성"],"notProves":["bytes의 진실성","canonicalizer 자체의 무결성"]},
    "sources":["LeanFinance/Backtest/Artifact.lean","LeanFinance/Backtest/IntegrityCertificate.lean","LeanFinance/Certificate/Verification.lean","tools/lfv_adapter/canonical.py"],"docs":["docs/REFERENCE_ADAPTER.md"],"commands":["python -m tools.lfv_adapter --help"],
    "challenge":{"prompt":"동일 digest를 서로 다른 artifact kind에서 그대로 비교하면 생길 수 있는 문제는?","options":["domain confusion","유동성 증가","Bayesian update"],"answer":0,"explanation":"kind와 schema를 digest domain에 포함해야 type confusion을 줄일 수 있다."},
    "quiz":[{"question":"Hash가 직접 보장하지 않는 것은?","choices":["bytes 동일성","raw data의 경제적 진실성","tamper detection"],"answer":1,"explanation":"hash는 입력 bytes에 대한 commitment다."},{"question":"이 레슨의 명시적 보증 경계 밖에 있는 것은?","choices":["bytes의 진실성","선택된 canonical bytes와 artifact kind의 동일성","ArtifactKind와 domain separation의 필요성"],"answer":0,"explanation":"bytes의 의미적 진실성은 별도 경계다."}]
  },
  {
    "id":"pit-lineage","track":"backtest","order":2,"title":"PIT lineage와 feature closure","subtitle":"각 feature가 생성 당시 이용 가능했던 입력만 재귀적으로 사용했는지 확인합니다.","difficulty":"중급","minutes":30,
    "covers":["backtest","pit-study","examples"],"prerequisites":["artifact-identity"],
    "outcomes":["availability time과 event time을 구분한다.","recursive lineage closure를 설명한다.","survivorship bias와 revision leakage를 fixture에서 찾는다."],
    "concepts":["event time","availableAt","generatedAt","lineage closure","revision","universe snapshot"],
    "why":"미래정보 사용은 raw row 하나뿐 아니라 derived feature의 조상 전체에서 발생할 수 있다.",
    "assurance":{"proves":["선언된 lineage graph의 모든 입력이 cutoff 이전이라는 사실","exact universe fixture consistency"],"notProves":["vendor timestamp의 진실성","누락된 lineage edge 부재"]},
    "sources":["LeanFinance/Backtest/FeatureLineage.lean","LeanFinance/Backtest/LineageClosure.lean","LeanFinance/Backtest/NoFutureInformation.lean","LeanFinance/Backtest/PointInTimeData.lean","tools/pit_study/"],"docs":["docs/POINT_IN_TIME_DATA_CONTRACTS.md"],"commands":["python -m unittest discover -s tools/pit_study/tests -v"],
    "challenge":{"prompt":"feature F가 cutoff 이전에 생성됐지만 입력 G가 미래 revision이면?","options":["안전","lineage closure 위반","hash가 자동 수정"],"answer":1,"explanation":"F의 timestamp만 보지 않고 모든 ancestor availability를 검사해야 한다."},
    "quiz":[{"question":"Universe snapshot의 역할은?","choices":["해당 시점 eligible asset 집합 고정","TSA key rotation","proof search"],"answer":0,"explanation":"당시 존재하고 거래 가능한 자산 집합을 고정한다."},{"question":"이 레슨의 명시적 보증 경계 밖에 있는 것은?","choices":["vendor timestamp의 진실성","선언된 lineage graph의 cutoff 적합성","exact universe fixture consistency"],"answer":0,"explanation":"vendor statement의 진실성은 인증과 별개다."}]
  },
  {
    "id":"committed-search","track":"backtest","order":3,"title":"Committed search ledger","subtitle":"선택된 trial뿐 아니라 전체 탐색 prefix와 anchor를 검증합니다.","difficulty":"중급","minutes":28,
    "covers":["backtest","adapter","external-quorum"],"prerequisites":["artifact-identity"],
    "outcomes":["trial chain과 commitment를 설명한다.","선택 trial membership과 search completeness를 구분한다.","pre-decision anchor의 역할을 설명한다."],
    "concepts":["SearchLedger","Trial","commitment chain","anchor","selected trial","completeness"],
    "why":"결과 하나만 재현 가능해도 수많은 실패 trial을 숨겼다면 선택편향은 남는다.",
    "assurance":{"proves":["선택 trial이 committed ledger에 포함됨","ledger prefix가 anchor target과 일치함"],"notProves":["instrumentation 밖 trial 부재","provider honesty"]},
    "sources":["LeanFinance/Backtest/SearchLedger.lean","LeanFinance/Backtest/CommittedSearchLedger.lean","tools/lfv_adapter/"],"docs":["docs/REFERENCE_ADAPTER.md","docs/RFC3161_ANCHORS.md"],"commands":["python -m tools.lfv_adapter check-generated --help"],
    "challenge":{"prompt":"선택 trial이 ledger에 존재한다는 사실만으로 hidden trial 부재가 증명되나?","options":["예","아니오"],"answer":1,"explanation":"membership는 completeness와 다르다. 독립 실행 관측이 필요하다."},
    "quiz":[{"question":"pre-decision anchor가 막는 핵심 공격은?","choices":["결과를 본 뒤 ledger prefix 재작성","시장 가격 변화","Lean type error"],"answer":0,"explanation":"외부 존재 시각은 사후 ledger construction을 제한한다."},{"question":"이 레슨의 명시적 보증 경계 밖에 있는 것은?","choices":["instrumentation 밖 trial 부재","선택 trial membership","anchor target 일치"],"answer":0,"explanation":"관측되지 않은 실행 부재는 self-certified할 수 없다."}]
  },
  {
    "id":"proof-carrying-certificate","track":"backtest","order":4,"title":"Proof-carrying certificate와 adapter","subtitle":"외부 empirical execution을 Lean contract로 넘기는 전체 handoff를 봅니다.","difficulty":"고급","minutes":32,
    "covers":["backtest","certificate","adapter","generated","ci"],"prerequisites":["pit-lineage","committed-search"],
    "outcomes":["adapter의 untrusted/trusted boundary를 그린다.","canonical bundle과 generated Lean witness의 연결을 설명한다.","재생성 검사의 의미를 말한다."],
    "concepts":["adapter contract","bundle","generated witness","soundness","reproducibility"],
    "why":"외부 프로그램은 값을 계산하지만, Lean은 그 값에 붙은 논리 계약을 검사한다.",
    "assurance":{"proves":["generated witness가 formal contract를 만족","checked-in artifact와 재생성 결과 일치"],"notProves":["외부 계산의 통계적 타당성","host/compiler compromise 부재"]},
    "sources":["LeanFinance/Backtest/AdapterContract.lean","LeanFinance/Backtest/Certificate.lean","LeanFinance/Generated/ReferenceAdapter.lean","tools/lfv_adapter/"],"docs":["docs/REFERENCE_ADAPTER.md","README.md"],"commands":["python -m tools.lfv_adapter build --spec examples/reference_adapter/experiment.json --out /tmp/lfv-learning --allow-local-anchor","lake build"],
    "challenge":{"prompt":"Adapter를 trusted optimizer로 볼 필요가 없는 이유는?","options":["Lean이 최종 contract를 재검사할 수 있어서","Python은 항상 정확해서","JSON은 증명이어서"],"answer":0,"explanation":"adapter 산출물은 witness이며 Lean checker가 의미론을 검증한다."},
    "quiz":[{"question":"byte-for-byte regeneration이 주로 잡는 것은?","choices":["generator drift와 checked-in artifact 불일치","미래 profitability","provider collusion"],"answer":0,"explanation":"동일 입력에서 동일 산출물이 나오는지 확인한다."},{"question":"이 레슨의 명시적 보증 경계 밖에 있는 것은?","choices":["외부 계산의 통계적 타당성","generated witness contract","artifact 재생성 일치"],"answer":0,"explanation":"통계적 타당성은 별도 empirical claim이다."}]
  }
]);
