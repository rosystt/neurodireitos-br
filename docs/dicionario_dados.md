# Dicionário de dados

Descreve cada coluna de cada arquivo de dados do projeto. Atualize este documento sempre que um arquivo ou coluna for criado ou alterado.

## `data/raw/inventario.csv`

Uma linha por aparelho **candidato** avaliado para a amostra — inclusive os que ficaram de fora, para que a seleção seja auditável. É o único arquivo de `data/raw/` preenchido por pesquisa manual, e não por download; toda linha traz a data e as URLs que sustentam o registro.

Codificação UTF-8, separador vírgula, campos vazios quando a informação não se aplica ou não foi coletada. A consistência é verificada por `python -m src.validar_inventario`.

| Coluna | Tipo | Descrição | Origem |
|---|---|---|---|
| `id` | texto | Identificador do aparelho (`A01`, `A02`…). Não muda depois de atribuído. | Atribuído no projeto |
| `aparelho` | texto | Nome comercial do aparelho. | Site do fabricante |
| `fabricante` | texto | Razão social da empresa responsável, como aparece na política de privacidade ou no site. | Política ou site do fabricante |
| `pais_sede` | texto | País da sede do fabricante. | Política ou site do fabricante |
| `tipo_aparelho` | texto | Formato do aparelho: `headband`, `headband de sono`, `headset`, `fones de ouvido`, `fones de ouvido de sono`, `kit de pesquisa`. | Classificação do projeto |
| `status_inclusao` | categoria | `incluido` (atende ao critério de inclusão), `pendente` (falta confirmar algum requisito) ou `excluido`. | Classificação do projeto |
| `motivo_status` | categoria | Vazio para incluídos. Para os demais: `envio_br_nao_confirmado`, `politica_nao_localizada`, `escopo_a_decidir`, `nao_entrega_no_brasil`, `nao_e_eeg`, `nao_e_de_consumo`, `nao_lancado`. | Classificação do projeto |
| `canal_venda_br` | categoria | Evidência de venda ou entrega no Brasil (ver abaixo). | Pesquisa em marketplaces e lojas oficiais |
| `url_evidencia_venda` | URL | Página que sustenta o valor de `canal_venda_br`. | Marketplace ou loja oficial |
| `preco_referencia` | decimal | Preço de tabela do aparelho, sem impostos de importação nem frete. Vazio se não coletado. | `fonte_preco` |
| `moeda` | texto | Moeda de `preco_referencia`, em código ISO 4217 (ex.: `USD`). | `fonte_preco` |
| `fonte_preco` | URL | Página de onde o preço foi lido. | Loja oficial, revendedor ou imprensa |
| `url_politica` | URL | Política de privacidade aplicável ao aparelho. Vazio se não localizada. | Site do fabricante |
| `idioma_politica` | texto | Idioma da política, em código ISO 639-1 (`en`, `pt`…). | Leitura da página |
| `data_coleta` | data | Data em que a linha foi verificada, no formato `AAAA-MM-DD`. | Registro do projeto |
| `observacoes` | texto | Ressalvas sobre a linha: fontes secundárias, pontos a confirmar, políticas complementares. | Registro do projeto |

### Valores de `canal_venda_br`

Ordenados da evidência mais forte para a mais fraca:

| Valor | Significado |
|---|---|
| `marketplace_br` | Há anúncio do aparelho em marketplace brasileiro (Amazon.com.br ou Mercado Livre). |
| `loja_oficial_checkout_brasil` | O checkout da loja oficial lista o Brasil entre os países de entrega. |
| `loja_oficial_cita_brasil` | A loja oficial menciona o Brasil nas condições de envio. |
| `loja_oficial_envio_mundial` | A loja oficial declara envio internacional ou mundial, sem listar países. |
| `nao_confirmado` | Nenhuma evidência de entrega no Brasil foi encontrada. |
| `nao_entrega` | A loja oficial restringe o envio a países que não incluem o Brasil. |

Só os quatro primeiros valores satisfazem o critério de inclusão.

A lista de países do checkout foi lida abrindo o carrinho da loja oficial com um produto, sem preencher dados nem concluir a compra.
