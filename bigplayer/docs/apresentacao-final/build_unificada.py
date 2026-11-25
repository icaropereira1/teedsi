"""Gera Apresentacao_Final_Unificada.pptx: a primeira apresentação (9 slides) e a apresentação final
(7 slides, os mesmos de build_pptx.py) num só arquivo, em ordem cronológica.

Parte do arquivo da primeira apresentação (1920 × 1080) e acrescenta os slides da final desenhados
em escala 1,5. O slide 1 da final vira o roteiro (sem repetir título e nomes da capa).
Requer: pip install python-pptx matplotlib.
Rodar: python docs/apresentacao-final/build_unificada.py [caminho da primeira apresentação .pptx]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from lxml import etree
from PIL import ImageFont
from pptx import Presentation
from pptx.oxml.ns import qn

import build_pptx as bp

HERE = Path(__file__).resolve().parent
PRIMEIRA = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "apresentacao-inicial" / "Big_Player.pptx"
OUT = HERE / "Apresentacao_Final_Unificada.pptx"

# Ordem final: ("P", n) = slide n da primeira apresentação, ("F", n) = slide n da final.
ORDEM = [
    ("P", 1),  # capa: Big Player
    ("P", 2),  # o que é um big player
    ("P", 3),  # como ele age e como pegamos o vácuo
    ("F", 1),  # roteiro: linha do tempo do projeto
    ("P", 4),  # os dados
    ("F", 2),  # base limpa, hold-out trancado
    ("P", 5),  # o horário domina o volume
    ("P", 6),  # WDO: sem normalizar, detectamos o relógio
    ("P", 7),  # como testamos (estudo de evento)
    ("P", 8),  # resultados: 46 testes
    ("F", 3),  # Gate 1: efeito em 15 min
    ("P", 9),  # conclusão do Gate 1 e próximos passos
    ("F", 4),  # parte 2: preço nos horários de pico
    ("F", 5),  # depois do pico
    ("F", 6),  # dias de alta e de baixa
    ("F", 7),  # estrangeiro × pessoa física e conclusões
]
FINAIS = (lambda p: bp.slide1(p, capa=False), bp.slide2, bp.slide3, bp.slide4, bp.slide5, bp.slide6, bp.slide7)

# ---------------------------------------------------------------- fonte da primeira apresentação
# Ela veio do Canva com a fonte Agrandir, que o Google Apresentações não tem: ele troca por Arial, que é
# mais larga, e o texto passa a quebrar em mais linhas e vazar da caixa. O Canva também fixa o espaçamento
# entre linhas em pontos, e o Google o lê como múltiplo da linha simples (~1,15 × corpo), deixando cada
# linha mais alta. Aqui a fonte vira Arial, o espaçamento vira percentual com a mesma altura de antes e,
# nas caixas em que o texto ainda não cabe, o corpo de letra diminui até caber.
EMU_PX = 9525
LINHA_SIMPLES = 1.18  # altura da linha simples da Arial no Google Apresentações, medida, em múltiplos do corpo
ARIAL = {False: r"C:\Windows\Fonts\arial.ttf", True: r"C:\Windows\Fonts\arialbd.ttf"}
_fontes: dict = {}


def _fonte(bold: bool, sz_pt: float):
    chave = (bold, round(sz_pt * 4))
    if chave not in _fontes:
        _fontes[chave] = ImageFont.truetype(ARIAL[bold], max(1, round(sz_pt * 96 / 72 * 4)))  # 4× para precisão
    return _fontes[chave]


def _largura(txt: str, bold: bool, sz_pt: float) -> float:
    return _fonte(bold, sz_pt).getlength(txt) / 4


def _corpo_padrao(txBody) -> int:
    """Corpo (em centésimos de pt) mais usado na caixa: vale para as linhas vazias, que não têm o seu."""
    szs = [int(r.get("sz")) for r in txBody.iter(qn("a:rPr")) if r.get("sz")]
    return max(set(szs), key=szs.count) if szs else 1800


def _altura_paragrafo(p, larg_px: float, f: float, padrao: int = 1800) -> float:
    """Altura em px do parágrafo <a:p> com os corpos multiplicados por f (quebra de linha simulada)."""
    pPr = p.find(qn("a:pPr"))
    marL = int(pPr.get("marL", 0)) / EMU_PX if pPr is not None else 0
    pedacos, sz_max = [], 0.0
    for r in p.findall(qn("a:r")):
        rPr = r.find(qn("a:rPr"))
        sz = int(rPr.get("sz", 1800)) / 100 * f if rPr is not None else 18 * f
        bold = rPr is not None and rPr.get("b") in ("1", "true")
        sz_max = max(sz_max, sz)
        for tok in re.findall(r"\S+|\s+", r.findtext(qn("a:t")) or ""):
            pedacos.append((tok, bold, sz))
    if not sz_max:
        end = p.find(qn("a:endParaRPr"))
        sz_max = int(end.get("sz", padrao) if end is not None else padrao) / 100 * f
    linhas, x, util = 1, 0.0, larg_px - marL
    for tok, bold, sz in pedacos:
        w = _largura(tok, bold, sz)
        if not tok.isspace() and x > 0 and x + w > util:
            linhas, x = linhas + 1, 0.0
        if not (tok.isspace() and x == 0):
            x += w
    ln = pPr.find(qn("a:lnSpc")) if pPr is not None else None
    mult = 1.0
    if ln is not None and ln.find(qn("a:spcPct")) is not None:
        mult = int(ln.find(qn("a:spcPct")).get("val")) / 100000
    alt_linha = mult * LINHA_SIMPLES * sz_max * 96 / 72
    extra = 0.0
    for tag in ("a:spcBef", "a:spcAft"):
        el = pPr.find(qn(tag)) if pPr is not None else None
        if el is not None and el.find(qn("a:spcPts")) is not None:
            extra += int(el.find(qn("a:spcPts")).get("val")) / 100 * f * 96 / 72
    return linhas * alt_linha + extra


def ajustar_texto(slide) -> list[str]:
    """Troca Agrandir por Arial e reduz o corpo das caixas cujo texto não cabe mais. Devolve o que mudou."""
    log = []
    for sh in slide.shapes:
        if not sh.has_text_frame or not sh.text_frame.text.strip():
            continue
        txBody = sh.text_frame._txBody
        for el in txBody.iter(qn("a:latin"), qn("a:ea"), qn("a:cs"), qn("a:sym")):
            if el.get("typeface", "").startswith("Agrandir"):
                el.set("typeface", "Arial")
        padrao = _corpo_padrao(txBody)
        for p in txBody.findall(qn("a:p")):   # espaçamento fixo (pt) → percentual com a mesma altura
            pPr = p.find(qn("a:pPr"))
            ln = pPr.find(qn("a:lnSpc")) if pPr is not None else None
            pts = ln.find(qn("a:spcPts")) if ln is not None else None
            if pts is None:
                continue
            szs = [int(r.get("sz")) for r in p.iter(qn("a:rPr"), qn("a:endParaRPr")) if r.get("sz")]
            sz = max(szs) if szs else padrao
            ln.remove(pts)
            pct = int(pts.get("val")) / sz / LINHA_SIMPLES
            etree.SubElement(ln, qn("a:spcPct")).set("val", str(int(pct * 100000)))
        bp_ = txBody.find(qn("a:bodyPr"))
        ins = lambda k, d: int(bp_.get(k, d)) / EMU_PX  # noqa: E731
        larg = sh.width / EMU_PX - ins("lIns", 91440) - ins("rIns", 91440)
        alt = sh.height / EMU_PX - ins("tIns", 45720) - ins("bIns", 45720)
        paras = txBody.findall(qn("a:p"))
        altura = lambda f: sum(_altura_paragrafo(p, larg, f, padrao) for p in paras)  # noqa: E731
        if altura(1.0) <= alt * 1.02:
            continue
        f = 1.0
        while f > 0.5 and altura(f) > alt * 1.02:
            f -= 0.01
        for el in txBody.iter(qn("a:rPr"), qn("a:endParaRPr"), qn("a:defRPr")):
            if el.get("sz"):
                el.set("sz", str(int(int(el.get("sz")) * f)))
        for tag in ("a:spcBef", "a:spcAft"):
            for el in txBody.iter(qn(tag)):
                pts = el.find(qn("a:spcPts"))
                if pts is not None:
                    pts.set("val", str(int(int(pts.get("val")) * f)))
        log.append(f"{sh.name}: corpo × {f:.2f} ({sh.text_frame.text[:40]!r})")
    return log


def main() -> None:
    prs = Presentation(PRIMEIRA)
    n_prim = len(prs.slides)
    for i, s in enumerate(prs.slides, 1):
        for linha in ajustar_texto(s):
            print(f"  primeira, slide {i}: {linha}")
    bp.ESCALA = prs.slide_width / (1280 * 9525)
    assert abs(prs.slide_height - 720 * 9525 * bp.ESCALA) < 9525, "a primeira apresentação não é 16:9"
    bp.TOTAL = len(ORDEM)
    bp.NUMERO = {n: ORDEM.index(("F", n)) + 1 for n in range(1, len(FINAIS) + 1)}
    for fn in FINAIS:
        fn(prs)

    lista = prs.slides._sldIdLst
    ids = list(lista)
    pos = {("P", i + 1): el for i, el in enumerate(ids[:n_prim])}
    pos |= {("F", i + 1): el for i, el in enumerate(ids[n_prim:])}
    assert sorted(pos) == sorted(ORDEM), "ORDEM precisa citar cada slide uma vez"
    for el in ids:
        lista.remove(el)
    for chave in ORDEM:
        lista.append(pos[chave])

    prs.core_properties.title = "Apresentação Final Unificada"
    prs.core_properties.author = "Gabriel Camargo Silva, Ícaro Alves de Sá, João Gabriel Abreu Soares"
    prs.save(OUT)
    print(f"ok: {OUT} ({len(prs.slides)} slides)")


if __name__ == "__main__":
    main()
