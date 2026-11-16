// Fonte: data/processed/grafo/paises.csv
UNWIND $linhas AS linha
MERGE (p:Pais {nome: linha.nome});
