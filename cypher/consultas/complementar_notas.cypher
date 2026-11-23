// Pergunta complementar — as políticas dos aparelhos que chegam ao Brasil
// oferecem menos garantias do que as do grupo de comparação? Resumo da nota
// ponderada por grupo. percentileCont dá a mesma mediana do pandas.
MATCH (e:Empresa)
RETURN e.grupo AS grupo,
       count(e) AS politicas,
       min(e.nota) AS nota_minima,
       percentileCont(e.nota, 0.5) AS nota_mediana,
       round(avg(e.nota), 1) AS nota_media,
       max(e.nota) AS nota_maxima_obtida,
       max(e.nota_maxima) AS nota_maxima_possivel
ORDER BY grupo;
