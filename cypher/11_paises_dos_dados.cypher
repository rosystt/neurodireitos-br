// Fonte: data/processed/grafo/paises_dos_dados.csv
// relacao: ARMAZENA_EM ou TRANSFERE_PARA. Cypher não aceita tipo de relação
// como parâmetro, por isso há um comando para cada tipo.
UNWIND [linha IN $linhas WHERE linha.relacao = 'ARMAZENA_EM'] AS linha
MATCH (e:Empresa {id: linha.id_empresa})
MATCH (p:Pais {nome: linha.pais})
MERGE (e)-[r:ARMAZENA_EM]->(p)
SET r.evidencia = linha.evidencia, r.id_documento = linha.id_documento;

UNWIND [linha IN $linhas WHERE linha.relacao = 'TRANSFERE_PARA'] AS linha
MATCH (e:Empresa {id: linha.id_empresa})
MATCH (p:Pais {nome: linha.pais})
MERGE (e)-[r:TRANSFERE_PARA]->(p)
SET r.evidencia = linha.evidencia, r.id_documento = linha.id_documento;
