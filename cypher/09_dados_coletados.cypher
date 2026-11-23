// Fonte: data/processed/grafo/dados_coletados.csv
// O nó :Dado é a categoria; a relação guarda como a política chama o dado e
// se ele é inferido (produzido a partir de outro dado).
UNWIND $linhas AS linha
MATCH (e:Empresa {id: linha.id_empresa})
MERGE (d:Dado {categoria: linha.categoria})
MERGE (e)-[c:COLETA {descricao: linha.descricao}]->(d)
SET c.inferido = linha.inferido = 'sim',
    c.evidencia = linha.evidencia,
    c.id_documento = linha.id_documento;
