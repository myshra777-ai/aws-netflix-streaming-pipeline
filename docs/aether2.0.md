flowchart LR
  %% Lanes as subgraphs
  subgraph CP[Control Plane]
    CR[Contract Registry\n(S3 YAML)]
    BMR[Batch Metadata Registry\n(DynamoDB, strong)]
    TER[Trust & Exposure Registry\n(BatchMetadata view)]
    TE[Trust Engine]
    AC[Aether Console / API]
    ALS[Audit Log Stream\n(Immutable)]
    ERV[Exposure Registry View\n(state = APPROVED)]
    ECR[Exposure Contract Registry]
    VG[View Generator\n(Dept Views)]
    RJ[Reconciliation Job]
  end

  subgraph DP[Data Plane]
    PS[Producer Services]
    SL[Streaming Layer\n(Kinesis / Kafka)]
    RLS3[Raw Landing S3]
    L1[Lambda A:\nBatch Registrar]
    SFO[Step Functions\nOrchestrator]
    L2[Lambda B:\nContract Auditor]
    GCE[Glue/Spark\nContract Enforcer]
    AS3[Analytics S3\n(clean rows)]
    DLQ_BATCH[DLQ_BATCH S3]
    DLQ_ROW[Row DLQ S3]
    MANI[Approved Paths\nS3 Manifest]
  end

  subgraph AP[Access Plane]
    AMG[Approved Manifest\nGenerator]
    WLV[Warehouse\nLogical Views]
    DV[Dept Views]
    BIC[BI / ML /\nAd-hoc Consumers]
  end

  %% Main data flow (Data Plane)
  PS --> SL --> RLS3
  RLS3 -->|Event Trigger| L1
  L1 -->|REGISTERED\nstate_version=1| BMR

  BMR --> SFO
  SFO --> L2
  L2 -->|UPDATE\nREGISTERED→CONTRACT_OK\nor REGISTERED→FAILED_DLQ_BATCH| BMR
  L2 --> DLQ_BATCH

  BMR -->|state=CONTRACT_OK| GCE
  GCE --> AS3
  GCE --> DLQ_ROW
  GCE -->|state=ANALYTICS_READY\n+ DQ stats| BMR

  %% Control-plane trust & approval
  BMR -->|ANALYTICS_READY + DQ stats| TE
  TE --> AC
  AC -->|Approval Tx\n(ANALYTICS_READY→APPROVED\n+ state_version check)| BMR

  %% Audit log on transitions
  BMR -. state transitions .-> ALS
  L2 -. transitions .-> ALS
  GCE -. transitions .-> ALS
  AC  -. approval .-> ALS

  %% Exposure & manifests
  BMR -->|filter state=APPROVED| ERV
  ERV --> AMG
  AMG --> MANI
  MANI --> WLV

  %% Dept exposure contracts
  ECR --> VG --> DV

  %% Reconciliation
  AS3 --> RJ
  BMR --> RJ
  RJ --> ALS
  RJ -->|Drift Report / Alerts| AC

  %% Access-plane consumers
  WLV --> BIC
  DV  --> BIC
