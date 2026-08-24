window.LFV_ACADEMY.lessons.push(...[
  {
    "id":"certifiable-alpha","track":"finance","order":7,"title":"Certifiable Alpha","subtitle":"관측된 초과수익과 증거로 방어 가능한 알파 구간을 분리합니다.","difficulty":"고급","minutes":32,
    "covers":["epistemic","backtest"],"prerequisites":["evidence-debt","version-space"],
    "outcomes":["observed, economic, certifiable alpha를 구분한다.","증거가 가능한 history/model space를 어떻게 줄이는지 설명한다.","점 추정치보다 certifiable interval이 정직한 이유를 말한다."],
    "concepts":["RealizedAlpha","CertifiableAlpha","EvidenceState","lower bound","model space","history space"],
    "why":"같은 백테스트 수익률도 숨은 탐색·미래정보·모델 불확실성이 남아 있으면 투자자가 방어할 수 있는 알파는 달라진다.",
    "assurance":{"proves":["선언된 evidence refinement가 admissible history/model 수를 늘리지 않는다는 구조적 결과"],"notProves":["실제 미래 기대수익률","현실 시장에서의 정확한 alpha lower bound"]},
    "sources":["LeanFinance/Alpha/Certifiable.lean","LeanFinance/Alpha.lean"],"docs":["docs/FORMAL_CLAIMS.md"],"commands":["lake env lean LeanFinance/Alpha/Certifiable.lean"],
    "challenge":{"prompt":"백테스트 8%와 certifiable alpha가 다른 가장 직접적인 이유는?","options":["같은 결과를 만든 숨은 history가 여러 개일 수 있어서","Int가 실수보다 작아서","Lean 파일이 짧아서"],"answer":0,"explanation":"증거가 구분하지 못하는 조작 history가 남아 있으면 8% 전체를 방어할 수 없다."},
    "quiz":[{"question":"강한 증거가 직접 줄이는 것은?","choices":["허용 가능한 history/model space","시장 변동성 자체","모든 거래비용"],"answer":0,"explanation":"증거는 가능한 설명 집합을 줄이지 미래 시장을 고정하지 않는다."},{"question":"Certifiable alpha가 증명하지 않는 것은?","choices":["미래 수익의 확정","선언된 모델 안의 구간 의미","증거 상태와 알파 해석의 연결"],"answer":0,"explanation":"미래 수익성과 일반화는 별도 통계·시장 가정이다."}]
  },
  {
    "id":"fake-alpha","track":"finance","order":8,"title":"Fake Alpha Benchmark","subtitle":"알려진 조작을 주입하고 최소 증거로 clean alpha ranking을 복구합니다.","difficulty":"고급","minutes":38,
    "covers":["backtest","epistemic","examples"],"prerequisites":["certifiable-alpha","pit-lineage","committed-search"],
    "outcomes":["미래정보·생존편향·parameter mining·평가 변경이 alpha를 어떻게 부풀리는지 계산한다.","미검출 distortion을 interval width로 읽는다.","최소 evidence portfolio와 lower-cost counterexample을 해석한다."],
    "concepts":["future information","survivorship bias","parameter mining","cost mutation","benchmark switching","ranking recovery"],
    "why":"가짜 알파 탐지 능력을 주장하려면 ground truth가 알려진 controlled injection benchmark가 먼저 필요하다.",
    "assurance":{"proves":["선언된 distortion과 detection map 아래 최소비용 evidence가 clean ranking을 정확히 복구함"],"notProves":["현실의 모든 조작 유형 완전성","실제 전략 alpha의 정확한 분해"]},
    "sources":["LeanFinance/Alpha/FakeAlphaBenchmark.lean","tools/fake_alpha_benchmark/","examples/fake_alpha/controlled.json"],"docs":["docs/FAKE_ALPHA_EXECUTABLE_BENCHMARK.md"],"commands":["python -m unittest discover -s tools/fake_alpha_benchmark/tests -v","python -m tools.fake_alpha_benchmark analyze --benchmark examples/fake_alpha/controlled.json --out /tmp/fake-alpha.json"],
    "challenge":{"prompt":"60 bps clean alpha가 1,660 bps로 보인 compound attack을 바로 믿으면 안 되는 이유는?","options":["1,600 bps가 선언된 연구 distortion에서 왔기 때문","basis point는 수익률이 아니기 때문","JSON은 신뢰할 수 없기 때문"],"answer":0,"explanation":"controlled benchmark에서는 observed-clean 차이의 원인이 명시적으로 알려져 있다."},
    "quiz":[{"question":"선택 증거가 일부 distortion만 검출하면 interval upper endpoint는?","choices":["미검출 inflation을 포함한 채 남음","무조건 clean alpha","항상 0"],"answer":0,"explanation":"검출하지 못한 조작은 제거할 근거가 없으므로 구간 폭으로 남는다."},{"question":"benchmark 결과의 외삽 한계는?","choices":["현실의 미지 공격까지 자동 탐지한다고 말할 수 없음","정확한 finite optimum을 말할 수 없음","ranking을 계산할 수 없음"],"answer":0,"explanation":"정확성은 주입된 distortion 및 후보 evidence language에 상대적이다."}]
  },
  {
    "id":"evidence-adjusted-portfolio","track":"finance","order":9,"title":"Evidence-Adjusted Portfolio","subtitle":"수익·위험뿐 아니라 certifiable lower bound, evidence debt와 공통 의존성을 함께 최적화합니다.","difficulty":"고급","minutes":36,
    "covers":["market","epistemic"],"prerequisites":["certifiable-alpha","connectivity-robustness"],
    "outcomes":["raw-alpha optimum과 evidence-adjusted optimum이 달라질 수 있음을 설명한다.","shared vendor/model domain을 숨은 concentration risk로 계산한다.","objective weight가 금융 법칙이 아니라 governance input임을 구분한다."],
    "concepts":["certifiable lower bound","evidence debt","robustness","dependency concentration","portfolio objective"],
    "why":"낮은 return correlation만으로는 같은 데이터·모델·provider 실패에 함께 노출된 전략을 분산했다고 볼 수 없다.",
    "assurance":{"proves":["선언된 정수 objective와 finite 후보에서의 exact optimum","다른 조건이 같을 때 dependency concentration 증가가 score를 높이지 못함"],"notProves":["evidence debt의 시장가격","선택된 weight가 모든 투자자에게 최적임"]},
    "sources":["LeanFinance/Portfolio/EvidenceAdjusted.lean","LeanFinance/Portfolio/ExactEvidenceAdjusted.lean","tools/evidence_portfolio/","examples/evidence_portfolio/hidden_common_risk.json"],"docs":["docs/EVIDENCE_ADJUSTED_PORTFOLIO_SYNTHESIS.md"],"commands":["python -m unittest discover -s tools/evidence_portfolio/tests -v"],
    "challenge":{"prompt":"관측 alpha가 가장 큰 두 전략이 같은 vendor를 공유한다면 evidence-adjusted optimizer가 볼 추가 비용은?","options":["dependency concentration","무위험수익률만","파일 수"],"answer":0,"explanation":"공통 evidence domain은 methodology shock의 동시 실패 경로가 된다."},
    "quiz":[{"question":"Controlled fixture에서 raw objective가 고른 것은?","choices":["vendorValue + vendorMomentum","independentTrend + independentQuality","전략 하나도 선택하지 않음"],"answer":0,"explanation":"headline alpha와 conventional risk만 보면 공통 vendor 조합이 우세하다."},{"question":"Evidence-adjusted optimum이 실제 시장에서 더 높은 수익을 보장하나?","choices":["아니다. 선언 objective 안의 exact optimum이다","항상 그렇다","Lean이므로 미래도 고정된다"],"answer":0,"explanation":"실제 preference와 risk price는 empirical/governance boundary다."}]
  },
  {
    "id":"certifiability-crowding","track":"finance","order":10,"title":"Certifiability–Crowding Law","subtitle":"강한 검증이 자본을 끌어들여 capacity-limited alpha를 소모하는 역설을 분석합니다.","difficulty":"연구","minutes":38,
    "covers":["market","strategy-ecology","epistemic"],"prerequisites":["evidence-adjusted-portfolio","strategy-ecology"],
    "outcomes":["evidence confidence→allocation→impact→deployable alpha 경로를 그린다.","knowledge gain과 deployable alpha decay가 동시에 가능함을 설명한다.","zero-impact control이 필요한 이유를 말한다."],
    "concepts":["certifiability","allocator confidence","capacity","crowding cost","deployable alpha","zero-impact control"],
    "why":"검증은 알파를 파괴하는 것이 아니라 더 투자 가능하게 만들며, 그 결과 유한한 기회의 capacity가 소모될 수 있다.",
    "assurance":{"proves":["고정 economic alpha와 비음수 allocation/impact response에서 confidence 증가가 deployable alpha를 늘리지 못함"],"notProves":["실제 allocator response 크기","검증된 모든 전략의 alpha가 반드시 감소함"]},
    "sources":["LeanFinance/Alpha/CertifiabilityCrowding.lean","tools/certifiability_crowding/","examples/certifiability_crowding/capacity.json"],"docs":["docs/CERTIFIABILITY_CROWDING_LAW.md"],"commands":["python -m unittest discover -s tools/certifiability_crowding/tests -v"],
    "challenge":{"prompt":"검증 후 deployable alpha가 줄기 위한 필수 연결고리는?","options":["자본 유입과 market impact/capacity","더 긴 README","낮은 hash cost"],"answer":0,"explanation":"impact가 0이면 allocation이 늘어도 alpha는 그대로인 control이 이를 보여준다."},
    "quiz":[{"question":"limitedCapacitySignal에서 지식은 개선되지만 alpha가 음수가 되는 이유는?","choices":["유입 자본이 좁은 capacity를 크게 초과해 impact가 커짐","economic alpha가 처음부터 0","증거가 수익을 직접 삭제"],"answer":0,"explanation":"원인은 검증 자체가 아니라 검증이 유발한 allocation과 capacity channel이다."},{"question":"이 정리를 실제 법칙으로 부르기 전에 필요한 것은?","choices":["dated credibility shocks, flows, capacity와 impact의 실증","더 많은 색상","Int를 Float로 변경"],"answer":0,"explanation":"구조적 가능성과 현실의 효과 크기는 구분해야 한다."}]
  },
  {
    "id":"epistemic-liquidation","track":"finance","order":11,"title":"Epistemic Liquidation","subtitle":"공통 연구근거의 붕괴가 저상관 전략의 동시 청산과 2차 contagion을 만드는 경로를 봅니다.","difficulty":"연구","minutes":40,
    "covers":["market","constraints","dynamics"],"prerequisites":["certifiability-crowding","constraints-dynamics"],
    "outcomes":["return correlation과 evidence dependency correlation을 구분한다.","1차 evidence withdrawal과 2차 margin contagion을 분리한다.","실증 가능한 hidden-common-risk 예측을 만든다."],
    "concepts":["methodology shock","evidence dependency","synchronized withdrawal","price impact","margin feedback","tail correlation"],
    "why":"서로 다른 종목·factor를 거래해도 같은 vendor나 research engine에 의존하면 방법론 충격 때 함께 신뢰를 잃을 수 있다.",
    "assurance":{"proves":["선언된 충격·withdrawal·impact 식에서의 구조적 양의 반응","controlled scenario의 deterministic 결과"],"notProves":["실제 시장에서 vendor shock가 tail event를 일으켰다는 인과 추정","현실 parameter calibration"]},
    "sources":["LeanFinance/Market/EpistemicCrowding.lean","LeanFinance/Market/EpistemicLiquidation.lean","tools/epistemic_liquidation/","examples/epistemic_liquidation/shared_vendor_shock.json"],"docs":["docs/EPISTEMIC_LIQUIDATION_DYNAMICS.md"],"commands":["python -m unittest discover -s tools/epistemic_liquidation/tests -v"],
    "challenge":{"prompt":"return correlation이 낮은 두 전략이 동시에 청산될 수 있는 숨은 경로는?","options":["공통 evidence domain 실패","서로 다른 ticker 이름","낮은 quiz 점수"],"answer":0,"explanation":"공통 vendor·engine·provider는 과거 수익 상관과 별개의 동시 신뢰 붕괴 경로다."},
    "quiz":[{"question":"independentTrend가 1차 withdrawal은 피하고도 손실을 볼 수 있는 이유는?","choices":["다른 전략의 매도가 가격을 움직여 margin feedback이 전염될 수 있어서","같은 vendor를 사용해서","수익 상관이 1이어서"],"answer":0,"explanation":"시장 impact는 evidence-independent strategy에도 2차로 전파될 수 있다."},{"question":"Epistemic liquidation을 실증하려면 추가로 통제해야 할 것은?","choices":["holdings·factor·liquidity crowding과 ordinary performance chasing","HTML 문법만","TSA nonce만"],"answer":0,"explanation":"기존 crowding 경로와 구분해야 evidence dependency의 추가 설명력을 판단할 수 있다."}]
  }
]);
