# Advanced search capabilities

**Status:** Fuzzy lookup fully implemented, DiskANN and BM25 in planning phase
**Date:** 2025-10-25

---

## Table of contents

1. [Overview](#overview)
2. [Fuzzy key lookup (BM25)](#fuzzy-key-lookup-bm25) ✅
3. [Full-text search (BM25)](#full-text-search-bm25) 🔨
4. [Disk-based vector search (DiskANN)](#disk-based-vector-search-diskann) 🔨
5. [Hybrid search](#hybrid-search) 🔨
6. [Performance comparison](#performance-comparison)

---

## Overview

REM Database provides multiple search capabilities optimized for different use cases:

| Search Type | Use Case | Status | Latency | Scalability |
|-------------|----------|--------|---------|-------------|
| **HNSW vector** | Fast semantic search | ✅ Production | <5ms | 1M-10M vectors |
| **Fuzzy key lookup** | Typo-tolerant key search | ✅ Production | <10ms | 1M-100M keys |
| **BM25 full-text** | Document keyword search | 🔨 Planned | <15ms | 1M-100M docs |
| **DiskANN vector** | Billion-scale semantic | 🔨 Planned | <20ms | 10M-1B vectors |
| **Hybrid** | Best of vector + keyword | 🔨 Planned | <20ms | 1M-100M docs |

**Architecture philosophy:**
- Use existing HNSW for <1M vectors (fast, simple)
- Add fuzzy lookup for interactive key search
- Plan BM25 for document retrieval
- Plan DiskANN for >10M vectors (memory-efficient)

---

## Fuzzy key lookup (BM25)

### Overview

Fuzzy key lookup enhances the existing key index with **three-tier cascading search**:

1. **Exact match** (O(1)) - Direct hash lookup
2. **Prefix match** (O(log n + k)) - RocksDB prefix scan
3. **Fuzzy match** (O(terms × log n)) - BM25 keyword search

**Benefits:**
- Typo tolerance: "alise company" finds "alice@company.com"
- Partial matching: "alice" finds all alice emails
- Keyword search: "rust tokio" finds "https://docs.rust-lang.org/tokio"
- Zero maintenance: Index updates automatically on insert/update/delete

### Architecture

```text
Column Family: bm25_index
├─ term:rust:df → 150                      (document frequency)
├─ term:rust:posting:tenant:type:uuid → 5  (term frequency)
├─ doc:tenant:type:uuid:length → 320       (document length in tokens)
├─ meta:num_docs → 10000
└─ meta:avg_doc_length → 250.5

Column Family: key_index (existing)
└─ key:alice@company.com:uuid → tenant:type
```

**Design decision:** Separate `bm25_index` CF allows independent tuning and caching.

### Lookup flow

```text
Query: "alice company"

Stage 1: Exact match
┌─────────────────────────┐
│ Lookup: key:alice company:* │
│ CF: key_index           │
└─────────────────────────┘
         ↓ (no match)

Stage 2: Prefix match
┌─────────────────────────┐
│ Lookup: key:alice company* │
│ Scan: First 10 matches  │
│ CF: key_index           │
└─────────────────────────┘
         ↓ (no match)

Stage 3: Fuzzy BM25
┌─────────────────────────┐
│ Tokenize: ["alice", "company"] │
│ Lookup: term:alice:posting:*   │
│         term:company:posting:* │
│ Score: BM25(alice) + BM25(company) │
│ CF: bm25_index          │
└─────────────────────────┘
         ↓
Results: [(tenant:person:uuid, 0.85), ...]
```

**Performance:**
- Exact: <0.1ms (hash lookup)
- Prefix: <2ms (RocksDB prefix scan)
- Fuzzy: <10ms (BM25 scoring)

### BM25 scoring formula

```rust
/// BM25 score for term t in document d
fn bm25_score(
    tf: f32,           // Term frequency in document
    df: f32,           // Document frequency (docs containing term)
    doc_len: f32,      // Length of current document
    avg_doc_len: f32,  // Average document length
    total_docs: f32,   // Total documents
    k1: f32,           // Typically 1.2
    b: f32,            // Typically 0.75
) -> f32 {
    // IDF component
    let idf = ((total_docs - df + 0.5) / (df + 0.5) + 1.0).ln();

    // Normalization
    let norm = 1.0 - b + b * (doc_len / avg_doc_len);

    // BM25 formula
    idf * (tf * (k1 + 1.0)) / (tf + k1 * norm)
}
```

### Automatic index maintenance

**No manual rebuilds required!** The index updates automatically:

```rust
// Insert entity
db.insert("person", {
    "email": "alice@company.com",  // ← key_field
})?;

// Behind the scenes:
// 1. Store entity in RocksDB
// 2. Update key_index (existing)
// 3. Update BM25 index (NEW):
//    - Tokenize: ["alice", "company", "com"]
//    - Increment term:alice:df
//    - Add posting term:alice:posting:tenant:person:uuid
//    - Update meta:num_docs, meta:avg_doc_length

// Update entity
db.update(uuid, {"email": "alice@newcompany.com"})?;
// → Remove old key from both indexes
// → Add new key to both indexes

// Delete entity
db.delete(uuid)?;
// → Remove from both indexes
// → Decrement frequencies
```

### API usage

```rust
use percolate_rocks::Database;

let db = Database::open("./data")?;

// Exact lookup (existing)
let entity = db.get("person", "alice@company.com")?;

// Fuzzy lookup (NEW)
let results = db.lookup_fuzzy("alice company", 10)?;

for result in results {
    println!("{}: {} (score: {})",
        result.match_type,
        result.key_value,
        result.score
    );
}

// Output:
// Fuzzy: alice@company.com (0.85)
// Fuzzy: bob@company.com (0.42)
```

### CLI integration

```bash
# Exact lookup (existing)
rem get person "alice@company.com"

# Fuzzy lookup (NEW)
rem lookup "alice company" --limit 10

# Output:
# Match | Key                 | Type   | Score
# ------|---------------------|--------|-------
# Fuzzy | alice@company.com   | person | 0.85
# Fuzzy | alice@example.com   | person | 0.65
```

### Use cases

#### ✅ Use fuzzy lookup when:

1. **Users type queries** - Search bars, CLI, autocomplete
2. **Typos expected** - Human input, interactive tools
3. **Partial information** - "I think it's alice at some company..."
4. **Keyword-based search** - URIs, names, emails

#### ❌ Don't use fuzzy lookup when:

1. **Programmatic access** - Use `db.get(type, key)` for exact lookups
2. **High write volume** - Index overhead may be prohibitive
3. **Metadata filtering** - Use SQL predicates instead
4. **Semantic similarity** - Use vector search instead

### Performance characteristics

| Query Type | Dataset | Cold Cache | Warm Cache |
|------------|---------|-----------|------------|
| Exact | 1M keys | 0.1ms | 0.01ms |
| Prefix (10) | 1M keys | 2ms | 0.5ms |
| Fuzzy (2 terms) | 1M keys | 10ms | 5ms |
| Fuzzy (4 terms) | 1M keys | 15ms | 7ms |

**Write overhead:**
- Insert with key: +25% (2ms → 2.5ms)
- Update key: +33% (3ms → 4ms)
- Delete with key: +50% (1ms → 1.5ms)

**Index size:**
- 10k keys: ~0.5 MB
- 100k keys: ~5 MB
- 1M keys: ~50 MB

---

## Full-text search (BM25)

**Status:** 🔨 Planned (similar to fuzzy lookup, but for document content)

### Overview

Full-text BM25 extends the fuzzy lookup approach to **entire document content** instead of just key fields.

**Use cases:**
- Search articles by content: "machine learning tensorflow"
- Search documentation: "how to install rust"
- Search code comments: "authentication middleware"

### Architecture (planned)

```text
Column Family: bm25_fulltext
├─ term:learning:df → 500
├─ term:learning:posting:doc_uuid → {tf: 5, positions: [10, 45, ...]}
├─ doc:doc_uuid:stats → {length: 1500, fields: {...}}
└─ meta:corpus → {num_docs: 100000, avg_length: 1200}
```

**Key differences from fuzzy lookup:**
- Indexes **all text fields** (not just key field)
- Stores **term positions** for phrase queries
- Supports **field boosting** (title: 2x, content: 1x)
- Larger index size (~10-15% of document size)

### Implementation plan

See [Phase 2 in search-opt-plan.md](#phase-2-bm25-implementation) for detailed tasks.

**Estimated time:** 1-2 weeks

**Key components:**
1. Tokenizer with stemming and stopwords
2. Inverted index with position storage
3. BM25 scorer with field boosting
4. RocksDB persistence

---

## Disk-based vector search (DiskANN)

**Status:** 🔨 Planned (for >10M vectors)

### Overview

DiskANN is Microsoft's graph-based ANN algorithm optimized for disk storage:
- Stores graph + vectors on SSD (memory-mapped)
- Keeps compressed vectors in memory (product quantization)
- Scales to billions of vectors on single machine

**When to use:**
- ✅ >10M vectors - HNSW memory cost becomes prohibitive
- ✅ Limited RAM - Edge devices, cost-sensitive deployments
- ✅ Budget > latency - 20ms queries acceptable vs 5ms HNSW
- ✅ Fast SSD available - NVMe minimizes disk read penalty

**When NOT to use:**
- ✅ <1M vectors - HNSW is faster and simpler
- ✅ Latency critical - Need <5ms queries
- ✅ High QPS - Thousands of queries per second
- ✅ Frequently updated - HNSW handles updates better

### Architecture

```text
┌─────────────────────────────────────┐
│         DiskANN Index               │
├─────────────────────────────────────┤
│  Memory (200 MB for 1M vectors):    │
│  - Compressed vectors (PQ)          │
│  - Graph navigation cache           │
├─────────────────────────────────────┤
│  RocksDB or mmap (6 GB on SSD):     │
│  - Full-precision vectors           │
│  - Graph edges (Vamana)             │
│  - Metadata                         │
└─────────────────────────────────────┘
```

**Memory savings:** 97% less RAM (6.2GB → 200MB for 1M vectors)

### Performance comparison

**HNSW (current):**
```
Vectors: 1M × 1536 × 4 bytes = 6 GB
Graph: 1M × 32 neighbors × 4 bytes = 128 MB
Total: ~6.2 GB in RAM
Search: 2-3ms
```

**DiskANN:**
```
Memory:
  PQ vectors: 1M × 64 bytes = 64 MB
  Graph cache: 1M × 32 × 4 bytes = 128 MB
  Total: ~200 MB in RAM

Disk:
  Full vectors: 6 GB
  Graph: 128 MB
  Total: ~6.2 GB on SSD

Search: 8-16ms
```

**Trade-off:** 3-5x slower queries, but 30-50x less memory

### Implementation approaches

#### Option 1: Custom DiskANN on RocksDB (high effort)
- Full control, optimized for REM
- 8-12 weeks implementation
- Requires graph algorithm expertise

#### Option 2: Migrate to Qdrant (pragmatic)
- Production-ready with quantization
- Memory-mapped vectors
- RocksDB as metadata store
- Best pragmatic choice for >10M vectors

#### Option 3: Use Milvus with DiskANN
- Official DiskANN implementation
- Scales to billions
- Heavy infrastructure (Docker, etcd, MinIO)
- Only for >100M vectors with ops team

### Quick win: Add quantization to current HNSW

**Before implementing DiskANN, try scalar quantization:**

```rust
pub struct QuantizedVector {
    quantized: Vec<u8>,    // Compressed (1/4 size)
    min: f32,
    max: f32,
}

// Two-stage search
pub fn search_quantized(&self, query: &[f32], top_k: usize) -> Result<Vec<Uuid>> {
    // Stage 1: Search with quantized vectors (fast, approximate)
    let candidates = self.hnsw.search_quantized(query, top_k * 10)?;

    // Stage 2: Rescore with full precision (accurate)
    let rescored = candidates.iter()
        .map(|&id| {
            let full_vec = self.get_full_vector(id)?;
            let distance = cosine_distance(query, &full_vec);
            Ok((id, distance))
        })
        .collect::<Result<Vec<_>>>()?;

    Ok(rescored.into_iter().take(top_k).map(|(id, _)| id).collect())
}
```

**Impact:**
- 75% memory reduction (f32 → u8)
- <1% accuracy drop (with rescoring)
- 2-3x faster search (cache-friendly)
- Implementation: 1-2 weeks

**This gives you 80% of DiskANN's benefits with 10% of the effort.**

---

## Hybrid search

**Status:** 🔨 Planned

### Overview

Hybrid search combines **vector search** (semantic) with **keyword search** (exact matches) for best-of-both-worlds retrieval.

**Why hybrid?**
- Vector search: Finds semantically similar content
- Keyword search: Ensures exact term matches
- Combined: Better recall and precision

### Architecture

```text
User Query: "rust tokio async programming"
    ↓
┌───────────────────────────────────┐
│     Query Analysis (auto)          │
│  - Detect query type               │
│  - Choose fusion strategy          │
└───────────────────────────────────┘
    ↓
┌───────────────┬───────────────────┐
│   BM25 Search │  Vector Search    │
│   (keywords)  │  (semantic)       │
└───────┬───────┴───────┬───────────┘
        │               │
        ↓               ↓
    [docs with         [docs with
     exact terms]       similar meaning]
        │               │
        └───────┬───────┘
                ↓
    ┌───────────────────────┐
    │   Score Fusion (RRF)   │
    │  - Merge rankings      │
    │  - Deduplicate         │
    │  - Sort by fused score │
    └───────────────────────┘
                ↓
         Final Results
```

### Fusion algorithms

#### 1. Reciprocal rank fusion (RRF)

```rust
fn reciprocal_rank_fusion(
    bm25_results: &[ScoredDoc],
    vector_results: &[ScoredDoc],
    k: f32,  // Typically 60
) -> Vec<ScoredDoc> {
    let mut scores: HashMap<Uuid, f32> = HashMap::new();

    // Add BM25 contributions
    for (rank, doc) in bm25_results.iter().enumerate() {
        *scores.entry(doc.id).or_insert(0.0) += 1.0 / (k + rank as f32);
    }

    // Add vector contributions
    for (rank, doc) in vector_results.iter().enumerate() {
        *scores.entry(doc.id).or_insert(0.0) += 1.0 / (k + rank as f32);
    }

    // Sort by fused score
    let mut results: Vec<_> = scores.into_iter()
        .map(|(id, score)| ScoredDoc { id, score })
        .collect();
    results.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap());
    results
}
```

**Advantages:**
- No score normalization needed
- Robust to score scale differences
- Proven in IR research

#### 2. Weighted linear fusion

```rust
fn weighted_fusion(
    bm25_results: &[ScoredDoc],
    vector_results: &[ScoredDoc],
    alpha: f32,  // Weight for vector (e.g., 0.7)
    beta: f32,   // Weight for BM25 (e.g., 0.3)
) -> Vec<ScoredDoc> {
    // Normalize scores to [0, 1]
    let bm25_norm = normalize(bm25_results);
    let vector_norm = normalize(vector_results);

    // Combine
    let mut scores: HashMap<Uuid, f32> = HashMap::new();
    for doc in bm25_norm {
        *scores.entry(doc.id).or_insert(0.0) += beta * doc.score;
    }
    for doc in vector_norm {
        *scores.entry(doc.id).or_insert(0.0) += alpha * doc.score;
    }

    // Sort
    let mut results: Vec<_> = scores.into_iter()
        .map(|(id, score)| ScoredDoc { id, score })
        .collect();
    results.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap());
    results
}
```

**Advantages:**
- Tunable weights (emphasize semantic or keywords)
- Adaptive based on query type

### Two-stage retrieval

**For performance optimization:**

```rust
pub fn two_stage_search(
    &self,
    query: &str,
    top_k: usize,
) -> Result<Vec<ScoredDoc>> {
    // Stage 1: Fast keyword pre-filter (top-1000)
    let candidates = self.bm25.search(query, 1000)?;

    // Stage 2: Vector rerank top candidates (top-10)
    let query_embedding = self.embed(query)?;
    let rescored = candidates.iter()
        .map(|doc| {
            let embedding = self.get_embedding(doc.id)?;
            let score = cosine_similarity(&query_embedding, &embedding);
            Ok(ScoredDoc { id: doc.id, score })
        })
        .collect::<Result<Vec<_>>>()?;

    rescored.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap());
    Ok(rescored.into_iter().take(top_k).collect())
}
```

**Benefits:**
- Faster than full vector search (BM25 pre-filter is cheap)
- Better than BM25 alone (vector rerank improves relevance)
- Expected: +15-25% accuracy improvement

---

## Performance comparison

### Memory footprint (1M vectors, 1536 dims)

| Index Type | Memory | Disk | Total |
|------------|--------|------|-------|
| HNSW (current) | 6.2 GB | 0 | 6.2 GB |
| HNSW + SQ8 | 1.5 GB | 0 | 1.5 GB |
| DiskANN | 200 MB | 6.2 GB | 6.4 GB |
| BM25 (fuzzy) | 50 MB | 50 MB | 100 MB |
| BM25 (fulltext) | 500 MB | 500 MB | 1 GB |

### Query latency (p95)

| Index Type | <1M docs | 1M-10M docs | >10M docs |
|------------|----------|-------------|-----------|
| HNSW | 5ms | 10ms | ❌ OOM |
| HNSW + SQ8 | 5ms | 10ms | 50ms |
| DiskANN | 10ms | 20ms | 50ms |
| BM25 (fuzzy) | 10ms | 15ms | 20ms |
| BM25 (fulltext) | 15ms | 20ms | 30ms |
| Hybrid (RRF) | 20ms | 30ms | 50ms |

### Build time (1M docs)

| Index Type | Build Time | Update Cost |
|------------|-----------|-------------|
| HNSW | <1 hr | <1ms per doc |
| HNSW + SQ8 | <1 hr | <1ms per doc |
| DiskANN | <5 hr | ❌ Rebuild required |
| BM25 (fuzzy) | <30 min | <0.5ms per doc |
| BM25 (fulltext) | <30 min | <0.5ms per doc |

### Scalability limits

| Index Type | Max Docs | Bottleneck |
|------------|----------|------------|
| HNSW | 10M | Memory |
| HNSW + SQ8 | 50M | Memory + search time |
| DiskANN | 1B+ | Disk I/O |
| BM25 (fuzzy) | 100M | Index size |
| BM25 (fulltext) | 100M | Index size |

---

## Implementation roadmap

### Phase 1: Fuzzy lookup ✅ (completed)
- [x] BM25 index for key fields
- [x] Three-tier cascading search
- [x] Automatic index maintenance
- [x] Integration tests
- [x] CLI integration

### Phase 2: Full-text BM25 🔨 (planned)
- [ ] Tokenizer with stemming
- [ ] Inverted index with positions
- [ ] Field boosting
- [ ] RocksDB persistence
- [ ] CLI integration

**Estimated time:** 1-2 weeks

### Phase 3: DiskANN 🔨 (planned)
- [ ] Vamana graph construction
- [ ] Greedy search algorithm
- [ ] Product quantization
- [ ] Memory-mapped storage
- [ ] Benchmarking

**Estimated time:** 8-12 weeks (or use Qdrant)

### Phase 4: Hybrid search 🔨 (planned)
- [ ] RRF fusion algorithm
- [ ] Weighted fusion
- [ ] Two-stage retrieval
- [ ] Query analysis
- [ ] Adaptive weighting

**Estimated time:** 1-2 weeks

### Phase 5: Optimization 🔨 (planned)
- [ ] SIMD distance functions
- [ ] Parallel graph construction
- [ ] BM25 posting compression
- [ ] Batch search
- [ ] Comprehensive benchmarks

**Estimated time:** 1-2 weeks

---

## References

### BM25 + RocksDB
- Rockset Converged Index: https://rockset.com/blog/how-rocksets-converged-index-powers-real-time-analytics/
- Sonic (RocksDB-backed search): https://github.com/valeriansaliou/sonic
- Tantivy BM25: https://docs.rs/tantivy/latest/src/tantivy/query/bm25.rs.html

### DiskANN
- DiskANN paper: https://suhasjs.github.io/files/diskann_neurips19.pdf
- CoreNN (RocksDB + Vamana): https://blog.wilsonl.in/corenn/
- Microsoft DiskANN: https://github.com/microsoft/DiskANN
- Qdrant with quantization: https://qdrant.tech/articles/hybrid-search/

### Hybrid search
- Reciprocal Rank Fusion: https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf
- Two-stage retrieval: https://arxiv.org/abs/2004.08588
