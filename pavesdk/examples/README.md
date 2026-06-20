# PaveDB SDK Examples

These examples use the HTTP client against a running PaveDB server.

They are installed with `pavedb-sdk` and can be run with:

```bash
python -m pavesdk.examples.http_search
python -m pavesdk.examples.observability
```

Set connection details with environment variables:

```bash
export PAVEDB_URL=http://localhost:8086
export PAVEDB_API_KEY=super-sekret
export PAVEDB_TENANT=demo
export PAVEDB_COLLECTION=twenty-thousand-leagues
```

The examples use the SDK demo file at `../demo/20k_leagues.txt`, relative to
the SDK checkout. That file is Project Gutenberg eBook #164, _Twenty Thousand
Leagues under the Sea_ by Jules Verne, and includes its own Project Gutenberg
header/license text.
