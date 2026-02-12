---
name: bio-research
description: Preclinical research tools — literature review, scRNA-seq analysis, sequencing pipelines, drug discovery, target prioritization, and research problem selection frameworks. Derived from Anthropic knowledge-work-plugins (Apache-2.0).
---

# Bio Research

Connect to preclinical research tools and databases for literature search, genomics analysis, target prioritization, and drug discovery to accelerate early-stage life sciences R&D. Includes systematic framework for research problem selection (Fischbach and Walsh).

## Activation Triggers

Activate when the user's request involves:
- Literature search or systematic review
- Genomics, transcriptomics, or scRNA-seq analysis
- Bioinformatics pipelines (nf-core, sequencing)
- Drug discovery, target identification, or compound screening
- Research problem selection or hypothesis prioritization
- Clinical trial landscape analysis

## Commands

### `/bio:literature-review`
Systematic literature review: search databases, access full-text, synthesize findings, annotated bibliography.

**Methodology:** Structured search strategy → relevance screening → data extraction → thematic synthesis → gap identification → evidence quality assessment.

### `/bio:analyze-scrna`
Single-cell RNA sequencing analysis: QC, integration, batch correction, cell type annotation.

**Framework:** scverse best practices. Supports .h5ad/.h5 files. MAD-based filtering. Deep learning: scVI, scANVI, totalVI, PeakVI, MultiVI, DestVI for integration, batch correction, label transfer, multi-modal analysis.

### `/bio:run-pipeline`
Execute sequencing pipelines: download public data (GEO/SRA), run nf-core pipelines, verify outputs.

**Pipelines:** RNA-seq (nf-core/rnaseq), variant calling (nf-core/sarek), ATAC-seq (nf-core/atacseq).

### `/bio:drug-discovery`
Drug discovery workflow: bioactive compound search, target prioritization, clinical trial landscape.

**Target validation:** Genetic evidence (GWAS, rare variants), expression data, druggability assessment, safety profiling.
**Compound screening:** Bioactivity databases, SAR, selectivity profiling, ADMET prediction.

## Auto-Firing Skills

### Research Problem Selection
**Fires when:** User discusses choosing research direction or project prioritization.
Fischbach and Walsh framework: ideation, feasibility assessment, risk assessment, optimization, decision trees, adversity planning, synthesis.

### Single-Cell Analysis
**Fires when:** User mentions scRNA-seq, single-cell, cell types.

### Literature Synthesis
**Fires when:** User asks about papers or state of the art.
Proper citations, avoid over-reliance on single studies, identify methodological limitations.

### Sequencing Pipelines
**Fires when:** User mentions sequencing data, nf-core, or bioinformatics pipelines.

### Drug Target Analysis
**Fires when:** User discusses drug targets or compound screening.
Target identification → genetic evidence → druggability → safety → compound screening → clinical landscape.

## Configuration

```yaml
research_focus: []     # Lab's primary research areas
data_paths: {}         # Default locations for sequencing data
pipeline_defaults: {}  # Default parameters for pipelines
publication_targets: [] # Target journals and formatting
```

## Connectors

| Connector | Purpose | Degraded Behavior |
|-----------|---------|-------------------|
| Literature (PubMed) | Biomedical literature | Web search for papers |
| Preprint (bioRxiv) | Early-stage research | Web search |
| Chemical DB (ChEMBL) | Bioactive compounds | User provides data |
| Drug Targets (Open Targets) | Target prioritization | Literature-based analysis |
| Clinical Trials (ClinicalTrials.gov) | Trial data | Web search |
| Lab Notebook (Benchling) | Protocols, results | User provides protocols |
| ML Platform (Owkin) | Biomedical ML | Local analysis |
