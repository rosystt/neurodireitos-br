"""Conexão com o Neo4j AuraDB a partir das credenciais do arquivo .env.

Uso como teste de conexão (na raiz do projeto, com o venv ativo):

    python -m src.conexao_neo4j
"""

import os
import sys

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase

VARIAVEIS_OBRIGATORIAS = ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD")


def criar_driver() -> Driver:
    """Cria o driver do Neo4j lendo as credenciais do .env.

    Levanta RuntimeError se alguma variável obrigatória estiver ausente,
    para o erro aparecer aqui e não como falha obscura de autenticação.
    """
    load_dotenv()
    ausentes = [v for v in VARIAVEIS_OBRIGATORIAS if not os.getenv(v)]
    if ausentes:
        raise RuntimeError(
            "Variáveis ausentes no .env: "
            + ", ".join(ausentes)
            + ". Copie o .env.example para .env e preencha."
        )
    return GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]),
    )


def banco() -> str:
    """Nome do banco de dados (padrão do AuraDB: 'neo4j')."""
    return os.getenv("NEO4J_DATABASE", "neo4j")


def testar_conexao() -> None:
    """Verifica a conectividade e executa uma consulta mínima."""
    with criar_driver() as driver:
        driver.verify_connectivity()
        registros, _, _ = driver.execute_query(
            "RETURN 'conexão ok' AS mensagem", database_=banco()
        )
        print(registros[0]["mensagem"])


if __name__ == "__main__":
    try:
        testar_conexao()
    except Exception as erro:  # mensagem curta em vez de traceback no teste manual
        print(f"Falha na conexão: {erro}", file=sys.stderr)
        sys.exit(1)
