# Cube Budget Optimizer

Ferramenta Python dockerizada que importa listas de cartas Magic: The Gathering, consulta preços na LigaMagic e encontra a combinação de compras com o **menor número de lojas** e depois o **menor preço total**.

## Requisitos

- Docker
- Docker Compose

Não é necessária instalação local do Python.

## Início Rápido

```bash
# Copiar variáveis de ambiente
cp .env.example .env

# Construir a imagem
docker compose build

# Verificar saúde do sistema
docker compose run --rm app doctor

# Otimizar uma lista de cartas
docker compose run --rm app optimize /app/data/input/cube.txt

# Ver estatísticas
docker compose run --rm app stats

# Limpar containers parados do projeto
docker compose down --remove-orphans
```

Coloque sua lista de cartas em `data/input/cube.txt` (uma carta por linha).

## Comandos CLI

| Comando | Descrição |
|---------|-----------|
| `optimize <file>` | Pipeline completo: scrape → otimização → relatórios |
| `update-cache [file]` | Força re-scrape das cartas |
| `report [--run-id UUID]` | Gera relatórios de um run existente |
| `export [--format excel\|csv\|markdown]` | Exporta resultados |
| `clean [--cache\|--logs\|--reports\|--all]` | Limpeza de dados |
| `doctor` | Verificação de saúde do sistema |
| `stats` | Estatísticas do banco de dados |

### Opções do optimize

```bash
docker compose run --rm app optimize /app/data/input/cube.txt \
  --fresh          # Ignora cache
  --resume         # Retoma run interrompido
  --max-stores 5   # Limite de lojas
  --solver auto    # auto | greedy | ilp | ortools
  --output-dir /app/reports
```

## Testes

```bash
docker compose run --rm app pytest
docker compose run --rm app pytest --cov=cube_budget --cov-report=term-missing
```

## Estrutura do Projeto

```
src/cube_budget/
├── cli/           # Interface Typer + Rich
├── config/        # Configuração YAML
├── core/          # Modelos de domínio
├── services/      # Orquestração
├── providers/     # Scraper LigaMagic
├── database/      # SQLite + repositórios
├── cache/         # Cache inteligente
├── optimizer/     # Algoritmos de otimização
├── reports/       # Excel, CSV, Markdown
└── utils/         # Logger, retry, etc.
```

## Volumes Docker

| Volume | Conteúdo |
|--------|----------|
| `data/db/` | Banco SQLite |
| `data/cache/` | Cache em disco |
| `reports/` | Relatórios gerados |
| `logs/` | Logs Loguru |
| `data/input/` | Listas de cartas |

## Configuração

Edite `config/default.yaml` ou use variáveis de ambiente (`.env`):

```env
CUBE_LOG_LEVEL=INFO
CUBE_HEADLESS=true
CUBE_CACHE_TTL_HOURS=24
```

## Algoritmo de Otimização

Pipeline híbrido em 3 estágios:

1. **Greedy Set Cover** — warm-start e upper bound
2. **PuLP/CBC ou OR-Tools CP-SAT** — solução ótima (seleção automática por tamanho)
3. **Minimização de preço** — fixando o número mínimo de lojas

Prioridade: menor lojas → menor preço (frete não considerado).

## Dev Container

Abra o projeto no Cursor/VS Code e selecione "Reopen in Container" para ambiente de desenvolvimento completo.

## Distribuição

```bash
# Build produção
docker build -f docker/Dockerfile.prod -t cube-budget-optimizer:latest .

# Publicar no GHCR
docker tag cube-budget-optimizer:latest ghcr.io/USER/cube-budget-optimizer:latest
docker push ghcr.io/USER/cube-budget-optimizer:latest

# Uso sem clone
docker run --rm \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/reports:/app/reports \
  ghcr.io/USER/cube-budget-optimizer:latest \
  optimize /app/data/input/cube.txt
```

## Licença

MIT
