"""Regenera a figura e o PDF da etapa 1; requer requirements-relatorio.txt.

A fonte editável é docs/relatorios/etapa-1-wiki-vote.md. O renderizador aceita
os elementos Markdown usados nesse documento, incluindo quebras de página
explícitas. Não executa a análise nem altera dados ou tabelas de auditoria.
"""

from collections import Counter
import csv
from html import escape
import json
from pathlib import Path
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table,
    TableStyle,
)

RAIZ = Path(__file__).resolve().parents[1]
FONTE = RAIZ / "docs/relatorios/etapa-1-wiki-vote.md"
PDF = FONTE.with_suffix(".pdf")
FIGURA = RAIZ / "docs/figuras/distribuicao_graus.png"


def gerar_figura():
    """CCDF empírica: conta graus >= x com todos os vértices no denominador."""
    with (RAIZ / "resultados/etapa-1/graus.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.1), layout="constrained")
    for ax, key, label, color in zip(
        axes, ("grau_entrada", "grau_saida"), ("entrada", "saída"),
        ("#245b80", "#bc571c"),
    ):
        counts = Counter(int(row[key]) for row in rows)
        remaining = len(rows) - counts[0]
        x, y = [], []
        for degree in sorted(k for k in counts if k > 0):
            x.append(degree)
            y.append(remaining / len(rows))
            remaining -= counts[degree]
        ax.step(x, y, where="pre", color=color, linewidth=1.6)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_title(f"Grau de {label} acumulado", fontsize=10)
        ax.set_xlabel(f"Grau de {label}", fontsize=9)
        ax.set_ylabel("Fração com grau ≥ x", fontsize=9)
        ax.grid(alpha=0.2)
        ax.tick_params(labelsize=8)
    FIGURA.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURA, dpi=180)
    plt.close(fig)


def registrar_fontes():
    fonts = Path(matplotlib.get_data_path()) / "fonts/ttf"
    for name, filename in (
        ("Relatorio", "DejaVuSans.ttf"),
        ("RelatorioBold", "DejaVuSans-Bold.ttf"),
        ("RelatorioMono", "DejaVuSansMono.ttf"),
    ):
        pdfmetrics.registerFont(TTFont(name, str(fonts / filename)))
    pdfmetrics.registerFontFamily("Relatorio", normal="Relatorio", bold="RelatorioBold")


def inline(text):
    """Escapa o texto e converte somente links, negrito e código inline."""
    text = escape(text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<link href="\2" color="#245b80">\1</link>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return re.sub(r"`([^`]+)`", r'<font name="RelatorioMono" size="8.3">\1</font>', text)


def gerar_pdf():
    registrar_fontes()
    body = ParagraphStyle("Texto", fontName="Relatorio", fontSize=9.5, leading=13.1, spaceAfter=7)
    heading = ParagraphStyle("Secao", parent=body, fontName="RelatorioBold", fontSize=12, leading=16, spaceBefore=12, spaceAfter=7, keepWithNext=True)
    title = ParagraphStyle("Titulo", parent=heading, fontSize=19, leading=24, spaceBefore=0, spaceAfter=16)
    cell = ParagraphStyle("Celula", parent=body, fontSize=8.6, leading=11.8, spaceAfter=0)
    code = ParagraphStyle("Codigo", parent=body, fontName="RelatorioMono", fontSize=8.3, leading=12)
    audit = json.loads((RAIZ / "resultados/etapa-1/auditoria.json").read_text(encoding="utf-8"))
    source = FONTE.read_text(encoding="utf-8").replace("{{python_auditoria}}", audit["python"])
    source = source.replace("{{tempo_auditoria}}", f'{audit["tempo_auditoria_segundos"]:.2f}'.replace(".", ","))
    lines = source.splitlines()
    width = A4[0] - 104
    story = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line == "<!-- pagebreak -->":
            story.append(PageBreak())
        elif line.startswith("# "):
            story.append(Paragraph(inline(line[2:]), title))
        elif line.startswith("## "):
            story.append(Paragraph(inline(line[3:]), heading))
        elif line.startswith("```"):
            block = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                block.append(lines[i])
                i += 1
            story.append(Preformatted("\n".join(block), code))
        elif line.startswith("| "):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                values = [value.strip() for value in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", value) for value in values):
                    if not rows:
                        values = [f"**{value}**" for value in values]
                    rows.append([Paragraph(inline(value), cell) for value in values])
                i += 1
            cols = len(rows[0])
            widths = [width / cols] * cols
            if cols == 3 and "Critério" in line:
                widths = [width * .22, width * .56, width * .22]
            table = Table(rows, colWidths=widths, hAlign="LEFT", repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf0f4")),
                ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#8b99a3")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.extend([table, Spacer(1, 9)])
            continue
        elif line.startswith("!["):
            match = re.fullmatch(r"!\[.*\]\((.+)\)", line)
            figure = Image(str(FONTE.parent / match[1]))
            figure.drawHeight *= width / figure.drawWidth
            figure.drawWidth = width
            story.extend([figure, Spacer(1, 8)])
        else:
            paragraph = [line]
            while i + 1 < len(lines) and lines[i + 1].strip():
                i += 1
                paragraph.append(lines[i].strip())
            story.append(Paragraph("<br/>".join(inline(p) for p in paragraph), body))
        i += 1

    def rodape(canvas, document):
        canvas.saveState()
        canvas.setFont("Relatorio", 8)
        canvas.setFillColor(colors.HexColor("#53616b"))
        canvas.drawRightString(A4[0] - 52, 30, f"GCC118 | {document.page}")
        canvas.restoreState()

    document = SimpleDocTemplate(
        str(PDF), pagesize=A4, rightMargin=52, leftMargin=52,
        topMargin=45, bottomMargin=45,
        title="Etapa 1 - Análise exploratória da Wiki-Vote",
        author="Kauê de Oliveira Silva",
    )
    document.build(story, onFirstPage=rodape, onLaterPages=rodape)


if __name__ == "__main__":
    gerar_figura()
    gerar_pdf()
    print(f"Figura: {FIGURA}")
    print(f"Relatório: {PDF}")
