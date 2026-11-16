"""Limpeza das políticas: do HTML bruto ao texto corrido.

Nada em data/raw/ é alterado. Cada HTML vira um arquivo de texto em
data/interim/politicas/, só com o conteúdo do documento: sem menus,
rodapés, scripts e, quando a página reúne vários documentos, sem as
seções que não são a política de privacidade.
"""

import csv
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

from src.coleta import PASTA_POLITICAS, ler_registro

PASTA_INTERIM = Path("data/interim/politicas")
RESUMO = PASTA_INTERIM / "resumo.csv"
COLUNAS_RESUMO = [
    "id_documento", "arquivo_bruto", "sha256_bruto", "arquivo_texto",
    "idioma", "caracteres", "palavras", "recorte",
]

TAGS_DESCARTADAS = [
    "script", "style", "noscript", "template", "svg", "iframe", "form",
    "button", "nav", "header", "footer", "aside",
]
TAGS_DE_BLOCO = [
    "p", "div", "section", "article", "li", "ul", "ol", "tr", "table",
    "blockquote", "h1", "h2", "h3", "h4", "h5", "h6", "br",
]
# Do mais específico para o mais genérico; vale o primeiro com texto suficiente.
SELETORES_DE_CONTEUDO = [
    ".shopify-policy__container", "main article", "article", "main",
    "[role=main]", "#MainContent", "#content", ".content",
]
MINIMO_DE_CARACTERES = 1500

# Páginas em que o seletor de conteúdo não basta: ou reúnem vários
# documentos, ou trazem menus e rodapés dentro da área principal.
# Guarda-se da linha que casa com o primeiro marcador até antes da que casa
# com o segundo (None = até o fim). Cada marcador é uma expressão regular
# aplicada a uma linha inteira, sem diferenciar maiúsculas de minúsculas.
RECORTES = {
    # Página com todos os documentos legais da Muse.
    "P01-1": (r"# Privacy Policy", r"# Hardware Warnings"),
    "P02-1": (r"# Privacy Policy", None),
    "P03-2": (r"# EMOTIV Consumer Health Data Privacy Policy", None),
    "P05-1": (r"# Privacy Policy", r"Order Now"),
    "P09-1": (r"INTRODUCTION TO NEUPHONY", r"# New from Neuphony\?"),
    # Política e termos de uso na mesma página.
    "P13-1": (r"Privacy Policy and Terms of Use", r"TERMS OF USE"),
}

# Stopwords suficientes para distinguir os idiomas da amostra.
PALAVRAS_POR_IDIOMA = {
    "en": {"the", "and", "of", "to", "we", "your", "or", "that", "with", "for"},
    "pt": {"de", "que", "os", "para", "nós", "seus", "uma", "não", "com", "dados"},
    "es": {"el", "los", "para", "que", "nosotros", "sus", "una", "con", "datos", "del"},
}


def _html_embutido(html: str) -> str | None:
    """Recupera o HTML guardado como texto dentro de um script.

    Algumas páginas não trazem o documento no HTML: ele vem em uma string
    JavaScript com os sinais de tag escapados (\\u003C). Devolve a maior
    dessas strings, já decodificada, ou None se não houver.
    """
    candidatas = re.findall(r'"((?:[^"\\]|\\.)*\\u003C(?:[^"\\]|\\.)*)"', html)
    if not candidatas:
        return None
    try:
        return json.loads(f'"{max(candidatas, key=len)}"')
    except json.JSONDecodeError:
        return None


def _texto_em_linhas(no) -> str:
    """Converte um trecho de HTML em texto, uma linha por bloco."""
    for tag in no.find_all(TAGS_DESCARTADAS):
        tag.decompose()
    for tag in no.find_all(TAGS_DE_BLOCO):
        if re.fullmatch(r"h[1-6]", tag.name):
            tag.insert(0, "# ")  # marca títulos, usados nos recortes
        tag.insert_before("\n")
        tag.insert_after("\n")

    linhas = []
    for linha in no.get_text("").replace("\xa0", " ").splitlines():
        linha = re.sub(r"[ \t​]+", " ", linha).strip()
        if linha and linha != "#" and (not linhas or linha != linhas[-1]):
            linhas.append(linha)
    return "\n".join(linhas)


def extrair_texto(conteudo: bytes) -> str:
    """Extrai o texto do documento a partir dos bytes do HTML bruto."""
    sopa = BeautifulSoup(conteudo, "html.parser")  # detecta a codificação pelos bytes

    for seletor in SELETORES_DE_CONTEUDO:
        no = sopa.select_one(seletor)
        if no and len(no.get_text(" ", strip=True)) >= MINIMO_DE_CARACTERES:
            return _texto_em_linhas(no)

    texto = _texto_em_linhas(BeautifulSoup(str(sopa.body or sopa), "html.parser"))
    if len(texto) >= MINIMO_DE_CARACTERES:
        return texto

    # Página quase vazia: o documento pode estar embutido em um script.
    embutido = _html_embutido(conteudo.decode(sopa.original_encoding or "utf-8", errors="replace"))
    if embutido:
        return _texto_em_linhas(BeautifulSoup(embutido, "html.parser"))
    return texto


def recortar(texto: str, inicio: str, fim: str | None) -> str:
    """Guarda da linha que casa com `inicio` até antes da que casa com `fim`.

    Levanta ValueError se um marcador não for encontrado: quando o site muda
    de estrutura, a falha aparece aqui, e não como uma política incompleta.
    """
    linhas = texto.splitlines()

    def posicao(padrao: str, a_partir_de: int) -> int:
        for i in range(a_partir_de, len(linhas)):
            if re.fullmatch(padrao, linhas[i], flags=re.IGNORECASE):
                return i
        raise ValueError(f"Marcador de recorte não encontrado: {padrao}")

    primeira = posicao(inicio, 0)
    ultima = len(linhas) if fim is None else posicao(fim, primeira + 1)
    return "\n".join(linhas[primeira:ultima])


def detectar_idioma(texto: str) -> str:
    """Devolve o código ISO 639-1 do idioma predominante (en, pt, es ou zh)."""
    if len(re.findall(r"[一-鿿]", texto)) > len(texto) * 0.2:
        return "zh"
    palavras = re.findall(r"[a-záéíóúãõâêôçñ]+", texto.lower())
    return max(PALAVRAS_POR_IDIOMA, key=lambda idioma: sum(p in PALAVRAS_POR_IDIOMA[idioma] for p in palavras))


def contar_palavras(texto: str, idioma: str) -> int:
    """Conta palavras; em chinês, que não separa palavras por espaço, conta ideogramas."""
    if idioma == "zh":
        return len(re.findall(r"[一-鿿]", texto))
    return len(re.findall(r"\w+", texto))


def limpar_politicas() -> list[dict]:
    """Limpa a coleta mais recente de cada documento e grava o resumo."""
    PASTA_INTERIM.mkdir(parents=True, exist_ok=True)

    # O registro está em ordem cronológica: a última coleta bem-sucedida prevalece.
    mais_recente = {
        linha["id_documento"]: linha
        for linha in ler_registro()
        if linha["status_http"] == "200"
    }

    resumo = []
    for id_documento, coleta in sorted(mais_recente.items()):
        texto = extrair_texto((PASTA_POLITICAS / coleta["arquivo"]).read_bytes())
        recorte = id_documento in RECORTES
        if recorte:
            texto = recortar(texto, *RECORTES[id_documento])

        idioma = detectar_idioma(texto)
        arquivo_texto = f"{id_documento}.txt"
        (PASTA_INTERIM / arquivo_texto).write_text(texto + "\n", encoding="utf-8", newline="\n")
        resumo.append({
            "id_documento": id_documento,
            "arquivo_bruto": coleta["arquivo"],
            "sha256_bruto": coleta["sha256"],
            "arquivo_texto": arquivo_texto,
            "idioma": idioma,
            "caracteres": len(texto),
            "palavras": contar_palavras(texto, idioma),
            "recorte": "sim" if recorte else "nao",
        })

    with RESUMO.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS_RESUMO, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(resumo)
    return resumo
