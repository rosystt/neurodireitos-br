"""Valida data/processed/criterios.csv e sua coerência com docs/criterios.md.

Uso (na raiz do projeto, com o venv ativo):

    python -m src.validar_criterios

Sai com código 1 se encontrar algum problema.
"""

import re
import sys
from pathlib import Path

import pandas as pd

CAMINHO_CSV = Path("data/processed/criterios.csv")
CAMINHO_DOC = Path("docs/criterios.md")

COLUNAS = [
    "id", "criterio", "pergunta", "peso", "hipotese",
    "fonte_lgpd", "fonte_pl_522", "fonte_colorado", "fonte_california", "fonte_chile",
]
COLUNAS_FONTE = [c for c in COLUNAS if c.startswith("fonte_")]
PESOS = {"1", "2", "3"}
HIPOTESES = {"H1", "H2", "H3"}
# Título de cada critério no documento: "### C01 — Categoria específica (peso 3)"
PADRAO_TITULO = re.compile(r"^### (C\d{2}) — (.+?) \(peso (\d)\)\s*\n+\*\*(.+?)\*\*", re.MULTILINE)


def validar(df: pd.DataFrame, documento: str) -> list[str]:
    """Devolve a lista de problemas encontrados (vazia se estiver tudo certo)."""
    if list(df.columns) != COLUNAS:
        return [f"Colunas diferentes do esperado: {list(df.columns)}"]

    erros = []

    def registrar(mascara: pd.Series, mensagem: str) -> None:
        ids = df.loc[mascara, "id"].tolist()
        if ids:
            erros.append(f"{mensagem}: {', '.join(ids)}")

    registrar(df["id"].duplicated(keep=False), "id duplicado")
    registrar(~df["id"].str.fullmatch(r"C\d{2}"), "id fora do formato C00")
    registrar(df["criterio"].eq("") | df["pergunta"].eq(""), "critério ou pergunta vazios")
    registrar(~df["pergunta"].str.endswith("?"), "pergunta sem ponto de interrogação")
    registrar(~df["peso"].isin(PESOS), "peso fora de 1 a 3")
    registrar(~df["hipotese"].isin(HIPOTESES), "hipótese inválida")
    registrar(df[COLUNAS_FONTE].eq("").all(axis=1), "critério sem nenhuma fonte legal")

    if not 8 <= len(df) <= 12:
        erros.append(f"A régua deve ter de 8 a 12 critérios; tem {len(df)}")

    # O documento e a tabela precisam descrever os mesmos critérios.
    no_documento = {
        id_: (nome, peso, pergunta)
        for id_, nome, peso, pergunta in PADRAO_TITULO.findall(documento)
    }
    na_tabela = {
        linha.id: (linha.criterio, linha.peso, linha.pergunta)
        for linha in df.itertuples()
    }
    for id_ in sorted(set(no_documento) | set(na_tabela)):
        if id_ not in no_documento:
            erros.append(f"{id_} está na tabela, mas não no documento")
        elif id_ not in na_tabela:
            erros.append(f"{id_} está no documento, mas não na tabela")
        elif no_documento[id_] != na_tabela[id_]:
            erros.append(f"{id_} difere entre o documento e a tabela (nome, peso ou pergunta)")

    return erros


def main() -> None:
    df = pd.read_csv(CAMINHO_CSV, dtype=str, keep_default_na=False)
    erros = validar(df, CAMINHO_DOC.read_text(encoding="utf-8"))

    print(f"{len(df)} critérios; pontuação máxima: {df['peso'].astype(int).sum()}")
    if erros:
        print("\nProblemas encontrados:", *erros, sep="\n- ")
        sys.exit(1)
    print("Régua válida e coerente com docs/criterios.md.")


if __name__ == "__main__":
    main()
