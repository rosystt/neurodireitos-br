// Fonte: data/processed/grafo/notas.csv
// Nota ponderada da política (0 a nota_maxima), gravada como número.
UNWIND $linhas AS linha
MATCH (e:Empresa {id: linha.id_empresa})
SET e.nota = toInteger(linha.nota_ponderada),
    e.nota_maxima = toInteger(linha.nota_maxima);
