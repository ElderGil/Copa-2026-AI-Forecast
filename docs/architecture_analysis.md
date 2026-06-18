# Analise de Arquitetura e Ciência de Dados: Copa 2026 AI Forecast

Este documento apresenta uma revisão crítica de arquitetura e modelagem preditiva para o projeto **Copa 2026 AI Forecast**. Ele atua como guia técnico e de validação para o agente executor.

---

## 1. Avaliação Crítica da Arquitetura do Sistema

A estrutura de pacotes proposta no `plan.md` está correta e segue boas práticas de separação de conceitos em engenharia de machine learning local:

```text
src/copa_forecast/
├── data/         # Ingestão raw, parsing, normalização e validação de contratos
├── features/     # Engenharia de atributos (janelas temporais e prevenção de leakage)
├── models/       # Modelagem preditiva (baselines, modelos de partida e calibração)
├── simulation/   # Simulação Monte Carlo (regras do torneio e cálculo de tabelas)
└── reporting/    # Explanabilidade de previsões e geração de artefatos
```

### Pontos Fortes Arquiteturais:
1. **DuckDB + Parquet como Storage Engine**: O uso de arquivos locais versionados (Parquet/DuckDB) é altamente apropriado para um ambiente local de analista. O DuckDB oferece desempenho excepcional em consultas de agregação analítica sem a sobrecarga de gerenciar instâncias de bancos de dados relacionais (como PostgreSQL).
2. **Ingestão Raw com Caching**: Guardar a carga bruta original (`fifa_extracts`) antes de qualquer parsing/normalização (conforme `data-model.md`) garante **reprodutibilidade e rastreabilidade**, permitindo reavaliar previsões antigas sob a perspectiva exata do que a FIFA declarava na data de execução.
3. **Validação por Contratos (YAML/Pydantic)**: A definição do contrato de configuração (`forecast-config.schema.yaml`) reduz falhas de parsing ao lidar com APIs ou fontes externas voláteis.

### Vulnerabilidades Arquiteturais Detectadas:
* **Volatilidade das APIs da FIFA**: Estruturas de endpoints e formatos de payloads da FIFA mudam sem aviso prévio. Se o parser estiver acoplado ao pipeline principal, qualquer mudança quebra o ETL inteiro.
  * *Diretriz*: Implementar o padrão **Adapter (ou Strategy)** em `src/copa_forecast/data/sources/fifa.py`, separando o crawler (que busca e persiste o payload) do parser. Deve ser fácil injetar um novo adaptador de parsing sem tocar no motor de ingestão e normalização.
* **Complexidade do Novo Regulamento da Copa 2026 (48 seleções)**: O torneio terá 12 grupos de 4 times, classificando os 2 primeiros de cada grupo + os **8 melhores terceiros colocados** para a fase de 32 avos (Round of 32). A lógica de desempate e mapeamento de chaves entre diferentes grupos é complexa.
  * *Diretriz*: Escrever testes unitários em `tests/unit/test_rules.py` cobrindo cenários limite de comparação de terceiros colocados (critérios de cartões amarelos/Fair Play, saldo de gols e sorteio).

---

## 2. Avaliação de Modelagem Científica de Dados

A premissa esportiva do modelo está muito bem fundamentada e contorna o viés comum de *"all-time prestige"* (reputação histórica de seleções tradicionais), priorizando a **recência e o momento atual das seleções**.

### Pontos Fortes Científicos:
1. **Decaimento Exponencial de Partidas**: Usar janelas de 12 e 24 meses aplicando decaimento temporal (half-life configurable via YAML) é estatisticamente robusto. Evita descartar dados úteis de forma abrupta e, ao mesmo tempo, remove o impacto de resultados antigos que não refletem o elenco/comissão técnica atual.
2. **Modelagem de Partida vs. Previsão Direta do Campeão**: Prever probabilidades de partida ($V, E, D$) antes de simular o chaveamento permite capturar a variabilidade de cenários de empates na fase de grupos, que impactam drasticamente as chances de cruzamento nas fases seguintes.
3. **Calibração de Probabilidades**: Modelos de aprendizado de máquina frequentemente geram previsões excessivamente confiantes. A inclusão explícita de uma camada de calibração (`Brier Score` e `Log Loss`) em `src/copa_forecast/models/calibration.py` é essencial para dar credibilidade às probabilidades geradas.

### Riscos de Modelagem e Viés Científico:
* **Vazamento Temporal (Data Leakage)**: Ao criar atributos de histórico de partidas (como o Elo ajustado ao oponente), é fácil usar inadvertidamente o Elo atualizado de um oponente com jogos posteriores à data de corte (`as_of_date`).
  * *Diretriz*: No módulo `leakage.py`, os testes devem verificar se o Elo do oponente na partida $X$ foi calculado utilizando estritamente as partidas anteriores a $X$.
* **Escassez de Amostras para Países que Jogam Pouco**: Países de federações menores ou países-sede (que jogaram menos jogos oficiais e mais amistosos nos últimos 24 meses) podem ter suas estatísticas enviesadas.
  * *Diretriz*: Introduzir uma regularização baseada na força média da confederação do país (CONCACAF, CAF, AFC, etc.) como um *Bayesian prior* para estabilizar a variância em seleções com poucas partidas na janela ativa.
* **O Impacto de Empates e Decisão por Pênaltis**: O mata-mata da Copa do Mundo se estende para prorrogação e pênaltis. Simular apenas o tempo regulamentar é insuficiente.
  * *Diretriz*: O modelo de partida em `match_model.py` deve estimar as probabilidades do tempo regulamentar ($p_W, p_D, p_L$). Se a simulação de mata-mata indicar empate, deve-se aplicar uma probabilidade de vitória de prorrogação/pênalti derivada de atributos de resiliência defensiva e histórico de penalidades (ou uma distribuição simplificada baseada em ranking de força).

---

## 3. Guia de Revisão Automática para o Agente Executor

Ao finalizar a implementação das fases do projeto, o agente executor **MUST** executar o script de verificação de qualidade automatizado:

```bash
python3 scripts/verify_implementation.py
```

Este script irá validar de forma automatizada:
1. **Estrutura e Preenchimento de Arquivos**: Garante que nenhum módulo do pipeline analítico seja um stub vazio ou um arquivo de marcação apenas com `pass`.
2. **Execução de Testes Unitários e Integração**: Dispara a suíte de testes `pytest` e retorna o resultado.
3. **Padrão de Validade de Arquivos CSV**: Verifica se os relatórios analíticos em CSV exportados contêm o cabeçalho **BOM UTF-8 (`0xEF, 0xBB, 0xBF`)** para evitar problemas com acentuação no Excel.
4. **Validação de Prevenção de Leakage**: Confirma a presença das lógicas de restrição de data baseadas no `as_of_date` no módulo de atributos.
