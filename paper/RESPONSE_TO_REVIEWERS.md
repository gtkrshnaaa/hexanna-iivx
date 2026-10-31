# Response to Editors and Reviewers

**Manuscript Title:** A Deterministic, Metadata-Driven Agent Harness for Out-of-Core Local Data Engineering  
**Authors:** I Putu Gede Gilang Teja Krishna, Sri Redjeki  
**Target Venue:** Elsevier Journal of Systems and Software (JSS)  
**Status:** Major Revision Response Letter

---

Dear Editors and Reviewers,

We sincerely thank the Reviewers for their constructive critiques, which have substantially elevated the rigor and empirical depth of our manuscript. In this revision, we have executed comprehensive improvements across four major dimensions:

### 1. Model-Agnostic Validation (Open-Weight MoE vs. Commercial Lightweight API)
- **Reviewer Critique:** Ambiguity regarding whether the harness relies on the latent parametric strength of a specific frontier model or whether the metadata-first protocol empowers cost-efficient lightweight models.
- **Authors' Revision:** In Section 4.1 and Section 5.5 (Table 4), we have expanded our experimental benchmark to formally evaluate Hexanna IIVX across two complementary, cost-effective inference backends via OpenAI-compatible REST gateways:
  1. **DeepSeek-V4.1-Flash** (representing open-weight, mixture-of-experts MoE architectures optimized for code generation).
  2. **Gemini 3.8 Flash** (representing high-speed, cost-effective commercial reasoning APIs with strict instruction-following capabilities).
- **Key Finding:** We demonstrate that both models achieve 100.0% task validity within a maximum of two retry cycles across all TPC-H query profiles at SF-10 (60 million records). Prompt wire footprint remains strictly bounded at 846 vs. 848 tokens, empirically verifying the $\mathcal{O}(1)$ wire token complexity invariant (Theorem 1).

### 2. Rigorous Justification of Baselines ("Strawman" Framing Defense)
- **Reviewer Critique:** Comparing out-of-core memory footprint directly against PandasAI can be viewed as unfair because Pandas is inherently an in-memory eager evaluation library.
- **Authors' Revision:** In Section 4.4 and Section 5.1, we have clarified our baseline taxonomy into three distinct functional axes:
  1. **Autonomous Status Quo (PandasAI):** Evaluated not as an optimized out-of-core engine, but as the empirical embodiment of the prevailing in-memory agentic paradigm (e.g., LangChain Pandas DataFrame Agent, Open-Interpreter default).
  2. **Vectorized Streaming Baseline (Polars Streaming):** Demonstrates how a modern multithreaded dataframe operates with lazy execution without hard physical memory clamps.
  3. **Theoretical Performance Ceiling (Raw DuckDB):** Measures the marginal cognitive overhead introduced by autonomous agent orchestration compared to zero-LLM manual execution under identical 2 GB memory and NVMe spilling limits.

### 3. Formalization of the Self-Healing Loop and Error Mapping
- **Reviewer Critique:** Lack of formal algorithmic detail regarding prompt delta construction upon execution failure.
- **Authors' Revision:** In Section 3.3, we have formalized the self-healing dispatch function $\mathcal{H}(q_k, E)$ and prompt delta construction $\Delta_k \in \{\mathcal{E}_{\text{syntax}}, \mathcal{E}_{\text{type}}, \mathcal{E}_{\text{empty}}\}$, detailing how surgical feedback prevents context drift while maintaining strict schema compliance.

### 4. Mathematical and Typographical Polishing
- **Reviewer Critique:** Minor typographical and LaTeX math formatting artifacts.
- **Authors' Revision:** All tables (including Table 1) have been audited and updated to strictly format mathematical bounds ($\mathcal{O}(1)$ and $\mathcal{O}(N)$), standardized scaling notation (`SF-10 (10 GB)`), and publication compliance.

We believe these revisions address all reviewer concerns and establish a rigorous, reproducible contribution to the systems literature.

Sincerely,  
**The Authors**  
I Putu Gede Gilang Teja Krishna  
Sri Redjeki  
*Faculty of Information Technology, Universitas Teknologi Digital Indonesia (UTDI)*
