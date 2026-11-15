# Neurodireitos BR

**Status: em andamento** — Fase 1 (inventário de aparelhos) concluída: de 24 candidatos avaliados, 13 aparelhos formam o grupo principal (chegam ao Brasil), 6 formam o grupo de comparação e 5 foram excluídos. Fase 3 (coleta e limpeza) concluída: 21 documentos de 15 políticas coletados e limpos, e 6 proposições sobre dados neurais levantadas na Câmara e no Senado.

## Pergunta de pesquisa

Os dados neurais coletados por aparelhos de EEG de consumo no Brasil estão protegidos, considerando que a LGPD não cita dados neurais e que os projetos de lei sobre o tema ainda tramitam?

## Objetivo

Medir quanto as políticas de privacidade de aparelhos de EEG de consumo vendidos no Brasil protegem os dados cerebrais dos usuários, e representar a rede de empresas, dados, terceiros e leis em um grafo no Neo4j.

## Hipóteses

São hipóteses a testar, não a provar:

1. A maioria das políticas não trata dado neural como categoria específica.
2. Parte relevante das empresas compartilha dados com terceiros ou guarda os dados fora do Brasil.
3. As políticas oferecem menos garantias do que exigem as leis de referência (Colorado, Califórnia, Chile).

Pergunta complementar: as políticas dos aparelhos que chegam ao Brasil oferecem menos garantias do que as dos aparelhos vendidos só em mercados onde leis de dados neurais já estão em vigor?

## Escopo da versão 1

- **Dentro:** os aparelhos de EEG de consumo (headbands, fones, tiaras, wearables de sono) vendidos ou entregues no Brasil, com política de privacidade pública, mais um grupo de comparação de aparelhos equivalentes que não chegam ao Brasil.
- **Tamanho:** o plano inicial previa de 15 a 20 aparelhos vendidos no Brasil. O levantamento encontrou 13, de 9 fabricantes; por isso o grupo principal é tratado como um levantamento de todos os casos localizados, e não como uma amostra.
- **Fora:** dispositivos médicos e implantes, análise jurídica formal e coleta de dados de usuários.

## Critério de inclusão

Um aparelho entra no **grupo principal** (`brasil`) quando atende a **todos** os requisitos:

1. Capta sinais cerebrais por **EEG** (aparelhos só de fNIRS ou de estimulação ficam de fora).
2. É vendido como produto de **consumo** — bem-estar, foco, meditação ou sono — e não como dispositivo médico, implante ou kit de pesquisa.
3. É **vendido ou entregue no Brasil**, com evidência registrada: anúncio em marketplace brasileiro, Brasil na lista de países do checkout ou nas condições de envio da loja oficial, ou declaração de envio mundial.
4. Tem **política de privacidade pública**, acessível sem compra ou cadastro.
5. Está **à venda** na data da coleta (produtos apenas anunciados ficam de fora).

### Grupo de comparação

Um aparelho entra no grupo `comparacao` quando atende aos requisitos 1, 2, 4 e 5, mas a loja oficial **não entrega no Brasil** — verificado na lista de países do checkout ou na política de envio. São aparelhos vendidos principalmente nos Estados Unidos, onde leis estaduais sobre dados neurais já estão em vigor.

O grupo foi definido **antes** da régua de critérios e de qualquer leitura das políticas. Ele serve só de referência: os achados sobre o Brasil vêm exclusivamente do grupo principal.

Todos os candidatos avaliados — incluídos, pendentes e excluídos, com o motivo — estão em [`data/raw/inventario.csv`](data/raw/inventario.csv); as colunas estão descritas em [`docs/dicionario_dados.md`](docs/dicionario_dados.md). Para conferir a consistência do arquivo:

```bash
python -m src.validar_inventario
```

## Método (resumo)

1. Inventário dos aparelhos e das políticas de privacidade.
2. Régua de critérios fechada **antes** da avaliação, com base na LGPD, no PL 522/22 e nas leis do Colorado, da Califórnia e do Chile.
3. Coleta e limpeza dos textos das políticas e dos projetos de lei (APIs de Dados Abertos da Câmara e do Senado).
4. Avaliação: padrão-ouro manual em 3 políticas, classificação das demais com LLM e medição da concordância entre os dois.
5. Carga em grafo no Neo4j e consultas Cypher que respondem às hipóteses.
6. Visualização interativa e publicação dos achados.

## Estrutura do repositório

```
neurodireitos-br/
├── data/
│   ├── raw/          # políticas baixadas, como vieram (nunca editadas à mão)
│   ├── interim/      # textos limpos
│   └── processed/    # CSVs finais que vão para o Neo4j
├── docs/             # régua de critérios e dicionário de dados
├── notebooks/        # 01_coleta, 02_limpeza, 03_avaliacao, 04_grafo
├── src/              # funções reaproveitáveis
├── cypher/           # scripts de carga e consultas
└── viz/              # página do grafo interativo
```

## Como reproduzir

Requer Python 3.11 ou superior (testado em 3.13).

```bash
git clone https://github.com/rosystt/neurodireitos-br.git
cd neurodireitos-br

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

pip install -r requirements.txt
```

Para as etapas que usam o grafo, crie uma instância gratuita no [Neo4j AuraDB](https://neo4j.com/product/auradb/), copie `.env.example` para `.env`, preencha as credenciais e teste:

```bash
python -m src.conexao_neo4j
```

Depois, execute os notebooks em ordem (`01` a `04`). O `01_coleta` baixa as políticas de novo, com a data do dia no nome dos arquivos; para reproduzir a análise com os mesmos textos, use os que já estão em `data/raw/politicas/`.

Para conferir os dados depois de cada etapa:

```bash
python -m src.validar_inventario
python -m src.validar_coleta
```

## Limitações

- Poucos casos: 13 aparelhos de 9 fabricantes no grupo principal e 6 no de comparação. Os resultados são contagens descritivas, sem teste estatístico, e a comparação entre grupos indica tendência, não prova diferença.
- O levantamento pode ter deixado de fora aparelhos vendidos no Brasil por canais não pesquisados.
- Políticas de privacidade mudam; cada texto é registrado com a data de coleta e o hash do arquivo baixado. A análise vale para as versões coletadas em 15/11/2026.
- A política de um dos fabricantes existe apenas em chinês.
- A avaliação é feita por quem não é jurista. Os achados descrevem o que as políticas dizem ou deixam de dizer — não são parecer jurídico nem afirmam descumprimento de lei por qualquer empresa.

## Licença

Código sob licença [MIT](LICENSE).
