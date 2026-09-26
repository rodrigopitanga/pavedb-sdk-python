<!-- (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

## 0.1.5 — 2026-09-26

### Infrastructure
- Support Twine 7 GitLab uploads
- Drop disabled SDK package registry
- Restore GitLab package publishing

### SDK
- Cover the PaveDB 0.9.7 archive, reindex, create and search options

### Known Issues
- The `pavedb` local provider (`connect("./data")`) does not yet implement the
  new collection archive and reindex methods, nor the new create and search
  options; use an HTTP client for them. Tracked as
  [B91](https://gitlab.com/flowlexi/pavedb/-/work_items/339).

---

## 0.1.4 — 2026-08-13

### SDK
- Add runnable book examples (P1-66)
- Fix book example cleanup (P1-66)
- Remove unused retrieval state (P1-66)
- Remove unused evidence state (P1-66)
- Assert generated examples index in sdist (P1-66)
- Preserve every Lattice sample row (P1-66)

### Infrastructure
- Publish SDK releases from changelog
- Match the changelog format and check packaging on every pipeline
- Adopt core's Makefile dialect and release semantics
- Pick the interpreter from the declared Python range

---

## 0.1.3 — 2026-08-03

- Add generated API reference and example documentation.

---

## 0.1.2 — 2026-07-28

- Add raw-vector collection support.

---

## 0.1.1 — 2026-06-20

- Add runnable HTTP examples.

---

## 0.1.0 — 2026-06-20

- Introduce the Python HTTP client.

---
