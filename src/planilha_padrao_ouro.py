"""Planilha Excel da avaliação manual do padrão-ouro, em português.

O arquivo de referência continua sendo o CSV (data/interim/avaliacao/manual/
padrao_ouro.csv), que o notebook 03 compara com as respostas do modelo. O
.xlsx só facilita o preenchimento: traz a regra de cada critério ao lado da
pergunta, uma lista suspensa para a resposta e os caminhos dos textos (o
original e a tradução para o português, alinhada linha a linha).

A planilha não mostra nenhuma resposta do modelo: quem preenche deve julgar
sem conhecê-las.

Uso (na raiz do projeto, com o venv ativo):

    python -m src.planilha_padrao_ouro gerar      # CSV -> .xlsx (não sobrescreve um .xlsx existente)
    python -m src.planilha_padrao_ouro importar   # .xlsx preenchido -> CSV
"""

import re
import sys
from pathlib import Path

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

PASTA = Path("data/interim/avaliacao/manual")
CSV = PASTA / "padrao_ouro.csv"
XLSX = PASTA / "padrao_ouro.xlsx"
CRITERIOS_MD = Path("docs/criterios.md")
PASTA_POLITICAS = Path("data/interim/politicas")
PASTA_TRADUCOES = Path("data/interim/traducoes")

RESPOSTAS = ["sim", "nao", "nao_menciona"]
COLUNAS_CSV = ["id_politica", "id_criterio", "pergunta", "resposta", "evidencia", "observacoes", "id_documento", "linha"]
ABA = "Avaliação"
CABECALHO = ["Política", "Fabricante", "Critério", "Pergunta", "Como responder", "Resposta", "Evidência (trecho copiado)", "Observações"]
LARGURAS = [9, 18, 22, 40, 70, 15, 60, 30]

INSTRUCOES = """Como preencher

1. Use a aba "Avaliação". Cada linha é uma política e um critério (3 políticas × 12 critérios).
2. Leia a política inteira antes de responder. Os textos ficam na aba "Textos": a tradução para o português tem as mesmas linhas do original em inglês.
3. Na coluna "Resposta", escolha na lista: sim, nao ou nao_menciona. A coluna "Como responder" diz quando usar cada uma.
4. Toda resposta sim ou nao precisa de evidência: copie e cole na coluna "Evidência" o trecho que sustenta a resposta. Pode colar da tradução ou do original; o programa encontra a linha sozinho.
5. "Observações" é opcional: use para dúvidas, restrições ("só vale para a Califórnia") ou partes encontradas pela metade.
6. Não consulte as respostas do modelo antes de terminar (data/processed/avaliacoes.csv e data/interim/avaliacao/llm/). A comparação só vale se o seu julgamento for independente.
7. Salve o arquivo como .xlsx mesmo, sem mudar o nome. Depois, peça para importar (python -m src.planilha_padrao_ouro importar).

Regras que valem para todos os critérios
"""


# --- Leitura da régua -------------------------------------------------------

def regras_gerais() -> str:
    """As regras numeradas de docs/criterios.md que valem para todos os critérios."""
    texto = CRITERIOS_MD.read_text(encoding="utf-8")
    bloco = texto.split("Regras que valem para todos os critérios:", 1)[1].split("## Critérios", 1)[0]
    return _limpar_markdown(bloco).strip()


def regras_por_criterio() -> dict[str, str]:
    """Para cada critério, o que vale como sim, nao e nao_menciona (sem as fontes legais)."""
    texto = CRITERIOS_MD.read_text(encoding="utf-8")
    secoes = re.split(r"^### (C\d{2}) — .*$", texto, flags=re.M)
    regras = {}
    for id_criterio, corpo in zip(secoes[1::2], secoes[2::2]):
        corpo = corpo.split("\n## ", 1)[0]
        linhas = [
            linha for linha in corpo.strip().splitlines()
            if linha.strip() and not linha.startswith(("**", "Fontes:"))
        ]
        regras[id_criterio] = _limpar_markdown("\n".join(linhas)).strip()
    return regras


def _limpar_markdown(texto: str) -> str:
    texto = re.sub(r"\*\*(.+?)\*\*", r"\1", texto)
    texto = re.sub(r"\*(.+?)\*", r"\1", texto)
    texto = texto.replace("`", "")
    return re.sub(r"^- ", "• ", texto, flags=re.M)


# --- Textos das políticas ---------------------------------------------------

def documentos(id_politica: str) -> list[str]:
    return sorted(arquivo.stem for arquivo in PASTA_POLITICAS.glob(f"{id_politica}-*.txt"))


def localizar_evidencia(id_politica: str, trecho: str) -> tuple[str, str]:
    """Documento e linha onde o trecho aparece, na tradução ou no original.

    A comparação ignora diferenças de espaços e de maiúsculas. Devolve
    ("", "") se o trecho não for encontrado.
    """
    alvo = _normalizar(trecho)
    if not alvo:
        return "", ""
    for documento in documentos(id_politica):
        for arquivo in (PASTA_TRADUCOES / f"{documento}_pt.txt", PASTA_POLITICAS / f"{documento}.txt"):
            if not arquivo.exists():
                continue
            for numero, linha in enumerate(arquivo.read_text(encoding="utf-8").splitlines(), start=1):
                if alvo in _normalizar(linha):
                    return documento, str(numero)
    return "", ""


def _normalizar(texto: str) -> str:
    texto = texto.replace("“", '"').replace("”", '"').replace("’", "'")
    return re.sub(r"\s+", " ", texto).strip().lower()


# --- Gerar ------------------------------------------------------------------

def gerar() -> None:
    if XLSX.exists():
        sys.exit(f"{XLSX} já existe; não vou sobrescrever o que pode ter sido preenchido.")
    manual = pd.read_csv(CSV, dtype=str, keep_default_na=False).reindex(columns=COLUNAS_CSV, fill_value="")
    criterios = pd.read_csv("data/processed/criterios.csv", dtype=str).set_index("id")
    fabricantes = pd.read_csv("data/raw/fontes_politicas.csv", dtype=str).drop_duplicates("id_politica").set_index("id_politica")["fabricante"]
    regras = regras_por_criterio()

    livro = Workbook()
    _aba_instrucoes(livro.active)
    _aba_avaliacao(livro.create_sheet(ABA), manual, criterios, fabricantes, regras)
    _aba_textos(livro.create_sheet("Textos"), sorted(manual["id_politica"].unique()), fabricantes)
    livro.active = 1
    livro.save(XLSX)
    print(f"{XLSX} criado: {len(manual)} linhas para preencher.")


def _aba_instrucoes(aba) -> None:
    aba.title = "Como preencher"
    aba.column_dimensions["A"].width = 120
    linhas = (INSTRUCOES + "\n" + regras_gerais()).splitlines()
    for numero, texto in enumerate(linhas, start=1):
        celula = aba.cell(row=numero, column=1, value=texto)
        celula.alignment = Alignment(wrap_text=True, vertical="top")
        if numero == 1 or texto.startswith("Regras que valem"):
            celula.font = Font(bold=True, size=13)


def _aba_avaliacao(aba, manual, criterios, fabricantes, regras) -> None:
    aba.append(CABECALHO)
    for linha in manual.itertuples():
        aba.append([
            linha.id_politica,
            fabricantes.get(linha.id_politica, ""),
            f"{linha.id_criterio} — {criterios.loc[linha.id_criterio, 'criterio']}",
            linha.pergunta,
            regras[linha.id_criterio],
            linha.resposta,
            linha.evidencia,
            linha.observacoes,
        ])

    destaque = PatternFill("solid", start_color="DDEBF7")
    for coluna, largura in enumerate(LARGURAS, start=1):
        aba.column_dimensions[aba.cell(row=1, column=coluna).column_letter].width = largura
        cabecalho = aba.cell(row=1, column=coluna)
        cabecalho.font = Font(bold=True)
        cabecalho.fill = destaque
    for linha in aba.iter_rows(min_row=2):
        for celula in linha:
            celula.alignment = Alignment(wrap_text=True, vertical="top")
    aba.freeze_panes = "F2"
    aba.auto_filter.ref = aba.dimensions

    lista = DataValidation(type="list", formula1='"' + ",".join(RESPOSTAS) + '"', allow_blank=True)
    lista.error = "Escolha sim, nao ou nao_menciona."
    lista.errorTitle = "Resposta inválida"
    aba.add_data_validation(lista)
    lista.add(f"F2:F{aba.max_row}")


def _aba_textos(aba, politicas, fabricantes) -> None:
    raiz = Path.cwd()
    aba.append(["Política", "Fabricante", "Documento", "Tradução para o português", "Original"])
    for celula in aba[1]:
        celula.font = Font(bold=True)
    for id_politica in politicas:
        for documento in documentos(id_politica):
            traducao = raiz / PASTA_TRADUCOES / f"{documento}_pt.txt"
            aba.append([
                id_politica, fabricantes.get(id_politica, ""), documento,
                str(traducao) if traducao.exists() else "(sem tradução)",
                str(raiz / PASTA_POLITICAS / f"{documento}.txt"),
            ])
    for coluna, largura in zip("ABCDE", [9, 20, 11, 80, 80]):
        aba.column_dimensions[coluna].width = largura


# --- Importar ---------------------------------------------------------------

def importar() -> None:
    if not XLSX.exists():
        sys.exit(f"{XLSX} não existe; gere a planilha primeiro.")
    aba = load_workbook(XLSX, read_only=True)[ABA]
    linhas = list(aba.iter_rows(values_only=True))
    if list(linhas[0][: len(CABECALHO)]) != CABECALHO:
        sys.exit("O cabeçalho da aba 'Avaliação' foi alterado; não dá para importar com segurança.")
    preenchido = pd.DataFrame(
        [[("" if valor is None else str(valor).strip()) for valor in linha[: len(CABECALHO)]] for linha in linhas[1:]],
        columns=CABECALHO,
    )

    manual = pd.read_csv(CSV, dtype=str, keep_default_na=False).reindex(columns=COLUNAS_CSV, fill_value="")
    if len(preenchido) != len(manual):
        sys.exit(f"A planilha tem {len(preenchido)} linhas, e o CSV tem {len(manual)}.")
    criterio = preenchido["Critério"].str.split(" — ").str[0]
    if not (preenchido["Política"].eq(manual["id_politica"]) & criterio.eq(manual["id_criterio"])).all():
        sys.exit("A ordem das linhas mudou (talvez por um filtro ou ordenação salvos); desfaça e salve de novo.")

    problemas = []
    for posicao, linha in preenchido.iterrows():
        rotulo = f"{linha['Política']} {criterio[posicao]}"
        resposta = linha["Resposta"]
        if resposta and resposta not in RESPOSTAS:
            problemas.append(f"{rotulo}: resposta '{resposta}' fora da lista")
            continue
        documento, numero = localizar_evidencia(linha["Política"], linha["Evidência (trecho copiado)"])
        if resposta in ("sim", "nao") and not linha["Evidência (trecho copiado)"]:
            problemas.append(f"{rotulo}: resposta {resposta} sem evidência")
        elif linha["Evidência (trecho copiado)"] and not documento:
            problemas.append(f"{rotulo}: o trecho da evidência não foi encontrado nos textos; confira se foi copiado inteiro")
        manual.loc[posicao, ["resposta", "evidencia", "observacoes", "id_documento", "linha"]] = [
            resposta, linha["Evidência (trecho copiado)"], linha["Observações"], documento, numero,
        ]

    manual.to_csv(CSV, index=False, encoding="utf-8", lineterminator="\n")
    respondidas = int((manual["resposta"] != "").sum())
    print(f"{CSV} atualizado: {respondidas} de {len(manual)} respostas preenchidas.")
    if problemas:
        print("Pontos a conferir:")
        for problema in problemas:
            print(f"- {problema}")


if __name__ == "__main__":
    comandos = {"gerar": gerar, "importar": importar}
    if len(sys.argv) != 2 or sys.argv[1] not in comandos:
        sys.exit("Uso: python -m src.planilha_padrao_ouro [gerar|importar]")
    comandos[sys.argv[1]]()
