"""Monta as tabelas de nós e de relações do grafo em data/processed/grafo/.

Cada tabela corresponde a um script de carga em cypher/. Esta etapa cobre a
parte fixa do grafo — empresas, aparelhos, países, leis e critérios. As
respostas das políticas aos critérios entram depois da avaliação.

Uso (na raiz do projeto, com o venv ativo):

    python -m src.preparar_grafo
"""

from pathlib import Path

import pandas as pd

PASTA = Path("data/processed/grafo")

# Coluna de fonte da régua -> lei citada. A coluna do Chile reúne duas normas,
# distinguidas pelo início do texto da citação.
LEI_POR_COLUNA = {
    "fonte_lgpd": "LGPD",
    "fonte_pl_522": "PL-522-2022",
    "fonte_colorado": "CO-HB-24-1058",
    "fonte_california": "CA-SB-1223",
}
LEI_CHILE_POR_PREFIXO = {"Constituição": "CL-LEY-21383", "Corte Suprema": "CL-ROL-105065-2023"}


def _ler(caminho: str) -> pd.DataFrame:
    return pd.read_csv(caminho, dtype=str, keep_default_na=False)


def montar_empresas_e_aparelhos() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Empresas e aparelhos incluídos no inventário, ligados pela política."""
    inventario = _ler("data/raw/inventario.csv")
    inventario = inventario[inventario["status_inclusao"] == "incluido"]
    principais = _ler("data/raw/fontes_politicas.csv").query("tipo == 'principal'")
    inventario = inventario.merge(
        principais[["fabricante", "id_politica"]], on="fabricante", validate="many_to_one"
    ).rename(columns={"id_politica": "id_empresa"})

    empresas = (
        inventario[["id_empresa", "fabricante", "pais_sede", "grupo", "url_politica"]]
        .drop_duplicates()
        .rename(columns={"fabricante": "nome"})
        .sort_values("id_empresa")
    )
    if empresas["id_empresa"].duplicated().any():
        raise ValueError("Empresa com país-sede, grupo ou política divergentes entre aparelhos")

    aparelhos = inventario[[
        "id", "aparelho", "tipo_aparelho", "id_empresa", "grupo", "canal_venda_br",
        "url_evidencia_venda", "preco_referencia", "moeda", "data_coleta",
    ]].rename(columns={"aparelho": "nome", "tipo_aparelho": "tipo"}).sort_values("id")
    return empresas, aparelhos


def montar_leis() -> pd.DataFrame:
    """Leis de referência mais as proposições brasileiras que tratam do tema."""
    referencia = _ler("data/raw/leis_referencia.csv")

    projetos = _ler("data/interim/projetos_lei.csv").query("trata_do_tema == 'sim'")
    proposicoes = pd.DataFrame({
        "id": projetos["sigla"] + "-" + projetos["numero"] + "-" + projetos["ano"],
        "nome": projetos["sigla"] + " " + projetos["numero"] + "/" + projetos["ano"],
        "tipo": projetos["sigla"].map({"PL": "projeto de lei", "PLP": "projeto de lei", "PEC": "proposta de emenda constitucional"}),
        "pais": "Brasil",
        "jurisdicao": "federal",
        "status": projetos["situacao"].str.contains("Retirado").map({True: "retirado", False: "em_tramitacao"}),
        "data_vigencia": "",
        "cita_dado_neural": "sim",
        "url": projetos["url"],
    })
    return pd.concat([referencia, proposicoes], ignore_index=True)


def montar_lei_criterio(criterios: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por lei que fundamenta um critério, com o dispositivo citado."""
    linhas = []
    for criterio in criterios.itertuples():
        for coluna, id_lei in LEI_POR_COLUNA.items():
            if dispositivo := getattr(criterio, coluna):
                linhas.append((id_lei, criterio.id, dispositivo))
        if dispositivo := criterio.fonte_chile:
            id_lei = next(lei for prefixo, lei in LEI_CHILE_POR_PREFIXO.items() if dispositivo.startswith(prefixo))
            linhas.append((id_lei, criterio.id, dispositivo))
    return pd.DataFrame(linhas, columns=["id_lei", "id_criterio", "dispositivo"])


def main() -> None:
    PASTA.mkdir(parents=True, exist_ok=True)
    empresas, aparelhos = montar_empresas_e_aparelhos()
    leis = montar_leis()
    criterios = _ler("data/processed/criterios.csv")
    lei_criterio = montar_lei_criterio(criterios)

    faltantes = set(lei_criterio["id_lei"]) - set(leis["id"])
    if faltantes:
        raise ValueError(f"Critérios citam leis ausentes da tabela de leis: {sorted(faltantes)}")

    paises = pd.DataFrame({"nome": sorted({"Brasil", *empresas["pais_sede"], *leis["pais"]})})
    tabelas = {
        "paises": paises, "empresas": empresas, "aparelhos": aparelhos,
        "leis": leis, "criterios": criterios[["id", "criterio", "pergunta", "peso", "hipotese"]],
        "lei_criterio": lei_criterio,
    }
    for nome, tabela in tabelas.items():
        tabela.to_csv(PASTA / f"{nome}.csv", index=False, encoding="utf-8", lineterminator="\n")
        print(f"{nome}: {len(tabela)} linhas")


if __name__ == "__main__":
    main()
