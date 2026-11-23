"""Roda as consultas das hipóteses no Neo4j e grava os resultados em CSV.

Cada arquivo de cypher/consultas/ tem uma consulta; o resultado vai para
data/processed/resultados/, com o mesmo nome. Listas viram texto separado
por ponto e vírgula.

Uso (na raiz do projeto, com o venv ativo, o .env preenchido e o grafo carregado):

    python -m src.consultas
"""

from pathlib import Path

import pandas as pd
from neo4j import Driver

from src.conexao_neo4j import banco, criar_driver
from src.grafo import PASTA_CYPHER, ler_comandos

PASTA_CONSULTAS = PASTA_CYPHER / "consultas"
PASTA_RESULTADOS = Path("data/processed/resultados")


def consultar(driver: Driver, nome: str) -> pd.DataFrame:
    """Roda a consulta cypher/consultas/<nome>.cypher e devolve o resultado."""
    (comando,) = ler_comandos(f"consultas/{nome}.cypher")
    registros, _, chaves = driver.execute_query(comando, database_=banco())
    tabela = pd.DataFrame([registro.data() for registro in registros], columns=chaves)
    return tabela.map(lambda valor: ";".join(sorted(map(str, valor))) if isinstance(valor, list) else valor)


def nomes_das_consultas() -> list[str]:
    return sorted(arquivo.stem for arquivo in PASTA_CONSULTAS.glob("*.cypher"))


def main() -> None:
    PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    with criar_driver() as driver:
        for nome in nomes_das_consultas():
            tabela = consultar(driver, nome)
            tabela.to_csv(PASTA_RESULTADOS / f"{nome}.csv", index=False, encoding="utf-8", lineterminator="\n")
            print(f"== {nome} ({len(tabela)} linhas)")
            print(tabela.to_string(index=False), end="\n\n")


if __name__ == "__main__":
    main()
