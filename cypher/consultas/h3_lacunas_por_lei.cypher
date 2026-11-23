// H3 — as políticas oferecem menos garantias do que as leis de referência
// exigem. Para cada norma em vigor que protege o sinal neural de forma
// específica, os critérios que ela fundamenta e quantas políticas do grupo
// brasil não respondem sim (lacunas). Entram todos os critérios que a norma
// fundamenta, de qualquer hipótese; a nota total está em complementar_notas.
MATCH (l:Lei)-[:PROTEGE {nivel: 'especifica'}]->(:Dado {categoria: 'sinal_neural'})
MATCH (l)-[:FUNDAMENTA]->(c:Criterio)
MATCH (e:Empresa {grupo: 'brasil'})-[r:RESPONDE]->(c)
WITH l, c, count(e) AS politicas, count(CASE WHEN r.resposta <> 'sim' THEN 1 END) AS lacunas
RETURN l.id AS lei,
       l.jurisdicao AS jurisdicao,
       count(c) AS criterios_fundamentados,
       sum(politicas) AS respostas,
       sum(lacunas) AS lacunas,
       round(100.0 * sum(lacunas) / sum(politicas), 1) AS pct_lacunas
ORDER BY lei;
