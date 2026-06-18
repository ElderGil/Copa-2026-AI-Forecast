# ADR 0001: Operacao batch Python com publicacao estatica

## Status

Accepted

## Contexto

O projeto precisa atualizar previsoes uma vez por dia, publicar uma pagina HTML
com ranking e pilares por selecao, e manter o README com estatisticas de
validacao. A arquitetura atual ja separa ETL, features, modelo, simulacao,
backtest e renderizacao estatica dentro de um unico pacote Python.

Criar um servico web permanente neste momento aumentaria custo operacional,
superficie de falha e necessidade de observabilidade sem melhorar diretamente a
qualidade preditiva. O produto publico esperado e uma one-page atualizada, nao
uma aplicacao transacional.

## Decisao

Manter a arquitetura como batch Python modular e publicar os artefatos estaticos
em GitHub Pages.

O GitHub Actions passa a ser o orquestrador operacional:

- prepara uma configuracao diaria datada;
- executa ETL oficial FIFA;
- gera forecast e site estatico;
- atualiza estatisticas de validacao no README;
- roda `scripts/verify_implementation.py`;
- publica `public/` via GitHub Pages.

O workflow roda diariamente as `04:17 America/Sao_Paulo` e tambem pode ser
acionado manualmente com `workflow_dispatch`.

## Consequencias

- Simplicidade operacional: nenhum backend sempre ligado.
- Reprodutibilidade: cada execucao tem `run_id`, `as_of_date`, fontes e
  artefatos persistidos.
- Publicacao barata e aberta: GitHub Pages atende a experiencia atual.
- Limitacao assumida: atualizacoes intra-dia exigem acionamento manual do
  workflow ou uma futura mudanca de frequencia.
- Evolucao futura: se surgirem necessidades de API publica, notificacoes em
  tempo real ou armazenamento historico consultavel, separar um servico de
  leitura pode virar uma nova ADR.
