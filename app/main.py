import hashlib, os, shutil, uuid
from pathlib import Path
from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from .config import settings
from .database import Base, engine, get_db
from .models import Paper
from .services.extractor import extract_papers, write_split

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Question Paper Intelligence API", version="1.0.0")
app.mount("/app", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="app")

def serialize(p: Paper):
    return {"id":p.id,"title":p.title,"subject":p.subject,"courseCode":p.course_code,"department":p.department,"semester":p.semester,"year":p.year,"month":p.month,"marks":p.marks,"duration":p.duration,"pageCount":p.page_count,"createdAt":p.created_at.isoformat()}

@app.get("/api/health")
def health(): return {"status":"healthy"}

@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)):
    total = db.query(func.count(Paper.id)).scalar() or 0
    return {"totalPapers":total,"subjects":db.query(func.count(func.distinct(Paper.subject))).scalar() or 0,"departments":db.query(func.count(func.distinct(Paper.department))).scalar() or 0,"years":db.query(func.count(func.distinct(Paper.year))).scalar() or 0,"storageBytes":sum(os.path.getsize(p.pdf_path) for p in db.query(Paper).all() if os.path.exists(p.pdf_path)),"recent":[serialize(p) for p in db.query(Paper).order_by(Paper.created_at.desc()).limit(5)]}

@app.get("/api/papers")
def papers(q: str = "", department: str = "", year: str = "", semester: str = "", db: Session = Depends(get_db)):
    query = db.query(Paper)
    if q:
        like = f"%{q}%"; query = query.filter(or_(Paper.subject.ilike(like), Paper.course_code.ilike(like), Paper.text_content.ilike(like)))
    for field, value in ((Paper.department, department), (Paper.year, year), (Paper.semester, semester)):
        if value: query = query.filter(field == value)
    return [serialize(p) for p in query.order_by(Paper.year.desc(), Paper.created_at.desc()).limit(200)]

@app.get("/api/papers/{paper_id}/download")
def download(paper_id: int, db: Session = Depends(get_db)):
    paper = db.get(Paper, paper_id)
    if not paper or not os.path.exists(paper.pdf_path): raise HTTPException(404, "Paper not found")
    return FileResponse(paper.pdf_path, media_type="application/pdf", filename=f"{paper.subject}_{paper.year}.pdf")

@app.post("/api/uploads")
async def upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"): raise HTTPException(400, "Only PDF uploads are supported in this MVP")
    token = uuid.uuid4().hex; source = settings.storage_path / f"source_{token}.pdf"
    with source.open("wb") as stream: shutil.copyfileobj(file.file, stream)
    try: detected = extract_papers(str(source))
    except Exception as exc: source.unlink(missing_ok=True); raise HTTPException(422, f"Unable to read PDF: {exc}")
    saved, duplicates = [], 0
    for item in detected:
        digest = hashlib.sha256(item.text.encode("utf-8", errors="ignore")).hexdigest()
        if db.query(Paper).filter_by(content_hash=digest).first(): duplicates += 1; continue
        safe = "".join(c if c.isalnum() else "_" for c in item.metadata["subject"])[:60] or "paper"
        target = settings.storage_path / f"{safe}_{item.metadata['year']}_{token[:8]}_{item.start + 1}.pdf"
        write_split(str(source), str(target), item.start, item.end)
        meta = item.metadata
        paper = Paper(title=f"{meta['subject']} · {meta['year']}", pdf_path=str(target), content_hash=digest, text_content=item.text, page_count=item.end-item.start+1, **meta)
        db.add(paper); db.flush(); saved.append(serialize(paper))
    db.commit(); source.unlink(missing_ok=True)
    return {"detected":len(detected),"saved":len(saved),"duplicates":duplicates,"papers":saved}
