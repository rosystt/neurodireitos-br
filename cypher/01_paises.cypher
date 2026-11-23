// Fonte: data/processed/grafo/paises.csv
// tipo: 'pais' ou 'regiao' (União Europeia, Espaço Econômico Europeu), citada
// por políticas como destino dos dados.
UNWIND $linhas AS linha
MERGE (p:Pais {nome: linha.nome})
SET p.tipo = linha.tipo;
