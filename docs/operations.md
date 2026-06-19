# Operacao diaria e publicacao

Este projeto publica um snapshot estatico do forecast em `public/` e usa GitHub
Actions para manter a pagina e as estatisticas de validacao atualizadas.

## Rotina automatizada

- Workflow: `.github/workflows/daily-forecast.yml`
- Agendamento: todos os dias as `04:17` em `America/Sao_Paulo`
- Acionamento manual: aba Actions, workflow `Daily forecast and Pages deploy`
- Config gerada: `.generated/fifa.daily.forecast.json`
- Fonte oficial: `configs/fifa.real.forecast.json`
- Publicacao: GitHub Pages via artifact de `public/`

O horario `04:17` foi escolhido como padrao conservador. A Copa 2026 sera
disputada no Canada, Mexico e Estados Unidos; jogos noturnos no oeste da America
do Norte podem terminar tarde no horario do Brasil. A execucao depois das 04h no
Brasil reduz a chance de ler um dia ainda incompleto.

## O que a rotina executa

```bash
python scripts/prepare_daily_config.py \
  --config configs/fifa.real.forecast.json \
  --output .generated/fifa.daily.forecast.json \
  --as-of-date "$AS_OF_DATE" \
  --run-id "$RUN_ID" \
  --github-url "$REPOSITORY_URL"

copa-forecast etl-recent-matches --config .generated/fifa.daily.forecast.json

copa-forecast backtest \
  --config .generated/fifa.daily.forecast.json \
  --matches data/processed/recent_matches/latest_matches.json

copa-forecast forecast \
  --config .generated/fifa.daily.forecast.json \
  --recent-matches data/processed/recent_matches/latest_matches.json

python scripts/verify_implementation.py
```

> A ordem importa: o `backtest` roda **antes** do `forecast` porque é ele quem
> ajusta a temperatura de calibração no rolling-origin. O `forecast` então
> publica probabilidades já usando essa temperatura recém-ajustada. Essa é
> exatamente a ordem do workflow em `.github/workflows/daily-forecast.yml`
> (ETL → backtest → forecast → quality gate).

## Garantias da operacao

- A data diaria muda o limite `as_of_date`, mas as janelas esportivas continuam
  definidas na configuracao: 12 meses como janela atual e 24 meses como limite
  maximo.
- O README e o HTML sao atualizados somente depois do backtest e do quality gate
  do revisor.
- A rotina agendada e manual comita `README.md` e `public/` quando houver
  alteracoes publicaveis.
- O site e servido como HTML/CSS/JS estatico; nao ha backend sempre ligado.

## Configuracao no GitHub

Antes da primeira publicacao, o repositorio deve estar configurado para publicar
GitHub Pages por GitHub Actions. A documentacao oficial do GitHub descreve que
custom workflows usam `actions/configure-pages`, `actions/upload-pages-artifact`
e `actions/deploy-pages`, alem das permissoes `pages: write` e `id-token: write`:

- [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [GitHub Actions schedule e workflow_dispatch](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
