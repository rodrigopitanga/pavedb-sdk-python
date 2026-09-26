<!-- (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# Roadmap

Parity of `HttpClient` and the `BaseClient` surface (which the `pavedb`
package's local provider also implements) with the PaveDB `/v1` contract is
tracked here. Keys refer to the core PaveDB roadmap.

## Queue

- PaveDB 0.9.7 collection archive: dump, restore as new and restore over an
  existing collection (P1-54).
- PaveDB 0.9.7 reindex jobs: start, get, cancel, pause/resume (P1-55).
- `create_collection` options: add the 0.9.7 fields `embedder`,
  `search_mode`, `chunking`, `priority_key`.
- `search` options: add the 0.9.7 fields `mode` and `content_filter`.
