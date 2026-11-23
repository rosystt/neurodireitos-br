// Fonte: data/processed/grafo/protecao.csv
// nivel: 'especifica' (a norma cita dado neural) ou 'generica' (LGPD, por
// analogia com dado sensível). Só normas vigentes ou julgadas.
UNWIND $linhas AS linha
MATCH (l:Lei {id: linha.id_lei})
MERGE (d:Dado {categoria: linha.categoria})
MERGE (l)-[p:PROTEGE]->(d)
SET p.nivel = linha.nivel;
