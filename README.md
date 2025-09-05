# AppGestaoTI Agent

Agente de telemetria e inventário para o sistema **AppGestaoTI**, desenvolvido pela **RabeloTech**.

O agente roda como **serviço do Windows** (via [WinSW](https://github.com/winsw/winsw)) e coleta periodicamente:
- **Métricas** (CPU, memória, disco, processos, uptime, sessão de usuário ativo)
- **Inventário** (hardware, rede, sistema operacional)
- **Sessões ativas**

Os dados são enviados ao backend do AppGestaoTI através das rotas:

- `POST /api/telemetry/enroll`
- `POST /api/telemetry/inventory`
- `POST /api/telemetry/metrics`

---

## 📦 Estrutura do Instalador

O instalador único detecta a arquitetura do Windows e instala a versão correta do agente:



---

## 🚀 Instalação

1. Baixe o instalador **`AppGestaoTI-Agent-Setup.exe`**.
2. Execute como **Administrador** (clique direito → *Executar como administrador*).
3. O instalador vai:
   - Copiar os binários corretos para a pasta destino.
   - Registrar o serviço `AppGestaoTI Agent`.
   - Iniciar o serviço automaticamente.

---

## ✅ Validação

### 1. Verificar no **Services.msc**
- Abra `services.msc`
- Procure por **AppGestaoTI Agent**
- O status deve estar **Em execução (Running)**

### 2. Verificar via prompt
```powershell
sc query "appgestaoti-agent"




appgestaoti-agent/
├─ app/                     # código do agente
│  ├─ core/
│  ├─ daemon/
│  ├─ system/
│  ├─ workflows/
│  ├─ cli/
│  └─ ui_tray/
│
├─ tests/                   # <-- pasta de testes automatizados
│  ├─ __init__.py
│  ├─ test_core_state.py         # testa leitura/gravação do state
│  ├─ test_core_http.py          # testa headers e clientes http
│  ├─ test_workflow_enroll.py    # testa fluxo de enroll com mock de backend
│  ├─ test_workflow_inventory.py # testa envio de inventário e deduplicação
│  ├─ test_workflow_metrics.py   # testa envio de métricas
│  ├─ test_system_inventory.py   # testa coleta de inventário (mock psutil/powershell)
│  └─ test_system_metrics.py     # testa coleta de métricas
│
├─ installer/
├─ requirements.txt
├─ README.md
└─ pyproject.toml / setup.cfg    # (opcional) configuração de build/lint/test
