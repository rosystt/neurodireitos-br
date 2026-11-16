"""Coleta das políticas de privacidade e dos projetos de lei.

Tudo o que é baixado vai para data/raw/ exatamente como veio do servidor.
Cada download é registrado com data, hora, status e hash, porque políticas
de privacidade mudam e a análise precisa dizer de que versão está falando.
"""

import csv
import hashlib
import json
import time
from datetime import date, datetime, timezone
from pathlib import Path

import requests

RAIZ_RAW = Path("data/raw")
FONTES_POLITICAS = RAIZ_RAW / "fontes_politicas.csv"
PASTA_POLITICAS = RAIZ_RAW / "politicas"
REGISTRO_POLITICAS = PASTA_POLITICAS / "coletas.csv"
PASTA_PROJETOS = RAIZ_RAW / "projetos_lei"

CABECALHOS = {
    # Vários sites recusam clientes sem identificação de navegador.
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
    ),
    "Accept-Language": "en,pt-BR;q=0.8",
}
COLUNAS_REGISTRO = [
    "id_documento", "url", "url_final", "status_http", "data_hora_utc",
    "arquivo", "bytes", "sha256",
]
STATUS_TENTAR_DE_NOVO = {429, 500, 502, 503, 504}

API_CAMARA = "https://dadosabertos.camara.leg.br/api/v2"
API_SENADO = "https://legis.senado.leg.br/dadosabertos"


def baixar(url: str, tentativas: int = 4, espera: float = 20.0, **kwargs) -> requests.Response:
    """Faz um GET com novas tentativas quando o servidor limita ou falha.

    A espera dobra a cada tentativa. Devolve a última resposta, mesmo com
    erro, para que quem chamou possa registrar o status.
    """
    kwargs.setdefault("headers", CABECALHOS)
    kwargs.setdefault("timeout", 45)
    for tentativa in range(1, tentativas + 1):
        resposta = requests.get(url, **kwargs)
        if resposta.status_code not in STATUS_TENTAR_DE_NOVO or tentativa == tentativas:
            return resposta
        time.sleep(espera * 2 ** (tentativa - 1))
    return resposta


def ler_fontes(caminho: Path = FONTES_POLITICAS) -> list[dict]:
    """Lê a lista de documentos de política a coletar."""
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def ler_registro(caminho: Path = REGISTRO_POLITICAS) -> list[dict]:
    """Lê o registro das coletas já feitas (vazio se ainda não existe)."""
    if not caminho.exists():
        return []
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def coletar_politicas(
    fontes: list[dict] | None = None,
    data_coleta: date | None = None,
    pausa: float = 5.0,
) -> list[dict]:
    """Baixa cada documento e salva o conteúdo bruto com a data no nome.

    Documentos já coletados na mesma data são pulados, então a função pode
    ser executada de novo sem baixar tudo outra vez. Devolve os registros
    das coletas feitas nesta execução.
    """
    fontes = ler_fontes() if fontes is None else fontes
    data_coleta = data_coleta or date.today()
    PASTA_POLITICAS.mkdir(parents=True, exist_ok=True)

    registro = ler_registro()
    ja_coletados = {linha["arquivo"] for linha in registro if linha["status_http"] == "200"}
    novos = []

    for fonte in fontes:
        nome_arquivo = f"{fonte['id_documento']}_{data_coleta.isoformat()}.html"
        if nome_arquivo in ja_coletados and (PASTA_POLITICAS / nome_arquivo).exists():
            continue

        resposta = baixar(fonte["url"])
        linha = {
            "id_documento": fonte["id_documento"],
            "url": fonte["url"],
            "url_final": resposta.url,
            "status_http": str(resposta.status_code),
            "data_hora_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "arquivo": "",
            "bytes": "",
            "sha256": "",
        }
        if resposta.status_code == 200:
            # Bytes exatamente como vieram: a limpeza decide a codificação depois.
            (PASTA_POLITICAS / nome_arquivo).write_bytes(resposta.content)
            linha.update(
                arquivo=nome_arquivo,
                bytes=str(len(resposta.content)),
                sha256=hashlib.sha256(resposta.content).hexdigest(),
            )
        novos.append(linha)
        time.sleep(pausa)

    if novos:
        with REGISTRO_POLITICAS.open("w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=COLUNAS_REGISTRO, lineterminator="\n")
            escritor.writeheader()
            escritor.writerows(registro + novos)
    return novos


def _json(url: str, **params) -> dict:
    resposta = baixar(url, params=params, headers={**CABECALHOS, "Accept": "application/json"})
    resposta.raise_for_status()
    return resposta.json()


def _salvar_json(dados: dict | list, nome: str) -> Path:
    PASTA_PROJETOS.mkdir(parents=True, exist_ok=True)
    caminho = PASTA_PROJETOS / nome
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return caminho


def detalhar_camara(id_proposicao: int) -> dict:
    """Baixa detalhes, autores e proposições relacionadas de uma proposição da Câmara."""
    detalhes = _json(f"{API_CAMARA}/proposicoes/{id_proposicao}")["dados"]
    dados = {
        "coletado_em_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "detalhes": detalhes,
        "autores": _json(f"{API_CAMARA}/proposicoes/{id_proposicao}/autores")["dados"],
        "relacionadas": _json(f"{API_CAMARA}/proposicoes/{id_proposicao}/relacionadas")["dados"],
    }
    _salvar_json(dados, f"camara_{detalhes['siglaTipo']}_{detalhes['numero']}_{detalhes['ano']}.json")
    return dados


def buscar_camara(termo: str, ano_inicial: int = 2019) -> list[dict]:
    """Busca proposições da Câmara por palavra-chave, percorrendo todas as páginas."""
    resultados, pagina = [], 1
    while True:
        lote = _json(
            f"{API_CAMARA}/proposicoes",
            keywords=termo, dataApresentacaoInicio=f"{ano_inicial}-01-01",
            itens=100, pagina=pagina, ordem="ASC", ordenarPor="id",
        )["dados"]
        resultados.extend(lote)
        if len(lote) < 100:
            break
        pagina += 1
    _salvar_json(
        {"termo": termo, "coletado_em_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "dados": resultados},
        f"camara_busca_{termo.replace(' ', '_')}.json",
    )
    return resultados


def buscar_senado(termo: str) -> list[dict]:
    """Busca matérias do Senado por palavra-chave e devolve a lista encontrada."""
    dados = _json(f"{API_SENADO}/materia/pesquisa/lista", palavraChave=termo)
    dados["coletado_em_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _salvar_json(dados, f"senado_busca_{termo.replace(' ', '_')}.json")
    materias = dados["PesquisaBasicaMateria"].get("Materias", {}).get("Materia", [])
    # A API devolve um objeto, e não uma lista, quando há um único resultado.
    return materias if isinstance(materias, list) else [materias]


def detalhar_senado(sigla: str, numero: int, ano: int) -> dict:
    """Baixa os detalhes de uma matéria do Senado pela identificação."""
    dados = _json(f"{API_SENADO}/materia/{sigla}/{numero}/{ano}")
    dados["coletado_em_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _salvar_json(dados, f"senado_{sigla}_{numero}_{ano}.json")
    return dados["DetalheMateria"]["Materia"]
