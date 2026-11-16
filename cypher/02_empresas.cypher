// Fonte: data/processed/grafo/empresas.csv
// grupo: 'brasil' (vende ou entrega no Brasil) ou 'comparacao' (não entrega).
UNWIND $linhas AS linha
MERGE (e:Empresa {id: linha.id_empresa})
SET e.nome = linha.nome,
    e.grupo = linha.grupo,
    e.url_politica = linha.url_politica
WITH e, linha
MATCH (p:Pais {nome: linha.pais_sede})
MERGE (e)-[:SEDIADA_EM]->(p);
