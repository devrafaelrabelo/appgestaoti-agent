# inicia o repo
git init
git add .
git commit -m "chore(repo): initial empty repo"

# cria develop
git checkout -b develop

# ===== Sprint 1 =====

# Commit 1: setup de tooling e testes
git checkout -b feature/ci-and-tests develop
git add requirements.txt requirements-dev.txt pytest.ini .gitignore
git commit -m "chore(ci): add base tooling (pytest, respx) and deps"

# Commit 2: esqueleto do app (config/logging/entrypoint)
git add run_appgestaoti.py appgestaoti_agent/__init__.py appgestaoti_agent/logging_config.py appgestaoti_agent/config.py
git commit -m "feat(core): add entrypoint, logging setup and TOML config loader"

# Commit 3: transporte http assíncrono + enrollment
git add appgestaoti_agent/transport/http_client.py appgestaoti_agent/transport/enrollment.py
git commit -m "feat(transport): AsyncClient with http2 fallback and enrollment call"

# Commit 4: storage e serviços (scheduler+agent)
git add appgestaoti_agent/storage/device_store.py appgestaoti_agent/services/scheduler.py appgestaoti_agent/services/agent_service.py
git commit -m "feat(agent): device store, scheduler loop (iterations), and AgentService"

# Commit 5: testes
git add tests/conftest.py tests/test_transport.py tests/test_agent_service.py
git commit -m "test: add respx/httpx tests for transport and agent service"

# Push e PR
git push -u origin feature/ci-and-tests
# (abra PR: base=develop, compare=feature/ci-and-tests; após review → merge)

# atualizar develop local
git checkout develop
git pull

# (opcional) cortar release alpha
git checkout -b release/0.1.0-alpha.1
# se quiser editar CHANGELOG.md aqui, faça e comite:
# git add CHANGELOG.md && git commit -m "docs(release): v0.1.0-alpha.1"
git push -u origin release/0.1.0-alpha.1
# abra PR base=main; após merge:
git checkout main
git pull
git tag -a v0.1.0-alpha.1 -m "appgestaoti_agent 0.1.0-alpha.1"
git push origin v0.1.0-alpha.1