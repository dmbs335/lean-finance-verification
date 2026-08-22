import LeanFinance.Backtest.PointInTimeData

namespace LeanFinance.Examples.PointInTimeData

open LeanFinance.Backtest

def dataset (digest : String) : ArtifactRef .dataset :=
  { algorithm := .sha256
    schemaId := "pit-fixture-v1"
    digest := digest }

def originalVintage : DatasetVersion :=
  { logicalId := "prices"
    revision := 1
    firstPublishedAt := 1
    retrievedAt := 21
    content := dataset "prices-v1"
    supersedes := none }

def revisedVintage : DatasetVersion :=
  { logicalId := "prices"
    revision := 2
    firstPublishedAt := 45
    retrievedAt := 45
    content := dataset "prices-v2"
    supersedes := some originalVintage.content }

theorem revision_chain_valid :
    RevisionStep originalVintage revisedVintage := by
  simp [RevisionStep, originalVintage, revisedVintage]

def listings : List ListingRecord :=
  [{ assetId := "ALPHA", listedAt := 0, delistedAt := none },
   { assetId := "BETA", listedAt := 0, delistedAt := some 40 },
   { assetId := "GAMMA", listedAt := 20, delistedAt := none }]

def universeAt20 : UniverseSnapshot :=
  { asOf := 20
    members := ["ALPHA", "BETA", "GAMMA"]
    source := dataset "universe-20" }

def universeAt40 : UniverseSnapshot :=
  { asOf := 40
    members := ["ALPHA", "GAMMA"]
    source := dataset "universe-40" }

theorem universe_20_includes_future_delisting :
    universeAt20.ExactFor listings := by
  constructor
  · decide
  · intro assetId
    constructor
    · intro member
      simp [universeAt20] at member
      rcases member with rfl | rfl | rfl
      · exact ⟨listings[0], by simp [listings], rfl, by simp [ListingRecord.EligibleAt]⟩
      · exact ⟨listings[1], by simp [listings], rfl, by simp [ListingRecord.EligibleAt]⟩
      · exact ⟨listings[2], by simp [listings], rfl, by simp [ListingRecord.EligibleAt]⟩
    · rintro ⟨record, recordMember, rfl, eligible⟩
      simp [listings] at recordMember
      rcases recordMember with rfl | rfl | rfl <;>
        simp [universeAt20]

theorem universe_40_excludes_delisted_asset :
    universeAt40.ExactFor listings := by
  constructor
  · decide
  · intro assetId
    constructor
    · intro member
      simp [universeAt40] at member
      rcases member with rfl | rfl
      · exact ⟨listings[0], by simp [listings], rfl, by simp [ListingRecord.EligibleAt]⟩
      · exact ⟨listings[2], by simp [listings], rfl, by simp [ListingRecord.EligibleAt]⟩
    · rintro ⟨record, recordMember, rfl, eligible⟩
      simp [listings] at recordMember
      rcases recordMember with rfl | rfl | rfl
      · simp [universeAt40]
      · simp [ListingRecord.EligibleAt] at eligible
      · simp [universeAt40]

def delisting : CorporateAction :=
  { actionId := "BETA-delisting"
    assetId := "BETA"
    kind := .delisting
    announcedAt := 35
    effectiveAt := 40 }

def adjusted : AdjustedSeriesCertificate :=
  { rawData := dataset "raw-prices"
    actions := [delisting]
    adjustedData := dataset "adjusted-prices"
    generatedAt := 41 }

theorem adjustment_is_point_in_time : adjusted.Valid := by
  simp [AdjustedSeriesCertificate.Valid, adjusted, delisting,
    CorporateAction.KnownAt, ArtifactRef.Valid, NonEmptyString, dataset]

end LeanFinance.Examples.PointInTimeData
