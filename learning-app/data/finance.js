window.LFV_ACADEMY.lessons.push(...[
  {
    "id":"game-theory","track":"finance","order":1,"title":"게임이론 계층","subtitle":"플레이어·행동·믿음·제약·best response·equilibrium을 읽습니다.","difficulty":"중급","minutes":28,
    "covers":["game-theory","core"],"prerequisites":["project-map","lean-reading"],
    "outcomes":["Bayesian game의 구성요소를 저장소 타입에 대응한다.","feasible action과 best response의 차이를 설명한다.","시장 행위자 모델을 이후 dynamics와 연결한다."],
    "concepts":["Player","Action","Belief","Payoff","Constraint","BestResponse","Equilibrium"],
    "why":"금융시장을 한 가격 시계열이 아니라 이질적 행위자의 전략적 상호작용으로 표현하는 기반이다.",
    "assurance":{"proves":["정의된 payoff/feasibility 관계에 대한 논리적 결과"],"notProves":["실제 투자자의 payoff 추정 정확도","현실 시장의 유일 equilibrium"]},
    "sources":["LeanFinance/GameTheory/Player.lean","LeanFinance/GameTheory/Action.lean","LeanFinance/GameTheory/Belief.lean","LeanFinance/GameTheory/Payoff.lean","LeanFinance/GameTheory/BestResponse.lean","LeanFinance/GameTheory/Equilibrium.lean"],"docs":[],"commands":["lake env lean LeanFinance/GameTheory.lean"],
    "challenge":{"prompt":"Best response를 정의하려면 최소 무엇이 필요한가?","options":["행동 가능성·payoff 비교","timestamp signature","Merkle root"],"answer":0,"explanation":"전략 선택은 feasible set과 payoff ordering을 전제로 한다."},
    "quiz":[{"question":"Bayesian game에서 belief의 역할은?","choices":["상대 type/상태에 대한 불확실성을 표현","파일 hash","코드 formatting"],"answer":0,"explanation":"belief는 불완전정보 하에서 기대 payoff를 구성한다."},{"question":"이 레슨의 명시적 보증 경계 밖에 있는 것은?","choices":["실제 투자자의 payoff 추정 정확도","정의된 payoff/feasibility 관계에 대한 논리적 결과","Bayesian game의 구성요소를 저장소 타입에 대응한다."],"answer":0,"explanation":"실제 payoff calibration은 외부 empirical boundary다."}]
  },
  {
    "id":"market-microstructure","track":"finance","order":2,"title":"시장미시구조","subtitle":"order flow, price impact, market maker, Kyle-style abstraction을 연결합니다.","difficulty":"중급","minutes":32,
    "covers":["market","core"],"prerequisites":["game-theory"],
    "outcomes":["order와 order flow를 구분한다.","price formation과 liquidity의 인과 위치를 설명한다.","Kyle-style quoting이 어떤 abstraction인지 말한다."],
    "concepts":["Order","OrderFlow","PriceFormation","MarketMaker","Liquidity","Kyle model","EquilibriumPrice"],
    "why":"가격 변화의 일부를 외생 뉴스가 아니라 주문 흐름·정보 비대칭·유동성 공급자의 반응으로 분석하는 계층이다.",
    "assurance":{"proves":["선언된 price impact와 quoting 식의 구조적 결과"],"notProves":["실제 시장 impact parameter","모든 거래소 microstructure"]},
    "sources":["LeanFinance/Market/Order.lean","LeanFinance/Market/OrderFlow.lean","LeanFinance/Market/PriceFormation.lean","LeanFinance/Market/KyleModel.lean","LeanFinance/Market/MarketMaker.lean","LeanFinance/Market/Liquidity.lean","LeanFinance/Market/EquilibriumPrice.lean"],"docs":[],"commands":["lake env lean LeanFinance/Market.lean"],
    "challenge":{"prompt":"유동성이 낮아질 때 같은 order flow의 price impact는 일반적으로?","options":["작아진다","커질 수 있다","항상 0"],"answer":1,"explanation":"얕은 유동성에서 order imbalance가 가격을 더 크게 움직일 수 있다."},
    "quiz":[{"question":"Market maker 모델은 주로 무엇을 연결하나?","choices":["inventory/information과 quote","PIT dataset과 vendor license","Lean parser와 CI"],"answer":0,"explanation":"quote 결정은 inventory·information·adverse selection과 연결된다."},{"question":"이 레슨의 명시적 보증 경계 밖에 있는 것은?","choices":["실제 시장 impact parameter","선언된 price impact와 quoting 식의 구조적 결과","order와 order flow를 구분한다."],"answer":0,"explanation":"실제 parameter calibration은 별도 empirical task다."}]
  },
  {
    "id":"constraints-dynamics","track":"finance","order":3,"title":"제약과 강제 동역학","subtitle":"Margin, VaR, redemption, short squeeze가 state transition을 어떻게 유발하는지 봅니다.","difficulty":"중급","minutes":30,
    "covers":["constraints","dynamics"],"prerequisites":["market-microstructure"],
    "outcomes":["risk constraint와 voluntary strategy를 구분한다.","forced flow가 regime transition으로 증폭되는 경로를 그린다.","정적 threshold와 동적 feedback을 구분한다."],
    "concepts":["MarginCall","VaR","Redemption","ShortSqueeze","StateTransition","Regime","EquilibriumTransition"],
    "why":"시장은 최적화하는 행위자만이 아니라 규제·레버리지·환매 제약에 의해 강제되는 행위자의 시스템이다.",
    "assurance":{"proves":["선언된 trigger에서 발생하는 구조적 flow/transition"],"notProves":["실제 margin rule calibration","위기 시점 예측"]},
    "sources":["LeanFinance/Constraints/MarginCall.lean","LeanFinance/Constraints/VaR.lean","LeanFinance/Constraints/Redemption.lean","LeanFinance/Constraints/ShortSqueeze.lean","LeanFinance/Dynamics/StateTransition.lean","LeanFinance/Dynamics/Regime.lean","LeanFinance/Dynamics/EquilibriumTransition.lean"],"docs":[],"commands":["lake env lean LeanFinance/Constraints.lean","lake env lean LeanFinance/Dynamics.lean"],
    "challenge":{"prompt":"강제매도가 feedback을 만드는 가장 직접적인 경로는?","options":["가격하락→제약위반→추가매도","서명→hash→timestamp","문서→README"],"answer":0,"explanation":"constraint-triggered flow가 가격을 다시 움직여 제약을 강화한다."},
    "quiz":[{"question":"VaR constraint와 margin call의 공통점은?","choices":["상태에 따라 feasible position을 축소","항상 자발적","데이터 vendor 인증"],"answer":0,"explanation":"둘 다 특정 상태에서 행동 가능 집합을 제한한다."},{"question":"이 레슨의 명시적 보증 경계 밖에 있는 것은?","choices":["실제 margin rule calibration","선언된 trigger에서 발생하는 구조적 flow/transition","risk constraint와 voluntary strategy를 구분한다."],"answer":0,"explanation":"현실 calibration과 crisis timing은 증명 범위 밖이다."}]
  },
  {
    "id":"hidden-state-inference","track":"finance","order":4,"title":"숨은 상태와 역게임 추론","subtitle":"관측 가격에서 latent state나 전략을 역추론할 때의 식별 한계를 다룹니다.","difficulty":"고급","minutes":30,
    "covers":["inference","dynamics","game-theory"],"prerequisites":["game-theory","constraints-dynamics"],
    "outcomes":["observation과 hidden state를 구분한다.","inverse game이 왜 비식별적일 수 있는지 설명한다.","evidence separation과 identifiability의 공통 구조를 찾는다."],
    "concepts":["HiddenState","InverseGame","identification","observational equivalence"],
    "why":"같은 가격·order flow가 서로 다른 hidden state와 전략 조합에서 나올 수 있다. 이 비식별성은 뒤의 evidence separation과 같은 수학적 패턴을 가진다.",
    "assurance":{"proves":["정의된 observation map에서의 식별/비식별 결과"],"notProves":["실제 latent state의 유일한 복원","모델 밖 전략 부재"]},
    "sources":["LeanFinance/Inference/HiddenState.lean","LeanFinance/Inference/InverseGame.lean"],"docs":[],"commands":["lake env lean LeanFinance/Inference.lean"],
    "challenge":{"prompt":"두 hidden state가 모든 관측에서 같다면?","options":["추가 가정 없이 구분 가능","현재 observation map으로는 식별 불가","자동으로 같은 state"],"answer":1,"explanation":"관측 동치가 유지되면 inverse problem은 비식별적이다."},
    "quiz":[{"question":"Evidence separation과 hidden-state identification의 공통점은?","choices":["관측 동치 class에서 target이 일정해야 함","둘 다 CSS 문제","둘 다 timestamp만 필요"],"answer":0,"explanation":"target이 observation equivalence class 위에서 well-defined여야 한다."},{"question":"이 레슨의 명시적 보증 경계 밖에 있는 것은?","choices":["실제 latent state의 유일한 복원","정의된 observation map에서의 식별/비식별 결과","observation과 hidden state를 구분한다."],"answer":0,"explanation":"실제 latent state의 유일 복원은 보장하지 않는다."}]
  },
  {
    "id":"strategy-ecology","track":"finance","order":5,"title":"전략 생태계와 인과 상호작용","subtitle":"전략의 효과가 context와 다른 전략의 존재에 따라 바뀌는 구조를 학습합니다.","difficulty":"고급","minutes":28,
    "covers":["strategy-ecology","dynamics"],"prerequisites":["hidden-state-inference"],
    "outcomes":["전략을 고정된 alpha가 아닌 context-dependent intervention으로 본다.","interaction kernel의 방향성과 비대칭을 설명한다.","전략 포화·crowding을 causal effect 변화로 해석한다."],
    "concepts":["strategy interaction","context","intervention","crowding","causal edge"],
    "why":"가치·모멘텀 같은 전략 이름보다, 어떤 context에서 다른 전략과 상호작용해 payoff를 바꾸는지가 핵심이다.",
    "assurance":{"proves":["정의된 intervention/kernel 가정에서의 인과 관계"],"notProves":["실제 alpha의 영속성","시장 전체 전략 taxonomy의 완전성"]},
    "sources":["LeanFinance/StrategyEcology.lean","LeanFinance/StrategyEcology/"],"docs":["docs/CAUSAL_STRATEGY_INTERACTION_KERNEL.md"],"commands":["lake env lean LeanFinance/StrategyEcology.lean"],
    "challenge":{"prompt":"전략 A가 B에 영향을 주지만 B가 A에 같은 영향을 주지 않는 경우 kernel은?","options":["반드시 대칭","방향성을 가질 수 있음","정의 불가"],"answer":1,"explanation":"시장 영향은 capacity·liquidity·execution channel 때문에 비대칭일 수 있다."},
    "quiz":[{"question":"Crowding을 단순 보유량이 아닌 무엇으로 볼 수 있나?","choices":["상호작용과 payoff 변화의 context","파일 크기","TSA nonce"],"answer":0,"explanation":"전략 생태계에서는 crowding이 다른 전략의 causal effect를 바꾼다."},{"question":"이 레슨의 명시적 보증 경계 밖에 있는 것은?","choices":["실제 alpha의 영속성","정의된 intervention/kernel 가정에서의 인과 관계","전략을 고정된 alpha가 아닌 context-dependent intervention으로 본다."],"answer":0,"explanation":"실제 alpha 지속성은 empirical boundary다."}]
  },
  {
    "id":"supply-chain","track":"finance","order":6,"title":"산업 병목과 공급망","subtitle":"capacity, qualification, substitution, rent concentration을 검증 가능한 구조로 봅니다.","difficulty":"고급","minutes":28,
    "covers":["supply-chain"],"prerequisites":["project-map"],
    "outcomes":["static centrality와 dynamic bottleneck을 구분한다.","qualification delay와 substitution constraint를 모델에 연결한다.","pricing power claim의 가정을 식별한다."],
    "concepts":["capacity","dependency","qualification","substitution","rent","bottleneck"],
    "why":"병목은 단순히 central node가 아니라 수요 충격을 흡수할 대체 경로와 증설 속도가 부족한 동적 위치다.",
    "assurance":{"proves":["선언된 capacity/substitution/qualification 가정 아래의 병목·rent 결과"],"notProves":["실제 기업의 미래 초과이윤","완전한 공급망 관측"]},
    "sources":["LeanFinance/SupplyChain.lean","LeanFinance/SupplyChain/"],"docs":["docs/DYNAMIC_BOTTLENECK_VERIFICATION.md"],"commands":["lake env lean LeanFinance/SupplyChain.lean"],
    "challenge":{"prompt":"동적 병목을 판단할 때 centrality만으로 부족한 이유는?","options":["대체·증설·qualification 시간이 빠질 수 있어서","그래프는 항상 틀려서","Lean이 그래프를 못 다뤄서"],"answer":0,"explanation":"실제 rent는 대체가능성과 adjustment time에 의해 결정된다."},
    "quiz":[{"question":"Qualification delay는 무엇을 강화할 수 있나?","choices":["단기 switching friction과 pricing power","hash collision","UI latency"],"answer":0,"explanation":"승인 지연은 대체 공급자의 즉시 진입을 막는다."},{"question":"이 레슨의 명시적 보증 경계 밖에 있는 것은?","choices":["실제 기업의 미래 초과이윤","선언된 capacity/substitution/qualification 가정 아래의 병목·rent 결과","static centrality와 dynamic bottleneck을 구분한다."],"answer":0,"explanation":"미래 초과이윤은 formal result가 아니다."}]
  }
]);
