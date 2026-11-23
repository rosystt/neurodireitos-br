// Fonte: data/processed/grafo/respostas.csv (Fase 4, avaliação por modelo de linguagem)
// resposta: 'sim' (mais protetivo), 'nao' ou 'nao_menciona'. Uma relação por
// política e critério; rodar de novo substitui a resposta anterior.
UNWIND $linhas AS linha
MATCH (e:Empresa {id: linha.id_empresa})
MATCH (c:Criterio {id: linha.id_criterio})
MERGE (e)-[r:RESPONDE]->(c)
SET r.resposta = linha.resposta,
    r.evidencia = linha.evidencia,
    r.id_documento = linha.id_documento,
    r.justificativa = linha.justificativa,
    r.modelo = linha.modelo,
    r.versao_prompt = linha.versao_prompt,
    r.versao_regua = linha.versao_regua;
