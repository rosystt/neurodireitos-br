// Fonte: data/processed/grafo/leis.csv
// Normas em vigor e decisões julgadas ligam-se ao país por VIGORA_EM;
// proposições (em tramitação ou retiradas), por PROPOSTA_EM.
UNWIND $linhas AS linha
MERGE (l:Lei {id: linha.id})
SET l.nome = linha.nome,
    l.tipo = linha.tipo,
    l.jurisdicao = linha.jurisdicao,
    l.status = linha.status,
    l.data_vigencia = CASE linha.data_vigencia WHEN '' THEN null ELSE date(linha.data_vigencia) END,
    l.cita_dado_neural = (linha.cita_dado_neural = 'sim'),
    l.url = linha.url
WITH l, linha
MATCH (p:Pais {nome: linha.pais})
FOREACH (_ IN CASE WHEN linha.status IN ['vigente', 'julgado'] THEN [1] ELSE [] END |
  MERGE (l)-[:VIGORA_EM]->(p))
FOREACH (_ IN CASE WHEN linha.status IN ['em_tramitacao', 'retirado'] THEN [1] ELSE [] END |
  MERGE (l)-[:PROPOSTA_EM]->(p));
