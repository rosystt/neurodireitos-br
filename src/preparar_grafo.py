"""Monta as tabelas de nós e de relações do grafo em data/processed/grafo/.

Cada tabela corresponde a um script de carga em cypher/. São duas partes:

- fixa: empresas, aparelhos, países, leis e critérios;
- avaliada: as respostas de cada política aos critérios, as notas e os fatos
  extraídos das políticas (tipos de dado, terceiros e países dos dados), vindos
  da Fase 4 (data/processed/).

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

# Regiões citadas pelas políticas como destino dos dados. Viram nós :Pais com
# tipo 'regiao', para que nenhuma linha da avaliação seja descartada.
REGIOES = {"União Europeia", "Espaço Econômico Europeu"}

# Só normas que já produzem efeito protegem um dado; proposições ficam de fora.
STATUS_COM_EFEITO = {"vigente", "julgado"}

PAPEL_PARA_RELACAO = {"armazenamento": "ARMAZENA_EM", "transferencia": "TRANSFERE_PARA"}


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


def montar_respostas() -> pd.DataFrame:
    """Uma linha por política e critério, com a resposta do modelo e a evidência."""
    avaliacoes = _ler("data/processed/avaliacoes.csv")
    return avaliacoes[[
        "id_politica", "id_criterio", "resposta", "evidencia", "id_documento",
        "justificativa", "modelo", "versao_prompt", "versao_regua",
    ]].rename(columns={"id_politica": "id_empresa"})


def montar_notas() -> pd.DataFrame:
    """Nota de cada política, gravada como propriedade do nó :Empresa."""
    pontuacao = _ler("data/processed/pontuacao.csv")
    return pontuacao[["id_politica", "nota_ponderada", "nota_maxima"]].rename(
        columns={"id_politica": "id_empresa"}
    )


def montar_dados_coletados() -> pd.DataFrame:
    """Uma linha por tipo de dado citado; a categoria vira o nó :Dado."""
    dados = _ler("data/processed/dados_coletados.csv")
    dados["inferido"] = dados["inferido"].map({"True": "sim", "False": "nao"})
    return dados[["id_politica", "categoria", "descricao", "inferido", "evidencia", "id_documento"]].rename(
        columns={"id_politica": "id_empresa"}
    )


def montar_terceiros() -> pd.DataFrame:
    """Uma linha por terceiro citado; a categoria vira o nó :Terceiro.

    O nome fica na relação: quase todos os nomes são descrições genéricas
    ("parceiros de publicidade"), que não se repetem entre políticas.
    """
    terceiros = _ler("data/processed/terceiros.csv")
    return terceiros[["id_politica", "categoria", "nome", "evidencia", "id_documento"]].rename(
        columns={"id_politica": "id_empresa", "nome": "nome_citado"}
    )


def montar_paises_dos_dados() -> pd.DataFrame:
    """Países de armazenamento e de transferência, com o tipo de relação."""
    paises = _ler("data/processed/paises_dos_dados.csv")
    desconhecidos = set(paises["papel"]) - set(PAPEL_PARA_RELACAO)
    if desconhecidos:
        raise ValueError(f"Papel de país sem relação definida: {sorted(desconhecidos)}")
    paises["relacao"] = paises["papel"].map(PAPEL_PARA_RELACAO)
    return paises[["id_politica", "pais", "relacao", "evidencia", "id_documento"]].rename(
        columns={"id_politica": "id_empresa"}
    )


def montar_protecao(leis: pd.DataFrame) -> pd.DataFrame:
    """Normas com efeito que protegem o sinal neural, e com que nível.

    Derivada só da tabela de leis, sem juízo jurídico novo: norma que cita
    dado neural protege de forma específica; a LGPD, que não cita, protege de
    forma genérica (por analogia com dado sensível — ver docs/criterios.md).
    Fica restrita ao sinal neural porque a cobertura das inferências varia
    entre as leis e depende da revisão jurídica (issue #6).
    """
    com_efeito = leis[leis["status"].isin(STATUS_COM_EFEITO)]
    return pd.DataFrame({
        "id_lei": com_efeito["id"],
        "categoria": "sinal_neural",
        "nivel": com_efeito["cita_dado_neural"].map({"sim": "especifica", "nao": "generica"}),
    })


def main() -> None:
    PASTA.mkdir(parents=True, exist_ok=True)
    empresas, aparelhos = montar_empresas_e_aparelhos()
    leis = montar_leis()
    criterios = _ler("data/processed/criterios.csv")
    lei_criterio = montar_lei_criterio(criterios)

    faltantes = set(lei_criterio["id_lei"]) - set(leis["id"])
    if faltantes:
        raise ValueError(f"Critérios citam leis ausentes da tabela de leis: {sorted(faltantes)}")

    respostas = montar_respostas()
    notas = montar_notas()
    dados = montar_dados_coletados()
    terceiros = montar_terceiros()
    paises_dados = montar_paises_dos_dados()
    protecao = montar_protecao(leis)

    sem_empresa = set().union(*(set(t["id_empresa"]) for t in (respostas, notas, dados, terceiros, paises_dados)))
    if faltantes := sem_empresa - set(empresas["id_empresa"]):
        raise ValueError(f"Avaliação cita políticas sem empresa no grafo: {sorted(faltantes)}")

    nomes = {"Brasil", *empresas["pais_sede"], *leis["pais"], *paises_dados["pais"]}
    paises = pd.DataFrame({"nome": sorted(nomes)})
    paises["tipo"] = paises["nome"].map(lambda nome: "regiao" if nome in REGIOES else "pais")
    tabelas = {
        "paises": paises, "empresas": empresas, "aparelhos": aparelhos,
        "leis": leis, "criterios": criterios[["id", "criterio", "pergunta", "peso", "hipotese"]],
        "lei_criterio": lei_criterio,
        "respostas": respostas, "notas": notas, "dados_coletados": dados,
        "terceiros": terceiros, "paises_dos_dados": paises_dados, "protecao": protecao,
    }
    for nome, tabela in tabelas.items():
        tabela.to_csv(PASTA / f"{nome}.csv", index=False, encoding="utf-8", lineterminator="\n")
        print(f"{nome}: {len(tabela)} linhas")


if __name__ == "__main__":
    main()
