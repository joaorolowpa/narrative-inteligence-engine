# AGENTS.md

## Objetivo
Guia operacional para contribuir neste monorepo com consistencia de arquitetura, testes e historico de commits.

## Visao Do Sistema
- `services/api`: API FastAPI com endpoint de saude `GET /health` em `http://localhost:8000/health`.
- `services/worker`: worker RQ consumindo fila `default` via Redis (`REDIS_URL`).
- `services/ui`: interface Streamlit em `http://localhost:8501`.
- `libs/core`: biblioteca compartilhada de dominio, schemas e repositorios.
- `infra/compose/docker-compose.yml`: orquestracao local de `api`, `worker`, `ui`, `redis`.
- `tests`: suite de testes Pytest (atualmente com teste de healthcheck).

## Fluxo De Execucao Local
- Subir stack: `docker compose -f infra/compose/docker-compose.yml up --build -d`
- Derrubar stack: `docker compose -f infra/compose/docker-compose.yml down`
- Rodar testes no container da API: `docker compose -f infra/compose/docker-compose.yml run --rm api pytest -q`
- Rodar lint no container da API: `docker compose -f infra/compose/docker-compose.yml run --rm api ruff check .`

## Boas Praticas
- Sempre validar endpoint de saude da API apos alteracoes (`/health`).
- Para mudancas de comportamento, criar/atualizar testes em `tests/` no mesmo commit.
- Manter compatibilidade com Python 3.11 e configuracao do `pyproject.toml`.
- Evitar acoplamento entre servicos; compartilhar contratos em `libs/core`.
- Nao commitar segredos, tokens ou credenciais.
- Preferir ajustes reprodutiveis via `docker compose` ao inves de passos manuais.

## Padrao De Commits (Indicacoes)
Seguir Conventional Commits no formato:

`<tipo>(<escopo opcional>): <resumo no imperativo>`

Tipos permitidos:
- `feat`: nova funcionalidade
- `fix`: correcao de bug
- `build`: mudancas de build/dependencias/container
- `test`: adicao/ajuste de testes
- `docs`: documentacao
- `refactor`: refatoracao sem alterar comportamento
- `chore`: tarefas de manutencao
- `ci`: pipeline/automacao

Regras:
- Resumo curto e objetivo (ate ~72 caracteres).
- Um assunto principal por commit.
- Quando houver impacto estrutural, usar escopo: `api`, `worker`, `ui`, `core`, `infra`, `repo`, `agents`.

Exemplos:
- `feat(api): adiciona endpoint de healthcheck`
- `test(api): valida resposta do endpoint /health`
- `build(ui): aumenta timeout e retries do pip no Dockerfile`
- `docs(agents): define boas praticas e padrao de commits`
