"""Confere as tabelas da avaliação em data/processed/.

Uso (na raiz do projeto, com o venv ativo):

    python -m src.validar_avaliacao

Sai com código 1 se encontrar algum problema.
"""

import sys

import pandas as pd

from src.avaliacao import MODELO, RESPOSTAS_VALIDAS, VERSAO_PROMPT, VERSAO_REGUA

PASTA = "data/processed"


def _ler(caminho: str) -> pd.DataFrame:
    return pd.read_csv(caminho, dtype=str, keep_default_na=False)


def validar() -> list[str]:
    """Devolve a lista de problemas encontrados (vazia se estiver tudo certo)."""
    avaliacoes = _ler(f"{PASTA}/avaliacoes.csv")
    pontuacao = _ler(f"{PASTA}/pontuacao.csv")
    criterios = _ler(f"{PASTA}/criterios.csv")
    politicas = set(_ler("data/raw/fontes_politicas.csv")["id_politica"])
    erros = []

    # Cobertura: toda política respondeu a todos os critérios, uma vez.
    esperado = {(politica, criterio) for politica in politicas for criterio in criterios["id"]}
    encontrado = set(zip(avaliacoes["id_politica"], avaliacoes["id_criterio"]))
    if faltam := sorted(esperado - encontrado):
        erros.append(f"Faltam {len(faltam)} respostas, por exemplo {faltam[:3]}")
    if sobram := sorted(encontrado - esperado):
        erros.append(f"Há respostas fora do esperado: {sobram[:3]}")
    if avaliacoes.duplicated(["id_politica", "id_criterio"]).any():
        erros.append("Resposta duplicada para a mesma política e critério")

    if not avaliacoes["resposta"].isin(RESPOSTAS_VALIDAS).all():
        erros.append("Resposta fora de sim, nao e nao_menciona")

    # Todas as políticas foram avaliadas nas mesmas condições.
    for coluna, valor in (("modelo", MODELO), ("versao_prompt", VERSAO_PROMPT), ("versao_regua", VERSAO_REGUA)):
        if set(avaliacoes[coluna]) != {valor}:
            erros.append(f"{coluna} não é '{valor}' em todas as respostas: {sorted(set(avaliacoes[coluna]))}")

    # A marca de revisão segue a regra da régua: sim ou nao sem trecho conferido.
    deveria = (avaliacoes["resposta"] != "nao_menciona") & (avaliacoes["evidencia_conferida"] != "confere")
    if not (deveria == (avaliacoes["precisa_revisao"] == "sim")).all():
        erros.append("precisa_revisao não bate com a regra (sim ou nao sem evidência conferida)")

    # A pontuação é a soma dos pesos dos critérios respondidos com sim.
    pesos = criterios.set_index("id")["peso"].astype(int)
    sim = avaliacoes[avaliacoes["resposta"] == "sim"]
    recalculada = sim["id_criterio"].map(pesos).groupby(sim["id_politica"]).sum()
    for linha in pontuacao.itertuples():
        if int(linha.nota_ponderada) != int(recalculada.get(linha.id_politica, 0)):
            erros.append(f"{linha.id_politica}: nota ponderada não bate com as respostas")
        if int(linha.respostas_sim) + int(linha.respostas_nao) + int(linha.respostas_nao_menciona) != len(criterios):
            erros.append(f"{linha.id_politica}: a soma das respostas não dá {len(criterios)}")
    if set(pontuacao["id_politica"]) != politicas:
        erros.append("A pontuação não cobre exatamente as políticas coletadas")

    return erros


def main() -> None:
    erros = validar()
    avaliacoes = _ler(f"{PASTA}/avaliacoes.csv")
    print(f"{avaliacoes['id_politica'].nunique()} políticas, {len(avaliacoes)} respostas")
    print(avaliacoes["resposta"].value_counts().to_string())
    print(f"respostas marcadas para revisão: {(avaliacoes['precisa_revisao'] == 'sim').sum()}")
    if erros:
        print("\nProblemas encontrados:", *erros, sep="\n- ")
        sys.exit(1)
    print("\nAvaliação válida.")


if __name__ == "__main__":
    main()
