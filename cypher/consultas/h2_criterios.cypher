// H2 — respostas aos critérios C06 (sem venda nem publicidade), C07 (terceiros
// identificados) e C08 (local de armazenamento), por grupo.
MATCH (e:Empresa)-[r:RESPONDE]->(c:Criterio {hipotese: 'H2'})
RETURN c.id AS criterio,
       c.nome AS nome,
       e.grupo AS grupo,
       count(*) AS politicas,
       count(CASE r.resposta WHEN 'sim' THEN 1 END) AS sim,
       count(CASE r.resposta WHEN 'nao' THEN 1 END) AS nao,
       count(CASE r.resposta WHEN 'nao_menciona' THEN 1 END) AS nao_menciona
ORDER BY criterio, grupo;
