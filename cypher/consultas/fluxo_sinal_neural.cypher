// Para onde vai o sinal neural coletado pelas empresas do grupo brasil, e se
// há norma com proteção específica em vigor no destino. Nos Estados Unidos
// as normas são estaduais (Colorado, Califórnia): estar no país não garante
// que o dado fique sob uma delas.
MATCH (e:Empresa {grupo: 'brasil'})-[:COLETA]->(:Dado {categoria: 'sinal_neural'})
MATCH (e)-[rel:ARMAZENA_EM|TRANSFERE_PARA]->(p:Pais)
OPTIONAL MATCH (l:Lei)-[:VIGORA_EM]->(p)
WHERE (l)-[:PROTEGE {nivel: 'especifica'}]->(:Dado {categoria: 'sinal_neural'})
WITH p, collect(DISTINCT e.id) AS empresas, collect(DISTINCT type(rel)) AS relacoes,
     collect(DISTINCT l.id + ' (' + l.jurisdicao + ')') AS normas_especificas
RETURN p.nome AS destino, p.tipo AS tipo, size(empresas) AS empresas,
       empresas AS ids, relacoes, normas_especificas
ORDER BY empresas DESC, destino;
