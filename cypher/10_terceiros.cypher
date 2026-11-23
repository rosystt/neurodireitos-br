// Fonte: data/processed/grafo/terceiros.csv
// O nó :Terceiro é a categoria; o nome citado pela política fica na relação.
UNWIND $linhas AS linha
MATCH (e:Empresa {id: linha.id_empresa})
MERGE (t:Terceiro {categoria: linha.categoria})
MERGE (e)-[c:COMPARTILHA_COM {nome_citado: linha.nome_citado}]->(t)
SET c.evidencia = linha.evidencia,
    c.id_documento = linha.id_documento;
