# Synthetic compact-Parquet corpus

This directory is a tiny interface fixture for the public repository. Every
record is invented, marked `synthetic=true`, and released as CC0 test data. It
contains no paper text and is **not citable scientific evidence**.

Use it exactly as a future public, allow-listed corpus package:

```bash
export GOAI_LOCAL_CORPUS_ROOTS="$PWD/examples/demo_corpus"
.venv/bin/python tools/preflight.py --corpus
```

The lit-search MCP tools can then call `local_corpus_status`,
`grep_local_corpus`, `read_local_document`, and `lookup_local_doi`. For example,
the synthetic DOI `10.0000/goai.demo.byzso` resolves inside `corpus.parquet`
without the private SQLite/shard index.

Rebuild the binary fixture after editing `demo_records.json`:

```bash
.venv/bin/python tools/build_demo_corpus.py
```
