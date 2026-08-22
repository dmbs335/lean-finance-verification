import LeanFinance.Backtest.Artifact

namespace LeanFinance.Backtest

/-- One immutable publication vintage of a logical dataset. Publication,
    retrieval, and revision identity are kept separate. -/
structure DatasetVersion where
  logicalId : String
  revision : Nat
  firstPublishedAt : Timestamp
  retrievedAt : Timestamp
  content : ArtifactRef .dataset
  supersedes : Option (ArtifactRef .dataset)
  deriving Repr

/-- The exact bytes were public and retrieved by the decision cutoff. -/
def DatasetVersion.AvailableAt
    (decisionAt : Timestamp)
    (version : DatasetVersion) : Prop :=
  version.firstPublishedAt ≤ version.retrievedAt ∧
    version.retrievedAt ≤ decisionAt

/-- One revision-chain edge preserves logical identity and increases both the
    revision number and publication time. -/
def RevisionStep
    (older newer : DatasetVersion) : Prop :=
  older.logicalId = newer.logicalId ∧
    older.revision < newer.revision ∧
    older.firstPublishedAt < newer.firstPublishedAt ∧
    newer.supersedes = some older.content

/-- Listing and delisting history used to derive a point-in-time universe. -/
structure ListingRecord where
  assetId : String
  listedAt : Timestamp
  delistedAt : Option Timestamp
  deriving Repr, DecidableEq

/-- Delisting is exclusive: an asset is no longer eligible at the delisting
    timestamp itself. -/
def ListingRecord.EligibleAt
    (record : ListingRecord)
    (asOf : Timestamp) : Prop :=
  record.listedAt ≤ asOf ∧
    match record.delistedAt with
    | none => True
    | some delistedAt => asOf < delistedAt

structure UniverseSnapshot where
  asOf : Timestamp
  members : List String
  source : ArtifactRef .dataset
  deriving Repr

/-- Exact point-in-time universe semantics: membership is equivalent to one
    eligible listing record, not merely a subset of surviving assets. -/
def UniverseSnapshot.ExactFor
    (listings : List ListingRecord)
    (snapshot : UniverseSnapshot) : Prop :=
  snapshot.members.Nodup ∧
    ∀ assetId,
      assetId ∈ snapshot.members ↔
        ∃ record,
          record ∈ listings ∧
            record.assetId = assetId ∧
              record.EligibleAt snapshot.asOf

inductive CorporateActionKind where
  | split
  | dividend
  | delisting
  | merger
  | symbolChange
  deriving Repr, DecidableEq

structure CorporateAction where
  actionId : String
  assetId : String
  kind : CorporateActionKind
  announcedAt : Timestamp
  effectiveAt : Timestamp
  deriving Repr, DecidableEq

/-- A transform may use only actions announced before its generation time. -/
def CorporateAction.KnownAt
    (generatedAt : Timestamp)
    (action : CorporateAction) : Prop :=
  action.announcedAt ≤ generatedAt

structure AdjustedSeriesCertificate where
  rawData : ArtifactRef .dataset
  actions : List CorporateAction
  adjustedData : ArtifactRef .dataset
  generatedAt : Timestamp
  deriving Repr

def AdjustedSeriesCertificate.Valid
    (certificate : AdjustedSeriesCertificate) : Prop :=
  certificate.rawData.Valid ∧
    certificate.adjustedData.Valid ∧
    ∀ action,
      action ∈ certificate.actions →
        action.KnownAt certificate.generatedAt

/-- Benchmark, metric, window, and cost assumptions are one preregistered
    evaluation contract rather than mutable report metadata. -/
structure EvaluationContract where
  contractId : String
  benchmarkId : String
  metricId : String
  lookbackPeriods : Nat
  costBasisPoints : Nat
  registeredAt : Timestamp
  deriving Repr

def EvaluationContract.PreregisteredFor
    (contract : EvaluationContract)
    (decisionAt : Timestamp) : Prop :=
  contract.registeredAt ≤ decisionAt

/-- Combined point-in-time research contract. -/
structure PointInTimeResearchCertificate where
  decisionAt : Timestamp
  vintage : DatasetVersion
  vintageAvailable : vintage.AvailableAt decisionAt
  listings : List ListingRecord
  universeSnapshot : UniverseSnapshot
  universeExact : universeSnapshot.ExactFor listings
  adjustedSeries : AdjustedSeriesCertificate
  adjustmentValid : adjustedSeries.Valid
  evaluation : EvaluationContract
  evaluationPreregistered : evaluation.PreregisteredFor decisionAt

end LeanFinance.Backtest
