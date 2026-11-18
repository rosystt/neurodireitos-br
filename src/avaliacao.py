"""Avaliação das políticas de privacidade com um modelo de linguagem.

Cada política é avaliada com o mesmo prompt, montado a partir da régua
congelada (docs/criterios.md) e dos textos limpos. A resposta bruta do modelo
é guardada inteira; as tabelas finais saem dela, com uma conferência
automática: todo trecho citado como evidência precisa existir, palavra por
palavra, no texto da política.

O modelo é chamado pelo Claude Code em modo não interativo (`claude -p`),
sem ferramentas e sem carregar configurações do usuário ou do projeto, para
que a classificação dependa só do prompt.
"""

import csv
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

MODELO = "claude-opus-5-5"
ESFORCO = "high"
VERSAO_PROMPT = "v1"
VERSAO_REGUA = "1.0"

PASTA_PROMPTS = Path("prompts")
REGUA = Path("docs/criterios.md")
FONTES = Path("data/raw/fontes_politicas.csv")
PASTA_TEXTOS = Path("data/interim/politicas")
PASTA_RESPOSTAS = Path("data/interim/avaliacao/llm")
PASTA_PROCESSED = Path("data/processed")

RESPOSTAS_VALIDAS = {"sim", "nao", "nao_menciona"}
# Trecho da régua enviado ao modelo: das definições até o fim dos critérios.
# Pesos, hipóteses e notas de revisão ficam de fora: não devem influir na resposta.
INICIO_REGUA = "## O que a régua mede — e o que não mede"
FIM_REGUA = "## Pesos e pontuação"


def _ler_csv(caminho: Path) -> list[dict]:
    with caminho.open(encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def _escrever_csv(caminho: Path, linhas: list[dict], colunas: list[str]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas)


def texto_da_regua() -> str:
    """Recorta da régua o trecho usado no prompt, sem os pesos nos títulos."""
    regua = REGUA.read_text(encoding="utf-8")
    trecho = regua[regua.index(INICIO_REGUA):regua.index(FIM_REGUA)]
    trecho = re.sub(r" \(peso \d\)", "", trecho)
    # A frase de abertura dos critérios fala dos pesos; sai junto com eles.
    trecho = re.sub(r"^Os pesos vão de .*\n+", "", trecho, flags=re.MULTILINE)
    return trecho.strip()


def documentos_da_politica(id_politica: str) -> dict[str, str]:
    """Textos limpos de uma política, por documento, com o principal primeiro."""
    fontes = [fonte for fonte in _ler_csv(FONTES) if fonte["id_politica"] == id_politica]
    if not fontes:
        raise ValueError(f"Política desconhecida: {id_politica}")
    fontes.sort(key=lambda fonte: (fonte["tipo"] != "principal", fonte["id_documento"]))
    return {
        fonte["id_documento"]: (PASTA_TEXTOS / f"{fonte['id_documento']}.txt").read_text(encoding="utf-8").strip()
        for fonte in fontes
    }


def montar_prompt(id_politica: str) -> tuple[str, str]:
    """Devolve o prompt de sistema e o de usuário para uma política."""
    documentos = "\n\n".join(
        f'<documento id="{id_documento}">\n{texto}\n</documento>'
        for id_documento, texto in documentos_da_politica(id_politica).items()
    )
    sistema = (PASTA_PROMPTS / "avaliacao_sistema.md").read_text(encoding="utf-8").strip()
    usuario = (PASTA_PROMPTS / "avaliacao_usuario.md").read_text(encoding="utf-8")
    # replace, e não format: os textos das políticas contêm chaves.
    usuario = usuario.replace("{regua}", texto_da_regua()).replace("{documentos}", documentos)
    return sistema, usuario


def chamar_modelo(sistema: str, usuario: str, limite_segundos: int = 1800) -> dict:
    """Envia o prompt ao modelo e devolve a saída completa do Claude Code."""
    executavel = shutil.which("claude")
    if executavel is None:
        raise RuntimeError("Claude Code não encontrado no PATH; instale-o para rodar a avaliação.")
    esquema = json.dumps(json.loads((PASTA_PROMPTS / "avaliacao_esquema.json").read_text(encoding="utf-8")))
    comando = [
        executavel, "-p",
        "--model", MODELO,
        "--effort", ESFORCO,
        "--system-prompt", sistema,
        "--tools", "",                 # nenhuma ferramenta: só leitura do prompt
        "--setting-sources", "",       # ignora configurações do usuário e do projeto
        "--strict-mcp-config",
        "--disable-slash-commands",
        "--no-session-persistence",
        "--output-format", "json",
        "--json-schema", esquema,
    ]
    # Pasta vazia como diretório de trabalho: nada do projeto entra no contexto.
    with tempfile.TemporaryDirectory() as pasta_neutra:
        processo = subprocess.run(
            comando, input=usuario.encode("utf-8"), capture_output=True,
            cwd=pasta_neutra, timeout=limite_segundos,
        )
    if processo.returncode != 0:
        # O Claude Code às vezes informa o erro na saída padrão, em JSON, e não na de erro.
        detalhe = (processo.stderr or processo.stdout).decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Claude Code falhou (código {processo.returncode}): {detalhe[:500] or 'sem mensagem'}")
    saida = json.loads(processo.stdout.decode("utf-8"))
    if saida.get("is_error") or not saida.get("structured_output"):
        raise RuntimeError(f"Resposta sem saída estruturada: {str(saida.get('result'))[:500]}")
    return saida


def avaliar_politica(id_politica: str, rodada: int = 1) -> Path:
    """Avalia uma política e guarda a resposta bruta; pula se a rodada já existe."""
    destino = PASTA_RESPOSTAS / f"{id_politica}_r{rodada}.json"
    if destino.exists():
        return destino

    sistema, usuario = montar_prompt(id_politica)
    saida = chamar_modelo(sistema, usuario)
    registro = {
        "id_politica": id_politica,
        "rodada": rodada,
        "modelo": MODELO,
        "modelo_usado": sorted(saida.get("modelUsage", {})),
        "esforco": ESFORCO,
        "versao_prompt": VERSAO_PROMPT,
        "versao_regua": VERSAO_REGUA,
        "sha256_prompt": hashlib.sha256((sistema + "\n" + usuario).encode("utf-8")).hexdigest(),
        "avaliado_em_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "duracao_ms": saida.get("duration_ms"),
        "uso": saida.get("usage"),
        "resposta": saida["structured_output"],
    }
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    return destino


def _normalizar(texto: str) -> str:
    """Iguala espaços, aspas e travessões, que variam entre a página e a citação."""
    texto = texto.translate(str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'", "–": "-", "—": "-", "\xa0": " "}))
    return re.sub(r"\s+", " ", texto).strip().lower()


def conferir_evidencia(evidencia: str, documentos: dict[str, str]) -> tuple[str, str]:
    """Diz se o trecho citado existe nos documentos e em qual.

    Devolve (situação, id_documento): `sem_evidencia`, `confere` ou
    `nao_confere`. Um trecho só confere se aparecer inteiro em um documento.
    """
    alvo = _normalizar(evidencia).strip('"')
    if not alvo:
        return "sem_evidencia", ""
    for id_documento, texto in documentos.items():
        if alvo in _normalizar(texto):
            return "confere", id_documento
    return "nao_confere", ""


def consolidar(rodada: int = 1) -> dict[str, list[dict]]:
    """Lê as respostas brutas de uma rodada e monta as tabelas, com as evidências conferidas."""
    avaliacoes, dados, terceiros, paises = [], [], [], []
    for arquivo in sorted(PASTA_RESPOSTAS.glob(f"*_r{rodada}.json")):
        registro = json.loads(arquivo.read_text(encoding="utf-8"))
        id_politica = registro["id_politica"]
        documentos = documentos_da_politica(id_politica)
        resposta = registro["resposta"]

        ids = [item["id_criterio"] for item in resposta["respostas"]]
        if sorted(ids) != [f"C{n:02d}" for n in range(1, 13)]:
            raise ValueError(f"{arquivo.name}: os critérios respondidos não são exatamente C01 a C12")

        for item in sorted(resposta["respostas"], key=lambda item: item["id_criterio"]):
            situacao, id_documento = conferir_evidencia(item["evidencia"], documentos)
            # A régua exige trecho para todo `sim` ou `nao`; sem trecho conferido, a resposta vai para revisão.
            precisa_revisao = item["resposta"] != "nao_menciona" and situacao != "confere"
            avaliacoes.append({
                "id_politica": id_politica, "id_criterio": item["id_criterio"],
                "resposta": item["resposta"], "evidencia": item["evidencia"],
                "id_documento": id_documento or item["id_documento"],
                "evidencia_conferida": situacao,
                "precisa_revisao": "sim" if precisa_revisao else "nao",
                "justificativa": item["justificativa"],
                "modelo": registro["modelo"], "versao_prompt": registro["versao_prompt"],
                "versao_regua": registro["versao_regua"], "avaliado_em_utc": registro["avaliado_em_utc"],
            })

        fatos = resposta["fatos"]
        for tabela, itens in ((dados, fatos["tipos_de_dado"]), (terceiros, fatos["terceiros"]), (paises, fatos["paises"])):
            for item in itens:
                situacao, id_documento = conferir_evidencia(item["evidencia"], documentos)
                tabela.append({
                    "id_politica": id_politica, **{chave: valor for chave, valor in item.items() if chave != "id_documento"},
                    "id_documento": id_documento or item["id_documento"], "evidencia_conferida": situacao,
                })
    return {"avaliacoes": avaliacoes, "dados": dados, "terceiros": terceiros, "paises": paises}


def pontuar(avaliacoes: list[dict]) -> list[dict]:
    """Nota de cada política: soma ponderada dos `sim`, contagem simples e distribuição."""
    pesos = {criterio["id"]: int(criterio["peso"]) for criterio in _ler_csv(PASTA_PROCESSED / "criterios.csv")}
    grupos = {
        fonte["id_politica"]: fonte["fabricante"]
        for fonte in _ler_csv(FONTES) if fonte["tipo"] == "principal"
    }
    grupo_por_fabricante = {
        linha["fabricante"]: linha["grupo"]
        for linha in _ler_csv(Path("data/raw/inventario.csv")) if linha["status_inclusao"] == "incluido"
    }
    notas = []
    for id_politica in sorted({linha["id_politica"] for linha in avaliacoes}):
        linhas = [linha for linha in avaliacoes if linha["id_politica"] == id_politica]
        conta = lambda resposta: sum(linha["resposta"] == resposta for linha in linhas)
        notas.append({
            "id_politica": id_politica, "fabricante": grupos[id_politica],
            "grupo": grupo_por_fabricante[grupos[id_politica]],
            "nota_ponderada": sum(pesos[linha["id_criterio"]] for linha in linhas if linha["resposta"] == "sim"),
            "nota_maxima": sum(pesos.values()),
            "respostas_sim": conta("sim"), "respostas_nao": conta("nao"),
            "respostas_nao_menciona": conta("nao_menciona"),
            "respostas_para_revisao": sum(linha["precisa_revisao"] == "sim" for linha in linhas),
        })
    return notas


def gravar_tabelas(rodada: int = 1) -> dict[str, list[dict]]:
    """Consolida a rodada e grava as tabelas finais em data/processed/."""
    tabelas = consolidar(rodada)
    tabelas["pontuacao"] = pontuar(tabelas["avaliacoes"])
    destinos = {
        "avaliacoes": "avaliacoes.csv", "pontuacao": "pontuacao.csv",
        "dados": "dados_coletados.csv", "terceiros": "terceiros.csv", "paises": "paises_dos_dados.csv",
    }
    for nome, arquivo in destinos.items():
        if tabelas[nome]:
            _escrever_csv(PASTA_PROCESSED / arquivo, tabelas[nome], list(tabelas[nome][0]))
    return tabelas


def concordancia(a: list[str], b: list[str]) -> dict[str, float]:
    """Concordância simples e kappa de Cohen entre duas listas de respostas alinhadas."""
    if len(a) != len(b) or not a:
        raise ValueError("As duas listas precisam ter o mesmo tamanho, maior que zero")
    total = len(a)
    observada = sum(x == y for x, y in zip(a, b)) / total
    esperada = sum((a.count(r) / total) * (b.count(r) / total) for r in RESPOSTAS_VALIDAS)
    kappa = 1.0 if esperada == 1 else (observada - esperada) / (1 - esperada)
    return {"itens": total, "concordancia": round(observada, 3), "kappa": round(kappa, 3)}
