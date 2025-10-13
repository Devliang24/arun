from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, List

from apirunner.models.report import RunReport, CaseInstanceResult, StepResult, AssertionResult


def _json(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        try:
            return json.dumps(str(obj), ensure_ascii=False)
        except Exception:
            return str(obj)


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\"", "&quot;")
        .replace("'", "&#39;")
    )


def _build_assert_table(asserts: List[AssertionResult]) -> str:
    rows = []
    for a in asserts or []:
        cells = [
            f"<td><code>{_escape_html(str(a.check))}</code></td>",
            f"<td><code>{_escape_html(str(a.comparator))}</code></td>",
            f"<td><code>{_escape_html(json.dumps(a.expect, ensure_ascii=False))}</code></td>",
            f"<td><code>{_escape_html(json.dumps(a.actual, ensure_ascii=False))}</code></td>",
            ("<td><span class='ok'>✓</span></td>" if a.passed else f"<td><span class='err' title='{_escape_html(a.message or '')}'>✗</span></td>")
        ]
        rows.append("<tr " + ("data-pass=1" if a.passed else "data-pass=0") + ">" + "".join(cells) + "</tr>")
    thead = "<thead><tr><th>check</th><th>op</th><th>expect</th><th>actual</th><th>结果</th></tr></thead>"
    return f"<table class='assert-table'>{thead}<tbody>{''.join(rows)}</tbody></table>"


def _build_step(step: StepResult) -> str:
    pass_cnt = sum(1 for a in (step.asserts or []) if a.passed)
    fail_cnt = sum(1 for a in (step.asserts or []) if not a.passed)

    req_json = _json(step.request)
    resp_json = _json(step.response)
    ext_json = _json(step.extracts) if (step.extracts or {}) else None
    curl = step.curl or ""

    head = (
        f"<div class='st-head' onclick=\"toggleStepBody(this)\">"
        f"<div><b>步骤：</b>{_escape_html(step.name)}</div>"
        f"<div><span class='pill {step.status}'>" + step.status + "</span>"
        f"<span class='muted' style='margin-left:8px;'>{step.duration_ms:.1f} ms</span>"
        f"<span class='muted' style='margin-left:8px;'>断言: {pass_cnt} ✓ / {fail_cnt} ✗</span>"
        f"</div></div>"
    )

    panels = []
    panels.append(
        "<div class='grid' style='margin-top:8px;'>"
        + (
            "<div class='panel' data-section='request'>"
            "<div class='p-head'><span>请求</span><span class='actions'><button onclick=\"copyPanel(this)\">复制</button></span></div>"
            f"<pre><code>{_escape_html(req_json)}</code></pre>"
            "</div>"
        )
        + (
            "<div class='panel' data-section='response'>"
            "<div class='p-head'><span>响应</span><span class='actions'><button onclick=\"copyPanel(this)\">复制</button></span></div>"
            f"<pre><code>{_escape_html(resp_json)}</code></pre>"
            "</div>"
        )
        + "</div>"
    )

    if ext_json and ext_json != "{}":
        panels.append(
            "<div class='panel' data-section='extracts' style='margin-top:8px;'>"
            "<div class='p-head'><span>提取变量</span><span class='actions'><button onclick=\"copyPanel(this)\">复制</button></span></div>"
            f"<pre><code>{_escape_html(ext_json)}</code></pre>"
            "</div>"
        )

    # Asserts table
    panels.append(
        "<div class='panel' style='margin-top:8px;'>"
        "<div class='p-head'><span>断言</span></div>"
        + _build_assert_table(step.asserts or [])
        + "</div>"
    )

    # cURL section
    if curl:
        panels.append(
            "<div class='panel' data-section='curl' style='margin-top:8px;'>"
            "<div class='p-head'><span>cURL</span><span class='actions'><button onclick=\"copyPanel(this)\">复制</button></span></div>"
            f"<pre><code>{_escape_html(curl)}</code></pre>"
            "</div>"
        )

    body = "<div class='body'>" + "".join(panels) + "</div>"
    return f"<div class='step'><div>{head}</div>{body}</div>"


def _build_case(case: CaseInstanceResult) -> str:
    params = case.parameters or {}
    params_html = f"<div class='muted'>参数：<code>{_escape_html(_json(params))}</code></div>" if params else ""

    head = (
        "<div class='head'>"
        f"<div><div><b>用例：</b>{_escape_html(case.name)}</div>{params_html}</div>"
        f"<div><span class='pill {case.status}'>{case.status}</span>"
        f"<span class='muted' style='margin-left:8px;'>{case.duration_ms:.1f} ms</span></div>"
        "</div>"
    )

    steps_html = "".join(_build_step(s) for s in (case.steps or []))
    return f"<div class='case' data-status='{case.status}' data-duration='{case.duration_ms:.3f}'>{head}<div class='body'>{steps_html}</div></div>"


def write_html(report: RunReport, outfile: str | Path) -> None:
    s = report.summary or {}
    gen_time = time.strftime("%Y-%m-%d %H:%M:%S")

    # Header + styles (light theme, GitHub-like)
    head_parts = []
    head_parts.append("""
<!doctype html><html lang='zh-CN'><head><meta charset='utf-8' /><meta name='viewport' content='width=device-width, initial-scale=1' />
<title>APIRunner 测试报告</title>
<style>
  :root { --bg:#ffffff; --fg:#24292f; --muted:#57606a; --ok:#1a7f37; --fail:#cf222e; --skip:#6e7781; --card:#f6f8fa; --accent:#0969da; --border:#d0d7de; --panel-head-bg:#f6f8fa; --step-head-bg:#f6f8fa; --chip-bg:#f6f8fa; --btn-bg:#ffffff; --input-bg:#ffffff; --code-key:#0550ae; --code-str:#0a3069; --code-num:#953800; --code-bool:#1a7f37; --code-null:#6e7781; --code-punct:#57606a; }
  html, body { margin:0; padding:0; background:var(--bg); color:var(--fg); font: 14px/1.45 -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif; }
  .wrap { max-width: 1100px; margin: 0 auto; padding: 0 16px 64px; }
  h1 { font-size: 20px; margin: 0; }
  .header-sticky { position: sticky; top: 0; z-index: 999; background: var(--bg); padding: 12px 0 10px; border-bottom: 1px solid var(--border); }
  .headbar { display:flex; justify-content: space-between; align-items: baseline; gap: 12px; margin-bottom: 8px; }
  .meta { color: var(--muted); font-size: 12px; }
  .summary { display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:16px; margin-bottom: 24px; }
  .badge { position:relative; padding:16px 18px; border-radius: 10px; background: var(--card); border:1px solid var(--border); box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
  .badge::before { content:''; position:absolute; top:0; left:0; width:4px; height:100%; border-radius:10px 0 0 10px; }
  .badge.total::before { background: var(--accent); }
  .badge.passed::before { background: var(--ok); }
  .badge.failed::before { background: var(--fail); }
  .badge.skipped::before { background: var(--skip); }
  .badge.duration::before { background: #8250df; }
  .badge-label { display:block; font-size:12px; color:var(--muted); margin-bottom:6px; }
  .badge-value { display:block; font-size:28px; font-weight:700; line-height:1; }
  .badge.passed .badge-value { color: var(--ok); }
  .badge.failed .badge-value { color: var(--fail); }
  .badge.skipped .badge-value { color: var(--skip); }
  .passed { color: var(--ok); }
  .failed { color: var(--fail); }
  .skipped { color: var(--skip); }
  .case { border: 1px solid var(--border); background: var(--card); border-radius: 10px; margin: 14px 0; overflow: hidden; }
  .case > .head { padding: 12px 12px; display:flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); }
  .pill { font-size: 12px; padding: 2px 8px; border-radius: 999px; border:1px solid var(--border); }
  .pill.passed { border-color: var(--ok); }
  .pill.failed { border-color: var(--fail); }
  .pill.skipped { border-color: var(--skip); }
  .body { padding: 10px 12px; }
  .step { border: 1px solid var(--border); border-radius: 8px; margin: 10px 0; overflow:hidden; }
  .step .st-head { padding: 8px 10px; display:flex; justify-content: space-between; align-items:center; background: var(--step-head-bg); cursor: pointer; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .panel { border:1px solid var(--border); border-radius:8px; overflow:hidden; }
  .panel .p-head { padding:6px 8px; background:var(--panel-head-bg); color:var(--muted); font-size:12px; display:flex; justify-content:space-between; align-items:center; }
  .panel .p-head .actions { display:flex; gap:6px; }
  .panel pre, .panel table { margin:0; padding:10px; overflow:auto; max-height: 360px; }
  .panel[data-section='curl'] pre { white-space: pre-wrap; word-break: break-word; }
  table { width: 100%; border-collapse: collapse; table-layout: fixed; }
  th { padding: 6px 8px; border-bottom: 1px solid var(--border); vertical-align: top; text-align: left; font-weight: 600; }
  td { padding: 6px 8px; border-bottom: 1px solid var(--border); vertical-align: top; word-break: break-word; }
  .assert-table th:nth-child(1), .assert-table td:nth-child(1) { width: 25%; }
  .assert-table th:nth-child(2), .assert-table td:nth-child(2) { width: 10%; }
  .assert-table th:nth-child(3), .assert-table td:nth-child(3) { width: 25%; }
  .assert-table th:nth-child(4), .assert-table td:nth-child(4) { width: 25%; }
  .assert-table th:nth-child(5), .assert-table td:nth-child(5) { width: 15%; text-align: center; }
  .ok { color: var(--ok); }
  .err { color: var(--fail); }
  .muted { color: var(--muted); }
  code { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace; font-size: 12px; }
  details { border-top: 1px dashed var(--border); }
  details > summary { cursor: pointer; list-style: none; padding: 8px 10px; color: var(--muted); }
  details > summary::-webkit-details-marker { display: none; }
  .toolbar { display:grid; grid-template-columns: 1fr auto; gap:8px; align-items:center; margin-bottom: 8px; }
  .toolbar .filters { display:flex; gap:8px; flex-wrap:wrap; align-items:center; }
  .toolbar button { padding:6px 10px; border-radius:6px; border:1px solid var(--border); background:var(--btn-bg); color:var(--fg); cursor:pointer; }
  .toolbar button:hover { border-color:var(--accent); }
  .toolbar .chip { background:var(--chip-bg); border:1px solid var(--border); padding:4px 8px; border-radius:999px; display:inline-flex; align-items:center; gap:6px; }
  .toolbar input[type='radio']{ accent-color: var(--accent); }
  .footer { margin-top: 24px; color: var(--muted); font-size: 12px; }
  .collapsed .body { display: none; }
</style>
<script>(function(){
  function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
  function highlightJSONSimple(text){
    let out = ''; let i = 0;
    while(i < text.length){
      const ch = text[i];
      if(ch==='\"'){
        let j=i+1; let str=''; let escaped=false;
        while(j<text.length){ const c=text[j]; str+=c; j++; if(c==='\\' && !escaped){ escaped=true; continue;} if(c==='\"' && !escaped){ break;} escaped=false; }
        out += "<span class='tok-str'>\""+esc(str)+"</span>"; i=j; continue;
      }
      if(/[-0-9]/.test(ch)){
        let j=i; let num=''; while(j<text.length && /[-0-9.eE]/.test(text[j])){ num+=text[j++]; }
        out += "<span class='tok-num'>"+esc(num)+"</span>"; i=j; continue;
      }
      if(text.startsWith('true', i) || text.startsWith('false', i)){
        const w = text.startsWith('true', i)?'true':'false'; out += "<span class='tok-bool'>"+w+"</span>"; i+=w.length; continue;
      }
      if(text.startsWith('null', i)){ out += "<span class='tok-null'>null</span>"; i+=4; continue; }
      out += esc(ch); i++;
    }
    return out;
  }
  window.toggleStepBody = function(headEl){ const step=headEl.closest('.step'); if(!step) return; step.classList.toggle('collapsed'); };
  window.copyPanel = async function(btn){ try{ const panel=btn.closest('.panel'); const code=panel?.querySelector('pre'); const text=code?(code.innerText||''):''; await navigator.clipboard.writeText(text); const old=btn.innerText; btn.innerText='已复制'; setTimeout(()=>btn.innerText=old, 1200);}catch(e){}}
  window.applyFilters = function(){ const sel=(document.querySelector("input[name='status-filter']:checked")?.value)||'all'; try{localStorage.setItem('arun_report_status', sel);}catch(e){} document.querySelectorAll('.case').forEach(c=>{ const st=c.dataset.status||''; c.style.display=(sel==='all'||st===sel)?'':''; }); };
  document.addEventListener('DOMContentLoaded', function(){
    try{ const saved=localStorage.getItem('arun_report_status')||'all'; const el=document.querySelector("input[name='status-filter'][value='"+saved+"']"); if(el) el.checked=true; }catch(e){}
    document.querySelectorAll("input[name='status-filter']").forEach(el=>{ el.addEventListener('change', window.applyFilters); });
    // JSON highlight
    document.querySelectorAll('.panel pre code').forEach(code=>{ const panel=code.closest('.panel'); if(panel && panel.dataset && panel.dataset.section==='curl') return; const raw=code.innerText||''; code.innerHTML=highlightJSONSimple(raw); });
    window.applyFilters();
  });
})();</script>
""")
    head_parts.append("</style>\n")
    head_parts.append("</head><body>\n<div class='wrap'>\n  <div class='header-sticky'>\n    <div class='headbar'>\n      <h1>APIRunner 测试报告</h1>\n      <div class='meta'>生成时间：" + _escape_html(gen_time) + "</div>\n    </div>\n")
    # Summary badges
    total = str(s.get('total', 0))
    passed = str(s.get('passed', 0))
    failed = str(s.get('failed', 0))
    skipped = str(s.get('skipped', 0))
    duration = f"{float(s.get('duration_ms', 0.0)):.1f}"
    head_parts.append("    <div class='summary'>\n")
    head_parts.append("      <div class='badge total'><span class='badge-label'>用例总数</span><span class='badge-value'>" + total + "</span></div>\n")
    head_parts.append("      <div class='badge passed'><span class='badge-label'>通过</span><span class='badge-value'>" + passed + "</span></div>\n")
    head_parts.append("      <div class='badge failed'><span class='badge-label'>失败</span><span class='badge-value'>" + failed + "</span></div>\n")
    head_parts.append("      <div class='badge skipped'><span class='badge-label'>跳过</span><span class='badge-value'>" + skipped + "</span></div>\n")
    head_parts.append("      <div class='badge duration'><span class='badge-label'>耗时</span><span class='badge-value'>" + duration + "<span style='font-size:14px;font-weight:400;margin-left:4px;'>ms</span></span></div>\n")
    head_parts.append("    </div>\n")
    head_parts.append("    <div class='toolbar'>\n      <div class='filters'>\n        <label class='chip'><input type='radio' name='status-filter' id='f-all' value='all' checked /> 全部</label>\n        <label class='chip'><input type='radio' name='status-filter' id='f-passed' value='passed' /> 通过</label>\n        <label class='chip'><input type='radio' name='status-filter' id='f-failed' value='failed' /> 失败</label>\n        <label class='chip'><input type='radio' name='status-filter' id='f-skipped' value='skipped' /> 跳过</label>\n      </div>\n      <button id='btn-toggle-expand' title='展开/收起全部' onclick=\"(function(){const steps=Array.from(document.querySelectorAll('.step')); const anyExpanded=steps.some(s=>!s.classList.contains('collapsed')); if(anyExpanded){steps.forEach(s=>s.classList.add('collapsed')); this.textContent='展开全部';} else {steps.forEach(s=>s.classList.remove('collapsed')); this.textContent='收起全部';}}).call(this)\">展开全部</button>\n    </div>\n  </div>\n")

    # Cases
    body_cases = []
    for c in report.cases:
        body_cases.append(_build_case(c))

    tail = """
  <div class='footer'>由 APIRunner 生成</div>
</div>
</body></html>
"""

    html = "".join(head_parts) + "".join(body_cases) + tail
    p = Path(outfile)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html, encoding="utf-8")
