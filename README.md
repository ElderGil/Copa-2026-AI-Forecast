# Copa 2026 AI Forecast 🇧🇷

[![Automated Review](https://img.shields.io/badge/Reviewer_Gate-Passed-success?style=flat-square)](#-o-experimento-multi-agente-builder--reviewer)
[![Python Version](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square)](https://www.python.org/)
[![Spec Kit Method](https://img.shields.io/badge/Workflow-Speckit_/_Specify-blueviolet?style=flat-square)](#-especificações-e-artefatos-do-spec-kit)

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
* **Modelo de Partida Multiclasse ($V/E/D$)**: Calculamos as probabilidades do tempo regulamentar, permitindo empates na fase de grupos — o maior gerador de zebras e redefinições de chaves.
* **Simulação de Chaveamento Real Monte Carlo (10.000+ rodadas)**: O motor de regras simula o torneio de ponta a ponta, implementando fielmente o novo e complexo regulamento da Copa de 2026 (48 times, 12 grupos de 4 e repescagem dos 8 melhores terceiros colocados via algoritmos de backtracking).
* **Calibração de Probabilidades e Zero-Leakage**: Modelos de classificação sofrem calibração estrita e são avaliados via **Log Loss** e **Brier Score** para garantir que probabilidades sejam confiáveis. A validação temporal (*rolling-origin*) impede vazamento de dados do futuro.

---

## 📂 Especificações e Artefatos do Spec Kit

Todo o planejamento e pesquisa do projeto estão disponíveis de forma transparente:

* **Constituição do Projeto**: [.specify/memory/constitution.md](file:///.specify/memory/constitution.md)
* **Especificação de Funcionalidades**: [specs/001-copa-forecast/spec.md](file:///specs/001-copa-forecast/spec.md)
* **Plano de Implementação**: [specs/001-copa-forecast/plan.md](file:///specs/001-copa-forecast/plan.md)
* **Notas de Pesquisa Matemática**: [specs/001-copa-forecast/research.md](file:///specs/001-copa-forecast/research.md)
* **Modelagem de Entidades de Dados**: [specs/001-copa-forecast/data-model.md](file:///specs/001-copa-forecast/data-model.md)
* **Contratos de Configuração**: [specs/001-copa-forecast/contracts/forecast-config.schema.yaml](file:///specs/001-copa-forecast/contracts/forecast-config.schema.yaml)
* **Lista de Tarefas da Spec**: [specs/001-copa-forecast/tasks.md](file:///specs/001-copa-forecast/tasks.md)

---

## 🛠️ Como Executar e Validar

### 1. Configurar o Ambiente Virtual
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
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

---

## 👥 Equipe de Desenvolvimento (Experimento Multi-Agente)

Este repositório foi construído de forma colaborativa por um desenvolvedor humano coordenando agentes autônomos de IA sob a metodologia Speckit:

| Contribuidor | Função | Natureza | Provedor |
| :--- | :--- | :--- | :--- |
| 🧑‍💻 **Elder Gil** | Human Tech Lead & Product Owner | Humano | Engenharia Geral |
| 🤖 **Agente Construtor (Codex/Constructor)** | Engenheiro de Software | Agente de IA | OpenAI / Gemini |
| 🤖 **Agente Revisor (Antigravity/Gemini 3.5)** | Arquiteto de Software & QA Gatekeeper | Agente de IA | Google DeepMind |


Co-authored-by: Antigravity Revisor <antigravity-agent@google.com>
Co-authored-by: Codex Construtor <codex-agent@openai.com>

<!-- validation-stats:start -->
## Estatísticas da Validação do Modelo

**Última atualização dos dados:** `2026-06-18`
**Modelo:** `Copa 2026 AI Forecast`
**Baseline principal:** `FIFA SUM-style Elo`

| Métrica | Copa 2026 AI Forecast | Baseline principal | Delta | Status |
|---|---:|---:|---:|---|
| Amostras avaliadas<br><sub><em>Partidas do período 2025-06-18 a 2026-06-18; cada previsão usa apenas jogos anteriores à partida avaliada.</em></sub> | 407 | - | - | Info |
| Acurácia 1X2<br><sub><em>Percentual de vezes em que o resultado mais provável foi o resultado real: vitória mandante, empate ou vitória visitante.</em></sub> | 57.00% | 56.27% | +0.74 p.p. | Atenção |
| Brier score<br><sub><em>Erro probabilístico multiclasses; quanto menor, melhor. Zero seria uma previsão perfeita.</em></sub> | 0.5876 | 0.6018 | -0.0142 | Atenção |
| Log loss<br><sub><em>Pune previsões confiantes e erradas; quanto menor, melhor. É mais severo que o Brier.</em></sub> | 1.0556 | 1.0082 | 0.0475 | Ruim |
| ECE calibração<br><sub><em>Expected Calibration Error; mede se a confiança prevista combina com a frequência real observada.</em></sub> | 0.1011 | - | - | Atenção |
| MCE calibração<br><sub><em>Maximum Calibration Error; pior desvio de calibração entre as faixas de confiança.</em></sub> | 0.2355 | - | - | Atenção |

**Legenda:** `Bom` melhora o baseline principal ou está em faixa saudável; `Atenção` indica ganho pequeno ou calibração a monitorar; `Ruim` indica resultado pior que o benchmark ou calibração fraca.

<sub><em>Baseline principal: FIFA/Coca-Cola World Ranking SUM methodology; computed locally from FIFA match records. Não redistribuímos tabela externa de ranking ou odds; o benchmark é calculado localmente a partir dos registros oficiais FIFA já ingeridos pelo pipeline.</em></sub>
<!-- validation-stats:end -->
