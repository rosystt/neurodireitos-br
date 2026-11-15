"""Levantamento dos projetos de lei sobre dados neurais na Câmara e no Senado.

A busca por palavra-chave traz também proposições que só usam o termo de
passagem (por exemplo, "rede neural" em um projeto sobre inteligência
artificial). Por isso todos os resultados ficam na tabela, com uma coluna
que diz se a ementa trata de fato do tema.
"""

import csv
import re
from datetime import date
from pathlib import Path

from src.coleta import buscar_camara, buscar_senado, detalhar_camara, detalhar_senado

TABELA = Path("data/interim/projetos_lei.csv")
COLUNAS = [
    "casa", "sigla", "numero", "ano", "ementa", "autoria", "data_apresentacao",
    "situacao", "url", "termos_busca", "trata_do_tema", "data_coleta",
]

TERMOS = [
    "dados neurais", "neural", "neurodireitos", "neurotecnologia",
    "integridade mental", "atividade cerebral",
]
TIPOS = {"PL", "PLP", "PEC"}
# Matérias conhecidas que a busca por palavra-chave do Senado não devolve.
MATERIAS_SENADO = [("PEC", 29, 2023)]

# A ementa trata do tema quando fala de dados ou direitos ligados ao cérebro.
PADRAO_TEMA = re.compile(
    r"dados? neura(l|is)|neurodireito|neurotecnologia|integridade mental|"
    r"atividade cerebral|interface c[ée]rebro",
    re.IGNORECASE,
)


def _linha(casa, sigla, numero, ano, ementa, autoria, data_apresentacao, situacao, url, termos):
    ementa = re.sub(r"\s+", " ", ementa or "").strip()
    return {
        "casa": casa, "sigla": sigla, "numero": int(numero), "ano": int(ano),
        "ementa": ementa, "autoria": autoria, "data_apresentacao": (data_apresentacao or "")[:10],
        "situacao": situacao or "", "url": url, "termos_busca": "; ".join(sorted(termos)),
        "trata_do_tema": "sim" if PADRAO_TEMA.search(ementa) else "nao",
        "data_coleta": date.today().isoformat(),
    }


def levantar_camara() -> list[dict]:
    """Busca cada termo na Câmara e detalha as proposições encontradas."""
    termos_por_id: dict[int, set[str]] = {}
    for termo in TERMOS:
        for proposicao in buscar_camara(termo):
            if proposicao["siglaTipo"] in TIPOS:
                termos_por_id.setdefault(proposicao["id"], set()).add(termo)

    linhas = []
    for id_proposicao, termos in termos_por_id.items():
        dados = detalhar_camara(id_proposicao)
        detalhes = dados["detalhes"]
        linhas.append(_linha(
            "Câmara", detalhes["siglaTipo"], detalhes["numero"], detalhes["ano"],
            detalhes["ementa"], "; ".join(autor["nome"] for autor in dados["autores"]),
            detalhes["dataApresentacao"], detalhes["statusProposicao"].get("descricaoSituacao"),
            f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={id_proposicao}",
            termos,
        ))
    return linhas


def levantar_senado() -> list[dict]:
    """Busca cada termo no Senado e acrescenta as matérias conhecidas."""
    encontradas: dict[tuple, dict] = {}
    for termo in TERMOS:
        for materia in buscar_senado(termo):
            if materia["Sigla"] not in TIPOS:
                continue
            chave = (materia["Sigla"], int(materia["Numero"]), int(materia["Ano"]))
            encontradas.setdefault(chave, {"materia": materia, "termos": set()})["termos"].add(termo)

    linhas = [
        _linha(
            "Senado", *chave, item["materia"].get("Ementa"), item["materia"].get("Autor", ""),
            item["materia"].get("Data"), "", item["materia"].get("UrlDetalheMateria", ""),
            item["termos"],
        )
        for chave, item in encontradas.items()
    ]

    for sigla, numero, ano in MATERIAS_SENADO:
        if (sigla, numero, ano) in encontradas:
            continue
        materia = detalhar_senado(sigla, numero, ano)
        basicos, identificacao = materia["DadosBasicosMateria"], materia["IdentificacaoMateria"]
        linhas.append(_linha(
            "Senado", sigla, numero, ano, basicos.get("EmentaMateria"),
            basicos.get("Autor", ""), basicos.get("DataApresentacao"), "",
            f"https://www25.senado.leg.br/web/atividade/materias/-/materia/{identificacao['CodigoMateria']}",
            {"inclusão manual"},
        ))
    return linhas


def montar_tabela() -> list[dict]:
    """Levanta as duas casas e grava a tabela, ordenada por casa, ano e número."""
    linhas = sorted(
        levantar_camara() + levantar_senado(),
        key=lambda linha: (linha["casa"], linha["ano"], linha["numero"]),
    )
    TABELA.parent.mkdir(parents=True, exist_ok=True)
    with TABELA.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)
    return linhas
