"""Valida a estrutura e a consistência de data/raw/inventario.csv.

Uso (na raiz do projeto, com o venv ativo):

    python -m src.validar_inventario

Sai com código 1 se encontrar algum problema.
"""

import sys
from pathlib import Path

import pandas as pd

CAMINHO = Path("data/raw/inventario.csv")

COLUNAS = [
    "id", "aparelho", "fabricante", "pais_sede", "tipo_aparelho",
    "status_inclusao", "motivo_status", "canal_venda_br", "url_evidencia_venda",
    "preco_referencia", "moeda", "fonte_preco", "url_politica",
    "idioma_politica", "data_coleta", "observacoes",
]
STATUS = {"incluido", "pendente", "excluido"}
CANAIS = {
    "marketplace_br", "loja_oficial_cita_brasil", "loja_oficial_envio_mundial",
    "nao_confirmado", "nao_entrega",
}
# Canais que contam como evidência de venda ou entrega no Brasil.
CANAIS_COM_EVIDENCIA = CANAIS - {"nao_confirmado", "nao_entrega"}
COLUNAS_URL = ["url_evidencia_venda", "fonte_preco", "url_politica"]


def validar(df: pd.DataFrame) -> list[str]:
    """Devolve a lista de problemas encontrados (vazia se estiver tudo certo)."""
    if list(df.columns) != COLUNAS:
        return [f"Colunas diferentes do esperado: {list(df.columns)}"]

    erros = []

    def registrar(mascara: pd.Series, mensagem: str) -> None:
        ids = df.loc[mascara, "id"].tolist()
        if ids:
            erros.append(f"{mensagem}: {', '.join(ids)}")

    vazio = df.eq("")
    incluido = df["status_inclusao"].eq("incluido")

    registrar(df["id"].duplicated(keep=False), "id duplicado")
    registrar(df[["aparelho", "fabricante"]].duplicated(keep=False), "aparelho repetido")
    for coluna in ("aparelho", "fabricante", "pais_sede", "tipo_aparelho", "data_coleta"):
        registrar(vazio[coluna], f"{coluna} vazio")
    registrar(~df["status_inclusao"].isin(STATUS), "status_inclusao inválido")
    registrar(~vazio["canal_venda_br"] & ~df["canal_venda_br"].isin(CANAIS), "canal_venda_br inválido")
    registrar(~incluido & vazio["motivo_status"], "pendente ou excluído sem motivo_status")
    registrar(incluido & ~vazio["motivo_status"], "incluído com motivo_status preenchido")

    # Critério de inclusão: evidência de venda no Brasil e política pública.
    registrar(incluido & ~df["canal_venda_br"].isin(CANAIS_COM_EVIDENCIA), "incluído sem evidência de venda no Brasil")
    registrar(incluido & vazio["url_evidencia_venda"], "incluído sem url_evidencia_venda")
    registrar(incluido & vazio["url_politica"], "incluído sem url_politica")
    registrar(~vazio["url_politica"] & vazio["idioma_politica"], "política sem idioma")

    for coluna in COLUNAS_URL:
        registrar(~vazio[coluna] & ~df[coluna].str.startswith("https://"), f"{coluna} não começa com https://")

    datas = pd.to_datetime(df["data_coleta"], format="%Y-%m-%d", errors="coerce")
    registrar(datas.isna(), "data_coleta fora do formato AAAA-MM-DD")

    precos = pd.to_numeric(df["preco_referencia"].where(~vazio["preco_referencia"]), errors="coerce")
    registrar(~vazio["preco_referencia"] & ~(precos > 0), "preco_referencia não é número positivo")
    registrar(~vazio["preco_referencia"] & (vazio["moeda"] | vazio["fonte_preco"]), "preço sem moeda ou sem fonte")

    return erros


def main() -> None:
    df = pd.read_csv(CAMINHO, dtype=str, keep_default_na=False)
    erros = validar(df)

    print(f"{len(df)} candidatos avaliados")
    print(df["status_inclusao"].value_counts().to_string())
    if erros:
        print("\nProblemas encontrados:", *erros, sep="\n- ")
        sys.exit(1)
    print("\nInventário válido.")


if __name__ == "__main__":
    main()
