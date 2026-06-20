<!-- (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com> -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# PaveDB Python Client

Python client package for PaveDB.

## Install

```bash
pip install pavedb-client
```

Install the PaveDB local engine separately when local persisted mode is needed:

```bash
pip install pavedb-client pavedb
```

## Planned Shape

- `pavedb-client` provides the shared client API and HTTP transport.
- `pavedb` provides the optional local provider for in-process persisted mode.
- `connect("https://...")` uses HTTP.
- `connect("./data")` uses the local provider when `pavedb` is installed.

The PaveDB server repository remains the source of truth for the OpenAPI
contract.

The HTTP client mirrors the local `Client -> Collection` handle shape exposed
by the PaveDB package.
