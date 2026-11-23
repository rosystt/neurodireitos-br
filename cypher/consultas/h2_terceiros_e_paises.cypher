// H2 — parte relevante das empresas compartilha dados com terceiros ou guarda
// os dados fora do Brasil. Uma linha por grupo, a partir dos fatos extraídos
// das políticas. Não citar país não significa guardar no Brasil: essas
// políticas aparecem em sem_pais_declarado. Atender ordem de autoridade é
// previsto em quase toda política e não é o compartilhamento que H2 mede; por
// isso terceiros_ou_fora usa compartilha_exceto_autoridades.
MATCH (e:Empresa)
OPTIONAL MATCH (e)-[:COMPARTILHA_COM]->(t:Terceiro)
OPTIONAL MATCH (e)-[:ARMAZENA_EM|TRANSFERE_PARA]->(p:Pais)
WITH e, collect(DISTINCT t.categoria) AS terceiros, collect(DISTINCT p.nome) AS paises
RETURN e.grupo AS grupo,
       count(e) AS politicas,
       count(CASE WHEN size(terceiros) > 0 THEN 1 END) AS compartilha_com_terceiros,
       count(CASE WHEN any(c IN terceiros WHERE c <> 'autoridades') THEN 1 END) AS compartilha_exceto_autoridades,
       count(CASE WHEN 'publicidade' IN terceiros THEN 1 END) AS compartilha_com_publicidade,
       count(CASE WHEN any(nome IN paises WHERE nome <> 'Brasil') THEN 1 END) AS dados_fora_do_brasil,
       count(CASE WHEN size(paises) = 0 THEN 1 END) AS sem_pais_declarado,
       count(CASE WHEN any(c IN terceiros WHERE c <> 'autoridades') OR any(nome IN paises WHERE nome <> 'Brasil') THEN 1 END) AS terceiros_ou_fora
ORDER BY grupo;
