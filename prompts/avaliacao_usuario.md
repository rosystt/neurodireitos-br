# Régua de critérios

{regua}

# Tarefa

Abaixo estão os documentos que formam a política de privacidade de um fabricante. Leia todos em conjunto e produza:

1. `respostas`: uma resposta para cada um dos 12 critérios (C01 a C12), na ordem. Para cada um, informe:
   - `id_criterio`;
   - `resposta`: `sim`, `nao` ou `nao_menciona`, conforme as regras de decisão do critério;
   - `evidencia`: o trecho literal que sustenta a resposta (vazio se não houver);
   - `id_documento`: o identificador do documento de onde o trecho saiu (vazio se não houver evidência);
   - `justificativa`: por que o trecho leva a essa resposta, ou o que faltou para um `sim`.

2. `fatos`: informações factuais declaradas na política, que não entram na nota.
   - `tipos_de_dado`: cada tipo de dado que a política diz coletar. `categoria` é uma das opções do esquema; `descricao` é como a política chama o dado; `inferido` é `true` quando o dado é produzido a partir de outro (por exemplo, nível de foco calculado a partir do sinal de EEG) e `false` quando é coletado diretamente.
   - `terceiros`: cada terceiro, ou categoria de terceiro, que a política diz receber dados. Use `nome` para o nome próprio, quando houver (por exemplo, o provedor de nuvem), ou para a categoria tal como a política a descreve.
   - `paises`: cada país ou região que a política cita como local de armazenamento ou como destino de transferência dos dados. Escreva o nome do país em português.

   Cada fato leva um trecho literal como evidência e o identificador do documento. Listas vazias são aceitas quando a política não traz a informação.

# Documentos

{documentos}
