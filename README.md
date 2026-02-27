# narrative-inteligence-engine

Monorepo com:

- `services/api` (FastAPI)
- `services/worker` (RQ)
- `services/ui` (Streamlit)
- `libs/core` (dominio, schemas e repos)
- `infra/compose` (docker-compose)
- `tests` (tests compartilhados)

## Quickstart

```bash
make up
curl localhost:8000/health
make test
```
