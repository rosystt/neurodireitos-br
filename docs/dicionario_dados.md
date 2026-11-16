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
| `status_inclusao` | categoria | `incluido` (entra na avaliação, em um dos dois grupos), `pendente` (falta confirmar algum requisito) ou `excluido`. | Classificação do projeto |
| `motivo_status` | categoria | Vazio para incluídos. Para os demais: `envio_br_nao_confirmado`, `politica_nao_localizada`, `nao_e_eeg`, `nao_e_de_consumo`, `nao_lancado`. | Classificação do projeto |
| `grupo` | categoria | Preenchido só para incluídos. `brasil`: vendido ou entregue no Brasil; é o grupo que responde à pergunta de pesquisa. `comparacao`: atende aos demais requisitos, mas a loja oficial não entrega no Brasil; serve de referência. | Classificação do projeto |
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

Os quatro primeiros valores satisfazem o requisito de venda no Brasil (grupo `brasil`). O grupo `comparacao` exige `nao_entrega`. Aparelhos com `nao_confirmado` ficam pendentes.

A lista de países do checkout foi lida abrindo o carrinho da loja oficial com um produto, sem preencher dados nem concluir a compra.

## `data/raw/fontes_politicas.csv`

Uma linha por documento de política a coletar. É preenchido à mão, a partir do inventário: um fabricante pode ter mais de um documento. A coerência com o inventário é verificada por `python -m src.validar_coleta`.

| Coluna | Tipo | Descrição | Origem |
|---|---|---|---|
| `id_documento` | texto | Identificador do documento (`P01-1`, `P01-2`…): política e número de ordem. | Atribuído no projeto |
| `id_politica` | texto | Identificador da política (`P01` a `P15`), uma por fabricante. É a unidade de avaliação. | Atribuído no projeto |
| `fabricante` | texto | Fabricante, escrito como no inventário. | `data/raw/inventario.csv` |
| `tipo` | categoria | `principal` (a política de privacidade em si; uma por fabricante) ou `complementar` (documento que a detalha, como política de dados de saúde ou resumo). | Classificação do projeto |
| `url` | URL | Endereço do documento. | Site do fabricante |
| `observacoes` | texto | Particularidades da página. | Registro do projeto |

## `data/raw/politicas/`

Páginas das políticas como vieram do servidor, em arquivos `<id_documento>_<AAAA-MM-DD>.html`, mais o registro `coletas.csv`, com uma linha por tentativa de download:

| Coluna | Tipo | Descrição | Origem |
|---|---|---|---|
| `id_documento` | texto | Documento baixado. | `fontes_politicas.csv` |
| `url` | URL | Endereço pedido. | `fontes_politicas.csv` |
| `url_final` | URL | Endereço que respondeu, depois de redirecionamentos. | Resposta do servidor |
| `status_http` | inteiro | Código de status da resposta (`200` = sucesso). | Resposta do servidor |
| `data_hora_utc` | data e hora | Momento do download, em UTC (ISO 8601). | Relógio da coleta |
| `arquivo` | texto | Nome do arquivo salvo; vazio se o download falhou. | Gerado na coleta |
| `bytes` | inteiro | Tamanho do arquivo salvo. | Gerado na coleta |
| `sha256` | texto | Hash SHA-256 do arquivo, para detectar alteração do bruto e mudança da política entre coletas. | Gerado na coleta |

## `data/raw/projetos_lei/`

Respostas das APIs de Dados Abertos da Câmara e do Senado, em JSON, como vieram: um arquivo por termo buscado (`camara_busca_*.json`, `senado_busca_*.json`) e um por proposição detalhada (`camara_PL_522_2022.json` etc.). Cada arquivo traz o campo `coletado_em_utc`.

## `data/interim/politicas/`

Um arquivo `<id_documento>.txt` por documento, com o texto limpo (UTF-8, uma linha por bloco, títulos marcados com `#`), mais `resumo.csv`:

| Coluna | Tipo | Descrição | Origem |
|---|---|---|---|
| `id_documento` | texto | Documento. | `fontes_politicas.csv` |
| `arquivo_bruto` | texto | Arquivo HTML de origem. | `coletas.csv` |
| `sha256_bruto` | texto | Hash do arquivo de origem, que liga o texto à coleta exata de onde saiu. | `coletas.csv` |
| `arquivo_texto` | texto | Arquivo de texto gerado. | Gerado na limpeza |
| `idioma` | texto | Idioma predominante, em código ISO 639-1. | Detectado na limpeza |
| `caracteres` | inteiro | Tamanho do texto limpo. | Calculado na limpeza |
| `palavras` | inteiro | Número de palavras; em chinês, número de ideogramas. | Calculado na limpeza |
| `recorte` | categoria | `sim` se só um trecho da página foi mantido (ver `RECORTES` em `src/limpeza.py`); `nao` caso contrário. | Gerado na limpeza |

## `data/interim/traducoes/`

Traduções para o português dos documentos que não estão em inglês nem em português, em arquivos `<id_documento>_pt.txt`. Cada tradução tem **o mesmo número de linhas do original**, de modo que a linha *n* da tradução corresponde à linha *n* do texto em `data/interim/politicas/`. O original continua sendo a fonte: todo trecho citado como evidência na avaliação deve ser conferido nele.

O registro `traducoes.csv` tem uma linha por tradução:

| Coluna | Tipo | Descrição | Origem |
|---|---|---|---|
| `id_documento` | texto | Documento traduzido. | `fontes_politicas.csv` |
| `arquivo_original` | texto | Texto limpo de origem, em `data/interim/politicas/`. | Limpeza |
| `sha256_original` | texto | Hash do texto de origem; se o original mudar, a tradução precisa ser refeita. | Calculado |
| `idioma_original` | texto | Idioma de origem, em código ISO 639-1. | Limpeza |
| `arquivo_traducao` | texto | Arquivo da tradução. | Registro do projeto |
| `idioma_traducao` | texto | Idioma de destino. | Registro do projeto |
| `metodo` | categoria | Como a tradução foi feita: `traducao_automatica_llm` ou `traducao_humana`. | Registro do projeto |
| `modelo` | texto | Modelo de linguagem usado, quando a tradução é automática. | Registro do projeto |
| `data_traducao` | data | Data da tradução (`AAAA-MM-DD`). | Registro do projeto |
| `revisao_humana` | categoria | `sim` se alguém fluente no idioma de origem revisou a tradução; `nao` caso contrário. | Registro do projeto |
| `observacoes` | texto | Decisões de tradução que merecem registro. | Registro do projeto |

## `data/interim/projetos_lei.csv`

Uma linha por proposição encontrada nas buscas, inclusive as que não tratam do tema.

| Coluna | Tipo | Descrição | Origem |
|---|---|---|---|
| `casa` | categoria | `Câmara` ou `Senado`. | API de origem |
| `sigla` | categoria | Tipo da proposição: `PL`, `PLP` ou `PEC`. | API |
| `numero` | inteiro | Número da proposição. | API |
| `ano` | inteiro | Ano de apresentação. | API |
| `ementa` | texto | Ementa oficial. | API |
| `autoria` | texto | Autores, separados por ponto e vírgula. | API |
| `data_apresentacao` | data | Data de apresentação (`AAAA-MM-DD`). | API |
| `situacao` | texto | Situação da tramitação na data da coleta. Vazio para o Senado, cuja busca não traz esse campo. | API da Câmara |
| `url` | URL | Página da proposição. | API |
| `termos_busca` | texto | Termos de busca que a encontraram, ou `inclusão manual`. | `src/projetos_lei.py` |
| `trata_do_tema` | categoria | `sim` se a ementa fala de dados ou direitos ligados ao cérebro (expressão `PADRAO_TEMA`); `nao` para resultados que só usam o termo de passagem. | Calculado |
| `data_coleta` | data | Data da consulta à API. | Registro do projeto |

## `data/processed/criterios.csv`

Uma linha por critério da régua de avaliação. É a versão em tabela de [`criterios.md`](criterios.md), usada pelo código e pela carga do grafo (nós `:Criterio`). A coerência entre os dois é verificada por `python -m src.validar_criterios`.

Codificação UTF-8, separador vírgula. Uma coluna de fonte vazia significa que aquela norma não foi usada como base do critério.

| Coluna | Tipo | Descrição | Origem |
|---|---|---|---|
| `id` | texto | Identificador do critério (`C01` a `C12`). | Atribuído no projeto |
| `criterio` | texto | Nome curto do critério. | `docs/criterios.md` |
| `pergunta` | texto | Pergunta respondida para cada política com `sim`, `nao` ou `nao_menciona`. | `docs/criterios.md` |
| `peso` | inteiro | Peso do critério na nota, de 1 a 3. | `docs/criterios.md` |
| `hipotese` | categoria | Hipótese do projeto que o critério ajuda a testar: `H1`, `H2` ou `H3`. | `docs/criterios.md` |
| `fonte_lgpd` | texto | Dispositivos da Lei 13.709/2018 que embasam o critério. | Texto da lei |
| `fonte_pl_522` | texto | Dispositivos propostos pelo PL 522/2022. | Texto integral do projeto |
| `fonte_colorado` | texto | Dispositivos do Colorado Privacy Act (com a redação do HB 24-1058). | Fontes secundárias, a conferir na revisão jurídica |
| `fonte_california` | texto | Dispositivos do CCPA (com a redação do SB 1223). | Fontes secundárias, a conferir na revisão jurídica |
| `fonte_chile` | texto | Norma ou decisão chilena que embasa o critério. | Texto da lei e fontes secundárias |

## `data/raw/leis_referencia.csv`

Uma linha por norma de referência da régua, preenchida à mão a partir das fontes citadas em [`criterios.md`](criterios.md). As proposições brasileiras não ficam aqui: vêm de `data/interim/projetos_lei.csv`.

| Coluna | Tipo | Descrição | Origem |
|---|---|---|---|
| `id` | texto | Identificador da norma (`LGPD`, `CO-HB-24-1058`…). | Atribuído no projeto |
| `nome` | texto | Nome usual da norma. | Texto da norma |
| `tipo` | categoria | `lei`, `emenda constitucional` ou `decisão judicial`. | Classificação do projeto |
| `pais` | texto | País da norma. | Texto da norma |
| `jurisdicao` | texto | `federal`, `nacional` ou o estado, no caso de leis estaduais. | Texto da norma |
| `status` | categoria | `vigente` ou, para decisão judicial, `julgado`. | Verificado em 15/11/2026 |
| `data_vigencia` | data | Data de início da vigência ou do julgamento (`AAAA-MM-DD`). | Texto da norma e fontes secundárias |
| `cita_dado_neural` | categoria | `sim` se a norma trata expressamente de dado neural ou atividade cerebral; `nao` caso contrário. | Leitura da norma |
| `url` | URL | Endereço da norma. | Site oficial ou repositório que a reproduz |

## `data/processed/grafo/`

Tabelas de nós e de relações do grafo, geradas por `python -m src.preparar_grafo` a partir do inventário, da lista de políticas, das leis e da régua. Nenhuma é editada à mão. O significado de cada rótulo e relação está em [`modelo_grafo.md`](modelo_grafo.md).

| Arquivo | Uma linha por | Colunas | Origem |
|---|---|---|---|
| `paises.csv` | país | `nome` | Sedes das empresas, países das leis e Brasil |
| `empresas.csv` | fabricante incluído | `id_empresa` (igual a `id_politica`), `nome`, `pais_sede`, `grupo`, `url_politica` | `inventario.csv` e `fontes_politicas.csv` |
| `aparelhos.csv` | aparelho incluído | `id`, `nome`, `tipo`, `id_empresa`, `grupo`, `canal_venda_br`, `url_evidencia_venda`, `preco_referencia`, `moeda`, `data_coleta` | `inventario.csv` |
| `leis.csv` | norma ou proposição | as colunas de `leis_referencia.csv`; para proposições, `status` vale `em_tramitacao` ou `retirado` | `leis_referencia.csv` e `projetos_lei.csv` (só as que tratam do tema) |
| `criterios.csv` | critério | `id`, `criterio`, `pergunta`, `peso`, `hipotese` | `data/processed/criterios.csv` |
| `lei_criterio.csv` | norma que fundamenta um critério | `id_lei`, `id_criterio`, `dispositivo` | Colunas `fonte_*` de `criterios.csv` |

