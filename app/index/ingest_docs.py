import os
import uuid
import time
from pathlib import Path
from dotenv import load_dotenv
from pypdf import PdfReader
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI

load_dotenv()

search_client = SearchClient(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name=os.getenv("AZURE_SEARCH_INDEX"),
    credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_ADMIN_KEY"))
)

aoai = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
)

emb_deployment = os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT")
docs_dir = Path(r"C:\Projektarbeiten\agentic-ai-mfg\docs\basic-docs")

def embed(text: str, max_retries: int = 3):
    """Embedding mit Retry-Logik"""
    for attempt in range(max_retries):
        try:
            r = aoai.embeddings.create(model=emb_deployment, input=text)
            return r.data[0].embedding
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"Embedding-Fehler (Versuch {attempt + 1}/{max_retries}): {e}")
                print(f"Warte {wait_time}s vor erneutem Versuch...")
                time.sleep(wait_time)
            else:
                print(f"Embedding fehlgeschlagen nach {max_retries} Versuchen: {e}")
                raise

def chunk_text(text: str, chunk_size: int = 1800, overlap: int = 200):
    text = " ".join(text.split())
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + chunk_size, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks

def extract_pdf_text(pdf_path: Path):
    """Extrahiert Text aus PDF mit Seitenzuordnung"""
    reader = PdfReader(str(pdf_path))
    pages_data = []
    
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages_data.append({
                "page_num": page_num,
                "text": text
            })
    
    return pages_data

pdfs = sorted(docs_dir.glob("*.pdf"))
if not pdfs:
    raise RuntimeError(f"Keine PDFs gefunden in: {docs_dir}")

batch = []
for pdf_path in pdfs:
    pages_data = extract_pdf_text(pdf_path)
    title = pdf_path.stem
    source = pdf_path.name

    for page_info in pages_data:
        page_num = page_info["page_num"]
        page_text = page_info["text"]
        
        # Chunking pro Seite
        chunks = chunk_text(page_text, chunk_size=1800, overlap=200)
        
        for chunk_idx, chunk_content in enumerate(chunks, start=1):
            vec = embed(chunk_content)
            batch.append({
                "id": str(uuid.uuid4()),
                "title": title,
                "source": source,
                "content": chunk_content,
                "chunk": chunk_idx,
                "page": page_num,  # Seitenzahl hinzugefügt!
                "contentVector": vec
            })

            if len(batch) >= 50:
                res = search_client.upload_documents(documents=batch)
                ok = sum(1 for r in res if r.succeeded)
                print(f"Uploaded {ok}/{len(res)}")
                batch = []

if batch:
    res = search_client.upload_documents(documents=batch)
    ok = sum(1 for r in res if r.succeeded)
    print(f"Uploaded {ok}/{len(res)}")
