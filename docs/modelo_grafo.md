# Modelo do grafo

Descreve os nós e as relações carregados no Neo4j. A carga é feita em duas etapas:

1. **Parte fixa** (já carregada): empresas, aparelhos, países, leis e critérios. Não depende da avaliação das políticas.
2. **Parte avaliada** (depois da Fase 4): as respostas de cada política aos critérios e os fatos extraídos das políticas — tipos de dado, terceiros e países de armazenamento.

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

## Parte avaliada (prevista)

```
(:Empresa)-[:ATENDE {resposta, evidencia}]->(:Criterio)
(:Empresa)-[:COLETA]->(:Dado {tipo, inferido})
(:Empresa)-[:COMPARTILHA_COM]->(:Terceiro {nome, categoria})
(:Empresa)-[:ARMAZENA_EM]->(:Pais)
(:Lei)-[:PROTEGE {nivel}]->(:Dado)
```

- `ATENDE.resposta` vale `sim`, `nao` ou `nao_menciona`.
- `Dado.inferido` separa o sinal bruto de EEG das inferências feitas a partir dele.
- `ARMAZENA_EM` é separada de `SEDIADA_EM`: uma empresa com sede em um país pode guardar os dados em outro.
- `PROTEGE.nivel` vale `especifica` ou `generica`.

## Como carregar

```bash
python -m src.preparar_grafo   # monta as tabelas em data/processed/grafo/
python -m src.grafo            # cria as restrições e carrega no Neo4j
```

Os comandos ficam em `cypher/`, um arquivo por tabela. Toda escrita usa `MERGE`, e há restrição de unicidade para a chave de cada rótulo: rodar a carga de novo atualiza o grafo sem duplicar nada.

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
```
