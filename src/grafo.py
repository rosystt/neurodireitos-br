"""Carga do grafo no Neo4j a partir das tabelas de data/processed/grafo/.

Os comandos ficam em cypher/, um arquivo por tabela. As linhas de cada CSV
são enviadas como parâmetro ($linhas), e toda escrita usa MERGE: rodar a
carga de novo atualiza o que existe, sem duplicar nós nem relações.

Uso (na raiz do projeto, com o venv ativo e o .env preenchido):

    python -m src.preparar_grafo
    python -m src.grafo
"""

import csv
from pathlib import Path

from neo4j import Driver

from src.conexao_neo4j import banco, criar_driver

PASTA_CYPHER = Path("cypher")
PASTA_TABELAS = Path("data/processed/grafo")
RESTRICOES = "00_restricoes.cypher"
# Ordem de carga: os nós precisam existir antes das relações que os ligam.
CARGAS = [
    ("01_paises.cypher", "paises.csv"),
    ("02_empresas.cypher", "empresas.csv"),
    ("03_aparelhos.cypher", "aparelhos.csv"),
    ("04_leis.cypher", "leis.csv"),
    ("05_criterios.cypher", "criterios.csv"),
    ("06_lei_criterio.cypher", "lei_criterio.csv"),
    # Parte avaliada (Fase 4)
    ("07_respostas.cypher", "respostas.csv"),
    ("08_notas.cypher", "notas.csv"),
    ("09_dados_coletados.cypher", "dados_coletados.csv"),
    ("10_terceiros.cypher", "terceiros.csv"),
    ("11_paises_dos_dados.cypher", "paises_dos_dados.csv"),
    ("12_protecao.cypher", "protecao.csv"),
]


def ler_comandos(arquivo: str) -> list[str]:
    """Lê um arquivo .cypher e devolve seus comandos, sem comentários."""
    linhas = [
        linha for linha in (PASTA_CYPHER / arquivo).read_text(encoding="utf-8").splitlines()
        if not linha.strip().startswith("//")
    ]
    return [comando.strip() for comando in "\n".join(linhas).split(";") if comando.strip()]


def ler_tabela(arquivo: str) -> list[dict]:
    with (PASTA_TABELAS / arquivo).open(encoding="utf-8", newline="") as tabela:
        return list(csv.DictReader(tabela))


def carregar(driver: Driver) -> None:
    """Cria as restrições e carrega todas as tabelas, na ordem de CARGAS."""
    for comando in ler_comandos(RESTRICOES):
        driver.execute_query(comando, database_=banco())
    for arquivo_cypher, arquivo_csv in CARGAS:
        linhas = ler_tabela(arquivo_csv)
        for comando in ler_comandos(arquivo_cypher):
            driver.execute_query(comando, linhas=linhas, database_=banco())
        print(f"{arquivo_cypher}: {len(linhas)} linhas enviadas")


def contar(driver: Driver) -> dict[str, int]:
    """Conta os nós por rótulo e as relações por tipo."""
    contagem = {}
    nos, _, _ = driver.execute_query(
        "MATCH (n) UNWIND labels(n) AS rotulo RETURN rotulo, count(*) AS total ORDER BY rotulo",
        database_=banco(),
    )
    relacoes, _, _ = driver.execute_query(
        "MATCH ()-[r]->() RETURN type(r) AS tipo, count(*) AS total ORDER BY tipo",
        database_=banco(),
    )
    contagem.update({f"(:{registro['rotulo']})": registro["total"] for registro in nos})
    contagem.update({f"[:{registro['tipo']}]": registro["total"] for registro in relacoes})
    return contagem


def main() -> None:
    with criar_driver() as driver:
        carregar(driver)
        print()
        for item, total in contar(driver).items():
            print(f"{item:20} {total}")


if __name__ == "__main__":
    main()
