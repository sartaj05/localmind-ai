from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "LocalMind_AI_Deployment_Setup_Guide.pdf"

NAVY = colors.HexColor("#17365D")
BLUE = colors.HexColor("#1F4E79")
LIGHT_BLUE = colors.HexColor("#D9EAF7")
PALE_BLUE = colors.HexColor("#F3F8FC")
GRAY = colors.HexColor("#666666")
GRID = colors.HexColor("#D9D9D9")


class NumberedCanvas:
    def __init__(self, canvas, doc):
        self.canvas = canvas
        self.doc = doc

    def draw(self):
        self.canvas.saveState()
        self.canvas.setFont("Helvetica", 8)
        self.canvas.setFillColor(GRAY)
        self.canvas.drawCentredString(A4[0] / 2, 10 * mm, f"LocalMind AI Deployment Setup Guide  |  Page {self.doc.page}")
        self.canvas.restoreState()


def footer(canvas, doc):
    NumberedCanvas(canvas, doc).draw()


def P(text, style):
    return Paragraph(text, style)


def make_table(headers, rows, widths):
    data = [[P(str(x), styles["TableHeader"]) for x in headers]]
    for row in rows:
        data.append([P(str(x), styles["TableBody"]) for x in row])
    table = Table(data, colWidths=[w * mm for w in widths], repeatRows=1, hAlign="LEFT")
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.45, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), PALE_BLUE))
    table.setStyle(TableStyle(style))
    return table


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="DocTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=22, leading=26, textColor=NAVY, spaceAfter=5))
styles.add(ParagraphStyle(name="Subtitle", parent=styles["Normal"], fontName="Helvetica-Oblique", fontSize=10.5, leading=14, textColor=GRAY, spaceAfter=14))
styles.add(ParagraphStyle(name="H1Custom", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=NAVY, spaceBefore=12, spaceAfter=6, keepWithNext=True))
styles.add(ParagraphStyle(name="H2Custom", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11.5, leading=14, textColor=BLUE, spaceBefore=8, spaceAfter=4, keepWithNext=True))
styles.add(ParagraphStyle(name="BodyCustom", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.4, leading=13, textColor=colors.HexColor("#222222"), spaceAfter=6))
styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.4, leading=11, textColor=colors.HexColor("#222222"), spaceAfter=3))
styles.add(ParagraphStyle(name="BulletCustom", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.2, leading=12.5, leftIndent=12, firstLineIndent=-7, bulletIndent=0, spaceAfter=3))
styles.add(ParagraphStyle(name="CodeCustom", parent=styles["Code"], fontName="Courier", fontSize=8.1, leading=10.2, backColor=colors.HexColor("#F4F6F8"), borderColor=GRID, borderWidth=0.4, borderPadding=5, spaceBefore=3, spaceAfter=7))
styles.add(ParagraphStyle(name="TableHeader", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=8.2, leading=10.2, textColor=colors.white))
styles.add(ParagraphStyle(name="TableBody", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.1, leading=10.5, textColor=colors.HexColor("#222222")))


def bullet(text):
    return P("&#8226; " + text, styles["BulletCustom"])


story = []
story.append(P("LocalMind AI Deployment Setup Guide", styles["DocTitle"]))
story.append(P("Local development setup, environment configuration, production shape, and operational checks", styles["Subtitle"]))
story.append(P("This guide is based on the current repository. The project is configured for a local-first Django, React, Ollama, and ChromaDB workflow. Follow the local setup for development, then complete the production checklist before exposing the application publicly.", styles["BodyCustom"]))

story.append(P("1 Prerequisites", styles["H1Custom"]))
for text in [
    "Python 3.11 or newer with a working virtual environment.",
    "Node.js 18 or newer and npm.",
    "Ollama installed and running on the local machine or a private reachable host.",
    "An Ollama model pulled before first use, for example <font name='Courier'>ollama pull phi3</font>.",
    "Optional scanned-PDF support: Tesseract OCR and Poppler.",
    "For production: PostgreSQL, HTTPS reverse proxy, durable file storage, and durable Chroma or another vector store.",
]:
    story.append(bullet(text))

story.append(P("2 Environment Variables", styles["H1Custom"]))
story.append(make_table(["Variable", "Local example", "Purpose"], [
    ("SECRET_KEY", "replace-with-random-secret", "Django signing and security key"),
    ("DEBUG", "True locally; False in production", "Debug mode switch"),
    ("ALLOWED_HOSTS", "127.0.0.1,localhost", "Allowed host names"),
    ("OLLAMA_BASE_URL", "http://localhost:11434", "Ollama API address"),
    ("DEFAULT_AI_MODEL", "phi3", "Default local model"),
    ("POPPLER_PATH", "optional Windows path", "Poppler path for OCR conversion"),
    ("TESSERACT_CMD", "optional tesseract.exe path", "Tesseract executable for OCR"),
], [34, 55, 81]))
story.append(Spacer(1, 5))
story.append(P("Create a .env file at the repository root. Never commit .env or production secrets.", styles["BodyCustom"]))

story.append(P("3 Windows Local Setup", styles["H1Custom"]))
setup_lines = [
    "cd E:\\path\\to\\localmind-ai",
    "python -m venv venv",
    ".\\venv\\Scripts\\Activate.ps1",
    "python -m pip install -r requirements.txt",
    "copy .env.example .env",
    "python manage.py makemigrations",
    "python manage.py migrate",
    "python manage.py createsuperuser",
    "python manage.py runserver",
]
story.append(P("<br/>".join(line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") for line in setup_lines), styles["CodeCustom"]))
story.append(P("Open a second terminal for the frontend:", styles["BodyCustom"]))
frontend_lines = [
    "cd frontend",
    "npm install",
    "npm run dev",
]
story.append(P("<br/>".join(frontend_lines), styles["CodeCustom"]))
story.append(P("Open the Vite URL, normally http://localhost:5173. The Django API is normally available at http://127.0.0.1:8000.", styles["BodyCustom"]))
story.append(P("Migration note", styles["H2Custom"]))
story.append(P("The repository currently ignores migration Python files. For team and production deployments, generate, review, and commit migrations so every environment applies the same schema history. Do not rely on a developer machine to recreate the schema during deployment.", styles["BodyCustom"]))

story.append(P("4 Ollama Setup", styles["H1Custom"]))
story.append(P("Start Ollama, pull the configured model, and confirm the local API is available:", styles["BodyCustom"]))
story.append(P("ollama serve<br/>ollama pull phi3<br/>ollama list", styles["CodeCustom"]))
story.append(P("The application calls the Ollama /api/generate and /api/tags endpoints. The selected model must exist on the host configured by OLLAMA_BASE_URL.", styles["BodyCustom"]))

story.append(P("5 First Run Smoke Test", styles["H1Custom"]))
for text in [
    "Open /api/docs/ and confirm the OpenAPI page loads.",
    "Register a user, log in, refresh a token, and open the profile endpoint.",
    "Check the AI health endpoint and model listing.",
    "Create a session, send a prompt, refresh the page, and verify message persistence.",
    "Upload a small PDF, TXT, or DOCX; build the knowledge base; ask a grounded question; and confirm sources are returned.",
    "Create a prompt template, reuse it in chat, inspect dashboard counts, and test a TXT or JSON export.",
]:
    story.append(bullet(text))

story.append(PageBreak())
story.append(P("6 Production Deployment Shape", styles["H1Custom"]))
story.append(P("The current codebase is appropriate for local development. A public deployment should use the following shape:", styles["BodyCustom"]))
story.append(make_table(["Component", "Recommended shape", "Required controls"], [
    ("Web API", "Django ASGI served by Uvicorn behind Nginx or a managed proxy", "HTTPS, health checks, timeouts, process restart"),
    ("Frontend", "npm run build served by CDN or Nginx", "API base URL and immutable asset caching"),
    ("Database", "PostgreSQL", "Backups, migrations, least-privilege account"),
    ("AI", "Private Ollama host with models pre-pulled", "Capacity, timeouts, model health, access control"),
    ("Files", "Durable object or volume storage", "Size limits, validation, backups, retention"),
    ("Vectors", "Durable Chroma volume or managed vector service", "Backup, user filters, rebuild procedure"),
    ("Jobs", "Redis plus Celery for indexing and title generation", "Retries, idempotency, status tracking"),
], [24, 75, 71]))
story.append(Spacer(1, 6))
story.append(P("A production process should never depend on a laptop-local SQLite file, an ephemeral Chroma directory, or an Ollama endpoint exposed directly to the public internet.", styles["BodyCustom"]))

story.append(P("7 Production Checklist", styles["H1Custom"]))
for text in [
    "Set DEBUG=False, a strong SECRET_KEY, exact ALLOWED_HOSTS, exact CORS origins, HTTPS, secure proxy headers, and secure cookies.",
    "Commit and apply migrations from a clean database before deployment.",
    "Replace SQLite for multi-user workloads and configure database backups.",
    "Persist media and vector data; test restore, deletion, and retention procedures.",
    "Enforce maximum upload size, allowed extensions, file validation, and private file access.",
    "Add tests, lint, frontend build checks, structured logs, request IDs, health probes, and error monitoring.",
    "Set Ollama resource limits and user/workspace rate limits; keep the AI host private.",
    "Review token storage, CORS, CSRF, security headers, admin access, ownership filters, and deletion behavior.",
]:
    story.append(bullet(text))

story.append(P("8 Troubleshooting", styles["H1Custom"]))
story.append(make_table(["Symptom", "Likely cause", "Action"], [
    ("Django import error", "Environment is inactive or dependencies are missing", "Activate venv and install requirements"),
    ("Ollama unavailable", "Service stopped, URL wrong, or model missing", "Start Ollama, check URL, run ollama list/pull"),
    ("RAG has no context", "Document is empty, unsupported, or not indexed", "Check text extraction and build status"),
    ("Scanned PDF has no text", "OCR tools are absent or paths unset", "Install Tesseract and Poppler and set paths"),
    ("Frontend cannot call API", "Backend, port, or CORS mismatch", "Check API URL and CORS origins"),
    ("Clean schema fails", "Migrations are not committed", "Generate and commit migrations"),
], [42, 61, 67]))

story.append(P("9 Launch Gate", styles["H1Custom"]))
story.append(P("LocalMind AI is ready for a portfolio demo or controlled beta after the core smoke test. Before public launch, complete clean migrations, production settings, automated tests, durable storage, upload security, monitoring, and robust Ollama failure handling. Complete workspace APIs, permissions, and UI before marketing the product as a collaboration platform.", styles["BodyCustom"]))

doc = BaseDocTemplate(str(OUT), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=16 * mm, bottomMargin=18 * mm, title="LocalMind AI Deployment Setup Guide", author="LocalMind AI")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=footer)])
doc.build(story)
print(OUT)
