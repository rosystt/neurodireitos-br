# Régua de critérios

**Versão 0.9 — proposta, aguardando revisão jurídica.** A régua só passa a valer para a avaliação depois de revisada por alguém de Direito digital e congelada como versão 1.0 (ver [Congelamento](#congelamento)).

Esta régua mede o que cada política de privacidade **declara** sobre dados neurais. Ela foi escrita antes da leitura das políticas, para que os critérios não sejam ajustados aos resultados.

## O que a régua mede — e o que não mede

- **Mede** o texto da política: o que ela afirma, nega ou deixa de dizer.
- **Não mede** a prática das empresas. Uma política pode prometer algo que a empresa não cumpre, ou silenciar sobre algo que ela faz bem.
- **Não é parecer jurídico.** Um "não" ou um "não menciona" descreve o texto; não afirma que a empresa descumpre uma lei.

## Definições

**Dado neural.** Informação obtida da medição da atividade do sistema nervoso — no caso desta amostra, o sinal de EEG captado pelo aparelho. Contam como referência ao dado neural os termos equivalentes usados pela política: *neural data*, *brain data*, *brainwave data*, *EEG data*, *biosignals* (quando o contexto indicar EEG) e suas traduções.

**Inferência.** Informação sobre a pessoa produzida a partir do sinal bruto: níveis de foco, calma, estresse ou atenção, estágios do sono, estados emocionais.

**Unidade de avaliação.** A política de privacidade, não o aparelho. Aparelhos do mesmo fabricante cobertos pela mesma política recebem a mesma avaliação. Quando o fabricante tem mais de um documento aplicável (por exemplo, política geral e política de dados de saúde), todos são lidos em conjunto.

## Respostas possíveis

| Resposta | Quando usar |
|---|---|
| `sim` | A política afirma expressamente o que o critério pergunta. |
| `nao` | A política afirma expressamente o contrário. |
| `nao_menciona` | A política não trata do assunto, ou trata só de dados pessoais em geral quando o critério exige menção ao dado neural. |

Regras que valem para todos os critérios:

1. Toda resposta `sim` ou `nao` exige um **trecho da política** que a sustente, registrado junto com a resposta.
2. Na dúvida entre `sim` e `nao_menciona`, a resposta é `nao_menciona`: afirmações vagas não contam como garantia.
3. Uma garantia limitada a moradores de um lugar específico (por exemplo, "se você mora na Califórnia") **não** vale como `sim`, porque não alcança o usuário no Brasil. Esse caso é registrado como `nao_menciona`, com a restrição anotada.
4. Todos os critérios foram escritos de modo que `sim` seja a resposta mais protetiva.

## Critérios

Os pesos vão de 1 a 3 e somam 25 pontos. A justificativa está em [Pesos e pontuação](#pesos-e-pontuação).

### C01 — Categoria específica (peso 3)

**A política trata o dado neural como uma categoria própria de dado?**

- `sim`: lista o dado neural (ou termo equivalente) entre as categorias de dados coletados, com nome próprio.
- `nao`: afirma que o aparelho não coleta ou não transmite dado neural.
- `nao_menciona`: não cita o dado neural, ou o dilui em expressões como "dados de uso" ou "dados do dispositivo".

Fontes: PL 522/2022, art. 5º, XX (proposto); Colorado, C.R.S. 6-1-1303; Califórnia, Civ. Code 1798.140; Chile, Constituição, art. 19, nº 1.

### C02 — Proteção reforçada (peso 3)

**A política dá ao dado neural proteção reforçada em relação aos demais dados pessoais?**

- `sim`: classifica o dado neural como sensível, ou descreve regras mais rígidas só para ele (acesso restrito, armazenamento separado, criptografia específica).
- `nao`: afirma que o dado neural recebe o mesmo tratamento dos demais dados.
- `nao_menciona`: não diferencia o tratamento.

Fontes: LGPD, arts. 5º, II, e 11 (por analogia com dado de saúde e biométrico, já que a lei não cita dado neural); PL 522/2022, art. 5º, II (proposto); Colorado, C.R.S. 6-1-1303; Califórnia, Civ. Code 1798.140; Chile, Constituição, art. 19, nº 1.

### C03 — Consentimento específico (peso 3)

**A política condiciona a coleta e o uso do dado neural a um consentimento específico e destacado do usuário?**

- `sim`: descreve um consentimento próprio para o dado neural, separado da aceitação geral dos termos.
- `nao`: indica que o uso do produto ou a aceitação dos termos já equivale ao consentimento.
- `nao_menciona`: não informa a base em que o dado neural é tratado.

Fontes: LGPD, art. 11, I (se o dado for tratado como sensível); PL 522/2022, art. 13-A, I (proposto); Colorado, C.R.S. 6-1-1308(7).

### C04 — Finalidades declaradas (peso 2)

**A política declara para quais finalidades específicas o dado neural é usado?**

- `sim`: associa finalidades determinadas ao dado neural (por exemplo, gerar a pontuação de foco, exibir o histórico de sessões).
- `nao`: reserva o direito de usar o dado neural para qualquer finalidade.
- `nao_menciona`: lista finalidades só para dados pessoais em geral.

Fontes: LGPD, arts. 6º, I, e 9º, I; PL 522/2022, art. 13-A, I (proposto); Colorado, C.R.S. 6-1-1308(2); Califórnia, Civ. Code 1798.100(a).

### C05 — Inferências informadas (peso 2)

**A política informa quais inferências sobre o usuário são feitas a partir do dado neural?**

- `sim`: nomeia as inferências produzidas (foco, estresse, estágios do sono etc.).
- `nao`: afirma que nenhuma inferência é feita, ou que nenhum dado derivado é guardado.
- `nao_menciona`: não distingue o sinal bruto das informações derivadas dele.

Fontes: LGPD, arts. 6º, VI, e 9º; PL 522/2022, art. 5º, XX (proposto), que alcança a informação obtida "direta ou indiretamente". É o critério com a base legal mais fraca; ele existe porque a separação entre sinal bruto e inferência é central no modelo do grafo.

Observação: aqui `nao` descreve uma prática que pode ser protetiva. Por isso o critério é reportado também em separado, fora da pontuação.

### C06 — Sem venda nem publicidade (peso 3)

**A política afirma que o dado neural não é vendido nem usado ou compartilhado para publicidade?**

- `sim`: afasta expressamente a venda e o uso publicitário do dado neural, ou dos dados pessoais em geral sem excetuar o neural.
- `nao`: admite a venda, ou o compartilhamento com anunciantes e redes de publicidade, sem excluir o dado neural.
- `nao_menciona`: não trata de venda nem de publicidade.

Fontes: LGPD, art. 11, § 3º; PL 522/2022, art. 13-C (proposto); Colorado, C.R.S. 6-1-1306(1)(a) e 6-1-1308(7); Califórnia, Civ. Code 1798.120 e 1798.121.

### C07 — Terceiros identificados (peso 1)

**A política identifica, por nome ou por categoria, os terceiros que recebem o dado neural?**

- `sim`: indica quem recebe o dado neural, por nome (por exemplo, o provedor de nuvem) ou por categoria definida, ou afirma que ele não é compartilhado com ninguém.
- `nao`: admite compartilhar com terceiros sem dizer quais.
- `nao_menciona`: identifica terceiros só para dados pessoais em geral.

Fontes: LGPD, arts. 9º, V, e 18, VII; Colorado, C.R.S. 6-1-1308(1); Califórnia, Civ. Code 1798.110.

### C08 — Local de armazenamento (peso 2)

**A política informa em que país os dados são armazenados e com que garantias são transferidos para o exterior?**

- `sim`: indica o país ou a região de armazenamento **e** o mecanismo de transferência internacional (cláusulas contratuais, decisão de adequação, consentimento).
- `nao`: informa que os dados podem ser enviados a qualquer país, sem garantias.
- `nao_menciona`: não informa onde os dados ficam.

Quando só uma das duas informações aparece, a resposta é `nao_menciona`, com a parte encontrada anotada.

Fontes: LGPD, arts. 33 a 36.

### C09 — Exclusão a pedido (peso 2)

**A política garante ao usuário a exclusão do seu dado neural mediante pedido?**

- `sim`: oferece a exclusão a qualquer usuário e indica como pedi-la.
- `nao`: afirma que o dado neural, ou cópias dele, é mantido mesmo após o pedido, além do que a lei exige.
- `nao_menciona`: não trata de exclusão, ou a oferece só a moradores de determinados lugares.

Fontes: LGPD, art. 18, VI; Colorado, C.R.S. 6-1-1306(1)(d); Califórnia, Civ. Code 1798.105; Chile, Corte Suprema, Rol 105.065-2023.

### C10 — Prazo de retenção (peso 1)

**A política informa por quanto tempo o dado neural é guardado ou o critério que define esse prazo?**

- `sim`: indica um prazo, ou um critério verificável (por exemplo, "até a exclusão da conta").
- `nao`: afirma guardar o dado por tempo indeterminado.
- `nao_menciona`: não trata de prazo, ou usa só fórmulas genéricas como "pelo tempo necessário".

Fontes: LGPD, arts. 9º, II, 15 e 16; Califórnia, Civ. Code 1798.100(a)(3).

### C11 — Uso secundário controlado (peso 2)

**A política condiciona o uso do dado neural em pesquisa ou no treinamento de algoritmos a consentimento separado ou à anonimização?**

- `sim`: exige adesão separada do usuário, ou garante que o dado é anonimizado antes desse uso.
- `nao`: reserva o uso do dado neural para pesquisa, melhoria de produto ou treinamento de algoritmos sem adesão separada e sem anonimização.
- `nao_menciona`: não trata desses usos.

A simples menção a dados "agregados" ou "desidentificados", sem descrever o que isso significa, não basta para `sim`.

Fontes: LGPD, arts. 6º, I, e 11, II, c; PL 522/2022, art. 13-A, II, a (proposto); Colorado, C.R.S. 6-1-1308(4); Califórnia, Civ. Code 1798.100(c); Chile, Corte Suprema, Rol 105.065-2023.

### C12 — Direitos no Brasil (peso 1)

**A política reconhece os direitos previstos na LGPD ou indica um canal de atendimento para titulares no Brasil?**

- `sim`: cita a LGPD ou o Brasil, indica um encarregado ou um canal para titulares brasileiros, ou declara que os direitos descritos valem para usuários de qualquer país.
- `nao`: restringe expressamente os direitos a moradores de outros lugares.
- `nao_menciona`: não cita o Brasil nem estende os direitos a todos os usuários.

Fontes: LGPD, arts. 3º, 18 e 41.

## Pesos e pontuação

**Pesos.** São um julgamento do projeto, não uma medida objetiva:

| Peso | Critérios | Razão |
|---|---|---|
| 3 | C01, C02, C03, C06 | Tratam do que é próprio do dado neural e do risco mais grave: reconhecimento, proteção reforçada, consentimento e uso comercial. |
| 2 | C04, C05, C08, C09, C11 | Deveres e direitos com efeito direto sobre o que acontece com o dado. |
| 1 | C07, C10, C12 | Transparência complementar. |

**Pontuação.** A nota de uma política é a soma dos pesos dos critérios respondidos com `sim`, de 0 a 25. `nao` e `nao_menciona` valem zero.

Como os pesos são discutíveis, todo resultado é reportado de três formas:

1. Nota ponderada (0 a 25).
2. Contagem simples de respostas `sim` (0 a 12), para mostrar que a conclusão não depende dos pesos.
3. Distribuição de `sim`, `nao` e `nao_menciona` por critério — o silêncio e a negativa valem os mesmos zero pontos, mas não significam a mesma coisa.

## Critérios e hipóteses

| Hipótese | Critérios |
|---|---|
| H1 — a maioria das políticas não trata dado neural como categoria específica | C01, C02 |
| H2 — parte relevante compartilha com terceiros ou guarda os dados fora do Brasil | C06, C07, C08 |
| H3 — as políticas oferecem menos garantias do que as leis de referência exigem | C03, C04, C05, C09, C10, C11, C12 e a nota total |

Além das respostas aos critérios, a avaliação extrai de cada política três **fatos**, que alimentam o grafo e não entram na nota: os terceiros citados, os países de armazenamento e os tipos de dado coletados.

## Leis de referência

Situação verificada em 15/11/2026.

| Norma | Lugar | Situação | O que traz sobre dado neural |
|---|---|---|---|
| Lei 13.709/2018 (LGPD) | Brasil | Em vigor | Não cita dado neural. Aplica-se como a qualquer dado pessoal e, por analogia, como dado sensível de saúde ou biométrico. |
| PL 522/2022 | Brasil | Em tramitação na Câmara (aguardando parecer na Comissão de Saúde; PL 6687/2025 apensado) | Inclui o dado neural entre os dados sensíveis, define o termo e cria regras próprias de tratamento (arts. 13-A a 13-E). |
| HB 24-1058 | Colorado (EUA) | Em vigor desde 07/08/2024 | Inclui o dado neural entre os dados sensíveis do Colorado Privacy Act, que exigem consentimento prévio. |
| SB 1223 | Califórnia (EUA) | Em vigor desde 01/01/2025 | Inclui o dado neural entre as informações pessoais sensíveis do CCPA, com direito de limitar seu uso. |
| Ley 21.383 | Chile | Em vigor desde 25/10/2021 | Emenda constitucional que manda proteger a atividade cerebral e a informação proveniente dela. |
| Corte Suprema, Rol 105.065-2023 | Chile | Julgado em 09/08/2023 | Ordenou a uma fabricante de EEG de consumo a eliminação dos dados cerebrais de um usuário. |

Os dispositivos do PL 522/2022 foram lidos no texto integral do projeto. As citações de artigos das leis estrangeiras vêm de fontes secundárias e ainda precisam ser conferidas no texto oficial — é um dos pontos da revisão jurídica.

Fontes:

- LGPD: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm
- PL 522/2022: https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao=2317524
- Colorado HB 24-1058: https://leg.colorado.gov/bills/hb24-1058
- Califórnia SB 1223: https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=202320240SB1223
- Chile, Ley 21.383: https://www.bcn.cl/leychile/navegar?idNorma=1166983

## Pontos para a revisão jurídica

1. As citações de artigos estão corretas e são as mais adequadas para cada critério?
2. A analogia do dado neural com dado sensível de saúde ou biométrico na LGPD (C02, C03) é defensável?
3. Falta algum critério relevante — por exemplo, tratamento de dados de crianças e adolescentes ou decisões automatizadas?
4. A regra 3 (garantia restrita a moradores de um lugar não vale como `sim`) é justa?
5. Os pesos refletem a gravidade relativa dos temas?

## Congelamento

1. A revisão jurídica gera ajustes nesta versão 0.9.
2. Fechados os ajustes, o documento vira versão 1.0 e o commit recebe a tag `criterios-v1.0` no Git.
3. A partir daí a régua não muda durante a avaliação. Qualquer alteração posterior exige nova versão, justificativa registrada aqui e reavaliação de **todas** as políticas.

A versão em tabela, usada pelo código e pelo grafo, está em [`data/processed/criterios.csv`](../data/processed/criterios.csv). `python -m src.validar_criterios` confere se ela e este documento estão de acordo.
