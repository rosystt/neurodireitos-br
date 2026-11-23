// H3 — proporção de respostas sim em cada critério de H3, por grupo.
MATCH (e:Empresa)-[r:RESPONDE]->(c:Criterio {hipotese: 'H3'})
WITH c, e.grupo AS grupo, count(*) AS politicas,
     count(CASE r.resposta WHEN 'sim' THEN 1 END) AS sim
RETURN c.id AS criterio, c.nome AS nome, grupo, politicas, sim,
       round(100.0 * sim / politicas, 1) AS pct_sim
ORDER BY criterio, grupo;
