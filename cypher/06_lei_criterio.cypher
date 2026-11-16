// Fonte: data/processed/grafo/lei_criterio.csv
// Cada relação guarda o dispositivo da lei que fundamenta o critério.
UNWIND $linhas AS linha
MATCH (l:Lei {id: linha.id_lei})
MATCH (c:Criterio {id: linha.id_criterio})
MERGE (l)-[f:FUNDAMENTA]->(c)
SET f.dispositivo = linha.dispositivo;
