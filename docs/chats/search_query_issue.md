## How to properly generate a RAG search query? What could be the issue with this example? "o2-sim material density scaling ALICE simulation documentation examples" (Think hard before responding!)

Nice — good eye spotting that query as a red flag. Below I’ll diagnose *exactly* what’s likely to go wrong with:

`o2-sim material density scaling ALICE simulation documentation examples`

and give concrete, ready-to-run replacements and a small recipe you can use in a RAG pipeline (dense vs sparse vs repo search).

# Quick diagnosis — what’s wrong with the example

* **Bag-of-words, no intent.** It’s just tokens; it doesn’t say *what* you want (how-to? API? parameter name? config file?).
* **Tokenization / spelling variants.** `o2-sim` may appear in sources as `o2`, `o2sim`, `O2-sim`, `ALICE O2` — search may miss variants.
* **Phrase vs separate tokens.** `material density scaling` might need to stay together as a phrase (`"material density"`) or be expressed as synonyms (`scale density`, `scale factor for density`, `rho`).
* **Ambiguity (ALICE).** ALICE is an experiment name (not a person) — but plain token matching can return unrelated “Alice” hits.
* **No filters / metadata.** No repo, path or filetype constraints (docs vs code). RAG benefits from telling the retriever where to look.
* **Wrong style for retrieval type.** Dense retrievers like natural sentences; BM25-like retrievers prefer targeted keywords/phrases and operators. A single bag-of-words is suboptimal for both.

# Principles (short)

1. **Decide intent** (docs vs examples vs parameter name).
2. **Normalize entities** (aliases: `o2-sim | o2 | ALICE O2`) and add technical synonyms (`density | mass density | rho`).
3. **Match query style to retriever** — full sentence for embeddings, quoted phrases + operators for sparse search, repo/filetype filters for code search.
4. **Generate several variants** and run them (hybrid retrieval + rerank).
5. **Use relevance feedback** (extract phrases from top hits, reformulate).

# Concrete improved queries — ready to use

**Dense / embedding-style (best for semantic vector retrieval / reranker)**

> `How can I apply a material density scaling factor in the ALICE O2 (o2-sim) simulation? Looking for documentation, config options and example code.`

**Sparse / BM25 / Elasticsearch-style (use quotes & operators)**

> `"material density" AND (scale OR scaling OR "scale factor") AND ("o2-sim" OR "ALICE O2") AND (documentation OR example OR tutorial)`

**Code-repo / GitHub-style (template)**

> `repo:<org>/<repo> "material density" (scale OR scaling) path:docs filename:md`
> (Replace `<org>/<repo>` with the real repo; or use `org:AliceO2` if searching an organization.)

**Google / site-limited search**

> `site:gitlab.cern.ch "material density" "o2-sim" example`
> (or `site:github.com "material density" "ALICE O2"`)

**Normalized/variant-aware query (ORs for token variants & synonyms)**

> `("o2-sim" OR "o2sim" OR "ALICE O2" OR "O2") AND ("material density" OR "mass density" OR rho OR "density scaling") AND (example OR tutorial OR documentation)`

**Elasticsearch match/phrase JSON (example snippet)**

```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "project": "o2-sim" }},
        { "match_phrase": { "content": "material density" }},
        {
          "multi_match": {
            "query": "scale scaling example documentation",
            "fields": ["content^2", "title"]
          }
        }
      ]
    }
  }
}
```

# Quick prompt you can use inside your RAG pipeline (LLM-based query rewriter)

Use this to automatically turn user text into search-friendly variants:

```
Input: <raw user query>
Task: Produce 3 queries for each retriever type:
  - dense: 1 concise natural-language question
  - sparse: 2 keyword/boolean queries (one strict with quotes, one broader)
  - repo: 2 repo-style queries (GitHub/GitLab)
Include synonyms and token variants. Keep each query ≤ 30 words.
```

# Why this actually improves retrieval

* **Dense**: full sentence captures user intent and gets semantically similar passages.
* **Sparse**: quotes + boolean force exact phrase matches and raise precision for docs that literally explain the parameter.
* **Repo filters**: drastically reduce noise from unrelated sites and prioritize README/docs/configs.
* **Variant ORs** handle different tokenizations/aliases.

# Debugging checklist (if results are still bad)

* Inspect top-5 results: are they on-topic? If *too few* relevant results → **broaden** (drop a constraint). If *too many* irrelevant → **narrow** (add quotes or repo/filetype).
* Try synonyms: `rho`, `mass density`, `scale factor`.
* Look for parameter names in top docs (e.g., `MaterialDensityScale`) and re-query that exact token.
* Use pseudo-relevance feedback: take top doc, extract candidate phrases, re-query.
* Use hybrid: run both dense and sparse, then deduplicate + rerank.

---

If you want, I’ll rewrite that exact short query into: (A) 5 dense variants, (B) 5 sparse/boolean queries, and (C) 3 GitHub-style repo queries tuned to your repository naming (tell me the repo/org if you want them targeted). Which of those would help you most right now?
