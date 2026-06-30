# Copa 2026 AI Forecast: One-Page Resumo de Decisões Técnicas e Estatísticas

Este documento atua como o **One-Page Pitch** do projeto, estruturado para ser compartilhado no **LinkedIn** ou servir de defesa contra críticas técnicas comuns no **GitHub**.

---

## ⚡ O Problema dos Modelos Tradicionais de Futebol
A maioria das previsões de futebol falha por dois motivos:
1. **Viés de Camisa (Historical Prestige)**: Utilizam dados agregados históricos (ex: títulos mundiais de 1970 ou 1994) como fatores principais de força, ignorando que seleções mudam drasticamente de elenco, comissão técnica e momento esportivo em curtos períodos de tempo.
2. **Previsão em Round-Robin Sintético**: Calculam chances de título ordenando forças estáticas de forma isolada, em vez de simular o chaveamento real do torneio (onde um time forte pode cair em um "grupo da morte" ou chaveamento desfavorável).

---

## 🛡️ Nossas Decisões Científicas e Técnicas (Blindagem contra Críticas)

### 1. Ingestão de Dados: A FIFA como Fonte da Verdade (ETL Estrito)
* **Decisão**: Todo o chaveamento, datas de jogos, regulamentos de desempate e resultados em tempo real vêm estritamente da extração automatizada de payloads oficiais da FIFA.
* **Justificativa**: Evita inconsistências comuns de arquivos de terceiros (Kaggle/comunidade) que demoram para atualizar ou interpretam regras de desempate de forma incorreta. O projeto salva os dados crus (`raw`) para auditoria completa.

### 2. Recência Esportiva com Decaimento Exponencial
* **Decisão**: Foco absoluto em janelas de 12 e 24 meses como atributos primários de força. Resultados de partidas antigas sofrem decaimento exponencial (half-life configurable, padrão 180 dias).
* **Justificativa**: Em seleções nacionais, o momento esportivo recente e amistosos de preparação pré-Copa são previsores infinitamente superiores a resultados acumulados de 10 anos atrás. Dados históricos longínquos entram apenas como *priors* Bayesianos reguladores para seleções com poucas partidas na janela.

### 3. Modelagem de Partida Multiclasse ($V, E, D$) antes do Torneio
* **Decisão**: Estimamos a probabilidade de Vitória, Empate e Derrota para o tempo regulamentar de cada partida individual, em vez de forçar um vencedor binário.
* **Justificativa**: A dinâmica de empates na fase de grupos da Copa é o maior gerador de zebras e surpresas que redesenham os cruzamentos das oitavas e quartas de final.

### 4. Simulação de Chaveamento Real via Monte Carlo (10,000+ Runs)
* **Decisão**: Não fazemos um ranking linear estático. O algoritmo simula a Copa do Mundo de ponta a ponta 10.000 vezes, incluindo a nova regra complexa da Copa 2026 (48 times, 12 grupos, com classificação dos 8 melhores terceiros colocados) e resoluções de prorrogação/pênaltis no mata-mata.
* **Justificativa**: Um time de menor força média pode ter um caminho muito aberto no chaveamento e alcançar uma semifinal com maior probabilidade que um favorito enfrentando chaves pesadas.
* **Acompanhamento ao vivo**: Conforme o mata-mata avança, os resultados reais (incluindo pênaltis) são respeitados — seleções eliminadas zeram a chance de título na hora — e a página exibe o caminho do título atualizado (16-avos → final, com vagas "A definir").

### 5. Rigor Científico: Calibração de Probabilidades e Zero-Leakage
* **Decisão**: Modelos de classificação não promovem previsões brutas. Aplicamos calibração (Platt Scaling ou Isotonic Regression) e validamos a assertividade usando métricas probabilísticas estritas: **Log Loss** e **Brier Score**.
* **Justificativa**: Previsões cruas de modelos de árvore de decisão tendem a ser superconfiantes. A calibração garante que um evento previsto com 70% de chance ocorra de fato em ~70% das simulações.
* **Leakage-Free**: O backtest histórico utiliza validação temporal de origem móvel (*rolling-origin*). Partidas do passado só são previstas com dados disponíveis *antes* da data do jogo, sem vazamento do futuro.

---

## ✍️ Sugestão de Post para o LinkedIn (Pronto para copiar)

> ⚽ **Como prever o campeão da Copa do Mundo 2026 com ciência de dados real e sem viés de camisa?**
> 
> A maioria das previsões de futebol sofre de dois problemas clássicos: apego à reputação histórica de seleções tradicionais ("camisa pesa") e simulações simplórias que não refletem o chaveamento real do torneio.
> 
> Para resolver isso de forma cientificamente blindada, acabo de estruturar o projeto **Copa 2026 AI Forecast** usando engenharia e ciência de dados moderna:
> 
> 🏗️ **Arquitetura Orientada a Contratos**: Ingestão estrita de payloads oficiais da FIFA via DuckDB e Parquet, com auditoria de dados originais.
> 📉 **Modelagem de Recência**: Menos peso para a história antiga, mais peso para o momento atual. Criamos janelas temporais de 12 a 24 meses com decaimento exponencial de relevância de partidas.
> ⚖️ **Calibração Estatística**: Previsão probabilística real calibrada (Platt Scaling) avaliada por Brier Score e Log Loss — nada de chutar números ou confiar em outputs puros de redes neurais ou classificadores brutos.
> 🎲 **Simulação Monte Carlo Realista**: O modelo roda o torneio de ponta a ponta 10.000 vezes, respeitando todas as regras oficiais da FIFA para 2026 (incluindo a repescagem dos 8 melhores terceiros colocados no novo formato de 48 seleções).
> 🕒 **Zero Leakage**: Backtests históricos baseados em rolling-origin para evitar vazamento temporal.
> 
> Todo o design do projeto é Spec-Driven, documentado de ponta a ponta sob a metodologia Spec Kit.
> 
> Acompanhe a evolução da implementação e confira a arquitetura completa no GitHub: [Link do Repositório]
> 
> #DataScience #MachineLearning #Python #DuckDB #Copa2026 #Analytics #SportsAnalytics
