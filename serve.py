"""Dependency-free local runner. Use when FastAPI packages are not installed yet."""
import json, mimetypes, re, shutil
from datetime import datetime
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).parent
STATIC, STORAGE, DATA = ROOT / "app" / "static", ROOT / "storage", ROOT / "fallback-data.json"
STORAGE.mkdir(exist_ok=True)

def read_data():
    return json.loads(DATA.read_text()) if DATA.exists() else []
def write_data(items): DATA.write_text(json.dumps(items, indent=2))
def make_id(items): return max((p["id"] for p in items), default=0) + 1

class App(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args): print("[Paper Intelligence]", fmt % args)
    def json(self, value, code=200):
        encoded = json.dumps(value).encode(); self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", len(encoded)); self.end_headers(); self.wfile.write(encoded)
    def do_GET(self):
        parsed = urlparse(self.path); path = parsed.path
        items = read_data()
        if path == "/api/health": return self.json({"status":"healthy", "runner":"dependency-free"})
        if path == "/api/dashboard":
            return self.json({"totalPapers":len(items),"subjects":len(set(p["subject"] for p in items)),"departments":0,"years":len(set(p["year"] for p in items)),"storageBytes":sum((STORAGE / p["fileName"]).stat().st_size for p in items if (STORAGE / p["fileName"]).exists()),"recent":list(reversed(items))[:5]})
        if path == "/api/papers":
            q = parse_qs(parsed.query).get("q", [""])[0].lower()
            return self.json([p for p in reversed(items) if not q or q in (p["subject"]+p["courseCode"]+p["year"]).lower()])
        found = re.fullmatch(r"/api/papers/(\d+)/download", path)
        if found:
            paper = next((p for p in items if p["id"] == int(found.group(1))), None); file = STORAGE / paper["fileName"] if paper else None
            if not file or not file.exists(): return self.json({"detail":"Paper not found"}, 404)
            self.send_response(200); self.send_header("Content-Type", "application/pdf"); self.send_header("Content-Disposition", f'attachment; filename="{file.name}"'); self.send_header("Content-Length", file.stat().st_size); self.end_headers(); shutil.copyfileobj(file.open("rb"), self.wfile); return
        if path in ("/", "/app", "/app/"): self.path = "/index.html"
        elif path.startswith("/app/"): self.path = path.removeprefix("/app")
        return super().do_GET()
    def do_POST(self):
        if self.path != "/api/uploads": return self.json({"detail":"Not found"}, 404)
        length = int(self.headers.get("Content-Length", 0)); body = self.rfile.read(length); ctype = self.headers.get("Content-Type", "")
        try:
            boundary = ctype.split("boundary=", 1)[1].encode(); part = next(x for x in body.split(b"--" + boundary) if b"filename=" in x)
            header, content = part.split(b"\r\n\r\n", 1); content = content.rsplit(b"\r\n", 1)[0]
            match = re.search(br'filename="([^\"]+)"', header); name = unquote(match.group(1).decode("utf-8", "ignore")) if match else "uploaded-paper.pdf"
        except Exception: return self.json({"detail":"Could not read uploaded file"}, 400)
        if not name.lower().endswith(".pdf"): return self.json({"detail":"Only PDF uploads are supported"}, 400)
        safe = re.sub(r"[^A-Za-z0-9._-]", "_", name); target = STORAGE / f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{safe}"; target.write_bytes(content)
        stem = Path(name).stem.replace("_", " ").replace("-", " "); year = (re.search(r"\b(20\d{2})\b", stem) or ["Unknown"])[0]; code = (re.search(r"\b[A-Z]{2,5}\d{3,4}\b", stem.upper()) or ["Unknown"])[0]
        items = read_data(); paper = {"id":make_id(items),"title":stem,"subject":re.sub(r"\b(20\d{2}|[A-Z]{2,5}\d{3,4})\b", "", stem, flags=re.I).strip() or "Unknown","courseCode":code,"department":"Unknown","semester":"Unknown","year":year,"month":"Unknown","marks":"Unknown","duration":"Unknown","pageCount":0,"createdAt":datetime.now().isoformat(),"fileName":target.name}; items.append(paper); write_data(items)
        return self.json({"detected":1,"saved":1,"duplicates":0,"papers":[paper]})

if __name__ == "__main__":
    import os
    os.chdir(STATIC)
    print("Question Paper Intelligence is running at http://localhost:8000/app/")
    ThreadingHTTPServer(("127.0.0.1", 8000), App).serve_forever()
