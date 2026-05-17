"""
构建 SKC_Query_v3.html
从 skc_master.db 读取全部 23,000+ 条记录，生成离线单文件 HTML。
"""
import json, os, sys, sqlite3
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = 'C:/Users/jiawa/skc_color/skc_master.db'

# ── 从数据库读取数据 ──
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
rows = conn.execute(
    'SELECT skc, pantone, pantone_base, series, name, hex, family, shade_range, needs_review '
    'FROM skc_colors WHERE status != "deleted" ORDER BY family, shade'
).fetchall()
conn.close()

RANGE_MAP = {
    '浅色调 Tint/Light': 0,
    'Tint/Light': 0,
    '中间色调 Mid/Standard': 1,
    'Mid/Standard': 1,
    '深色调 Deep/Dark': 2,
    'Deep/Dark': 2,
    '极深/特殊效果色': 3,
}

compact = []
for r in rows:
    sr = r['shade_range'] or ''
    rv = RANGE_MAP.get(sr, RANGE_MAP.get(sr.split(' ')[-1] if ' ' in sr else sr, 1))
    compact.append({
        's': r['skc'],
        'p': r['pantone'],
        'b': r['pantone_base'] or '',
        'e': r['series'] or '',
        'n': r['name'] or '',
        'h': r['hex'] or '',
        'f': r['family'] if r['family'] is not None else -1,
        'r': rv,
        'v': 1 if r['needs_review'] else 0,
    })

DB_JSON = json.dumps(compact, ensure_ascii=False, separators=(',', ':'))
COUNT = len(compact)

# ── CSS ──
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#f0f2f5;--card:#fff;--hd:#1a1a2e;--accent:#3b5bdb;
  --accent2:#0ca678;--warn:#f59f00;--danger:#e03131;
  --text:#1a1a2e;--muted:#868e96;--border:#dee2e6;
  --radius:10px;--shadow:0 2px 12px rgba(0,0,0,.08);
}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
.hd{background:var(--hd);color:#fff;padding:16px 28px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;box-shadow:0 2px 8px rgba(0,0,0,.3)}
.hd-title{font-size:17px;font-weight:700;letter-spacing:.5px}
.hd-sub{font-size:11px;color:#adb5bd;margin-top:2px}
.hd-stat{font-size:11px;color:#74c0fc;text-align:right}
.wrap{max-width:1200px;margin:0 auto;padding:20px 16px}
.tabs{display:flex;gap:4px;margin-bottom:16px;background:var(--card);border-radius:var(--radius);padding:4px;box-shadow:var(--shadow)}
.tab{flex:1;padding:9px;border:none;background:none;border-radius:7px;font-size:13px;font-weight:500;color:var(--muted);cursor:pointer;transition:.15s}
.tab.active{background:var(--hd);color:#fff}
.tab:hover:not(.active){background:#f1f3f5}
.panel{display:none}.panel.show{display:block}
.card{background:var(--card);border-radius:var(--radius);padding:20px;box-shadow:var(--shadow);margin-bottom:16px}
.row{display:flex;gap:8px;align-items:stretch}
input[type=text],textarea,select{padding:10px 13px;border:2px solid var(--border);border-radius:8px;font-size:13px;outline:none;transition:.15s;font-family:inherit}
input[type=text]:focus,textarea:focus,select:focus{border-color:var(--accent)}
textarea{width:100%;resize:vertical}
.btn{padding:10px 18px;border:none;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap;transition:.15s}
.btn-primary{background:var(--accent);color:#fff}.btn-primary:hover{opacity:.88}
.btn-success{background:var(--accent2);color:#fff}.btn-success:hover{opacity:.88}
.btn-ghost{background:#f1f3f5;color:var(--text)}.btn-ghost:hover{background:#e9ecef}
.lbl{font-size:11px;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.6px;display:block;margin-bottom:8px}
.res-card{display:none}.res-card.show{display:block}
.rh{display:flex;align-items:center;gap:18px;margin-bottom:18px;padding-bottom:16px;border-bottom:1px solid var(--border)}
.swatch{width:72px;height:72px;border-radius:10px;border:1px solid rgba(0,0,0,.08);flex-shrink:0}
.skc-num{font-size:44px;font-weight:800;font-family:monospace;color:var(--hd);letter-spacing:3px}
.cname{font-size:14px;color:var(--muted);margin-top:2px}
.tags{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
.tag{padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600}
.tf{background:#e7f5ff;color:#1971c2}.tr{background:#ebfbee;color:#2f9e44}
.tv{background:#fff9db;color:#e67700}.tx{background:#fff0f6;color:#c2255c}
.ts{background:#f3f0ff;color:#6741d9}
.grid4{display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}
.di{background:#f8f9fa;border-radius:8px;padding:12px 14px}
.lb{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;margin-bottom:4px}
.vl{font-size:14px;font-weight:600;font-family:monospace}
.vl-link{color:var(--accent);cursor:pointer}.vl-link:hover{text-decoration:underline}
.nf{text-align:center;padding:40px;color:var(--muted)}
.nf .ic{font-size:36px;margin-bottom:8px}
/* 同款跨系列 */
.xseries{margin-top:14px;padding-top:14px;border-top:1px solid var(--border)}
.xs-title{font-size:11px;color:var(--muted);font-weight:600;margin-bottom:8px;text-transform:uppercase;letter-spacing:.5px}
.xs-list{display:flex;gap:8px;flex-wrap:wrap}
.xs-item{display:flex;align-items:center;gap:6px;padding:5px 10px;background:#f1f3f5;border-radius:6px;font-size:12px;cursor:pointer;transition:.15s}
.xs-item:hover{background:#e9ecef;color:var(--accent)}
.xs-swatch{width:14px;height:14px;border-radius:3px;border:1px solid rgba(0,0,0,.1)}
/* 批量 */
.batch-stats{display:flex;gap:10px;flex-wrap:wrap}
.stat-chip{padding:5px 12px;border-radius:20px;font-size:12px;font-weight:600}
.sc-total{background:#e7f5ff;color:#1971c2}.sc-ok{background:#ebfbee;color:#2f9e44}
.sc-miss{background:#fff0f6;color:#c2255c}.sc-rev{background:#fff9db;color:#e67700}
.tbl-wrap{overflow-x:auto;border-radius:8px;border:1px solid var(--border)}
table{width:100%;border-collapse:collapse;font-size:13px}
thead tr{background:var(--hd);color:#fff}
th{padding:10px 12px;text-align:left;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.5px;white-space:nowrap}
tbody tr{border-bottom:1px solid var(--border)}
tbody tr:last-child{border-bottom:none}
tbody tr:hover{background:#f8f9fa}
td{padding:9px 12px;vertical-align:middle}
.td-sw{width:22px;height:22px;border-radius:4px;border:1px solid rgba(0,0,0,.1);display:inline-block;vertical-align:middle}
.td-skc{font-family:monospace;font-weight:700;font-size:14px}
.ok .td-skc{color:var(--accent2)}.rev .td-skc{color:var(--warn)}.miss td{color:#adb5bd}.miss .td-skc{color:#ccc}
.badge-rev{background:#fff9db;color:#e67700;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:700}
.badge-miss{background:#f1f3f5;color:#adb5bd;padding:2px 6px;border-radius:4px;font-size:10px}
.drop-zone{border:2px dashed var(--border);border-radius:var(--radius);padding:36px;text-align:center;cursor:pointer;transition:.2s;color:var(--muted)}
.drop-zone:hover,.drop-zone.drag{border-color:var(--accent);background:#e7f5ff20;color:var(--accent)}
.drop-zone .ic{font-size:32px;margin-bottom:8px}
.drop-zone .hint{font-size:12px;margin-top:4px}
.hist{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}
.hi{padding:5px 12px;background:#f1f3f5;border-radius:20px;font-size:12px;cursor:pointer;display:flex;align-items:center;gap:8px;transition:.15s}
.hi:hover{background:#e9ecef}
.dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.progress-bar{height:4px;background:#e9ecef;border-radius:2px;overflow:hidden;margin:8px 0;display:none}
.progress-fill{height:100%;background:var(--accent);border-radius:2px;transition:width .3s}
.inline-row{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-top:12px}
.input-methods{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:12px}
@media(max-width:700px){.input-methods{grid-template-columns:1fr}}
.method-card{border:2px solid var(--border);border-radius:var(--radius);padding:14px;transition:.15s;cursor:pointer}
.method-card:hover{border-color:var(--accent);background:#f8f9ff}
.method-card.active-method{border-color:var(--accent);background:#edf2ff}
.method-title{font-size:12px;font-weight:700;color:var(--text);margin-bottom:4px}
.method-hint{font-size:11px;color:var(--muted)}
.src-panel{display:none}.src-panel.show{display:block}
.convert-bar{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;padding:14px 16px;background:#f8f9fa;border-radius:var(--radius);border:1px solid var(--border)}
.convert-bar-left{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.ocr-thumb{max-height:160px;border-radius:8px;margin-top:10px;display:none;object-fit:contain;max-width:100%}
.paste-img-status{font-size:11px;color:var(--accent2);display:none;margin-top:4px}
@media(max-width:640px){.grid4{grid-template-columns:1fr 1fr}.grid3{grid-template-columns:1fr 1fr}.skc-num{font-size:32px}.tabs{flex-wrap:wrap}}
"""

# ── JS ──
JS = r"""
const RL=['浅色调','中间色调','深色调','极深/特殊'];
const FM={0:'白/米白',1:'黄',2:'橙',3:'红',4:'粉',5:'紫',6:'蓝',7:'绿',8:'棕',9:'灰/黑'};
const SERIES_LABEL={C:'印刷C面',U:'印刷U面',TCX:'纺织TCX',TPG:'纺织TPG',TPX:'纺织TPX',TSX:'纺织TSX',PASTEL:'粉彩/霓虹',METAL:'金属色',PC:'CMYK-C',PU:'CMYK-U',CP:'色桥-C',UP:'色桥-U',TPM:'金属闪光',TN:'尼龙',SP:'皮肤色'};

// 构建索引：精确 pantone → 记录，pantone_base → 所有记录列表
const IDX = {};   // pantone(大写) → record
const BASE = {};  // pantone_base(大写) → [records]

DB.forEach(r => {
  IDX[r.p.toUpperCase()] = r;
  const b = r.b.toUpperCase();
  if (b) {
    if (!BASE[b]) BASE[b] = [];
    BASE[b].push(r);
  }
});

document.getElementById('hd-stat').textContent =
  '共 ' + DB.length + ' 色 · 全系列 15 种色卡 · 6位SKC';

// ── 规范化输入 ──
// 处理各种格式：
//   "19-4150 TPG" -> "19-4150TPG"
//   "100 C"       -> "100 C"  (保留，因为 IDX 里就是 "100 C")
//   "877 U"       -> "877 U"
function normalizeInput(raw) {
  return raw.trim()
    // 仅对 XX-XXXX 类纺织色号，去掉数字与后缀之间的空格
    .replace(/(\d{2}-\d{4})\s+(TPG|TCX|TPX|TSX|TPM|TN|SP)$/i, (_, a, b) => a + b)
    .toUpperCase();
}

function dbLookup(input) {
  const k = normalizeInput(input);
  // 1. 精确匹配
  if (IDX[k]) return IDX[k];
  // 2. 带空格的变体（印刷类 "100 C" 数据库里可能是 "100C" 或 "100 C"）
  const kNoSpace = k.replace(/\s+/g, '');
  if (IDX[kNoSpace]) return IDX[kNoSpace];
  // 3. 加常见后缀尝试（用户输入了 base，自动补后缀）
  for (const s of ['TPG','TCX','TPX','TSX','C','U','CP','UP','PC','PU']) {
    if (IDX[k + s]) return IDX[k + s];
    if (IDX[k + ' ' + s]) return IDX[k + ' ' + s];
  }
  // 4. 对无空格的纺织后缀，尝试插入空格（"19-4150TPX" -> "19-4150 TPX"）
  const withSpace = k.replace(/(\d{2}-\d{4})(TPG|TCX|TPX|TSX|TPM|TN|SP)$/, '$1 $2');
  if (withSpace !== k && IDX[withSpace]) return IDX[withSpace];
  // 5. pantone_base 精确匹配
  if (BASE[k] && BASE[k].length) return BASE[k][0];
  if (BASE[kNoSpace] && BASE[kNoSpace].length) return BASE[kNoSpace][0];
  return null;
}

function getRelated(r) {
  // 同 pantone_base 的其他系列记录
  if (!r.b) return [];
  return (BASE[r.b.toUpperCase()] || []).filter(x => x.p !== r.p);
}

// ── Tab ──
function switchTab(name, el) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('show'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('panel-' + name).classList.add('show');
  el.classList.add('active');
}

// ── ① 单色查询 ──
let hist = [];
function querySingle() {
  const raw = document.getElementById('inp-single').value.trim();
  if (!raw) return;
  const r = dbLookup(raw);
  renderSingle(r, raw);
}
function renderSingle(r, q) {
  const el = document.getElementById('res-single');
  el.classList.add('show');
  if (!r) {
    el.innerHTML = '<div class="nf"><div class="ic">&#128269;</div>' +
      '<div>未找到 <b>' + q + '</b></div>' +
      '<div style="font-size:12px;margin-top:6px">支持格式：19-4150TPG · 19-4150 TCX · 100 C · 8965 C 等全系列</div></div>';
    return;
  }
  addHist(r, q);
  const rev = r.v ? '<span class="tag tv">&#9888; 边界色</span>' : '';
  const seriesLabel = SERIES_LABEL[r.e] || r.e || '—';
  const related = getRelated(r);
  let xseriesHtml = '';
  if (related.length) {
    const items = related.map(x =>
      '<div class="xs-item" onclick="jumpTo(\'' + x.p + '\')">' +
        '<div class="xs-swatch" style="background:' + x.h + '"></div>' +
        '<span class="tag ts" style="margin:0;padding:2px 6px">' + x.e + '</span>' +
        '<span style="font-family:monospace;font-size:11px">' + x.p + '</span>' +
        '<b style="font-family:monospace">' + x.s + '</b>' +
      '</div>'
    ).join('');
    xseriesHtml = '<div class="xseries"><div class="xs-title">同款其他系列 (' + related.length + ')</div>' +
      '<div class="xs-list">' + items + '</div></div>';
  }
  el.innerHTML =
    '<div class="rh">' +
      '<div class="swatch" style="background:' + r.h + '"></div>' +
      '<div>' +
        '<div class="skc-num">' + r.s + '</div>' +
        '<div class="cname">' + (r.n || r.p) + '</div>' +
        '<div class="tags">' +
          '<span class="tag ts">' + seriesLabel + '</span>' +
          '<span class="tag tf">' + (FM[r.f] || '—') + '</span>' +
          '<span class="tag tr">' + (RL[r.r] || '—') + '</span>' +
          rev +
        '</div>' +
      '</div>' +
    '</div>' +
    '<div class="grid4">' +
      '<div class="di"><div class="lb">SKC 编码</div><div class="vl" style="font-size:20px;color:var(--accent)">' + r.s + '</div></div>' +
      '<div class="di"><div class="lb">潘通色号</div><div class="vl" style="font-size:12px">' + r.p + '</div></div>' +
      '<div class="di"><div class="lb">HEX</div><div class="vl">' + r.h + '</div></div>' +
      '<div class="di"><div class="lb">系列</div><div class="vl" style="font-size:13px">' + seriesLabel + '</div></div>' +
      '<div class="di"><div class="lb">色系</div><div class="vl">' + (FM[r.f] || '—') + '</div></div>' +
      '<div class="di"><div class="lb">色阶区间</div><div class="vl" style="font-size:12px">' + (RL[r.r] || '—') + '</div></div>' +
      '<div class="di"><div class="lb">颜色名称</div><div class="vl" style="font-size:12px">' + (r.n || '—') + '</div></div>' +
      '<div class="di"><div class="lb">Base 码</div><div class="vl" style="font-size:12px">' + (r.b || '—') + '</div></div>' +
    '</div>' +
    xseriesHtml;
}
function jumpTo(p) {
  document.getElementById('inp-single').value = p;
  querySingle();
}
function addHist(r, q) {
  hist = hist.filter(h => h.r.s !== r.s);
  hist.unshift({r, q});
  if (hist.length > 12) hist.pop();
  const box = document.getElementById('hist-card');
  box.style.display = 'block';
  document.getElementById('hist-list').innerHTML = hist.map(h =>
    '<div class="hi" onclick="jumpTo(\'' + h.r.p + '\')">' +
      '<div class="dot" style="background:' + h.r.h + '"></div>' +
      '<span style="font-family:monospace">' + h.q + '</span>' +
      '<b>' + h.r.s + '</b>' +
    '</div>'
  ).join('');
}

// ── ② 批量转化 ──
function convertOne(input) {
  const r = dbLookup(input);
  const base = r ? r.b : normalizeInput(input);
  return {
    input: input.trim(),
    found: !!r,
    skc:    r ? r.s : '',
    name:   r ? r.n : '',
    hex:    r ? r.h : '',
    series: r ? r.e : '',
    family: r ? (FM[r.f] || '—') : '',
    range:  r ? (RL[r.r] || '—') : '',
    review: r ? !!r.v : false,
    base:   base,
    related: r ? getRelated(r) : [],
  };
}

// 输入源切换
function selectMethod(name) {
  document.querySelectorAll('.method-card').forEach(c => c.classList.remove('active-method'));
  document.querySelectorAll('.src-panel').forEach(p => p.classList.remove('show'));
  document.getElementById('method-' + name).classList.add('active-method');
  document.getElementById('src-' + name).classList.add('show');
}

// 正则提取潘通色号（支持全系列格式）
function extractPantones(text) {
  const results = [];
  // 纺织类：XX-XXXX + 可选系列后缀（有无空格皆可）
  const pat1 = /\b(\d{2}-\d{4}(?:\s*(?:TPG|TCX|TPX|TSX|TPM|TN|SP))?)\b/gi;
  let m;
  while ((m = pat1.exec(text)) !== null) {
    const p = m[1].replace(/(\d{2}-\d{4})\s+(TPG|TCX|TPX|TSX|TPM|TN|SP)/i, '$1$2').toUpperCase();
    if (p.length >= 7) results.push(p);
  }
  // 印刷类 CP/UP/PC/PU 后缀
  const pat2 = /\b(\d{2,4}\s*(?:CP|UP|PC|PU))\b/gi;
  while ((m = pat2.exec(text)) !== null) results.push(m[1].trim().toUpperCase());
  // 印刷类 单字母 C/U（数字+空格+C/U，避免误匹配）
  const pat3 = /\b(\d{2,4})\s+([CU])\b/g;
  while ((m = pat3.exec(text)) !== null) results.push(m[1] + ' ' + m[2].toUpperCase());
  // P系列：P X-X C/U/CP/UP
  const pat4 = /\b(P\s+[\dA-Z]+-[\dA-Z]+\s*(?:CP|UP|PC|PU|[CU]))\b/gi;
  while ((m = pat4.exec(text)) !== null) results.push(m[1].replace(/\s+/g,' ').trim().toUpperCase());
  return results;
}
function dedupe(arr) {
  const s = new Set();
  return arr.filter(p => p && !s.has(p) && s.add(p));
}

function getBatchFromText() {
  const raw = document.getElementById('inp-batch').value;
  return dedupe(extractPantones(raw));
}

// 文件导入
function dragOver(e) { e.preventDefault(); e.currentTarget.classList.add('drag'); }
function dragLeave(e) { e.currentTarget.classList.remove('drag'); }
function dropFile(e) { e.preventDefault(); e.currentTarget.classList.remove('drag'); const f = e.dataTransfer.files[0]; if (f) loadFile(f); }
function dropOcr(e) { e.preventDefault(); e.currentTarget.classList.remove('drag'); const f = e.dataTransfer.files[0]; if (f) loadOcrFile(f); }

function loadScript(src) {
  return new Promise((res, rej) => { const s = document.createElement('script'); s.src = src; s.onload = res; s.onerror = rej; document.head.appendChild(s); });
}
function extractFromCSV(text, col) {
  const lines = text.split('\n'); if (!lines.length) return extractPantones(text);
  const hdrs = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
  const idx = hdrs.findIndex(h => h.toLowerCase().includes(col.toLowerCase()));
  if (idx === -1) return extractPantones(text);
  return lines.slice(1).map(l => l.split(',')[idx]?.trim().replace(/^"|"$/g, '') || '').filter(v => v);
}
async function extractFromXLSX(file, col) {
  if (typeof XLSX === 'undefined') await loadScript('https://cdn.sheetjs.com/xlsx-0.20.0/package/dist/xlsx.full.min.js');
  const buf = await file.arrayBuffer();
  const wb = XLSX.read(buf, {type: 'array'});
  const ws = wb.Sheets[wb.SheetNames[0]];
  const rows = XLSX.utils.sheet_to_json(ws, {defval: ''});
  if (!rows.length) return extractPantones(XLSX.utils.sheet_to_csv(ws));
  const key = Object.keys(rows[0]).find(k => k.toLowerCase().includes(col.toLowerCase()));
  if (!key) return extractPantones(XLSX.utils.sheet_to_csv(ws));
  return rows.map(r => String(r[key] || '').trim()).filter(v => v);
}
async function extractFromDOCX(file) {
  if (typeof mammoth === 'undefined') await loadScript('https://cdn.jsdelivr.net/npm/mammoth@1.6.0/mammoth.browser.min.js');
  const buf = await file.arrayBuffer();
  const result = await mammoth.extractRawText({arrayBuffer: buf});
  return extractPantones(result.value);
}
async function extractFromPDF(file) {
  if (typeof pdfjsLib === 'undefined') {
    await loadScript('https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.min.js');
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/build/pdf.worker.min.js';
  }
  const buf = await file.arrayBuffer();
  const pdf = await pdfjsLib.getDocument({data: new Uint8Array(buf)}).promise;
  let text = '';
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    text += content.items.map(it => it.str).join(' ') + '\n';
  }
  return extractPantones(text);
}

let _filePantones = [];
async function loadFile(file) {
  if (!file) return;
  const ext = file.name.split('.').pop().toLowerCase();
  const col = document.getElementById('file-col').value || 'pantone';
  setFileStatus('读取中：' + file.name + ' …', 'var(--muted)');
  let pantones = [];
  try {
    if (ext === 'txt') pantones = extractPantones(await file.text());
    else if (ext === 'csv') pantones = extractFromCSV(await file.text(), col);
    else if (ext === 'xlsx' || ext === 'xlsm' || ext === 'xls') pantones = await extractFromXLSX(file, col);
    else if (ext === 'docx') pantones = await extractFromDOCX(file);
    else if (ext === 'pdf') pantones = await extractFromPDF(file);
    else { setFileStatus('不支持格式：' + ext, 'var(--danger)'); return; }
  } catch(e) {
    setFileStatus('读取失败：' + e.message, 'var(--danger)'); return;
  }
  _filePantones = dedupe(pantones);
  if (!_filePantones.length) {
    setFileStatus('未提取到色号，请检查文件内容或列名', 'var(--warn)');
  } else {
    setFileStatus('已读取 ' + file.name + '，提取到 ' + _filePantones.length + ' 个色号 — 点击"开始转换"', 'var(--accent2)');
  }
}
function setFileStatus(msg, color) {
  const el = document.getElementById('file-status');
  el.textContent = msg; el.style.color = color || 'var(--muted)';
}
function handleFileChange(inp) { const f = inp.files[0]; if (f) loadFile(f); }

// OCR
let _ocrPantones = [], _ocrDone = false;
async function loadOcrFile(file) {
  if (!file) return;
  _ocrDone = false; _ocrPantones = [];
  const thumb = document.getElementById('ocr-thumb');
  thumb.src = URL.createObjectURL(file); thumb.style.display = 'block';
  const status = document.getElementById('ocr-status');
  const bar = document.getElementById('ocr-progress');
  const fill = document.getElementById('ocr-fill');
  bar.style.display = 'block'; fill.style.width = '5%'; fill.style.background = 'var(--accent)';
  status.textContent = '加载 OCR 引擎（首次需下载约 10 MB）…'; status.style.color = 'var(--muted)';
  setBtnState('loading');
  try {
    if (typeof Tesseract === 'undefined') await loadScript('https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js');
    status.textContent = '识别中…'; fill.style.width = '20%';
    const result = await Tesseract.recognize(file, 'eng', {
      logger: m => { if (m.status === 'recognizing text') {
        const p = Math.round(20 + m.progress * 72);
        fill.style.width = p + '%'; status.textContent = '识别中 ' + p + '%';
      }}
    });
    fill.style.width = '100%';
    _ocrPantones = dedupe(extractPantones(result.data.text));
    _ocrDone = true;
    if (!_ocrPantones.length) {
      status.textContent = '未识别到潘通色号';
      fill.style.background = 'var(--warn)'; setBtnState('normal');
    } else {
      status.textContent = '识别完成，找到 ' + _ocrPantones.length + ' 个色号';
      status.style.color = 'var(--accent2)'; setBtnState('ready', _ocrPantones.length);
    }
  } catch(e) {
    status.textContent = 'OCR 失败：' + e.message;
    fill.style.background = 'var(--danger)'; setBtnState('normal');
  }
}
function setBtnState(state, count) {
  const btn = document.getElementById('btn-convert');
  if (!btn) return;
  if (state === 'loading') { btn.disabled = true; btn.textContent = '识别中…'; }
  else if (state === 'ready') { btn.disabled = false; btn.textContent = '▶ 开始转换（' + count + ' 个）'; }
  else { btn.disabled = false; btn.textContent = '▶ 开始转换'; }
}
function handleOcrChange(inp) { const f = inp.files[0]; if (f) loadOcrFile(f); }

// 剪贴板粘贴图片
document.addEventListener('DOMContentLoaded', () => {
  const ta = document.getElementById('inp-batch');
  ta.addEventListener('paste', async (e) => {
    const items = [...(e.clipboardData || e.originalEvent?.clipboardData)?.items || []];
    const imgItem = items.find(it => it.type.startsWith('image/'));
    if (!imgItem) return;
    e.preventDefault();
    selectMethod('ocr');
    const file = imgItem.getAsFile();
    const statusEl = document.getElementById('paste-img-status');
    statusEl.style.display = 'block';
    statusEl.textContent = '已粘贴截图，OCR 识别中…';
    await loadOcrFile(file);
    statusEl.textContent = _ocrDone && _ocrPantones.length
      ? '粘贴截图识别完成，找到 ' + _ocrPantones.length + ' 个色号'
      : '未识别到色号';
  });
});

// 统一转换入口
function runBatch() {
  const active = document.querySelector('.method-card.active-method');
  const method = active ? active.id.replace('method-', '') : 'text';
  let pantones = [];
  if (method === 'text') {
    pantones = getBatchFromText();
    if (!pantones.length) { showBatchError('未检测到潘通色号。\n支持格式：19-4150TPG · 100 C · P 1-1 C 等'); return; }
  } else if (method === 'file') {
    if (!_filePantones.length) { showBatchError('请先选择文件，等待读取完成后再转换'); return; }
    pantones = _filePantones;
  } else if (method === 'ocr') {
    if (!_ocrDone) { showBatchError('OCR 识别尚未完成，请等待后再转换'); return; }
    if (!_ocrPantones.length) { showBatchError('图片中未识别到潘通色号'); return; }
    pantones = _ocrPantones;
  }
  const results = pantones.map(p => convertOne(p));
  document.getElementById('batch-result').innerHTML = renderTable(results);
  document.getElementById('batch-result').scrollIntoView({behavior: 'smooth', block: 'start'});
}
function showBatchError(msg) {
  document.getElementById('batch-result').innerHTML =
    '<div class="card"><div class="nf"><div class="ic">&#9888;</div><div>' + msg + '</div></div></div>';
}

// 渲染结果表
function renderTable(results) {
  const cid = 'r' + Date.now();
  const total = results.length, found = results.filter(r => r.found).length;
  const miss = total - found, rev = results.filter(r => r.review).length;
  let rows = '';
  results.forEach((r, i) => {
    const cls = !r.found ? 'miss' : r.review ? 'rev' : 'ok';
    const sw = r.hex ? '<span class="td-sw" style="background:' + r.hex + '"></span>' : '—';
    const badge = r.review ? '<span class="badge-rev">边界色</span>'
                : !r.found ? '<span class="badge-miss">未找到</span>' : '&#10003;';
    const serLabel = r.series ? (SERIES_LABEL[r.series] || r.series) : '—';
    rows += '<tr class="' + cls + '">' +
      '<td style="color:var(--muted);font-size:11px">' + (i+1) + '</td>' +
      '<td style="font-family:monospace">' + r.input + '</td>' +
      '<td>' + sw + '</td>' +
      '<td class="td-skc">' + (r.skc || '—') + '</td>' +
      '<td style="font-size:12px">' + (r.name || '—') + '</td>' +
      '<td><span style="font-size:11px">' + serLabel + '</span></td>' +
      '<td>' + (r.family || '—') + '</td>' +
      '<td style="font-family:monospace;font-size:11px">' + (r.base || '—') + '</td>' +
      '<td>' + badge + '</td>' +
    '</tr>';
  });
  window['_data_' + cid] = results;
  return '<div class="card">' +
    '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px">' +
      '<div class="batch-stats">' +
        '<span class="stat-chip sc-total">共 ' + total + ' 条</span>' +
        '<span class="stat-chip sc-ok">&#10003; ' + found + ' 找到</span>' +
        (miss ? '<span class="stat-chip sc-miss">&#10007; ' + miss + ' 未找到</span>' : '') +
        (rev  ? '<span class="stat-chip sc-rev">&#9888; ' + rev + ' 需审核</span>' : '') +
      '</div>' +
      '<div style="display:flex;gap:8px">' +
        '<button class="btn btn-success" onclick="exportExcel(\'' + cid + '\')">&#8595; 导出 Excel</button>' +
        '<button class="btn btn-ghost" onclick="copyTsv(\'' + cid + '\')">复制表格</button>' +
      '</div>' +
    '</div>' +
    '<div class="tbl-wrap"><table id="tbl-' + cid + '">' +
      '<thead><tr><th>#</th><th>输入色号</th><th>颜色</th><th>SKC</th><th>颜色名</th><th>系列</th><th>色系</th><th>Base码</th><th>状态</th></tr></thead>' +
      '<tbody>' + rows + '</tbody>' +
    '</table></div></div>';
}

// 导出 Excel
async function exportExcel(cid) {
  const btn = event.target;
  if (typeof XLSX === 'undefined') {
    const old = btn.textContent; btn.textContent = '加载中…'; btn.disabled = true;
    await loadScript('https://cdn.sheetjs.com/xlsx-0.20.0/package/dist/xlsx.full.min.js');
    btn.textContent = old; btn.disabled = false;
  }
  const results = window['_data_' + cid] || [];
  const rows = results.map((r, i) => ({
    '#': i+1, '输入色号': r.input, 'SKC': r.skc, '颜色名': r.name,
    'HEX': r.hex, '系列': r.series, '色系': r.family, '色阶区间': r.range,
    'Base码': r.base,
    '状态': !r.found ? '未找到' : r.review ? '边界色' : '已找到',
  }));
  const ws = XLSX.utils.json_to_sheet(rows);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'SKC查询结果');
  XLSX.writeFile(wb, 'SKC_查询结果_' + new Date().toISOString().slice(0,10) + '.xlsx');
}
function copyTsv(cid) {
  const tbl = document.getElementById('tbl-' + cid); if (!tbl) return;
  const tsv = [...tbl.querySelectorAll('tr')].map(r =>
    [...r.querySelectorAll('th,td')].map(c => c.textContent.trim()).join('\t')
  ).join('\n');
  navigator.clipboard.writeText(tsv).then(() => {
    const b = event.target; b.textContent = '已复制'; setTimeout(() => b.textContent = '复制表格', 2000);
  });
}
"""

# ── HTML 模板 ──
HTML = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SKC 颜色编码系统 v3</title>
<style>{CSS}</style>
</head>
<body>
<div class="hd">
  <div>
    <div class="hd-title">SKC 颜色编码系统 v3</div>
    <div class="hd-sub">全系列 15 种潘通色卡 &middot; 6位SKC编码 &middot; 离线可用</div>
  </div>
  <div class="hd-stat" id="hd-stat">加载中&hellip;</div>
</div>

<div class="wrap">
  <div class="tabs">
    <button class="tab active" onclick="switchTab('single',this)">&#128269; 单色查询</button>
    <button class="tab" onclick="switchTab('batch',this)">&#128203; 批量查询</button>
  </div>

  <!-- ① 单色查询 -->
  <div class="panel show" id="panel-single">
    <div class="card">
      <label class="lbl">输入潘通色号（支持全系列）</label>
      <div class="row">
        <input type="text" id="inp-single"
          placeholder="例：19-4150TPG &nbsp;·&nbsp; 19-4150 TCX &nbsp;·&nbsp; 100 C &nbsp;·&nbsp; 877 U &nbsp;·&nbsp; P 1-1 C"
          autocomplete="off" spellcheck="false"
          onkeydown="if(event.key==='Enter')querySingle()" style="flex:1">
        <button class="btn btn-primary" onclick="querySingle()">查询</button>
      </div>
    </div>
    <div class="card res-card" id="res-single"></div>
    <div class="card" id="hist-card" style="display:none">
      <div style="font-size:12px;color:var(--muted);font-weight:600">最近查询</div>
      <div class="hist" id="hist-list"></div>
    </div>
  </div>

  <!-- ② 批量查询 -->
  <div class="panel" id="panel-batch">
    <div class="card">
      <div class="lbl" style="margin-bottom:10px">选择输入方式</div>
      <div class="input-methods">
        <div class="method-card active-method" id="method-text" onclick="selectMethod('text')">
          <div class="method-title">&#9997; 粘贴文本</div>
          <div class="method-hint">粘贴任意格式，自动提取色号</div>
        </div>
        <div class="method-card" id="method-file" onclick="selectMethod('file')">
          <div class="method-title">&#128194; 导入文件</div>
          <div class="method-hint">Excel / CSV / TXT / Word / PDF</div>
        </div>
        <div class="method-card" id="method-ocr" onclick="selectMethod('ocr')">
          <div class="method-title">&#128444; 图片识别</div>
          <div class="method-hint">截图 / 拍照，OCR 识别色号</div>
        </div>
      </div>

      <!-- 文本输入 -->
      <div class="src-panel show" id="src-text">
        <textarea id="inp-batch" rows="6"
          placeholder="支持任意格式，例如：&#10;19-4150TPG, 18-1660TCX, 100 C, 877 U, P 1-1 C&#10;或每行一个，或混合在段落中&#10;&#10;也可直接 Ctrl+V 粘贴截图，自动 OCR 识别"></textarea>
        <div style="display:flex;align-items:center;justify-content:space-between;margin-top:6px;flex-wrap:wrap;gap:6px">
          <span style="font-size:11px;color:var(--muted)">支持全系列格式 &middot; 粘贴图片直接 OCR</span>
          <div class="paste-img-status" id="paste-img-status"></div>
        </div>
      </div>

      <!-- 文件导入 -->
      <div class="src-panel" id="src-file">
        <div class="drop-zone" id="drop-zone"
             onclick="document.getElementById('file-inp').click()"
             ondragover="dragOver(event)" ondragleave="dragLeave(event)" ondrop="dropFile(event)">
          <div class="ic">&#128194;</div>
          <div style="font-weight:600">点击选择 或 拖拽文件到这里</div>
          <div class="hint">Excel (.xlsx .xls) &middot; Word (.docx) &middot; PDF &middot; CSV &middot; TXT</div>
        </div>
        <input type="file" id="file-inp" accept=".xlsx,.xlsm,.xls,.csv,.txt,.docx,.pdf" style="display:none" onchange="handleFileChange(this)">
        <div class="inline-row">
          <span style="font-size:12px;color:var(--muted)">Excel/CSV 列名：</span>
          <input type="text" id="file-col" value="pantone" style="width:120px">
          <span style="font-size:11px;color:var(--muted)">（找不到列名时自动全文扫描）</span>
        </div>
        <div id="file-status" style="font-size:12px;color:var(--muted);margin-top:8px">未选择文件</div>
      </div>

      <!-- 图片 OCR -->
      <div class="src-panel" id="src-ocr">
        <div class="drop-zone" id="ocr-drop"
             onclick="document.getElementById('ocr-inp').click()"
             ondragover="dragOver(event)" ondragleave="dragLeave(event)" ondrop="dropOcr(event)">
          <div class="ic">&#128444;</div>
          <div style="font-weight:600">点击选择图片 或 拖拽到这里</div>
          <div class="hint">PNG &middot; JPG &middot; WEBP &middot; 首次识别需联网下载 OCR 模型</div>
        </div>
        <input type="file" id="ocr-inp" accept="image/*" style="display:none" onchange="handleOcrChange(this)">
        <img id="ocr-thumb" class="ocr-thumb">
        <div class="progress-bar" id="ocr-progress">
          <div class="progress-fill" id="ocr-fill" style="width:0%"></div>
        </div>
        <div id="ocr-status" style="font-size:12px;color:var(--muted);margin-top:6px"></div>
      </div>

      <!-- 操作栏 -->
      <div class="convert-bar" style="margin-top:16px">
        <div style="font-size:12px;color:var(--muted)">查询所有系列，自动关联 Base 码</div>
        <div style="display:flex;gap:8px">
          <button class="btn btn-ghost" onclick="document.getElementById('inp-batch').value='';document.getElementById('batch-result').innerHTML=''">清空</button>
          <button class="btn btn-primary" id="btn-convert" style="padding:11px 28px;font-size:14px" onclick="runBatch()">&#9654; 开始查询</button>
        </div>
      </div>
    </div>

    <div id="batch-result"></div>
  </div>
</div>

<script>
const DB = {DB_JSON};
{JS}
</script>
</body>
</html>"""

OUT = 'SKC_Query_v3.html'
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(HTML)

size = os.path.getsize(OUT)
print(f'{OUT}  {size:,} bytes  ({size//1024} KB)  共 {COUNT} 条记录')
