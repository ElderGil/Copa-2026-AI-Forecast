# Copa 2026 AI Forecast 🇧🇷

[![Automated Review](https://img.shields.io/badge/Reviewer_Gate-Passed-success?style=flat-square)](#-o-experimento-multi-agente-builder--reviewer)
[![Python Version](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square)](https://www.python.org/)
[![Spec Kit Method](https://img.shields.io/badge/Workflow-Speckit_/_Specify-blueviolet?style=flat-square)](#-especificações-e-artefatos-do-spec-kit)
[![Daily Forecast](https://github.com/ElderGil/Copa-2026-AI-Forecast/actions/workflows/daily-forecast.yml/badge.svg)](https://github.com/ElderGil/Copa-2026-AI-Forecast/actions/workflows/daily-forecast.yml)

Um projeto analítico para prever o campeão da **Copa do Mundo FIFA 2026** utilizando ingestão oficial de dados da FIFA e modelagem probabilística baseada em recência esportiva.

---

## 🤖 O Experimento Multi-Agente (Builder + Reviewer)

Este repositório é, antes de tudo, um **experimento prático de engenharia de software autônoma**. Ele foi totalmente concebido, implementado, testado e validado através da colaboração estruturada entre dois agentes de IA coordenados por um desenvolvedor humano:

1. **Agente Construtor (Builder Agent)**: Responsável por analisar as especificações técnicas, desenhar os contratos de dados e implementar incrementalmente as funcionalidades (ETL, motores de regras e simulação preditiva).
2. **Agente Revisor (Reviewer Agent - Antigravity)**: Atua como o *Quality Gatekeeper* do projeto. Avalia decisões lógicas de ciência de dados (vazamento temporal, calibração multiclasse), realiza revisões arquiteturais e garante a conformidade com a constituição do repositório antes de autorizar os commits e pushes.

### 📐 Metodologia Spec-Driven (Speckit / Specify)
O projeto segue a filosofia rigorosa de desenvolvimento baseado em especificações:
* Nenhuma linha de código é escrita sem que a especificação da classificação (`spec.md`) e o plano de implementação (`plan.md`) estejam aprovados.
* Um **Daemon de Desenvolvimento local (`watch_and_verify.py`)** monitora os arquivos em tempo real e re-executa a validação qualitativa e a suíte de testes de forma contínua a cada alteração.

---

## ⚽ Premissas de Modelagem Esportiva

Muitos modelos de previsão de futebol falham por usar estatísticas históricas antigas e ignorar o chaveamento do torneio. Este projeto adota cinco decisões metodológicas estritas para garantir rigor estatístico:

* **FIFA como Fonte Única da Verdade**: Tabelas, grupos, calendários e resultados oficiais em tempo real vêm diretamente da ingestão de payloads originais da FIFA (ETL auditável).
* **Recência Esportiva com Decaimento Exponencial**: Em vez do prestígio histórico acumulado, o modelo foca no momento atual das seleções (janelas de 12 e 24 meses). Partidas mais antigas sofrem decaimento exponencial de peso (half-life parametrizável).
* **Modelo de Partida Multiclasse ($V/E/D$)**: Calculamos as probabilidades do tempo regulamentar. A probabilidade de empate é **dinâmica** — máxima em confrontos equilibrados (podendo ser o resultado mais provável) e decrescente conforme a diferença de força aumenta — e um termo de **mando de campo** ajusta jogos não neutros.
* **Simulação de Chaveamento Real Monte Carlo (10.000+ rodadas)**: O motor de regras simula o torneio de ponta a ponta cobrindo o formato de 2026 (48 times, 12 grupos de 4 e repescagem dos 8 melhores terceiros via backtracking). Os critérios de desempate cobrem pontos, saldo, gols pró e confronto direto; *fair-play* e sorteio ainda não são modelados.
* **Mata-mata Ancorado na Realidade**: Resultados já decididos do mata-mata são respeitados de forma determinística — uma seleção eliminada vai imediatamente a **0% de chance de título** (e nas fases seguintes), e disputas por **pênaltis** são honradas pelo placar real. A partir das oitavas o chaveamento da simulação é semeado pelo **sorteio oficial da FIFA** (via número de partida), garantindo que cada confronto bata com a chave real. A página pública exibe o **caminho do título ao vivo** (16-avos → final, com vagas "A definir") e ajusta o destaque para *top 10 → 8 (quartas) → 4 (semis) → 2 (final)*. O modelo estatístico de probabilidade de cada partida permanece inalterado.
* **Calibração de Probabilidades e Zero-Leakage**: As probabilidades 1X2 passam por **temperature scaling** ajustado no backtest *rolling-origin* e são avaliadas via **Log Loss** e **Brier Score**. A validação temporal impede vazamento de dados do futuro, com um guard auditado (`assert_no_future_records`) na saída do ETL.

---

## 📂 Especificações e Artefatos do Spec Kit

Todo o planejamento e pesquisa do projeto estão disponíveis de forma transparente:

* **Constituição do Projeto**: [.specify/memory/constitution.md](.specify/memory/constitution.md)
* **Especificação de Funcionalidades**: [specs/001-copa-forecast/spec.md](specs/001-copa-forecast/spec.md)
* **Plano de Implementação**: [specs/001-copa-forecast/plan.md](specs/001-copa-forecast/plan.md)
* **Notas de Pesquisa Matemática**: [specs/001-copa-forecast/research.md](specs/001-copa-forecast/research.md)
* **Modelagem de Entidades de Dados**: [specs/001-copa-forecast/data-model.md](specs/001-copa-forecast/data-model.md)
* **Contratos de Configuração**: [specs/001-copa-forecast/contracts/forecast-config.schema.yaml](specs/001-copa-forecast/contracts/forecast-config.schema.yaml)
* **Lista de Tarefas da Spec**: [specs/001-copa-forecast/tasks.md](specs/001-copa-forecast/tasks.md)
* **Remediação de Credibilidade (feature 002)**: [specs/002-credibility-remediation/spec.md](specs/002-credibility-remediation/spec.md)
* **Operação diária e publicação**: [docs/operations.md](docs/operations.md)

---

## 🛠️ Como Executar e Validar

### 1. Configurar o Ambiente Virtual
> **Requer Python 3.11 ou superior.** Em macOS, `python3` pode apontar para o
> Python 3.9 do sistema (sem `datetime.UTC` nem `zip(..., strict=...)`), o que
> quebra os testes — use o binário `python3.11` explicitamente.
```bash
python3.11 -m venv .venv
source .venv/bin/activate
python --version            # confirme: Python 3.11.x ou superior
pip install -e ".[dev]"     # inclui pytest e ruff
```

### 2. Rodar a Validação Automatizada (Quality Gate)
Este comando valida a estrutura física dos arquivos, integridade de contratos e executa a suíte de testes de unidade e integração:
```bash
.venv/bin/python scripts/verify_implementation.py
```

### 3. Rodar o Daemon do Watcher (Modo Desenvolvedor)
Para manter o ciclo de auto-revisão ativo durante o desenvolvimento:
```bash
.venv/bin/python scripts/watch_and_verify.py
```

### 4. Atualizar Previsões e Publicar
O repositório contém um workflow diário em `.github/workflows/daily-forecast.yml`.
Ele prepara uma configuração datada, roda ETL FIFA, gera o forecast, atualiza as
estatísticas de validação do README, executa `scripts/verify_implementation.py`
e publica `public/` no GitHub Pages.

O agendamento roda às `07:17 UTC` (≈ `04:17` em America/Sao_Paulo; o cron do
GitHub Actions é sempre UTC), com acionamento manual pela aba Actions. Detalhes
operacionais estão em [docs/operations.md](docs/operations.md).

---

## 👥 Equipe de Desenvolvimento (Experimento Multi-Agente)

Este repositório foi construído de forma colaborativa por um desenvolvedor humano coordenando agentes autônomos de IA sob a metodologia Speckit:

| Contribuidor | Função | Natureza | Provedor |
| :--- | :--- | :--- | :--- |
| 🧑‍💻 **Elder Gil** | Human Tech Lead & Product Owner | Humano | Engenharia Geral |
| 🤖 **Agente Construtor (Codex)** | Engenheiro de Software | Agente de IA | OpenAI |
| 🤖 **Agente Revisor (Antigravity)** | Arquiteto de Software & QA Gatekeeper | Agente de IA | Google (Gemini) |

<!-- validation-stats:start -->
## Estatísticas da Validação do Modelo

**Última atualização dos dados:** `2026-07-05`
**Modelo:** `Copa 2026 AI Forecast`
**Baseline principal:** `Benchmark local estilo Elo/SUM (calculado dos jogos FIFA — não é ranking oficial)`
**Calibração:** temperature scaling (T=2.4666)

| Métrica | Copa 2026 AI Forecast | Baseline principal | Delta | Status |
|---|---:|---:|---:|---|
| Amostras avaliadas<br><sub><em>Partidas do período 2025-07-05 a 2026-07-05; cada previsão usa apenas jogos anteriores à partida avaliada.</em></sub> | 506 | - | - | Info |
| Acurácia 1X2<br><sub><em>Percentual de vezes em que o resultado mais provável foi o resultado real: vitória mandante, empate ou vitória visitante.</em></sub> | 62.45% | 53.36% | +9.09 p.p. | Bom |
| Brier score<br><sub><em>Erro probabilístico multiclasses (após calibração); quanto menor, melhor. Zero seria uma previsão perfeita.</em></sub> | 0.5086 | 0.5802 | -0.0716 | Bom |
| Log loss<br><sub><em>Pune previsões confiantes e erradas (após calibração); quanto menor, melhor. É mais severo que o Brier.</em></sub> | 0.8913 | 0.9728 | -0.0815 | Bom |
| ECE calibração<br><sub><em>Expected Calibration Error; mede se a confiança prevista combina com a frequência real observada.</em></sub> | 0.1211 | - | - | Atenção |
| MCE calibração<br><sub><em>Maximum Calibration Error; pior desvio de calibração entre as faixas de confiança.</em></sub> | 0.2249 | - | - | Atenção |

**Legenda:** `Bom` melhora o baseline principal ou está em faixa saudável; `Atenção` indica ganho pequeno ou calibração a monitorar; `Ruim` indica resultado pior que o benchmark ou calibração fraca.

<sub><em>Baseline principal: benchmark local inspirado na metodologia Elo/SUM da FIFA/Coca-Cola, calculado a partir dos próprios registros de partidas FIFA (não é o ranking oficial publicado). Não redistribuímos tabela externa de ranking ou odds; o benchmark é calculado localmente a partir dos registros oficiais FIFA já ingeridos pelo pipeline.</em></sub>
<!-- validation-stats:end -->
