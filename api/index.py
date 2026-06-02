from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

HTML = """<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>即時翻譯工具</title>
  <style>
    :root{--bg:#07111f;--panel:rgba(9,20,36,.82);--line:rgba(95,215,255,.22);--text:#eaf7ff;--muted:#9bb1c4;--accent:#42d7ff;--accent2:#38f5b3;--danger:#ff6b8a;}
    *{box-sizing:border-box}
    body{margin:0;min-height:100vh;font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:radial-gradient(circle at top,#12304e 0,#07111f 42%,#040a12 100%);color:var(--text)}
    .wrap{max-width:980px;margin:0 auto;padding:24px 16px 40px}
    .hero{padding:24px 0 18px}
    .kicker{letter-spacing:.24em;text-transform:uppercase;color:var(--accent);font-size:.76rem}
    .title{font-size:clamp(2rem,5vw,4.5rem);line-height:.98;margin:.3rem 0 .8rem}
    .sub{color:var(--muted);max-width:64ch;line-height:1.7}
    .grid{display:grid;gap:16px;grid-template-columns:repeat(2,minmax(0,1fr))}
    @media (max-width:860px){.grid{grid-template-columns:1fr}}
    .card{background:linear-gradient(180deg,rgba(13,27,45,.92),rgba(6,14,26,.92));border:1px solid var(--line);border-radius:24px;padding:18px;box-shadow:0 30px 80px rgba(0,0,0,.35),inset 0 1px 0 rgba(255,255,255,.05);backdrop-filter:blur(16px)}
    .label{font-size:.82rem;color:var(--muted);margin-bottom:8px;text-transform:uppercase;letter-spacing:.14em}
    .controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
    .select,.input,.btn{border-radius:16px;border:1px solid rgba(86,170,208,.35);background:rgba(6,15,28,.9);color:var(--text)}
    .select,.input{padding:12px 14px;font-size:1rem}
    .input{width:100%;min-height:120px;resize:vertical}
    .btn{padding:12px 16px;font-weight:700;cursor:pointer}
    .primary{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#031019;border:none}
    .ghost{background:rgba(12,25,40,.8)}
    .danger{color:var(--danger)}
    .panel{min-height:170px;white-space:pre-wrap;line-height:1.8;font-size:1.08rem}
    .toprow{display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap}
    .badge{padding:8px 12px;border-radius:999px;background:rgba(66,215,255,.12);color:#bfefff;border:1px solid rgba(66,215,255,.18)}
    .tiny{font-size:.85rem;color:var(--muted);line-height:1.6}
    .stack{display:grid;gap:10px}
    .actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}
    .status{margin-top:10px;color:#b6c8d8;min-height:1.4em}
    .divider{height:1px;background:linear-gradient(90deg,transparent,var(--line),transparent);margin:14px 0}
  </style>
</head>
<body>
  <main class="wrap">
    <section class="hero">
      <div class="kicker">Instant Translation</div>
      <h1 class="title">繁中、英文、日文即時互譯</h1>
      <p class="sub">支援繁體中文、英文、日文互譯。你可以直接打字，或按麥克風說話，系統會把翻譯結果即時顯示，還能播放給對方聽。</p>
    </section>

    <section class="grid">
      <div class="card">
        <div class="toprow"><div class="label">輸入</div><div class="badge" id="conn">Cloudflare Worker 連線中</div></div>
        <div class="stack">
          <select id="direction" class="select">
            <option value="zh-TW:en">繁中 → 英文</option>
            <option value="en:zh-TW">英文 → 繁中</option>
            <option value="zh-TW:ja">繁中 → 日文</option>
            <option value="ja:zh-TW">日文 → 繁中</option>
            <option value="en:ja">英文 → 日文</option>
            <option value="ja:en">日文 → 英文</option>
          </select>
          <textarea id="input" class="input" placeholder="按麥克風說話，或直接輸入要翻譯的內容"></textarea>
          <div class="controls">
            <button id="mic" class="btn ghost">開始說話</button>
            <button id="translate" class="btn primary">立即翻譯</button>
          </div>
          <div id="status" class="status tiny">準備好了。</div>
        </div>
      </div>

      <div class="card">
        <div class="label">翻譯結果</div>
        <div id="output" class="panel">翻譯後的內容會顯示在這裡。</div>
        <div class="divider"></div>
        <div class="actions">
          <button id="play" class="btn ghost">播放</button>
          <button id="copy" class="btn ghost">複製</button>
        </div>
      </div>
    </section>
    <p class="tiny" style="margin-top:16px;">這個正式版會直接打 Cloudflare Worker，避免本機測試和上線行為不一致。</p>
  </main>

  <script>
    const BASE = "https://winfredkuo-translator.theoder.workers.dev";
    const input = document.getElementById('input');
    const output = document.getElementById('output');
    const statusEl = document.getElementById('status');
    const conn = document.getElementById('conn');
    const direction = document.getElementById('direction');
    const mic = document.getElementById('mic');
    const translateBtn = document.getElementById('translate');
    const playBtn = document.getElementById('play');
    const copyBtn = document.getElementById('copy');
    let lastText = '';

    function setStatus(text, error=false){statusEl.textContent=text; statusEl.className='status tiny '+(error?'danger':'');}
    function parseDir(){const [source_lang, target_lang] = direction.value.split(':'); return {source_lang, target_lang};}
    async function translate(){
      const text = input.value.trim();
      if(!text){setStatus('請先輸入或說話。', true); return;}
      setStatus('翻譯中...'); conn.textContent='連線正常';
      try{
        const r = await fetch(`${BASE}/api/translate`, {
          method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({...parseDir(), text})
        });
        const data = await r.json();
        if(!r.ok) throw new Error(data.detail || 'Translation failed');
        lastText = data.translated_text || '';
        output.textContent = lastText || '（空白）';
        setStatus('完成。');
      }catch(err){
        setStatus('翻譯失敗：' + err.message, true);
        conn.textContent='連線異常';
      }
    }
    translateBtn.onclick = translate;
    copyBtn.onclick = async () => { if(!lastText) return; await navigator.clipboard.writeText(lastText); setStatus('已複製翻譯結果。'); };
    playBtn.onclick = () => { if(!lastText || !('speechSynthesis' in window)) return; const u = new SpeechSynthesisUtterance(lastText); speechSynthesis.cancel(); speechSynthesis.speak(u); };
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if(SpeechRecognition){
      const rec = new SpeechRecognition(); rec.lang='zh-TW'; rec.interimResults=false; rec.continuous=false;
      mic.onclick = ()=>{ try{ rec.start(); setStatus('聆聽中...'); }catch(e){} };
      rec.onresult = (e)=>{ input.value = e.results[0][0].transcript; setStatus('辨識完成，按翻譯即可。'); };
      rec.onerror = ()=>setStatus('麥克風或辨識失敗。', true);
    } else {
      mic.textContent='此瀏覽器不支援語音'; mic.disabled = true;
    }
  </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(HTML)
