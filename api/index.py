from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

HTML = """<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Travel Translator</title>
  <style>
    body{margin:0;font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#07111f;color:#eaf7ff;display:grid;place-items:center;min-height:100vh;padding:24px}
    .card{max-width:860px;width:100%;background:rgba(9,20,36,.9);border:1px solid rgba(95,215,255,.25);border-radius:24px;padding:24px;box-shadow:0 30px 80px rgba(0,0,0,.35)}
    h1{font-size:clamp(2rem,4vw,4rem);line-height:1;margin:0 0 12px}
    p{color:#9bb1c4;line-height:1.8}
    .badge{display:inline-block;margin-bottom:12px;padding:8px 12px;border-radius:999px;background:rgba(66,215,255,.12);color:#bfefff;border:1px solid rgba(66,215,255,.18);font-size:.85rem}
    .grid{display:grid;gap:16px;grid-template-columns:repeat(2,minmax(0,1fr));margin-top:20px}
    @media (max-width:860px){.grid{grid-template-columns:1fr}}
    .panel{padding:18px;border-radius:20px;background:rgba(6,15,28,.95);border:1px solid rgba(86,170,208,.2);min-height:150px;white-space:pre-wrap}
    .small{font-size:.9rem;color:#9bb1c4}
  </style>
</head>
<body>
  <main class="card">
    <div class="badge">Vercel 已部署成功</div>
    <h1>旅行時可直接開口說，立刻翻成對方聽得懂的語言。</h1>
    <p>目前先確認 Vercel 入口正常。首頁穩定後，我們再把 Cloudflare Worker 翻譯和語音功能接回來。</p>
    <div class="grid">
      <div class="panel"><strong>狀態</strong><br><br>如果你看到這頁，代表 Vercel function 已正常啟動。</div>
      <div class="panel"><strong>下一步</strong><br><br>接著我們會把正式版前端和翻譯 API 串回來。</div>
    </div>
    <p class="small" style="margin-top:16px">這是一個診斷版首頁，用來先排除 500 錯誤。</p>
  </main>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(HTML)
