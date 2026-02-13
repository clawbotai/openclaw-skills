---
name: bio-research
description: Preclinical research tools — literature review, scRNA-seq analysis, sequencing pipelines, drug discovery, target prioritization, and research problem selection frameworks. Derived from Anthropic knowledge-work-plugins (Apache-2.0).
---

# Bio Research

Preclinical research tools: systematic literature review, single-cell RNA sequencing analysis, bioinformatics pipeline execution, drug discovery workflows, and target prioritization. Includes structured framework for research problem selection (Fischbach and Walsh).

## Activation Triggers

Activate when the user's request involves:
- Literature search, systematic review, or paper analysis
- Genomics, transcriptomics, or scRNA-seq analysis
- Bioinformatics pipelines (nf-core, sequencing, alignment)
- Drug discovery, target identification, or compound screening
- Research problem selection or hypothesis prioritization
- Clinical trial landscape analysis

## Commands

### `/bio:literature-review`
Systematic literature review with evidence quality assessment.

**Workflow:**
1. **Search strategy** — define PICO (Population, Intervention, Comparison, Outcome), generate search terms, identify databases (PubMed, bioRxiv, Google Scholar)
2. **Execute search** — structured queries with Boolean operators, MeSH terms
3. **Screen** — title/abstract screening against inclusion/exclusion criteria
4. **Extract** — key findings, methodology, sample sizes, effect sizes, limitations
5. **Synthesize** — thematic analysis, identify consensus vs controversy, evidence quality (RCT > cohort > case > expert opinion)
6. **Gap analysis** — what's missing? What contradictions exist? What's ripe for investigation?
7. **Bibliography** — annotated bibliography with relevance scores

**Citation rules:** Always include PMID. Distinguish preprint from peer-reviewed. Flag retracted papers. Note study limitations alongside findings.

### `/bio:analyze-scrna`
Single-cell RNA sequencing analysis pipeline.

**Workflow (scverse best practices):**
1. **Input** — .h5ad, .h5, or count matrix. Verify format, gene/cell counts.
2. **QC** — MAD-based filtering: mitochondrial % (<20%), gene count (200-5000), UMI count. Doublet detection (Scrublet/DoubletFinder).
3. **Normalization** — library size normalization, log1p transform, HVG selection (top 2000-4000)
4. **Integration** — if multi-sample: scVI for probabilistic integration, Harmony for fast linear correction, BBKNN for graph-based. Assess with kBET, LISI scores.
5. **Dimensionality reduction** — PCA (30-50 components), UMAP for visualization (not analysis)
6. **Clustering** — Leiden algorithm, test multiple resolutions (0.2-1.5), evaluate with silhouette scores
7. **Annotation** — marker genes, reference mapping (scANVI, CellTypist), manual curation
8. **DE analysis** — Wilcoxon rank-sum (default), pseudobulk for multi-sample, FDR correction (Benjamini-Hochberg)
9. **Visualization** — UMAP, dotplot, violin, heatmap, trajectory (PAGA, RNA velocity)

**Deep learning tools:**
| Tool | Purpose |
|------|---------|
| scVI | Probabilistic model, batch correction, imputation |
| scANVI | Semi-supervised label transfer |
| totalVI | CITE-seq (RNA + protein) |
| PeakVI | scATAC-seq |
| MultiVI | Multi-modal integration |
| DestVI | Spatial transcriptomics deconvolution |
| CellRank | Fate prediction from RNA velocity |

### `/bio:run-pipeline`
Execute bioinformatics sequencing pipelines.

**Workflow:**
1. **Data acquisition** — download from GEO/SRA (prefetch + fasterq-dump), verify checksums
2. **QC** — FastQC, MultiQC, adapter detection
3. **Pipeline selection:**
   - RNA-seq: `nf-core/rnaseq` (STAR + Salmon quantification)
   - Variant calling: `nf-core/sarek` (BWA-MEM2 + GATK HaplotypeCaller)
   - ATAC-seq: `nf-core/atacseq` (BWA + MACS2 peak calling)
   - ChIP-seq: `nf-core/chipseq`
4. **Configuration** — genome reference (GRCh38/GRCm39), compute resources, output directory
5. **Execution** — Nextflow with container engine (Docker/Singularity)
6. **Validation** — MultiQC report, alignment rates, duplication levels, expected gene counts

### `/bio:drug-discovery`
Drug discovery and target prioritization workflow.

**Workflow:**
1. **Target identification** — disease association (GWAS Catalog, Open Targets), expression data (GTEx, Human Protein Atlas), literature evidence
2. **Target validation:**
   - Genetic evidence: GWAS significance, rare variant studies, Mendelian disease links
   - Expression: tissue specificity, disease vs normal differential
   - Druggability: protein class, binding pocket availability, existing tool compounds
   - Safety: essential gene (DepMap), broad expression (off-target risk), known toxicology
3. **Compound screening** — ChEMBL bioactivity data, SAR analysis, selectivity profiling
4. **ADMET prediction** — absorption, distribution, metabolism, excretion, toxicity flags
5. **Clinical landscape** — ClinicalTrials.gov search for same target/indication, competitive positioning
6. **Target scorecard** — weighted scoring across evidence dimensions, go/no-go recommendation

## Auto-Firing Skills

### Research Problem Selection
**Fires when:** User discusses choosing research direction or project prioritization.

**Fischbach and Walsh framework:**
1. **Ideation** — brainstorm questions at intersection of capability and curiosity
2. **Feasibility** — technical (tools, data, model systems), resource (budget, time, personnel), expertise (team skills vs required skills)
3. **Risk assessment** — scientific risk (will it work?), competitive risk (will someone else publish first?), career risk (is it publishable regardless of outcome?)
4. **Optimization** — scope to minimum viable experiment, identify go/no-go checkpoints
5. **Decision** — score and rank candidates, select with explicit rationale
6. **Adversity planning** — what if primary hypothesis fails? Pre-register alternative analyses.

### Single-Cell Analysis
**Fires when:** User mentions scRNA-seq, single-cell, cell types, clusters.
Default to scverse ecosystem (scanpy, anndata, scvi-tools). Always check batch effects before biological interpretation. UMAP is for visualization only — never cluster on UMAP coordinates. Report QC metrics before any downstream analysis.

### Literature Synthesis
**Fires when:** User asks about papers, state of the art, or "what's known about."
Proper citations with PMID. Distinguish primary research from reviews. Identify methodological limitations. Note sample sizes. Flag if evidence is primarily from model organisms vs human data.

### Sequencing Pipelines
**Fires when:** User mentions sequencing data, FASTQ, BAM, nf-core, or bioinformatics.
Always start with QC. Use established pipelines (nf-core) over custom scripts. Document reference genome version. Container-based execution for reproducibility.

### Drug Target Analysis
**Fires when:** User discusses drug targets, compounds, or therapeutic approaches.
Triangulate evidence: genetic + expression + functional. Weight genetic evidence heavily (causal inference). Check Open Targets for aggregated scores. Always assess safety alongside efficacy. Report target tractability (small molecule vs antibody vs other modality).

## Configuration

```yaml
research_focus: []               # Lab's primary research areas (e.g., ["oncology", "immunology"])
default_genome: "GRCh38"        # Reference genome
data_paths:
  raw: ""                        # Raw sequencing data
  processed: ""                  # Processed outputs
  references: ""                 # Genome references
pipeline_defaults:
  executor: "local"              # local, slurm, aws
  container: "docker"            # docker, singularity
  max_cpus: 8
  max_memory: "32.GB"
publication_targets: []          # Target journals and formatting requirements
pubmed_email: ""                 # Required for NCBI API access
```

## Connectors

| Connector | Purpose | Degraded Behavior |
|-----------|---------|-------------------|
| PubMed (NCBI E-utilities) | Literature search, abstracts | Web search for papers |
| bioRxiv (API) | Preprint access | Web search for preprints |
| ChEMBL (REST API) | Bioactive compound data | User provides compound data |
| Open Targets (GraphQL) | Target-disease associations | Literature-based prioritization |
| ClinicalTrials.gov (API) | Trial data and landscape | Web search for trial info |
| GEO/SRA (NCBI) | Public sequencing data | User provides FASTQ files |
| Benchling (API) | Lab notebook, protocols | User provides protocols as text |

## Cross-Skill Integration

### Memory Protocol
- **Before `/bio:literature-review`**: `memory.py recall "[bio-research] {topic}"` — prior reviews, key papers, gaps identified
- **After analysis**: `memory.py remember "[bio-research] {analysis_type} on {dataset}: {key_finding}" --importance 0.8`
- **After `/bio:drug-discovery`**: store target scorecard as semantic memory

### Connected Skills
- **data-analysis** → statistical analysis on DE results, enrichment, clinical trial data
- **data-analysis** → dashboard generation for gene expression, volcano plots
- **enterprise-search** → pull prior lab communications and notes
- **docs-engine** → structure research reports using Diátaxis framework
