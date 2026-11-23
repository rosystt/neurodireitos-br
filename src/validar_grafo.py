"""Confere o grafo no Neo4j contra as tabelas de data/processed/grafo/.

Duas checagens:

1. Contagem: cada rótulo e cada tipo de relação tem no grafo o mesmo número
   de itens que as tabelas de origem (uma carga duplicada ou incompleta falha).
2. Hipóteses: cada consulta de cypher/consultas/ devolve o mesmo resultado que
   um cálculo independente, feito aqui com pandas direto dos CSVs.

Uso (na raiz do projeto, com o venv ativo, o .env preenchido e o grafo carregado):

    python -m src.validar_grafo

Sai com código 1 se encontrar algum problema.
"""

import sys

import pandas as pd
from neo4j import Driver

from src.conexao_neo4j import criar_driver
from src.consultas import consultar
from src.grafo import PASTA_TABELAS, contar

RESPOSTAS = ["sim", "nao", "nao_menciona"]
STATUS_COM_EFEITO = ["vigente", "julgado"]


def _ler(nome: str) -> pd.DataFrame:
    return pd.read_csv(PASTA_TABELAS / f"{nome}.csv", dtype=str, keep_default_na=False)


def _respostas_com_grupo() -> pd.DataFrame:
    """Respostas com o grupo da empresa e o nome e a hipótese do critério."""
    criterios = _ler("criterios").rename(columns={"id": "id_criterio", "criterio": "nome"})
    return (
        _ler("respostas")
        .merge(_ler("empresas")[["id_empresa", "grupo"]], on="id_empresa", validate="many_to_one")
        .merge(criterios[["id_criterio", "nome", "hipotese"]], on="id_criterio", validate="many_to_one")
    )


def _empresas_com(ids: pd.Series, empresas: pd.DataFrame) -> pd.Series:
    return empresas["id_empresa"].isin(set(ids))


# --- 1. Contagem -----------------------------------------------------------

def contagem_esperada() -> dict[str, int]:
    empresas, aparelhos, leis = _ler("empresas"), _ler("aparelhos"), _ler("leis")
    paises_dados = _ler("paises_dos_dados")
    categorias_dado = set(_ler("dados_coletados")["categoria"]) | set(_ler("protecao")["categoria"])
    return {
        "(:Pais)": len(_ler("paises")),
        "(:Empresa)": len(empresas),
        "(:Aparelho)": len(aparelhos),
        "(:Lei)": len(leis),
        "(:Criterio)": len(_ler("criterios")),
        "(:Dado)": len(categorias_dado),
        "(:Terceiro)": _ler("terceiros")["categoria"].nunique(),
        "[:SEDIADA_EM]": len(empresas),
        "[:FABRICA]": len(aparelhos),
        "[:VENDIDO_EM]": int((aparelhos["grupo"] == "brasil").sum()),
        "[:VIGORA_EM]": int(leis["status"].isin(STATUS_COM_EFEITO).sum()),
        "[:PROPOSTA_EM]": int((~leis["status"].isin(STATUS_COM_EFEITO)).sum()),
        "[:FUNDAMENTA]": len(_ler("lei_criterio")),
        "[:RESPONDE]": len(_ler("respostas")),
        "[:COLETA]": len(_ler("dados_coletados")),
        "[:COMPARTILHA_COM]": len(_ler("terceiros")),
        "[:ARMAZENA_EM]": int((paises_dados["relacao"] == "ARMAZENA_EM").sum()),
        "[:TRANSFERE_PARA]": int((paises_dados["relacao"] == "TRANSFERE_PARA").sum()),
        "[:PROTEGE]": len(_ler("protecao")),
    }


# --- 2. Hipóteses, recalculadas com pandas ---------------------------------

def _contar_respostas(hipotese: str) -> pd.DataFrame:
    respostas = _respostas_com_grupo().query("hipotese == @hipotese")
    tabela = (
        pd.crosstab([respostas["id_criterio"], respostas["nome"], respostas["grupo"]], respostas["resposta"])
        .reindex(columns=RESPOSTAS, fill_value=0)
        .reset_index()
        .rename(columns={"id_criterio": "criterio"})
    )
    tabela.columns.name = None
    tabela.insert(3, "politicas", tabela[RESPOSTAS].sum(axis=1))
    return tabela


def esperado_h1() -> pd.DataFrame:
    return _contar_respostas("H1")


def esperado_h2_criterios() -> pd.DataFrame:
    return _contar_respostas("H2")


def esperado_h3_criterios() -> pd.DataFrame:
    tabela = _contar_respostas("H3")
    tabela["pct_sim"] = (100 * tabela["sim"] / tabela["politicas"]).round(1)
    return tabela[["criterio", "nome", "grupo", "politicas", "sim", "pct_sim"]]


def esperado_h2_terceiros_e_paises() -> pd.DataFrame:
    empresas = _ler("empresas")
    terceiros, paises = _ler("terceiros"), _ler("paises_dos_dados")
    exceto_autoridades = _empresas_com(terceiros.query("categoria != 'autoridades'")["id_empresa"], empresas)
    fora = _empresas_com(paises.query("pais != 'Brasil'")["id_empresa"], empresas)
    marcas = pd.DataFrame({
        "grupo": empresas["grupo"],
        "politicas": 1,
        "compartilha_com_terceiros": _empresas_com(terceiros["id_empresa"], empresas),
        "compartilha_exceto_autoridades": exceto_autoridades,
        "compartilha_com_publicidade": _empresas_com(
            terceiros.query("categoria == 'publicidade'")["id_empresa"], empresas
        ),
        "dados_fora_do_brasil": fora,
        "sem_pais_declarado": ~_empresas_com(paises["id_empresa"], empresas),
        "terceiros_ou_fora": exceto_autoridades | fora,
    })
    return marcas.groupby("grupo").sum().astype(int).reset_index()


def esperado_h3_lacunas_por_lei() -> pd.DataFrame:
    especificas = _ler("protecao").query("nivel == 'especifica' and categoria == 'sinal_neural'")["id_lei"]
    ligacoes = _ler("lei_criterio").query("id_lei in @especificas")
    respostas = _respostas_com_grupo().query("grupo == 'brasil'")
    cruzado = ligacoes.merge(respostas, on="id_criterio")
    cruzado["lacuna"] = cruzado["resposta"] != "sim"
    tabela = (
        cruzado.groupby("id_lei")
        .agg(criterios_fundamentados=("id_criterio", "nunique"), respostas=("lacuna", "size"), lacunas=("lacuna", "sum"))
        .reset_index()
        .rename(columns={"id_lei": "lei"})
    )
    tabela["pct_lacunas"] = (100 * tabela["lacunas"] / tabela["respostas"]).round(1)
    tabela.insert(1, "jurisdicao", tabela["lei"].map(_ler("leis").set_index("id")["jurisdicao"]))
    return tabela


def esperado_complementar_notas() -> pd.DataFrame:
    notas = _ler("notas").merge(_ler("empresas")[["id_empresa", "grupo"]], on="id_empresa")
    notas[["nota_ponderada", "nota_maxima"]] = notas[["nota_ponderada", "nota_maxima"]].astype(int)
    return (
        notas.groupby("grupo")
        .agg(
            politicas=("id_empresa", "size"),
            nota_minima=("nota_ponderada", "min"),
            nota_mediana=("nota_ponderada", "median"),
            nota_media=("nota_ponderada", "mean"),
            nota_maxima_obtida=("nota_ponderada", "max"),
            nota_maxima_possivel=("nota_maxima", "max"),
        )
        .round({"nota_media": 1})
        .reset_index()
    )


ESPERADOS = {
    "h1_categoria_especifica": esperado_h1,
    "h2_criterios": esperado_h2_criterios,
    "h2_terceiros_e_paises": esperado_h2_terceiros_e_paises,
    "h3_criterios": esperado_h3_criterios,
    "h3_lacunas_por_lei": esperado_h3_lacunas_por_lei,
    "complementar_notas": esperado_complementar_notas,
}


def _normalizar(tabela: pd.DataFrame) -> pd.DataFrame:
    """Mesma ordem de linhas e números como float, para comparar grafo e pandas."""
    tabela = tabela.copy()
    for coluna in tabela.columns:
        numerica = pd.to_numeric(tabela[coluna], errors="coerce")
        tabela[coluna] = numerica.astype(float) if numerica.notna().all() else tabela[coluna].astype(str)
    return tabela.sort_values(list(tabela.columns)).reset_index(drop=True)


def divergencia(grafo: pd.DataFrame, esperado: pd.DataFrame) -> str | None:
    """Descreve a diferença entre as duas tabelas, ou None se forem iguais."""
    if list(grafo.columns) != list(esperado.columns):
        return f"colunas diferentes: {list(grafo.columns)} x {list(esperado.columns)}"
    try:
        pd.testing.assert_frame_equal(_normalizar(grafo), _normalizar(esperado), check_exact=False)
    except AssertionError as erro:
        return str(erro)
    return None


def validar(driver: Driver) -> list[str]:
    """Devolve a lista de problemas encontrados (vazia se estiver tudo certo)."""
    erros = []
    esperada, no_grafo = contagem_esperada(), contar(driver)
    for item, total in esperada.items():
        if no_grafo.get(item, 0) != total:
            erros.append(f"{item}: {no_grafo.get(item, 0)} no grafo, {total} nas tabelas")
    if sobrando := sorted(set(no_grafo) - set(esperada)):
        erros.append(f"Rótulos ou relações sem tabela de origem: {sobrando}")

    for nome, calcular in ESPERADOS.items():
        if problema := divergencia(consultar(driver, nome), calcular()):
            erros.append(f"{nome}: o grafo e o pandas divergem — {problema}")
    return erros


def main() -> None:
    with criar_driver() as driver:
        erros = validar(driver)
    if erros:
        print("Problemas encontrados:")
        for erro in erros:
            print(f"- {erro}")
        sys.exit(1)
    print(f"{len(contagem_esperada())} contagens e {len(ESPERADOS)} consultas conferidas contra os CSVs.")
    print("Grafo válido.")


if __name__ == "__main__":
    main()
