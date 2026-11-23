# Modelo do grafo

Descreve os nós e as relações carregados no Neo4j. A carga é feita em duas etapas:

1. **Parte fixa**: empresas, aparelhos, países, leis e critérios. Não depende da avaliação das políticas.
2. **Parte avaliada**: as respostas de cada política aos critérios, as notas e os fatos extraídos das políticas na Fase 4 — tipos de dado, terceiros e países dos dados.

## Parte fixa

```
(:Empresa)-[:SEDIADA_EM]->(:Pais)
(:Empresa)-[:FABRICA]->(:Aparelho)
(:Aparelho)-[:VENDIDO_EM]->(:Pais {nome: 'Brasil'})
(:Lei)-[:VIGORA_EM]->(:Pais)
(:Lei)-[:PROPOSTA_EM]->(:Pais)
(:Lei)-[:FUNDAMENTA]->(:Criterio)
```

### Nós

| Rótulo | Chave | Propriedades | Origem |
|---|---|---|---|
| `:Empresa` | `id` (`P01`…, o mesmo identificador da política) | `nome`, `grupo` (`brasil` ou `comparacao`), `url_politica` | `empresas.csv` |
| `:Aparelho` | `id` (`A01`…) | `nome`, `tipo`, `grupo`, `preco_referencia`, `moeda` | `aparelhos.csv` |
| `:Pais` | `nome` | — | `paises.csv` |
| `:Lei` | `id` (`LGPD`, `PL-522-2022`…) | `nome`, `tipo`, `jurisdicao`, `status`, `data_vigencia`, `cita_dado_neural`, `url` | `leis.csv` |
| `:Criterio` | `id` (`C01` a `C12`) | `nome`, `pergunta`, `peso`, `hipotese` | `criterios.csv` |

O rótulo `:Lei` reúne leis, emendas constitucionais, decisões judiciais e proposições; a propriedade `tipo` distingue cada caso, e `status` diz se a norma está `vigente`, `julgado` (decisão judicial), `em_tramitacao` ou `retirado`.

### Relações

| Relação | Propriedades | Significado |
|---|---|---|
| `SEDIADA_EM` | — | País da sede da empresa. |
| `FABRICA` | — | A empresa é a fabricante do aparelho. |
| `VENDIDO_EM` | `canal`, `evidencia`, `data_coleta` | O aparelho é vendido ou entregue no Brasil; `canal` guarda o tipo de evidência (ver `canal_venda_br` no dicionário de dados). Só existe para o grupo `brasil`. |
| `VIGORA_EM` | — | A norma está em vigor (ou a decisão foi proferida) naquele país. Leis estaduais dos Estados Unidos ligam-se ao país, com o estado em `jurisdicao`. |
| `PROPOSTA_EM` | — | A proposição tramita, ou foi retirada, naquele país. É separada de `VIGORA_EM` para que um projeto de lei nunca apareça como proteção em vigor. |
| `FUNDAMENTA` | `dispositivo` | A norma é fonte do critério; `dispositivo` guarda o artigo citado na régua. |

## Parte avaliada

```
(:Empresa)-[:RESPONDE {resposta, evidencia}]->(:Criterio)
(:Empresa)-[:COLETA {descricao, inferido}]->(:Dado {categoria})
(:Empresa)-[:COMPARTILHA_COM {nome_citado}]->(:Terceiro {categoria})
(:Empresa)-[:ARMAZENA_EM]->(:Pais)
(:Empresa)-[:TRANSFERE_PARA]->(:Pais)
(:Lei)-[:PROTEGE {nivel}]->(:Dado)
```

### Nós

| Rótulo | Chave | Propriedades | Origem |
|---|---|---|---|
| `:Empresa` (propriedades acrescentadas) | `id` | `nota` (0 a 25), `nota_maxima` | `notas.csv` |
| `:Dado` | `categoria` (`sinal_neural`, `inferencia_neural`…) | — | `dados_coletados.csv`, `protecao.csv` |
| `:Terceiro` | `categoria` (`publicidade`, `autoridades`…) | — | `terceiros.csv` |
| `:Pais` (propriedade acrescentada) | `nome` | `tipo`: `pais` ou `regiao` | `paises.csv` |

### Relações

| Relação | Propriedades | Significado |
|---|---|---|
| `RESPONDE` | `resposta`, `evidencia`, `id_documento`, `justificativa`, `modelo`, `versao_prompt`, `versao_regua` | Resposta da política ao critério: `sim` (mais protetivo), `nao` ou `nao_menciona`. Uma por política e critério. |
| `COLETA` | `descricao`, `inferido` (booleano), `evidencia`, `id_documento` | A política declara coletar um dado daquela categoria; `descricao` guarda como ela o chama. Pode haver várias por categoria. |
| `COMPARTILHA_COM` | `nome_citado`, `evidencia`, `id_documento` | A política declara compartilhar dados com um terceiro daquela categoria. |
| `ARMAZENA_EM` | `evidencia`, `id_documento` | A política declara guardar os dados naquele país ou região. |
| `TRANSFERE_PARA` | `evidencia`, `id_documento` | A política declara transferir os dados para aquele país ou região. |
| `PROTEGE` | `nivel` | A norma, vigente ou julgada, protege aquele tipo de dado: `especifica` se cita dado neural, `generica` se não cita (a LGPD, por analogia com dado sensível). |

### Decisões de modelagem

- **`RESPONDE`, e não `ATENDE`** (nome do plano inicial): a resposta pode ser `nao`, e uma relação `ATENDE` com `resposta: 'nao'` leria como o contrário do que diz.
- **Terceiros e dados como categorias.** Das 175 citações de terceiros, 157 têm nome distinto, quase todos genéricos ("parceiros de publicidade"). Um nó por nome não teria vizinhos em comum; o nó é a categoria, e o nome citado fica na relação. O mesmo vale para os tipos de dado.
- **Regiões como `:Pais`.** União Europeia e Espaço Econômico Europeu aparecem como destino dos dados. Entram com `tipo: 'regiao'`, para que nenhuma linha da avaliação seja descartada.
- **`ARMAZENA_EM` separada de `SEDIADA_EM` e de `TRANSFERE_PARA`**: uma empresa com sede em um país pode guardar os dados em outro e transferi-los para um terceiro.
- **`PROTEGE` sem juízo jurídico novo.** É derivada da tabela de leis (status e `cita_dado_neural`) e cobre só o sinal neural, porque a cobertura das inferências varia entre as leis e depende da revisão jurídica (issue #6). Proposições não protegem nada até entrarem em vigor.

## Como carregar

```bash
python -m src.preparar_grafo   # monta as tabelas em data/processed/grafo/
python -m src.grafo            # cria as restrições e carrega no Neo4j
python -m src.validar_grafo    # confere o grafo contra os CSVs
python -m src.consultas        # roda as consultas das hipóteses
```

Os comandos de carga ficam em `cypher/`, um arquivo por tabela; as consultas das hipóteses, em `cypher/consultas/`, uma por arquivo, com os resultados em `data/processed/resultados/`. Toda escrita usa `MERGE`, e há restrição de unicidade para a chave de cada rótulo: rodar a carga de novo atualiza o grafo sem duplicar nada.

A carga envia as linhas dos CSVs como parâmetro, pelo driver do Python, em vez de usar `LOAD CSV` com endereço do GitHub. Assim ela funciona a partir de qualquer cópia local do repositório, em qualquer branch.

## Consultas de conferência

```cypher
// Empresas por país-sede e grupo
MATCH (e:Empresa)-[:SEDIADA_EM]->(p:Pais)
RETURN p.nome AS pais, e.grupo AS grupo, count(*) AS empresas
ORDER BY empresas DESC;

// Leis em vigor no Brasil e se citam dado neural
MATCH (l:Lei {status: 'vigente'})-[:VIGORA_EM]->(:Pais {nome: 'Brasil'})
RETURN l.nome, l.cita_dado_neural;

// Quantas normas fundamentam cada critério
MATCH (c:Criterio)
OPTIONAL MATCH (l:Lei)-[:FUNDAMENTA]->(c)
RETURN c.id, c.nome, count(l) AS normas
ORDER BY c.id;

// Empresas do grupo brasil que coletam sinal neural e os destinos dos dados
MATCH (e:Empresa {grupo: 'brasil'})-[:COLETA]->(:Dado {categoria: 'sinal_neural'})
MATCH (e)-[:ARMAZENA_EM|TRANSFERE_PARA]->(p:Pais)
RETURN e.nome, collect(DISTINCT p.nome) AS destinos;
```
