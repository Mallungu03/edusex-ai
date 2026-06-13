"""Assistente de relatorios com IA simbolica.

O gerador transforma estatisticas e insights em texto narrativo. Para exportar
sem dependencias pesadas, PDF e DOCX sao produzidos com formatos minimos
validos, suficientes para download local e demonstracao academica.
"""

from __future__ import annotations

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from services.data_insights import top_insights


def generate_report_text(surveys: list[dict]) -> str:
    """Gera analise textual automatica a partir dos inqueritos."""

    insights = top_insights(surveys)
    lines = [
        "Relatorio Inteligente EduSex AI",
        "",
        f"O Sex Education Awareness Score nacional e {insights['awarenessScore']} em 100.",
        "A analise automatica demonstra os seguintes pontos principais:",
    ]
    lines.extend(f"- {item}" for item in insights["topInsights"])
    lines.append("")
    lines.append("Principais problemas identificados:")
    lines.extend(f"- {item}" for item in insights["problems"])
    lines.append("")
    lines.append("Oportunidades de intervencao:")
    lines.extend(f"- {item}" for item in insights["opportunities"])
    lines.append("")
    lines.append("Recomendacoes prioritarias:")
    lines.extend(f"- {item['title']} ({item['demand']} ocorrencias)" for item in insights["topRecommendations"])
    return "\n".join(lines)


def export_report(report_text: str, format_name: str) -> tuple[bytes, str, str]:
    """Exporta relatorio em txt, pdf ou docx."""

    if format_name == "docx":
        return _docx_bytes(report_text), "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "edusex_relatorio.docx"
    if format_name == "pdf":
        return _pdf_bytes(report_text), "application/pdf", "edusex_relatorio.pdf"
    return report_text.encode("utf-8"), "text/plain; charset=utf-8", "edusex_relatorio.txt"


def _docx_bytes(text: str) -> bytes:
    """Cria um DOCX minimo usando a especificacao Open XML."""

    def esc(value: str) -> str:
        return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    paragraphs = "".join(f"<w:p><w:r><w:t>{esc(line) or ' '}</w:t></w:r></w:p>" for line in text.splitlines())
    document = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{paragraphs}</w:body></w:document>"""
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>""")
        docx.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>""")
        docx.writestr("word/document.xml", document)
    return buffer.getvalue()


def _pdf_bytes(text: str) -> bytes:
    """Cria um PDF simples com texto monoespacado."""

    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    lines = safe.splitlines()[:55]
    content = "BT /F1 10 Tf 50 800 Td " + " T* ".join(f"({line[:95]})" for line in lines) + " ET"
    objects = [
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj",
        "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
        f"5 0 obj << /Length {len(content.encode('latin-1', 'ignore'))} >> stream\n{content}\nendstream endobj",
    ]
    pdf = "%PDF-1.4\n" + "\n".join(objects) + "\ntrailer << /Root 1 0 R >>\n%%EOF"
    return pdf.encode("latin-1", "ignore")
