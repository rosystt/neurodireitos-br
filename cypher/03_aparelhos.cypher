// Fonte: data/processed/grafo/aparelhos.csv
// VENDIDO_EM só existe para o grupo 'brasil' e guarda o tipo de evidência da venda.
UNWIND $linhas AS linha
MERGE (a:Aparelho {id: linha.id})
SET a.nome = linha.nome,
    a.tipo = linha.tipo,
    a.grupo = linha.grupo,
    a.preco_referencia = CASE linha.preco_referencia WHEN '' THEN null ELSE toFloat(linha.preco_referencia) END,
    a.moeda = CASE linha.moeda WHEN '' THEN null ELSE linha.moeda END
WITH a, linha
MATCH (e:Empresa {id: linha.id_empresa})
MERGE (e)-[:FABRICA]->(a)
WITH a, linha
WHERE linha.grupo = 'brasil'
MATCH (br:Pais {nome: 'Brasil'})
MERGE (a)-[v:VENDIDO_EM]->(br)
SET v.canal = linha.canal_venda_br,
    v.evidencia = linha.url_evidencia_venda,
    v.data_coleta = date(linha.data_coleta);
