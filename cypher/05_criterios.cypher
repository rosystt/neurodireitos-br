// Fonte: data/processed/grafo/criterios.csv
UNWIND $linhas AS linha
MERGE (c:Criterio {id: linha.id})
SET c.nome = linha.criterio,
    c.pergunta = linha.pergunta,
    c.peso = toInteger(linha.peso),
    c.hipotese = linha.hipotese;
