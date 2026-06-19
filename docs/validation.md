# Validacao

## Snapshot de validacao atual

Fonte da verdade ao vivo: o bloco `validation-stats` do `README.md`, regenerado
pelo `backtest` a cada execucao do workflow. Estado mais recente (modelo
`mvp-recency-sos-dynamic-draw-v4`, ja com o prior Elo global da feature 003):

- Data dos dados: `2026-06-18`
- Amostras avaliadas (rolling-origin): `458`
- Acuracia 1X2: `60.70%` (baseline local `52.84%`)
- Brier calibrado: `0.5227` (baseline `0.5815`)
- Log loss calibrado: `0.9097` (baseline `0.9742`)
- Temperatura de calibracao: `T=2.7941`
- ECE `0.1474` / MCE `0.2695` (calibracao ainda em monitoramento)

> As secoes abaixo sao **registros historicos** (logs por fase). Os numeros
> antigos sao preservados de proposito para auditoria; nao representam o estado
> atual do modelo.

## [Historico] 2026-06-18 - Phase 9: remediacao de credibilidade (feature 002)

Escopo em [specs/002-credibility-remediation/](../specs/002-credibility-remediation/).

- `pytest -q`: 53 testes passam (45 originais + 8 novos cobrindo empate dinamico,
  paridade da media ponderada, join normalizado, head-to-head e temperature
  scaling). `pytest` e `ruff` agora fazem parte das dev deps (`pip install -e
  ".[dev]"`), entao o validador roda direto via `pytest`.
- `ruff check .`: limpo (regras E/F/I/UP/B; E501 nao bloqueia codigo legado).
- `scripts/verify_implementation.py`: `[SUCCESS]` com a nova checagem funcional
  de vazamento temporal (rejeita registro datado no futuro).
- Backtest rolling-origin (407 amostras): empates passam a ser previstos
  (61/407), temperatura ajustada `T=2.395`; metricas calibradas
  Brier `0.567` / Log loss `0.969`. Recortes por competicao e janela adicionados.
- Observacao de validade de face: o ranking de campeao melhora parcialmente
  (Brasil sai de #25 para ~#19), mas a fragilidade residual vem do prior local
  cold-start, cuja substituicao por um Elo global historico esta listada como
  non-goal da feature 002.

## [Historico] 2026-06-18 - Phase 8: operacao diaria e publicacao

Comando executado no projeto real:

```bash
.venv/bin/python scripts/verify_implementation.py
```

Resultado:

- Status final: `[SUCCESS] All automated verification checks passed.`
- Estrutura e implementacoes nao vazias: todos os modulos obrigatorios
  verificados.
- Testes: 45 testes passaram via fallback `unittest`.
- Observacao local: `pytest` nao estava instalado ou nao estava no `PATH` do
  ambiente virtual local; o validador caiu corretamente para `unittest`.
- Artefatos CSV: BOM UTF-8 confirmado nos CSVs em `data/processed/`.
- Temporal leakage: logica de filtro temporal presente e verificada.

Essa validacao cobre a inclusao da rotina de configuracao diaria, workflow de
GitHub Pages, documentacao operacional e ADR da decisao batch/static.
