"""Sorteia as políticas do padrão-ouro e prepara a planilha da avaliação manual.

O padrão-ouro é a avaliação feita por uma pessoa, usada para medir o acerto
do modelo. A amostra é sorteada com semente fixa, antes de qualquer resultado
do modelo, para que a escolha não dependa do que ele respondeu.

Uso (na raiz do projeto, com o venv ativo):

    python -m src.amostra_padrao_ouro
"""

import csv
import random
from pathlib import Path

SEMENTE = 20261115
DATA_SORTEIO = "2026-11-15"
# Duas políticas do grupo principal e uma do grupo de comparação.
TAMANHO_POR_GRUPO = {"brasil": 2, "comparacao": 1}
# A pessoa que avalia precisa ler o original; ficam de fora os outros idiomas.
IDIOMAS_ACEITOS = {"en", "pt"}

PASTA = Path("data/interim/avaliacao")
AMOSTRA = PASTA / "amostra_padrao_ouro.csv"
PLANILHA = PASTA / "manual" / "padrao_ouro.csv"


def _ler(caminho: str) -> list[dict]:
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def sortear() -> list[dict]:
    """Sorteia a amostra, estratificada por grupo."""
    principais = [fonte for fonte in _ler("data/raw/fontes_politicas.csv") if fonte["tipo"] == "principal"]
    grupo = {
        linha["fabricante"]: linha["grupo"]
        for linha in _ler("data/raw/inventario.csv") if linha["status_inclusao"] == "incluido"
    }
    idioma = {linha["id_documento"]: linha["idioma"] for linha in _ler("data/interim/politicas/resumo.csv")}

    sorteio = random.Random(SEMENTE)
    amostra = []
    for nome_grupo, tamanho in TAMANHO_POR_GRUPO.items():
        candidatas = sorted(
            (fonte for fonte in principais
             if grupo[fonte["fabricante"]] == nome_grupo and idioma[fonte["id_documento"]] in IDIOMAS_ACEITOS),
            key=lambda fonte: fonte["id_politica"],
        )
        for fonte in sorted(sorteio.sample(candidatas, tamanho), key=lambda fonte: fonte["id_politica"]):
            amostra.append({
                "id_politica": fonte["id_politica"], "fabricante": fonte["fabricante"],
                "grupo": nome_grupo, "semente": SEMENTE, "data_sorteio": DATA_SORTEIO,
            })
    return amostra


def main() -> None:
    amostra = sortear()
    PASTA.mkdir(parents=True, exist_ok=True)
    with AMOSTRA.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(amostra[0]), lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(amostra)

    # Planilha em branco para a avaliação manual; nunca sobrescreve uma já preenchida.
    if not PLANILHA.exists():
        criterios = _ler("data/processed/criterios.csv")
        PLANILHA.parent.mkdir(parents=True, exist_ok=True)
        with PLANILHA.open("w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.writer(arquivo, lineterminator="\n")
            escritor.writerow(["id_politica", "id_criterio", "pergunta", "resposta", "evidencia", "observacoes"])
            for politica in amostra:
                for criterio in criterios:
                    escritor.writerow([politica["id_politica"], criterio["id"], criterio["pergunta"], "", "", ""])

    for politica in amostra:
        print(f"{politica['id_politica']}  {politica['grupo']:10}  {politica['fabricante']}")


if __name__ == "__main__":
    main()
