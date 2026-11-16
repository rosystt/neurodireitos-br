"""Confere se a coleta e a limpeza cobrem todas as políticas do inventário.

Uso (na raiz do projeto, com o venv ativo):

    python -m src.validar_coleta

Sai com código 1 se encontrar algum problema.
"""

import hashlib
import sys

import pandas as pd

from src.coleta import FONTES_POLITICAS, PASTA_POLITICAS, REGISTRO_POLITICAS
from src.limpeza import PASTA_INTERIM, RESUMO

INVENTARIO = "data/raw/inventario.csv"
PASTA_TRADUCOES = PASTA_INTERIM.parent / "traducoes"
TRADUCOES = PASTA_TRADUCOES / "traducoes.csv"
# Idiomas lidos no original; documentos em outros idiomas precisam de tradução.
IDIOMAS_SEM_TRADUCAO = {"en", "pt"}
TIPOS = {"principal", "complementar"}
# Abaixo disso o texto quase certamente não é uma política completa.
MINIMO_DE_PALAVRAS_PRINCIPAL = 500


def _ler(caminho) -> pd.DataFrame:
    return pd.read_csv(caminho, dtype=str, keep_default_na=False)


def validar() -> list[str]:
    """Devolve a lista de problemas encontrados (vazia se estiver tudo certo)."""
    fontes, registro, resumo = _ler(FONTES_POLITICAS), _ler(REGISTRO_POLITICAS), _ler(RESUMO)
    inventario = _ler(INVENTARIO)
    erros = []

    if fontes["id_documento"].duplicated().any():
        erros.append("id_documento duplicado na lista de fontes")
    if not fontes["tipo"].isin(TIPOS).all():
        erros.append("tipo de documento inválido na lista de fontes")
    if not fontes["url"].str.startswith("https://").all():
        erros.append("URL de fonte que não começa com https://")

    # Cada política tem exatamente um documento principal.
    principais = fontes[fontes["tipo"] == "principal"].groupby("id_politica").size()
    for id_politica in sorted(set(fontes["id_politica"])):
        if principais.get(id_politica, 0) != 1:
            erros.append(f"{id_politica} deve ter exatamente um documento principal")

    # Todo fabricante incluído no inventário tem política na lista, e vice-versa.
    incluidos = set(inventario.loc[inventario["status_inclusao"] == "incluido", "fabricante"])
    for fabricante in sorted(incluidos - set(fontes["fabricante"])):
        erros.append(f"Fabricante incluído sem política na lista de fontes: {fabricante}")
    for fabricante in sorted(set(fontes["fabricante"]) - incluidos):
        erros.append(f"Fabricante na lista de fontes, mas não incluído no inventário: {fabricante}")

    # A URL de política do inventário é a do documento principal.
    url_principal = fontes[fontes["tipo"] == "principal"].set_index("fabricante")["url"]
    for linha in inventario[inventario["status_inclusao"] == "incluido"].itertuples():
        if url_principal.get(linha.fabricante) != linha.url_politica:
            erros.append(f"{linha.id}: url_politica difere do documento principal de {linha.fabricante}")

    # Todo documento foi baixado, o arquivo bruto está intacto e virou texto.
    coletados = registro[registro["status_http"] == "200"].drop_duplicates("id_documento", keep="last")
    coletados = coletados.set_index("id_documento")
    textos = resumo.set_index("id_documento")
    for fonte in fontes.itertuples():
        id_documento = fonte.id_documento
        if id_documento not in coletados.index:
            erros.append(f"{id_documento}: sem coleta bem-sucedida")
            continue
        bruto = PASTA_POLITICAS / coletados.at[id_documento, "arquivo"]
        if not bruto.exists():
            erros.append(f"{id_documento}: arquivo bruto ausente")
        elif hashlib.sha256(bruto.read_bytes()).hexdigest() != coletados.at[id_documento, "sha256"]:
            erros.append(f"{id_documento}: arquivo bruto difere do hash registrado na coleta")
        if id_documento not in textos.index:
            erros.append(f"{id_documento}: sem texto limpo")
            continue
        if not (PASTA_INTERIM / textos.at[id_documento, "arquivo_texto"]).exists():
            erros.append(f"{id_documento}: arquivo de texto ausente")
        if textos.at[id_documento, "sha256_bruto"] != coletados.at[id_documento, "sha256"]:
            erros.append(f"{id_documento}: texto gerado a partir de uma coleta que não é a mais recente")
        palavras = int(textos.at[id_documento, "palavras"])
        if fonte.tipo == "principal" and palavras < MINIMO_DE_PALAVRAS_PRINCIPAL:
            erros.append(f"{id_documento}: texto principal curto demais ({palavras} palavras)")

    erros.extend(_validar_traducoes(resumo))
    return erros


def _validar_traducoes(resumo: pd.DataFrame) -> list[str]:
    """Todo documento em outro idioma tem tradução atual e alinhada linha a linha."""
    erros = []
    traducoes = _ler(TRADUCOES).set_index("id_documento")
    for doc in resumo[~resumo["idioma"].isin(IDIOMAS_SEM_TRADUCAO)].itertuples():
        if doc.id_documento not in traducoes.index:
            erros.append(f"{doc.id_documento}: documento em '{doc.idioma}' sem tradução")
            continue
        registro = traducoes.loc[doc.id_documento]
        original = PASTA_INTERIM / registro["arquivo_original"]
        traducao = PASTA_TRADUCOES / registro["arquivo_traducao"]
        if hashlib.sha256(original.read_bytes()).hexdigest() != registro["sha256_original"]:
            erros.append(f"{doc.id_documento}: o original mudou depois da tradução")
        linhas_original = original.read_text(encoding="utf-8").splitlines()
        linhas_traducao = traducao.read_text(encoding="utf-8").splitlines()
        if len(linhas_original) != len(linhas_traducao):
            erros.append(f"{doc.id_documento}: tradução com número de linhas diferente do original")
    return erros


def main() -> None:
    erros = validar()
    resumo = _ler(RESUMO)
    print(f"{len(resumo)} documentos limpos; {resumo['palavras'].astype(int).sum()} palavras no total")
    if erros:
        print("\nProblemas encontrados:", *erros, sep="\n- ")
        sys.exit(1)
    print("Coleta e limpeza válidas.")


if __name__ == "__main__":
    main()
