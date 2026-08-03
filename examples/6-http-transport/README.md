# HTTP transport

Run from an SDK checkout after installing `pavedb` alongside this SDK:

```bash
PYTHONPATH=examples python examples/6-http-transport/http_transport.py
```

The program starts a real local `pavesrv`, queries it through the SDK HTTP client,
then stops it and removes its temporary data. This book-derived example is
MIT-licensed; see `examples/LICENSE`.
