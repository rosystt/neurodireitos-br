// H1 — a maioria das políticas não trata dado neural como categoria específica.
// Critérios C01 (categoria específica) e C02 (proteção reforçada): quantas
// políticas de cada grupo respondem sim, nao e nao_menciona.
MATCH (e:Empresa)-[r:RESPONDE]->(c:Criterio {hipotese: 'H1'})
RETURN c.id AS criterio,
       c.nome AS nome,
       e.grupo AS grupo,
       count(*) AS politicas,
       count(CASE r.resposta WHEN 'sim' THEN 1 END) AS sim,
       count(CASE r.resposta WHEN 'nao' THEN 1 END) AS nao,
       count(CASE r.resposta WHEN 'nao_menciona' THEN 1 END) AS nao_menciona
ORDER BY criterio, grupo;
