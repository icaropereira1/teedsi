"""Gera Big_Player_apresentacao_final.pptx: os mesmos 7 slides do PDF, editáveis.

Gráficos desenhados com matplotlib e inseridos como PNG em 4× a resolução do slide (o Google
Apresentações convertia os gráficos nativos em imagens borradas); a linha do tempo dos dados
continua feita com formas. Os PNGs também ficam em graficos/. Dados: os mesmos CSVs versionados
que o build.sh usa. Falas sugeridas nas anotações.
Requer: pip install python-pptx matplotlib.   Rodar: python docs/apresentacao-final/build_pptx.py
"""
from __future__ import annotations

import csv
import json
from datetime import date
from io import BytesIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FixedLocator, FuncFormatter  # noqa: E402

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE, MSO_PATTERN
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

HERE = Path(__file__).resolve().parent
BP = HERE.parent.parent
D12 = BP / "docs" / "apresentacao-12-11" / "dados"
OUT = HERE / "Big_Player_apresentacao_final.pptx"
GRAF = HERE / "graficos"
SCALE = 4  # pixels de imagem por px do slide (1280 × 720)

FONT = "Segoe UI"
SURFACE, INK, INK2, GRID = "F1EEE9", "1A1A1A", "5C5852", "DAD5CD"
PURPLE, ORANGE, ORANGE_TXT, MINT = "7B57C8", "F0A030", "B86A00", "BCECE6"
PINK, MUTED, BAND, WHITE = "E06388", "8E887F", "E4DFD7", "FFFFFF"
HORAS = ["09:30", "10:00", "10:30", "11:00", "11:30", "12:00", "12:30", "13:00", "13:30",
         "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00", "17:30"]


# ---------------------------------------------------------------- dados
def read(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k, v in r.items():
            try:
                r[k] = float(v)
            except (TypeError, ValueError):
                pass
    return rows


EV_WDO = read(BP / "reports/estudo_evento_wdo.csv")
EV_WIN = read(BP / "reports/estudo_evento_win.csv")
EV_R2 = read(BP / "reports/estudo_evento_r2_wdo.csv")
EV_CONF = read(BP / "reports/confirmacao_a1_win.csv")
BUR = {a: read(BP / f"reports/buracos_{a}.csv") for a in ("wdo", "win")}
PICOS = {a: read(BP / f"pt2/reports/picos_{a}.csv") for a in ("wdo", "win")}
DEP = {a: read(BP / f"pt2/reports/depois_{a}.csv") for a in ("wdo", "win")}
P30 = {(s, t): read(D12 / f"medianas_pico30/pico30_{s}_{t}.csv")
       for s in ("wdo", "win", "dolarizado") for t in ("alta", "baixa", "todos")}
FLUXO = read(D12 / "fluxo_investidores/fluxo_investidores.csv")
MAN = {"wdo": json.loads((BP / "reports/split_manifest.json").read_text(encoding="utf-8")),
       "win": json.loads((BP / "reports/split_manifest_win.json").read_text(encoding="utf-8"))}


def br(x: float, dec: int = 1, plus: bool = False) -> str:
    if abs(x) < 1e-9:
        x = 0.0
    s = f"{abs(x):,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    r = round(x, dec)
    if r < 0:
        return "−" + s
    return ("+" + s) if (plus and r > 0) else s


def find(rows, **kw):
    return next(r for r in rows if all(r[k] == v for k, v in kw.items()))


# ---------------------------------------------------------------- primitivas (coordenadas em px de 1280 × 720)
def px(v: float) -> Emu:
    return Emu(int(round(v * 9525)))


def rgb(h: str) -> RGBColor:
    return RGBColor.from_string(h)


def text(slide, x, y, w, h, runs, size=11, color=INK, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, italic=False, name=None, line=None):
    """runs: str, ou lista de parágrafos; cada parágrafo é str ou lista de (texto, {opções})."""
    tb = slide.shapes.add_textbox(px(x), px(y), px(w), px(h))
    if name:
        tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    paras = runs if isinstance(runs, list) else [runs]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if line:
            p.line_spacing = line
        for t, o in ([(para, {})] if isinstance(para, str) else para):
            r = p.add_run()
            r.text = t
            f = r.font
            f.name = FONT
            f.size = Pt(o.get("size", size))
            f.bold = o.get("bold", bold)
            f.italic = o.get("italic", italic)
            f.color.rgb = rgb(o.get("color", color))
    return tb


def bullets(slide, x, y, w, h, items, size=11, gap=7):
    """items: lista de parágrafos (lista de runs). Marcador rosa nativo, sem caractere literal."""
    tb = text(slide, x, y, w, h, items, size=size, line=1.12)
    for p in tb.text_frame.paragraphs:
        pPr = p._p.get_or_add_pPr()
        pPr.set("marL", str(px(16)))
        pPr.set("indent", str(-px(16)))
        spc = etree.SubElement(pPr, qn("a:spcAft"))
        etree.SubElement(spc, qn("a:spcPts")).set("val", str(gap * 100))
        clr = etree.SubElement(pPr, qn("a:buClr"))
        etree.SubElement(clr, qn("a:srgbClr")).set("val", PINK)
        etree.SubElement(pPr, qn("a:buSzPct")).set("val", "90000")
        etree.SubElement(pPr, qn("a:buFont")).set("typeface", "Arial")
        etree.SubElement(pPr, qn("a:buChar")).set("char", "●")
    return tb


def rect(slide, x, y, w, h, fill, line=None, rounded=False, radius=0.12, transparency=0, name=None, line_w=1.2):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE,
                                 px(x), px(y), px(w), px(h))
    if rounded:
        shp.adjustments[0] = radius
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = rgb(fill)
        if transparency:
            sf = shp.fill._xPr.find(qn("a:solidFill"))
            etree.SubElement(sf[0], qn("a:alpha")).set("val", str(int((100 - transparency) * 1000)))
    if line:
        shp.line.color.rgb = rgb(line)
        shp.line.width = Pt(line_w)
    else:
        shp.line.fill.background()
    shp.shadow.inherit = False
    if name:
        shp.name = name
    return shp


def oval(slide, cx, cy, r, fill, line=INK):
    shp = slide.shapes.add_shape(MSO_SHAPE.OVAL, px(cx - r), px(cy - r), px(2 * r), px(2 * r))
    shp.fill.solid()
    shp.fill.fore_color.rgb = rgb(fill)
    shp.line.color.rgb = rgb(line)
    shp.line.width = Pt(0.75)
    shp.shadow.inherit = False
    return shp


def hline(slide, x1, y1, x2, y2, color=GRID, w=0.75, dash=False):
    ln = slide.shapes.add_connector(1, px(x1), px(y1), px(x2), px(y2))
    ln.line.color.rgb = rgb(color)
    ln.line.width = Pt(w)
    if dash:
        ln.line.dash_style = MSO_LINE.DASH
    return ln


def hatch(shp):
    """Listras diagonais (hold-out). O Google Apresentações mostra só a cor de fundo."""
    shp.fill.patterned()
    shp.fill.pattern = MSO_PATTERN.WIDE_UPWARD_DIAGONAL
    shp.fill.fore_color.rgb = rgb(MUTED)
    shp.fill.back_color.rgb = rgb("E9E4DC")
    return shp


def legend(slide, x, y, items, gap=22, size=9.5):
    """items: (tipo, cor, rótulo); tipo em rect | outline | hold | dot | line | dash | err | tick | band."""
    cx = x
    for kind, col, lab in items:
        if kind in ("rect", "band"):
            rect(slide, cx + 2, y + 2, 16, 11, col)
        elif kind == "outline":
            rect(slide, cx + 2, y + 2, 16, 11, col, line=INK, line_w=1)
        elif kind == "hold":
            hatch(rect(slide, cx + 2, y + 2, 16, 11, "E9E4DC", line=INK2, line_w=0.75))
        elif kind == "dot":
            oval(slide, cx + 10, y + 8, 5, col)
        elif kind in ("line", "dash"):
            hline(slide, cx, y + 8, cx + 22, y + 8, col, 2.5 if kind == "line" else 2, dash=kind == "dash")
        elif kind == "err":
            hline(slide, cx + 10, y, cx + 10, y + 16, INK, 1)
            oval(slide, cx + 10, y + 8, 5, col)
        elif kind == "tick":
            hline(slide, cx + 3, y + 8, cx + 19, y + 8, col, 3)
        w = len(lab) * size * 0.75 + 16  # largura média de caractere ≈ 0,75 × corpo em pt, em px, com folga
        text(slide, cx + 27, y, w, 16, lab, size=size, color=INK)
        cx += 27 + w + gap


# ---------------------------------------------------------------- gráficos (matplotlib → PNG em alta resolução)
plt.rcParams.update({"font.family": FONT, "axes.unicode_minus": True, "svg.fonttype": "none"})


def c(h: str) -> str:
    return "#" + h


def figure(w, h):
    """Figura com o tamanho do quadro no slide: 1 px do slide = 1/96 pol., então os corpos em pt batem."""
    return plt.figure(figsize=(w / 96, h / 96), dpi=96, facecolor=c(SURFACE))


def axes(fig, w, h, left, top, aw, ah, ymin, ymax, step, fmt, grid_axis="y", size=9.5):
    """Área de plotagem em px dentro do quadro w × h; eixo de valores com grade e sem traço."""
    ax = fig.add_axes([left / w, 1 - (top + ah) / h, aw / w, ah / h])
    ax.set_facecolor("none")
    for side_ in ("top", "right", "left", "bottom"):
        ax.spines[side_].set_visible(False)
    base = ax.spines["left" if grid_axis == "x" else "bottom"]
    base.set_visible(True)
    base.set_color(c(INK))
    base.set_linewidth(0.75)
    ax.tick_params(length=0, labelsize=size, colors=c(INK2), pad=5)
    ticks = [ymin + i * step for i in range(int(round((ymax - ymin) / step)) + 1)]
    val = ax.xaxis if grid_axis == "x" else ax.yaxis
    (ax.set_xlim if grid_axis == "x" else ax.set_ylim)(ymin, ymax)
    val.set_major_locator(FixedLocator(ticks))
    val.set_major_formatter(FuncFormatter(lambda v, _: fmt(v)))
    ax.grid(axis=grid_axis, color=c(GRID), linewidth=0.75)
    ax.set_axisbelow(True)
    return ax


def cat_axis(ax, labels, show=True, size=9.5):
    ax.set_xlim(-0.5, len(labels) - 0.5)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels if show else [""] * len(labels), fontsize=size, color=c(INK))


def axis_title(ax, label, which="y", size=9):
    kw = dict(fontsize=size, color=c(INK2), labelpad=6)
    (ax.set_ylabel if which == "y" else ax.set_xlabel)(label, **kw)


def picture(slide, fig, x, y, w, h, name):
    """Salva a figura em SCALE× a resolução do slide e a insere no quadro (x, y, w, h)."""
    GRAF.mkdir(exist_ok=True)
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=96 * SCALE, facecolor=fig.get_facecolor())
    plt.close(fig)
    (GRAF / f"{name}.png").write_bytes(buf.getvalue())
    buf.seek(0)
    pic = slide.shapes.add_picture(buf, px(x), px(y), px(w), px(h))
    pic.name = f"Gráfico {name}"
    return pic


def fmt_int(v):
    return br(v, 0)


def fmt_signed(v):
    return br(v, 0, True)


# ---------------------------------------------------------------- moldura comum
def frame(prs, n, kicker, title, notes):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = rgb(SURFACE)
    if kicker:
        text(s, 50, 32, 1000, 20, kicker.upper(), size=10.5, color=PINK, bold=True, name="Chamada")
    if title:
        text(s, 50, 52, 1180, 44, title, size=24, bold=True, name="Título")
    hline(s, 50, 690, 1230, 690, GRID, 0.75)
    text(s, 50, 695, 300, 16, "Big Player · TEEDSI", size=9, color=MUTED)
    text(s, 1130, 695, 100, 16, f"{n} / 7", size=9, color=MUTED, align=PP_ALIGN.RIGHT)
    s.notes_slide.notes_text_frame.text = notes
    return s


def chart_head(s, x, y, w, title, sub):
    text(s, x, y, w, 22, title, size=13, bold=True)
    text(s, x, y + 22, w, 30, sub, size=10, color=INK2)


def side(s, x, y, w, heading, items, box, box_small=None, box_y=None, size=11):
    text(s, x, y, w, 20, heading.upper(), size=11, bold=True, color=PURPLE)
    bullets(s, x, y + 28, w, 260, items, size=size)
    by = box_y if box_y else y + 300
    b = rect(s, x, by, w, 92 if box_small else 66, MINT, line=INK, rounded=True, radius=0.14, name="Destaque")
    paras = [[(box, {"bold": True, "size": 11.5})]]
    if box_small:
        paras.append([(box_small, {"size": 10})])
    tf = b.text_frame
    tf.margin_left = tf.margin_right = px(14)
    tf.margin_top = tf.margin_bottom = px(8)
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        for t, o in para:
            r = p.add_run()
            r.text = t
            r.font.name = FONT
            r.font.size = Pt(o["size"])
            r.font.bold = o.get("bold", False)
            r.font.color.rgb = rgb(INK)


def strip(s, cards, y=612, h=64):
    w = (1180 - 2 * 14) / 3
    for i, (fill, paras) in enumerate(cards):
        x = 50 + i * (w + 14)
        rect(s, x, y, w, h, fill, rounded=True, radius=0.1, transparency=40 if fill == WHITE else 0,
             line=INK if fill == MINT else None)
        text(s, x + 12, y + 8, w - 24, h - 14, [paras], size=10.5, anchor=MSO_ANCHOR.MIDDLE, line=1.1)


def B(t, color=INK):
    return (t, {"bold": True, "color": color})


def N(t):
    return (t, {})


# ================================================================ slides
def slide1(prs):
    s = frame(prs, 1, "TEEDSI · Data Science no mercado financeiro", None, NOTES[1])
    text(s, 50, 112, 640, 80, "Big Player", size=48, bold=True, name="Título")
    text(s, 50, 196, 640, 70, "O que fizemos desde o início: dos dados brutos de 1 minuto até o preço nos "
         "picos de volume do mini dólar e do mini índice.", size=16, color=INK2, line=1.1)
    text(s, 50, 290, 640, 50, [[N("Gabriel Camargo Silva · Ícaro Alves de Sá · João Gabriel Abreu Soares")],
                               [("Novembro de 2026", {"color": INK2})]], size=12, line=1.3)
    text(s, 730, 72, 500, 20, "LINHA DO TEMPO DO PROJETO", size=11, bold=True, color=INK2)
    steps = [
        (PURPLE, "Arquitetura e dados", "Tese do \"vácuo\", carga dos candles, hold-out de 12 meses trancado, calendário B3, buracos e rolagem."),
        (PURPLE, "Gate 1: estudo de evento", "6 definições de pico de fluxo, testes pré-registrados nos dois ativos. Resultado: no-go."),
        (ORANGE, "Parte 2 (03/11): preço nos picos", "A pedido do professor: contas simples, em pontos, no minuto antes, no minuto do pico e depois."),
        (ORANGE, "12/11: alta × baixa, dolarizado, fluxo", "T = minuto de maior volume, horizontes até T+15, índice em dólar e estrangeiro × pessoa física."),
        (PINK, "Hoje: síntese e próximos passos", "O pico de volume diz quanto o preço anda, não para onde."),
    ]
    y0, step = 104, 74
    hline(s, 742, y0 + 12, 742, y0 + 12 + step * 4, GRID, 2.25)
    for i, (col, head, sub) in enumerate(steps):
        y = y0 + i * step
        c = oval(s, 742, y + 12, 12.5, col, line=col)
        c.text_frame.text = str(i + 1)
        p = c.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        f = p.runs[0].font
        f.size, f.bold, f.color.rgb, f.name = Pt(10), True, rgb(WHITE), FONT
        c.text_frame.margin_left = c.text_frame.margin_right = c.text_frame.margin_top = c.text_frame.margin_bottom = 0
        text(s, 772, y + 2, 455, 20, head, size=12, bold=True)
        text(s, 772, y + 22, 455, 40, sub, size=10, color=INK2, line=1.05)
    kpis = [("~5 anos", "de candles de 1 minuto (2020–2025)"), ("1,19 mi", "candles na exploração (WDO + WIN)"),
            ("46", "testes pré-registrados no Gate 1"), ("12 meses", "de hold-out ainda intocados")]
    for i, (big, lab) in enumerate(kpis):
        x = 50 + i * 238
        rect(s, x, 586, 224, 80, WHITE, rounded=True, radius=0.12, transparency=40)
        text(s, x + 16, 594, 200, 34, big, size=20, bold=True, color=PURPLE)
        text(s, x + 16, 632, 200, 30, lab, size=10, color=INK2)


def slide2(prs):
    s = frame(prs, 2, "Etapa 1 · Arquitetura e dados (set–out/2026)",
              "Uma base limpa, com o último ano trancado para o teste final", NOTES[2])
    chart_head(s, 50, 108, 800, "Período coberto pelos dados de cada ativo",
               "candles de 1 minuto exportados do MetaTrader 5 · barras = período de exploração e de hold-out · rosa = dias úteis sem nenhum candle")
    # linha do tempo desenhada com formas (eixo em datas)
    ox, oy = 50, 175
    x0, x1 = ox + 70, ox + 780
    d0, d1 = date(2020, 7, 1).toordinal(), date(2026, 12, 31).toordinal()

    def sx(iso: str) -> float:
        d = date.fromisoformat(iso[:10]).toordinal()
        return x0 + (d - d0) / (d1 - d0) * (x1 - x0)

    for yv in range(2021, 2027):
        xx = sx(f"{yv}-01-01")
        hline(s, xx, oy + 40, xx, oy + 310, GRID, 0.75)
        text(s, xx - 25, oy + 318, 50, 16, str(yv), size=10, color=INK2, align=PP_ALIGN.CENTER)
    hline(s, x0, oy + 310, x1, oy + 310, INK, 1)
    for k, name, col, ry in (("wdo", "WDO · mini dólar", PURPLE, oy + 80), ("win", "WIN · mini índice", ORANGE, oy + 205)):
        m, bh = MAN[k], 46
        ex0, ho0, ho1 = sx(m["exploration"]["start"]), sx(m["holdout_start"]), sx(m["holdout"]["end"])
        text(s, ox + 10, ry - 34, 300, 20, name, size=11.5, bold=True)
        rect(s, ex0, ry, ho0 - ex0, bh, col)
        hatch(rect(s, ho0, ry, ho1 - ho0, bh, "E9E4DC", line=INK2, line_w=0.75))
        for b in BUR[k]:
            bx = sx(b["start"])
            rect(s, bx, ry - 4, max(3, sx(b["end"]) - bx), bh + 8, PINK)
        text(s, ex0 + 10, ry + 6, 300, 18, f"exploração · {int(m['exploration']['days']):,} pregões".replace(",", "."),
             size=10, bold=True, color=WHITE)
        text(s, ex0 + 10, ry + 24, 300, 16, f"{int(m['exploration']['rows']):,} candles de 1 min".replace(",", "."),
             size=9.5, color=WHITE)
        text(s, ho0 - 40, ry + bh + 6, (ho1 - ho0) + 80, 16, f"hold-out: {int(m['holdout']['days'])} pregões (trancado)",
             size=9.5, color=INK2, align=PP_ALIGN.CENTER)
        big = max(BUR[k], key=lambda b: b["trading_days"])
        bx = (sx(big["start"]) + sx(big["end"])) / 2
        text(s, bx - 80, ry - 24, 160, 16, f"buraco: {int(big['trading_days'])} pregões", size=9.5, bold=True,
             color="B03A5F", align=PP_ALIGN.CENTER)
    legend(s, x0, 548, [("rect", PURPLE, "exploração WDO"), ("rect", ORANGE, "exploração WIN"),
                        ("hold", None, "hold-out (últimos 12 meses)"), ("rect", PINK, "buraco nos dados")], gap=16)
    text(s, 50, 600, 800, 30, "Fonte: reports/split_manifest*.json e reports/buracos_*.csv · exploração WDO 17/09/2020–01/04/2025, "
         "WIN 15/10/2020–25/09/2025", size=9, color=MUTED)
    side(s, 880, 112, 350, "O que fizemos", [
        [B("Qualidade conferida: "), N("sem nulos nem duplicatas, OHLC 100% consistente, preços sempre no tick.")],
        [B("Buracos marcados, não apagados: "), N("3 trechos sem dado (o maior, jun–set/2023). Janelas móveis não atravessam o buraco.")],
        [B("Calendário B3 e rolagem: "), N("feriados, sessão curta/longa e dia de troca de contrato marcados em cada candle.")],
        [B("Volume depende do relógio: "), N("a manhã negocia ~3× a tarde, então o volume foi normalizado por horário (z-score).")],
    ], "99,9% dos candles ficaram utilizáveis, e o hold-out só abre uma vez, na avaliação final.", box_y=420)


def slide3(prs):
    s = frame(prs, 3, "Etapa 2 · Gate 1: estudo de evento (out/2026)",
              "O pico de fluxo não previu a direção do preço: Gate 1 deu no-go", NOTES[3])
    chart_head(s, 50, 108, 800, "Efeito de seguir a direção do evento, 15 minutos depois",
               "retorno na direção do evento menos o de minutos comuns parecidos (controle), em bps · barra = efeito, "
               "traço = intervalo de confiança de 95% (bootstrap por dia)")
    nome = {"E1": "E1 volume anômalo (z ≥ 3)", "E2": "E2 volume + lote grande", "E3": "E3 volume alto por 5 min",
            "P1": "P1 fluxo persistente", "X1": "X1 pressão no extremo", "A1": "A1 pausa com volume"}

    def pick(rows, ev):
        return find(rows, evento=ev, h_min=15.0)

    rows = [("WDO", pick(EV_WDO, "E1")), ("WDO", pick(EV_WDO, "E2")), ("WDO", pick(EV_WDO, "E3")),
            ("WDO", pick(EV_R2, "P1")), ("WDO", pick(EV_R2, "X1")), ("WDO", pick(EV_R2, "A1")),
            ("WIN", pick(EV_WIN, "E1")), ("WIN", pick(EV_WIN, "E2")), ("WIN", pick(EV_WIN, "E3")),
            ("WIN", pick(EV_CONF, "A1"))]
    cats = []
    for ativo, r in rows:
        extra = " (confirmação)" if ativo == "WIN" and r["evento"] == "A1" else ""
        cats.append(f"{ativo} · {nome[r['evento']]}{extra} · p = {br(r['p'], 3 if r['p'] < 0.1 else 2)}")
    W, H = 800, 444
    fig = figure(W, H)
    ax = axes(fig, W, H, 330, 8, 456, 384, -4, 3, 1, fmt_signed, grid_axis="x")
    for i, (ativo, r) in enumerate(rows):
        col = PURPLE if ativo == "WDO" else ORANGE
        a1 = r["evento"] == "A1"   # o candidato que não se confirmou
        ax.barh(i, r["efeito_bps"], height=0.58, color=c(MINT if a1 else col),
                edgecolor=c(col), linewidth=2 if a1 else 0, zorder=2)
        ax.errorbar(r["efeito_bps"], i, xerr=[[r["efeito_bps"] - r["ic95_inf"]], [r["ic95_sup"] - r["efeito_bps"]]],
                    fmt="none", ecolor=c(INK), elinewidth=1.25, capsize=3, capthick=1.25, zorder=3)
    ax.set_ylim(len(rows) - 0.5, -0.5)   # WDO E1 no topo
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(cats, fontsize=9.5, color=c(INK))
    ax.axvline(0, color=c(INK), linewidth=0.75, zorder=1)
    ax.spines["left"].set_visible(False)
    axis_title(ax, "efeito em 15 min (bps): retorno na direção do evento − controle", which="x", size=9.5)
    picture(s, fig, 50, 160, W, H, "slide3_gate1")
    legend(s, 60, 612, [("rect", PURPLE, "WDO"), ("rect", ORANGE, "WIN"),
                        ("outline", MINT, "A1: único positivo, não passou o limite e não se confirmou"),
                        ("err", MUTED, "IC 95%")], gap=18)
    text(s, 50, 640, 800, 30, "Fonte: reports/estudo_evento_*.csv e confirmacao_a1_win.csv · E1–E3: rodada 1 · P1, X1 e A1: "
         "rodada 2 · limite com correção de Bonferroni: p < 0,0033 (rodada 1) e p < 0,0017 (rodada 2)", size=9, color=MUTED)
    side(s, 880, 112, 350, "Como testamos", [
        [B("Regras escritas antes de ver o resultado "), N("(pré-registro): 6 definições de evento, 5 horizontes, 2 ativos.")],
        [N("Entrada no candle seguinte, saída no mesmo pregão, sem olhar o futuro.")],
        [B("Nenhum dos 46 testes passou. "), N("A maioria dos efeitos é negativa ou nula, e o sinal troca de ano para ano.")],
        [B("A1 (pausa com volume) "), N("foi o único positivo no WDO (+1,34 bps, p = 0,0145), mas não passou o limite e não se repetiu no WIN (p = 0,18).")],
    ], "Com candles de 1 minuto, não há sinal de continuação depois do pico de fluxo.",
        "Mesmo 1 bp seria menor que o custo de ida e volta (2 a 3 ticks).", box_y=440)


def slide4(prs):
    s = frame(prs, 4, "Etapa 3 · Parte 2, apresentação de 03/11",
              "Nos horários de pico, o preço anda mais, mas o minuto antes é comum", NOTES[4])
    chart_head(s, 50, 102, 1180, "Volume e movimento do preço nos horários redondos (:00 e :30)",
               "mediana de 1.034 pregões (WDO) e 1.118 (WIN) · movimento = |variação do preço médio (máx + mín + fech) / 3| no minuto, comparado dia a dia")
    legend(s, 50, 150, [("rect", PURPLE, "WDO · mini dólar"), ("rect", ORANGE, "WIN · mini índice"),
                        ("band", BAND, "faixa de acaso (margem de erro de 95%)"), ("dash", INK2, "1× = volume normal da tarde")], gap=20)
    labels = [h.lstrip("0").replace(":00", "h").replace(":", "h") for h in HORAS]
    # painel A: volume × tarde (colunas)
    text(s, 50, 176, 1100, 18, "A · volume no minuto do pico ÷ volume típico da tarde", size=10.5, bold=True)
    W, H = 1180, 150
    fig = figure(W, H)
    ax = axes(fig, W, H, 50, 6, 1120, 120, 0, 5, 1, lambda v: f"{br(v, 0)}×")
    cat_axis(ax, labels, show=False)
    for k, (a, col) in enumerate((("wdo", PURPLE), ("win", ORANGE))):
        vals = [find(PICOS[a], horario=h)["volume_x_tarde"] for h in HORAS]
        ax.bar([i + (k - 0.5) * 0.35 for i in range(len(HORAS))], vals, width=0.33, color=c(col), zorder=2)
    ax.axhline(1, color=c(INK2), linewidth=1.25, linestyle=(0, (4, 3)), zorder=3)
    picture(s, fig, 50, 194, W, H, "slide4a_volume")
    # painel B: % mexeu mais (linhas)
    text(s, 50, 352, 1100, 18, "B · % dos pregões em que o preço andou mais no minuto do pico (T) que no minuto antes (T−1)",
         size=10.5, bold=True)
    W, H = 1180, 228
    fig = figure(W, H)
    ax = axes(fig, W, H, 50, 8, 1120, 186, 45, 70, 5, lambda v: f"{br(v, 0)}%")
    cat_axis(ax, labels)
    ax.axhspan(47, 53, color=c(BAND), zorder=0, linewidth=0)
    ax.axhline(50, color=c(INK2), linewidth=1, linestyle=(0, (4, 3)), zorder=1)
    for a, col in (("wdo", PURPLE), ("win", ORANGE)):
        vals = [find(PICOS[a], horario=h)["pico_maior_pct"] for h in HORAS]
        ax.plot(range(len(HORAS)), vals, color=c(col), linewidth=1.75, marker="o", markersize=8,
                markeredgecolor=c(INK), markeredgewidth=0.75, zorder=3)
    v10 = find(PICOS["win"], horario="10:00")["pico_maior_pct"]
    ax.annotate(f"WIN 10h: {br(v10, 1)}%", (1, v10), xytext=(0, 8), textcoords="offset points", ha="center",
                va="bottom", fontsize=9, fontweight="bold", color=c(ORANGE_TXT))
    picture(s, fig, 50, 372, W, H, "slide4b_mexeu_mais")
    strip(s, [
        (WHITE, [B("Volume: ", PURPLE), N("picos às 9h30–12h, até 4,2× a tarde. Os maiores movimentos caem em divulgações dos EUA (CPI, payroll).")]),
        (WHITE, [B("WIN: ", ORANGE_TXT), N("o minuto do pico mexe mais em 15 de 17 horários (até 65% dos dias, às 10h). "), B("WDO: ", PURPLE), N("em 7 de 17.")]),
        (MINT, [B("No minuto antes do pico, a mediana com sinal é ~0: o preço não \"avisa\" a direção.")]),
    ])


def slide5(prs):
    s = frame(prs, 5, "Etapa 3 · Parte 2, apresentação de 03/11",
              "Depois do pico, o preço continua tanto quanto num minuto comum", NOTES[5])
    chart_head(s, 50, 108, 800, "% dos pregões em que o preço segue a direção do minuto do pico, 15 min depois",
               "fechamento em T+15 do mesmo lado do movimento em T · ponto = pico, traço cinza = minutos comuns (não :00/:30) da mesma hora")
    labels = [h.lstrip("0").replace(":00", "h").replace(":", "h") for h in HORAS]
    for i, (a, name, col) in enumerate((("wdo", "WDO · mini dólar", PURPLE), ("win", "WIN · mini índice", ORANGE))):
        y = 166 + i * 216
        text(s, 50, y, 300, 18, name, size=11, bold=True)
        rows = [find(DEP[a], horario=h, minutos_depois=15.0) for h in HORAS]
        W, H = 800, 194
        fig = figure(W, H)
        ax = axes(fig, W, H, 50, 6, 740, 160, 35, 60, 5, lambda v: f"{br(v, 0)}%")
        cat_axis(ax, labels, show=i == 1)
        xs = range(len(HORAS))
        ax.errorbar(xs, [r["continua_pct"] for r in rows], yerr=[r["margem_pct"] for r in rows], fmt="none",
                    ecolor=c(INK), elinewidth=1.25, capsize=3, capthick=1.25, zorder=2)
        ax.plot(xs, [r["normal_continua_pct"] for r in rows], linestyle="none", marker="_", markersize=14,
                markeredgewidth=2.5, color=c(MUTED), zorder=3)
        ax.plot(xs, [r["continua_pct"] for r in rows], linestyle="none", marker="o", markersize=8,
                color=c(col), markeredgecolor=c(INK), markeredgewidth=0.75, zorder=4)
        picture(s, fig, 50, y + 18, W, H, f"slide5_{a}_continua")
    legend(s, 60, 612, [("err", PURPLE, "pico WDO (± margem 95%)"), ("err", ORANGE, "pico WIN (± margem 95%)"),
                        ("tick", MUTED, "minuto comum da mesma hora")], gap=16)
    text(s, 50, 640, 800, 20, "Fonte: pt2/reports/depois_*.csv · margem = 1,96 × √(0,25 / casos), cerca de ±3 p.p.",
         size=9, color=MUTED)
    side(s, 880, 112, 350, "O que o preço faz depois", [
        [B("Sem direção: "), N("15 min depois, sobe em 47% a 55% dos pregões (WDO) e 46% a 52% (WIN). Mediana perto de zero.")],
        [B("Continuar = minuto comum: "), N("somando os horários, a diferença é de +0,0 a +0,4 p.p., dentro da margem de ±0,8.")],
        [B("Mas o movimento é maior: "), N("a faixa de 80% dos dias é mais larga que a normal em 13 de 18 horários (WDO) e 12 de 18 (WIN).")],
    ], "O pico de volume muda o tamanho do movimento, não a direção.",
        "A mediana depois do pico é menor que 1 tick na maioria dos horários.", box_y=370)


def slide6(prs):
    s = frame(prs, 6, "Etapa 4 · Apresentação de 12/11",
              "Separando dias de alta e de baixa, o movimento aparece e não reverte", NOTES[6])
    chart_head(s, 50, 102, 1180, "Preço em volta do minuto de maior volume do pregão, de T−1 a T+15",
               "mediana da variação do fechamento contra T−1 (1 minuto antes do pico), em pontos, no mesmo pregão · dia de alta = último fechamento acima da primeira abertura")
    # limites múltiplos do passo, senão as marcas do eixo saem tortas (−6,5; −4,5…)
    cfg = [("wdo", "WDO · mini dólar", "pontos (1 pt = R$ 10/contrato)", 2, (-8, 6), 2),
           ("win", "WIN · mini índice", "pontos (1 pt = R$ 0,20/contrato)", 1, (-150, 150), 50),
           ("dolarizado", "Índice dolarizado (1000 × WIN ÷ WDO)", "pontos do Ibovespa em US$", 1, (-40, 40), 10)]
    offs = [-1.0, 0.0, 3.0, 5.0, 10.0, 15.0]
    cats = ["T−1", "T (pico)", "T+3", "T+5", "T+10", "T+15"]
    for j, (k, name, unit, dec, lim, unit_step) in enumerate(cfg):
        x = 50 + j * 400
        text(s, x, 152, 380, 20, name, size=11.5, bold=True)
        vals = {t: [find(P30[(k, t)], grupo="DIA", offset=o)["mediana_pts"] for o in offs]
                for t in ("alta", "baixa", "todos")}
        W, H = 380, 360
        fig = figure(W, H)
        ax = axes(fig, W, H, 62, 10, 308, 300, lim[0], lim[1], unit_step, fmt_int)
        cat_axis(ax, cats)
        axis_title(ax, unit)
        xs = range(len(cats))
        ax.axhline(0, color=c(INK2), linewidth=0.75, zorder=1)
        ax.plot(xs, vals["todos"], color=c(MUTED), linewidth=1.75, linestyle=(0, (4, 3)), marker="o", markersize=5,
                markeredgecolor=c(INK), markeredgewidth=0.75, zorder=2)
        for t, col, txt, dy in (("alta", PURPLE, PURPLE, 7), ("baixa", ORANGE, ORANGE_TXT, -7)):
            ax.plot(xs, vals[t], color=c(col), linewidth=2.5, marker="o", markersize=8,
                    markeredgecolor=c(INK), markeredgewidth=0.75, zorder=3)
            for i in range(1, 6):
                ax.annotate(br(vals[t][i], dec, True), (i, vals[t][i]), xytext=(0, dy), textcoords="offset points",
                            ha="center", va="bottom" if dy > 0 else "top", fontsize=8.5, fontweight="bold",
                            color=c(txt), zorder=4)
        picture(s, fig, x, 174, W, H, f"slide6_{k}")
        n = lambda t: int(find(P30[(k, t)], grupo="DIA", offset=-1.0)["n"])
        text(s, x + 62, 540, 318, 16, f"n: {n('alta')} dias de alta · {n('baixa')} de baixa", size=9, color=INK2)
    legend(s, 112, 566, [("line", PURPLE, "dias de alta (fechamento > abertura)"), ("line", ORANGE, "dias de baixa"),
                         ("dash", MUTED, "todos os dias juntos (alta e baixa se anulam)")], gap=26)
    strip(s, [
        (WHITE, [N("O grosso do movimento acontece "), B("no próprio minuto do pico"), N("; há um respiro em T+3, mas não há reversão até T+15.")]),
        (WHITE, [N("O efeito é maior "), B("de manhã"), N(" (9h–11h) e encolhe depois das 13h (WDO: 0 a 1 tick). No dolarizado, ainda avança até T+15.")]),
        (MINT, [B("Atenção: só se sabe se o dia foi de alta no fechamento. É descritivo, não é um sinal operável.")]),
    ])


def slide7(prs):
    s = frame(prs, 7, "Etapa 4 · 12/11 · e síntese", "Estrangeiro e pessoa física andam em sentidos opostos", NOTES[7])
    e = [r["estrangeiro"] for r in FLUXO]
    p = [r["pessoa_fisica"] for r in FLUXO]
    n = len(e)
    me, mp = sum(e) / n, sum(p) / n
    cov = sum((a - me) * (b - mp) for a, b in zip(e, p))
    corr = cov / (sum((a - me) ** 2 for a in e) * sum((b - mp) ** 2 for b in p)) ** 0.5
    opostos = sum(1 for a, b in zip(e, p) if a * b < 0) / n * 100
    ini = "/".join(reversed(FLUXO[0]["data"].split("-")))
    chart_head(s, 50, 108, 740, "Saldo acumulado de compras − vendas na B3, por tipo de investidor",
               f"fluxo diário somado desde {ini}, em R$ bilhões · {n} pregões · correlação diária {br(corr, 2)}, "
               f"sinais opostos em {br(opostos, 0)}% dos dias")
    ce = cp = 0.0
    acc_e, acc_p, cats = [], [], []
    for r in FLUXO:
        ce += r["estrangeiro"]
        cp += r["pessoa_fisica"]
        acc_e.append(ce / 1000)
        acc_p.append(cp / 1000)
        y, m, d = r["data"].split("-")
        cats.append(f"{d}/{m}/{y[2:]}")
    W, H = 740, 420
    fig = figure(W, H)
    ax = axes(fig, W, H, 60, 10, 610, 360, -20, 80, 20, fmt_int)
    axis_title(ax, "saldo acumulado (R$ bilhões)")
    ax.set_xlim(-0.5, n - 0.5)
    ticks = list(range(0, n, 42))
    ax.set_xticks(ticks)
    ax.set_xticklabels([cats[i] for i in ticks], fontsize=9.5, color=c(INK))
    ax.axhline(0, color=c(INK2), linewidth=0.75, zorder=1)
    ax.plot(range(n), acc_e, color=c(PURPLE), linewidth=2.5, zorder=3)
    ax.plot(range(n), acc_p, color=c(ORANGE), linewidth=2.5, zorder=3)
    picture(s, fig, 50, 166, W, H, "slide7_fluxo")
    imax = max(range(n), key=lambda i: acc_e[i])
    d_pico = cats[imax].split("/")
    meses = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    legend(s, 60, 594, [
        ("line", PURPLE, f"estrangeiro: pico R$ {br(acc_e[imax], 0)} bi ({meses[int(d_pico[1]) - 1]}/{d_pico[2]}), "
                         f"hoje R$ {br(acc_e[-1], 0)} bi"),
        ("line", ORANGE, f"pessoa física: hoje R$ {br(acc_p[-1], 0)} bi"),
    ], gap=24)
    text(s, 50, 622, 740, 30, "Fonte: dadosdemercado.com.br/fluxo (página pública) · período nov/2025–nov/2026, sem sobreposição "
         "com os candles, por isso não foi cruzado com o preço", size=9, color=MUTED)
    side(s, 820, 112, 410, "Conclusões do projeto", [
        [B("Dados prontos e auditados"), N(", com hold-out intacto para um teste final honesto.")],
        [B("Volume alto, sozinho, não identifica o big player "), N("nem prevê direção (Gate 1: no-go).")],
        [B("O pico de volume diz quanto o preço vai mexer"), N(", não para onde.")],
        [N("Separar alta e baixa mostra que o pico acompanha a tendência do dia, mas isso só se vê depois do fechamento.")],
    ], "Próximos passos: dados negócio a negócio (quem agrediu), fluxo de investidores no mesmo período do preço, "
       "e um teste único no hold-out.", box_y=390)


# ---------------------------------------------------------------- falas sugeridas (anotações)
NOTES = {
    1: "Boa tarde. Nosso projeto é o Big Player: entender se dá para perceber, nos dados de mini dólar e mini índice, a atuação "
       "de quem opera muito e move o preço, e seguir esse movimento, como um carro que pega o vácuo do da frente. Hoje vamos "
       "resumir tudo o que fizemos: a preparação dos dados, o teste estatístico da primeira hipótese, a análise do preço nos "
       "picos de volume que o professor pediu, e a última etapa, com dias de alta e de baixa e o fluxo de investidores. São "
       "cerca de cinco anos de candles de 1 minuto, e o último ano de cada ativo ficou guardado, sem uso, para um teste final.\n\n"
       "Transição: \"Começando pelos dados.\"",
    2: "Usamos candles de 1 minuto exportados do MetaTrader: cerca de 575 mil no mini dólar e 618 mil no mini índice. Antes de "
       "qualquer análise, separamos o último ano de cada ativo, a parte hachurada, e trancamos esses dados no código: eles só "
       "serão abertos uma vez, para validar o resultado final. Depois conferimos a qualidade: não há nulos nem duplicatas e os "
       "preços estão sempre no tick certo. O problema sério foram os buracos, em rosa: o maior deixa três meses e meio sem dado "
       "em 2023. Decidimos não apagar nada, só marcar cada candle com o calendário da B3, os feriados, o trecho contínuo e o dia "
       "de rolagem de contrato. E um achado que guiou o resto: a manhã negocia cerca de três vezes o volume da tarde, então todo "
       "indicador de volume precisou ser comparado com o mesmo horário de outros dias.\n\n"
       "Transição: \"Com a base pronta, testamos a hipótese principal.\"",
    3: "A hipótese era: quando o volume dispara, o preço continua na direção daquele minuto. Escrevemos as regras antes de olhar "
       "o resultado: seis definições de evento, cinco horizontes de tempo e os dois ativos. A entrada é sempre no candle "
       "seguinte, para não usar informação do futuro, e o resultado é comparado com minutos comuns parecidos. O gráfico mostra o "
       "horizonte de 15 minutos. Quase todos os efeitos estão perto de zero ou negativos, e as barras cruzam o zero. O único "
       "positivo foi o A1, a pausa com volume, no mini dólar: +1,3 bps. Mas, com 46 testes, o limite corrigido de significância "
       "é bem mais exigente, e ele não passou. Testamos o A1 uma única vez no mini índice para confirmar, e não confirmou. Então "
       "a conclusão do Gate 1 é no-go: com candle de 1 minuto, não há sinal de continuação. E mesmo um efeito de 1 bp seria menor "
       "que o custo de entrar e sair.\n\n"
       "Transição: \"A partir daqui, a pedido do professor, voltamos ao básico: olhar o preço nos picos, em pontos.\"",
    4: "Olhamos todos os horários redondos, de 9h30 às 17h30. No painel de cima, o volume: de manhã, os picos chegam a 4 vezes o "
       "volume da tarde, e os maiores coincidem com divulgações de dados dos Estados Unidos, como inflação e emprego, às 9h30 ou "
       "10h30 de Brasília, dependendo do horário de verão americano. No painel de baixo, comparamos cada dia com ele mesmo: em "
       "que porcentagem dos pregões o preço andou mais no minuto do pico do que no minuto antes. No mini índice, isso acontece "
       "acima do acaso em 15 de 17 horários, chegando a 65% às 10h. No mini dólar, em 7 de 17. E no minuto antes do pico, a "
       "variação típica é zero: o preço não avisa para que lado vai.\n\n"
       "Transição: \"Se o pico mexe mais o preço, a pergunta seguinte é: depois dele, o preço segue na mesma direção?\"",
    5: "Aqui medimos em que porcentagem dos pregões o preço, 15 minutos depois, está do mesmo lado do movimento do minuto de pico. "
       "O ponto importante é comparar com o traço cinza, que é a mesma conta feita em minutos comuns da mesma hora. Em quase "
       "todos os horários, a bolinha fica em cima do traço, dentro da margem de erro. Somando todos os horários, a diferença é de "
       "no máximo 0,4 ponto percentual. Ao mesmo tempo, a faixa onde o preço termina é mais larga depois do pico. Ou seja: o pico "
       "muda o tamanho do movimento, não a direção.\n\n"
       "Transição: \"Na última etapa, o professor pediu para separar os dias de alta e de baixa.\"",
    6: "Aqui o T é o minuto de maior volume do pregão, e acompanhamos o preço até 15 minutos depois. A linha cinza mostra todos os "
       "dias juntos: fica perto de zero porque metade dos dias sobe e metade cai, e uma coisa anula a outra. Separando, o padrão "
       "aparece: nos dias de alta, o mini índice sobe 112 pontos no próprio minuto do pico; nos de baixa, cai 110. Há um pequeno "
       "respiro em T+3, mas o preço não reverte, e no índice dolarizado o movimento ainda cresce até T+15. Por janela de 30 "
       "minutos, o efeito é maior de manhã. Mas atenção: só sabemos se o dia foi de alta no fechamento. Então isso descreve o que "
       "acontece, não é um sinal que dê para operar.\n\n"
       "Transição: \"Por fim, olhamos quem está do outro lado: o fluxo por tipo de investidor.\"",
    7: "Este é o fluxo diário de compras menos vendas na B3, com dados públicos do último ano. O estrangeiro chegou a acumular "
       "cerca de 70 bilhões em abril e devolveu boa parte depois, enquanto a pessoa física foi no sentido contrário: em 68% dos "
       "dias, um compra enquanto o outro vende. Esse período não coincide com os nossos candles, então não cruzamos com o preço; "
       "fica como próximo passo. Para fechar: os dados estão prontos e auditados, com o último ano guardado. Volume alto, "
       "sozinho, não identifica o big player nem prevê direção. O pico de volume diz quanto o preço vai mexer, não para onde. "
       "Para separar o big player do resto do mercado, o próximo passo é usar dados negócio a negócio, que mostram quem agrediu. "
       "Obrigado, ficamos à disposição.",
}


def main() -> None:
    prs = Presentation()
    prs.slide_width, prs.slide_height = px(1280), px(720)
    prs.core_properties.title = "Big Player · apresentação final"
    prs.core_properties.author = "Gabriel Camargo Silva, Ícaro Alves de Sá, João Gabriel Abreu Soares"
    for fn in (slide1, slide2, slide3, slide4, slide5, slide6, slide7):
        fn(prs)
    prs.save(OUT)
    print(f"ok: {OUT}")


if __name__ == "__main__":
    main()
