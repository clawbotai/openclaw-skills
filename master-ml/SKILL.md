---
name: master-ml
description: Complete ML/MLOps engineer — model development, experiment tracking, feature engineering, ML pipelines, model serving, monitoring, responsible AI, LLMOps, and production ML infrastructure. Use for any ML/AI task.
model: opus
context: fork
---

# Master ML/MLOps Engineer

End-to-end machine learning: from data to production, from experiments to monitoring.

## ⚠️ Chunking Rule

Large ML systems routinely exceed 1000 lines. Generate ONE stage per response, confirm before proceeding:

1. **Data & EDA** → 2. **Feature Engineering** → 3. **Training & Experimentation** → 4. **Evaluation** → 5. **Serving & Deployment** → 6. **Monitoring & Observability**

For MLOps platforms, break into: Experiment Tracking → Model Registry → Training Pipelines → Deployment Automation → Monitoring.

---

## 1. Project Structure

```
ml-project/
├── data/
│   ├── raw/                  # Immutable original data
│   ├── processed/            # Transformed features
│   └── external/             # Third-party datasets
├── notebooks/                # Exploration only (not production)
├── src/
│   ├── data/                 # Data loading, validation (Great Expectations / Pandera)
│   ├── features/             # Feature engineering, feature store integration
│   ├── models/               # Model definitions, architectures
│   ├── training/             # Training loops, experiment configs
│   ├── evaluation/           # Metrics, fairness checks, explainability
│   ├── serving/              # Inference endpoints, batch prediction
│   └── monitoring/           # Drift detection, performance tracking
├── pipelines/                # Kubeflow / Vertex AI / Airflow DAGs
├── configs/                  # Hydra / YAML experiment configs
├── tests/                    # Unit + integration + model tests
├── dvc.yaml                  # Data versioning pipeline
├── MLproject                 # MLflow project definition
├── Dockerfile                # Reproducible training/serving image
└── pyproject.toml
```

## 2. Development Principles

### Baselines First
- Always start with a simple baseline (logistic regression, mean predictor, rule-based)
- Document baseline metrics before building complex models
- Every model must beat baseline to justify complexity

### Experiment Tracking (MLflow / W&B)
```python
import mlflow

with mlflow.start_run(run_name="xgb-v2"):
    mlflow.log_params({"max_depth": 6, "lr": 0.01, "n_estimators": 500})
    mlflow.log_metrics({"auc": 0.92, "f1": 0.87})
    mlflow.log_artifact("confusion_matrix.png")
    mlflow.sklearn.log_model(model, "model", registered_model_name="fraud-detector")
```
- Log ALL hyperparameters, metrics, artifacts, and environment
- Tag runs with dataset version (DVC hash) for full reproducibility
- Use MLflow Model Registry or W&B Model Registry for promotion workflow: Staging → Production

### Cross-Validation
- Use stratified k-fold (classification) or repeated k-fold (regression) — never single train/test
- Report mean ± std for all metrics
- Use time-based splits for temporal data (never leak future)

### Data Versioning (DVC)
```yaml
# dvc.yaml
stages:
  preprocess:
    cmd: python src/data/preprocess.py
    deps: [data/raw/]
    outs: [data/processed/]
  train:
    cmd: python src/training/train.py
    deps: [data/processed/, src/models/]
    outs: [models/]
    metrics: [metrics.json]
```
- Version data alongside code — every experiment links to exact data state
- Use remote storage (S3/GCS) for large datasets

## 3. Feature Engineering

### Best Practices
- Feature computation must be **identical** in training and serving (training-serving skew is the #1 production ML bug)
- Use feature stores (Feast) for shared, versioned, point-in-time correct features
- Document every feature: meaning, source, update frequency, expected distribution

### Feature Store Integration (Feast)
```python
from feast import FeatureStore
store = FeatureStore(repo_path="feature_repo/")

# Training: point-in-time join
training_df = store.get_historical_features(
    entity_df=entity_df,
    features=["user_features:avg_purchase_30d", "user_features:login_count_7d"]
).to_df()

# Serving: online lookup
features = store.get_online_features(
    features=["user_features:avg_purchase_30d"],
    entity_rows=[{"user_id": 123}]
).to_dict()
```

### Common Patterns
- **Numeric**: log transform, standardization, binning, interaction terms
- **Categorical**: target encoding (with proper CV), embeddings for high-cardinality
- **Temporal**: lag features, rolling windows, cyclical encoding (sin/cos)
- **Text**: TF-IDF → embeddings (sentence-transformers); use pre-trained for low-data
- **Missing data**: indicate missingness as feature; never silently impute

## 4. Training & Optimization

### Hyperparameter Optimization (Optuna)
```python
import optuna

def objective(trial):
    params = {
        "max_depth": trial.suggest_int("max_depth", 3, 10),
        "learning_rate": trial.suggest_float("lr", 1e-4, 0.1, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
    }
    model = train(params)
    return evaluate(model)  # Returns metric to optimize

study = optuna.create_study(direction="maximize", pruner=optuna.pruners.MedianPruner())
study.optimize(objective, n_trials=100)
```
- Use pruning (MedianPruner/HyperbandPruner) to stop bad trials early
- Log Optuna studies to MLflow for full traceability

### Distributed Training
- **Data parallel**: PyTorch DDP (`torchrun --nproc_per_node=4`) for multi-GPU
- **Model parallel**: Use FSDP or DeepSpeed for models that don't fit in one GPU
- **Gradient accumulation**: Simulate larger batches on limited hardware
- Always set seeds and use deterministic ops for reproducibility

### GPU Optimization
- Mixed precision training (`torch.amp`) — 2x speedup, less memory
- Gradient checkpointing for large models
- Pin memory, prefetch data, use `num_workers > 0` in DataLoader
- Profile with `torch.profiler` or NVIDIA Nsight before optimizing blindly

### AutoML
- Use for baseline establishment (AutoGluon, FLAML, H2O)
- Not a replacement for domain expertise — use to discover promising architectures
- Always validate AutoML outputs with proper CV and holdout sets

## 5. Evaluation & Responsible AI

### Comprehensive Evaluation
- **Classification**: precision, recall, F1, AUC-ROC, AUC-PR (for imbalanced), calibration
- **Regression**: MAE, RMSE, R², MAPE, residual analysis
- **Ranking**: NDCG, MAP, MRR
- Always evaluate on **subgroups** (slice-based analysis) — aggregate metrics hide failures

### Explainability (SHAP / LIME)
```python
import shap
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)
shap.summary_plot(shap_values, X_test)        # Global feature importance
shap.waterfall_plot(explainer(X_test[0:1]))    # Local explanation
```
- Every production model needs global + local explanations
- Use LIME for model-agnostic local explanations
- Store explanations as artifacts alongside predictions

### Fairness
- Measure disparate impact, equalized odds, demographic parity across protected groups
- Use Fairlearn or AIF360 for bias detection and mitigation
- Document fairness metrics in model cards (see Model Card template below)

### Model Cards
Every production model must have a model card documenting:
- Intended use, limitations, ethical considerations
- Training data description, evaluation metrics per subgroup
- Performance benchmarks, known failure modes

## 6. ML Pipelines

### Pipeline Orchestration
- **Kubeflow Pipelines**: Kubernetes-native, good for large-scale
- **Vertex AI Pipelines**: Managed, GCP-integrated
- **SageMaker Pipelines**: AWS-native end-to-end
- **Airflow/Dagster**: General-purpose, ML-aware scheduling
- **ZenML**: Framework-agnostic ML pipeline abstraction

### Pipeline Design
```
Data Validation → Feature Engineering → Training → Evaluation Gate → Registry → Deployment
                                                        ↓ (fail)
                                                   Alert + Block
```
- Every pipeline stage must be **idempotent** and **containerized**
- Evaluation gate: auto-block deployment if metrics regress vs. current production model
- Cache intermediate artifacts to avoid recomputation

## 7. Model Serving & Deployment

### Serving Frameworks
| Framework | Best For |
|-----------|----------|
| **TorchServe** | PyTorch models, multi-model serving |
| **Triton** | Multi-framework, GPU-optimized, dynamic batching |
| **BentoML** | Easy packaging, multi-framework, REST/gRPC |
| **vLLM** | LLM serving with PagedAttention |
| **TensorRT** | NVIDIA GPU optimization, INT8/FP16 |

### Deployment Patterns
- **Shadow mode**: New model receives traffic but doesn't serve responses — compare offline
- **Canary**: Route 5% → 25% → 100% with automated rollback on metric degradation
- **A/B testing**: Statistical comparison (use proper sample size calculations, avoid peeking)
- **Blue/Green**: Instant switchover with rollback capability
- **Multi-armed bandit**: Dynamic traffic allocation for continuous optimization

### Model Optimization for Serving
- Quantization (INT8/FP16) — `torch.quantization` or ONNX Runtime
- Distillation — train small student from large teacher
- ONNX export for framework-agnostic, optimized inference
- Batch prediction for non-latency-sensitive workloads (cheaper, simpler)

## 8. Monitoring & Observability

### What to Monitor
1. **Data drift**: Input feature distributions shifting (PSI, KL divergence, KS test)
2. **Prediction drift**: Output distribution changing
3. **Performance degradation**: Metric decay when labels arrive (delayed ground truth)
4. **System metrics**: Latency p50/p95/p99, throughput, GPU utilization, error rates

### Drift Detection
```python
from evidently import ColumnDriftMetric, Report
report = Report(metrics=[ColumnDriftMetric(column_name="feature_1")])
report.run(reference_data=train_df, current_data=prod_df)
```
- Use Evidently, NannyML, or Alibi Detect
- Alert on drift; auto-retrigger training pipeline if significant
- Monitor feature-level AND prediction-level drift

### Alerting Strategy
- **P0**: Model serving errors, latency > SLA → PagerDuty
- **P1**: Significant drift detected → Slack + auto-retrain trigger
- **P2**: Gradual performance decay → Weekly report
- Log all predictions with timestamps for retrospective analysis

## 9. LLMOps

### Fine-Tuning Workflows
- **Full fine-tuning**: Only when you have >10K examples and compute budget
- **LoRA/QLoRA**: Parameter-efficient fine-tuning — 10-100x less compute
- **RLHF/DPO**: Alignment tuning with preference data
- Always evaluate on held-out set + human evaluation

### RAG (Retrieval-Augmented Generation)
```
Query → Embedding → Vector Search → Top-K Chunks → LLM(context + query) → Response
```
- Chunk strategy matters: semantic chunking > fixed-size
- Use hybrid search (dense + sparse/BM25) for better recall
- Evaluate: faithfulness, relevance, answer correctness (RAGAS framework)
- Rerank retrieved chunks before passing to LLM (cross-encoder or Cohere Rerank)

### LLM Evaluation
- Use LLM-as-judge with structured rubrics (not vibes)
- Track: latency, token usage, cost per query, hallucination rate
- A/B test prompt variations with statistical rigor
- Version prompts alongside code

### LLM Serving
- Use vLLM or TGI for self-hosted — PagedAttention for efficient KV cache
- Implement streaming responses for UX
- Cache frequent queries (semantic similarity caching)
- Set up guardrails (content filtering, output validation)

## 10. Infrastructure Patterns

### Reproducibility Checklist
- [ ] Random seeds set (Python, NumPy, PyTorch, CUDA)
- [ ] Data versioned (DVC or equivalent)
- [ ] Environment pinned (Docker image or `pip freeze`)
- [ ] Experiment tracked (MLflow/W&B with all params + metrics)
- [ ] Code tagged (git SHA logged with each run)

### CI/CD for ML
```yaml
# .github/workflows/ml-ci.yml
on: [push]
jobs:
  test:
    steps:
      - run: pytest tests/ -v
      - run: python src/training/train.py --config configs/smoke_test.yaml  # Fast training sanity check
      - run: python src/evaluation/validate.py --threshold 0.85  # Gate on metrics
```
- Unit test data transforms, feature engineering, model I/O
- Integration test full pipeline on small data subset
- Model performance gate: block merge if metrics below threshold
- Test model inference latency in CI

### Cost Optimization
- Use spot/preemptible instances for training (checkpoint frequently)
- Right-size GPU: don't default to A100 — profile first
- Batch prediction > real-time when latency allows
- Auto-scale serving infrastructure based on traffic patterns
- Track compute cost per experiment in MLflow

---

## Quick Reference: When to Use What

| Need | Tool/Approach |
|------|--------------|
| Experiment tracking | MLflow, W&B |
| Data versioning | DVC, LakeFS |
| Feature store | Feast, Tecton |
| Hyperparameter tuning | Optuna, Ray Tune |
| Pipeline orchestration | Kubeflow, Vertex AI, SageMaker, ZenML |
| Model serving | Triton, BentoML, TorchServe, vLLM |
| Monitoring | Evidently, NannyML, Prometheus + Grafana |
| Explainability | SHAP, LIME, Captum |
| Fairness | Fairlearn, AIF360 |
| LLM fine-tuning | LoRA (PEFT), Axolotl, LLaMA-Factory |
| RAG evaluation | RAGAS, DeepEval |
| Distributed training | PyTorch DDP/FSDP, DeepSpeed, Ray Train |
