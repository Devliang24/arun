from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from apirunner.models.report import RunReport


TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>APIRunner 测试报告</title>
    <style>
      :root { --bg:#0b0b0f; --fg:#eaeaea; --muted:#9aa0a6; --ok:#2ea043; --fail:#e5534b; --skip:#c0c0c0; --card:#151821; --accent:#4f7cff; }
      html, body { margin:0; padding:0; background:var(--bg); color:var(--fg); font: 14px/1.45 -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif; }
      .wrap { max-width: 1100px; margin: 0 auto; padding: 24px 16px 64px; }
      h1 { font-size: 20px; margin: 0 0 12px; }
      .summary { display:flex; gap:12px; flex-wrap: wrap; margin-bottom: 16px; }
      .badge { padding:8px 10px; border-radius: 8px; background: var(--card); }
      .passed { color: var(--ok); }
      .failed { color: var(--fail); }
      .skipped { color: var(--skip); }
      .case { border: 1px solid #232a34; background: var(--card); border-radius: 10px; margin: 14px 0; overflow: hidden; }
      .case > .head { padding: 12px 12px; display:flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #232a34; }
      .pill { font-size: 12px; padding: 2px 8px; border-radius: 999px; border:1px solid #2a2f38; }
      .pill.passed { border-color: var(--ok); }
      .pill.failed { border-color: var(--fail); }
      .pill.skipped { border-color: var(--skip); }
      .body { padding: 10px 12px; }
      .step { border: 1px solid #20242d; border-radius: 8px; margin: 10px 0; overflow:hidden; }
      .step .st-head { padding: 8px 10px; display:flex; justify-content: space-between; align-items:center; background: #10131a; }
      .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
      .panel { border:1px solid #20242d; border-radius:8px; overflow:hidden; }
      .panel .p-head { padding:6px 8px; background:#11141b; color:var(--muted); font-size:12px; }
      .panel pre, .panel table { margin:0; padding:10px; overflow:auto; max-height: 360px; }
      table { width: 100%; border-collapse: collapse; table-layout: fixed; }
      th { padding: 6px 8px; border-bottom: 1px solid #1f2430; vertical-align: top; text-align: left; font-weight: 600; }
      td { padding: 6px 8px; border-bottom: 1px solid #1f2430; vertical-align: top; word-break: break-word; }
      .assert-table th:nth-child(1), .assert-table td:nth-child(1) { width: 25%; }
      .assert-table th:nth-child(2), .assert-table td:nth-child(2) { width: 10%; }
      .assert-table th:nth-child(3), .assert-table td:nth-child(3) { width: 25%; }
      .assert-table th:nth-child(4), .assert-table td:nth-child(4) { width: 25%; }
      .assert-table th:nth-child(5), .assert-table td:nth-child(5) { width: 15%; text-align: center; }
      .ok { color: var(--ok); }
      .err { color: var(--fail); }
      .muted { color: var(--muted); }
      code { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 12px; }
      details { border-top: 1px dashed #242a35; }
      details > summary { cursor: pointer; list-style: none; padding: 8px 10px; color: var(--muted); }
      details > summary::-webkit-details-marker { display: none; }
      .footer { margin-top: 24px; color: var(--muted); font-size: 12px; }
    </style>
    <script>
      function togglePassed(el){
        const hide = el.dataset.hide !== '1';
        document.querySelectorAll('.case').forEach(c => {
          if(c.dataset.status === 'passed') c.style.display = hide ? 'none' : '';
        });
        el.dataset.hide = hide ? '1':'0';
        el.innerText = hide ? '显示已通过用例' : '隐藏已通过用例';
      }
    </script>
  </head>
  <body>
    <div class="wrap">
      <h1>APIRunner 测试报告</h1>
      <div class="summary">
        <div class="badge">用例总数：<b>{{ s.total }}</b></div>
        <div class="badge">通过：<b class="passed">{{ s.passed }}</b></div>
        <div class="badge">失败：<b class="failed">{{ s.failed }}</b></div>
        <div class="badge">跳过：<b class="skipped">{{ s.skipped }}</b></div>
        <div class="badge">耗时：<b>{{ '%.1f' % s.duration_ms }} ms</b></div>
        <div class="badge"><button onclick="togglePassed(this)" data-hide="0">隐藏已通过用例</button></div>
      </div>

      {% for c in cases %}
      <div class="case" data-status="{{ c.status }}">
        <div class="head">
          <div>
            <div><b>用例：</b>{{ c.name }}</div>
            {% if c.parameters %}
              <div class="muted">参数：<code>{{ c.parameters | tojson_pretty }}</code></div>
            {% endif %}
          </div>
          <div>
            <span class="pill {{ c.status }}">{{ c.status }}</span>
            <span class="muted" style="margin-left:8px;">{{ '%.1f' % c.duration_ms }} ms</span>
          </div>
        </div>
        <div class="body">
          {% for s in c.steps %}
          <div class="step">
            <div class="st-head">
              <div><b>步骤：</b>{{ s.name }}</div>
              <div>
                <span class="pill {{ s.status }}">{{ s.status }}</span>
                <span class="muted" style="margin-left:8px;">{{ '%.1f' % s.duration_ms }} ms</span>
              </div>
            </div>

            <div class="body">
              <div class="panel">
                <div class="p-head">断言</div>
                <table class="assert-table">
                  <thead><tr><th>check</th><th>op</th><th>expect</th><th>actual</th><th>结果</th></tr></thead>
                  <tbody>
                    {% for a in s.asserts %}
                    <tr>
                      <td><code>{{ a.check }}</code></td>
                      <td><code>{{ a.comparator }}</code></td>
                      <td><code>{{ a.expect | tojson }}</code></td>
                      <td><code>{{ a.actual | tojson }}</code></td>
                      <td>{% if a.passed %}<span class="ok">✓</span>{% else %}<span class="err" title="{{ a.message }}">✗</span>{% endif %}</td>
                    </tr>
                    {% endfor %}
                  </tbody>
                </table>
              </div>

              {% if s.extracts %}
              <div class="panel" style="margin-top:8px;">
                <div class="p-head">提取变量</div>
                <pre><code>{{ s.extracts | tojson_pretty }}</code></pre>
              </div>
              {% endif %}

              <div class="grid" style="margin-top:8px;">
                <div class="panel">
                  <div class="p-head">请求</div>
                  <pre><code>{{ s.request | tojson_pretty }}</code></pre>
                </div>
                <div class="panel">
                  <div class="p-head">响应</div>
                  <pre><code>{{ s.response | tojson_pretty }}</code></pre>
                </div>
              </div>

            </div>
          </div>
          {% endfor %}
        </div>
      </div>
      {% endfor %}

      <div class="footer">由 APIRunner 生成</div>
    </div>
  </body>
 </html>
"""


def write_html(report: RunReport, outfile: str | Path) -> None:
    try:
        from jinja2 import Environment, select_autoescape  # type: ignore

        env = Environment(autoescape=select_autoescape(["html", "xml"]))
        # Compact JSON for assertion table cells, pretty JSON for other sections
        env.filters["tojson"] = lambda v: json.dumps(v, ensure_ascii=False)
        env.filters["tojson_pretty"] = lambda v: json.dumps(v, ensure_ascii=False, indent=2)
        tmpl = env.from_string(TEMPLATE)
        html = tmpl.render(s=report.summary, cases=report.cases)
    except Exception:
        # Fallback: minimal HTML without jinja2
        s = report.summary
        buf = []
        buf.append("<!doctype html><html><head><meta charset='utf-8'><title>APIRunner Report</title>")
        buf.append("<style>body{font-family:Arial;margin:20px} pre{background:#f7f7f7;padding:12px;border-radius:6px;overflow:auto}</style>")
        buf.append("</head><body>")
        buf.append(f"<h1>APIRunner 测试报告</h1><p>总数:{s.get('total',0)} 通过:{s.get('passed',0)} 失败:{s.get('failed',0)} 跳过:{s.get('skipped',0)} 耗时:{s.get('duration_ms',0):.1f}ms</p>")
        for c in report.cases:
            buf.append(f"<h3>用例: {c.name} [{c.status}] ({c.duration_ms:.1f}ms)</h3>")
            if c.parameters:
                buf.append("<pre><code>" + json.dumps(c.parameters, ensure_ascii=False, indent=2) + "</code></pre>")
            for st in c.steps:
                buf.append(f"<h4>步骤: {st.name} [{st.status}] ({st.duration_ms:.1f}ms)</h4>")
                if st.asserts:
                    buf.append("<pre><code>" + json.dumps([a.model_dump() for a in st.asserts], ensure_ascii=False, indent=2) + "</code></pre>")
                buf.append("<details><summary>请求/响应</summary>")
                buf.append("<pre><code>请求\n" + json.dumps(st.request, ensure_ascii=False, indent=2) + "\n响应\n" + json.dumps(st.response, ensure_ascii=False, indent=2) + "</code></pre>")
                buf.append("</details>")
        buf.append("</body></html>")
        html = "".join(buf)

    p = Path(outfile)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html, encoding="utf-8")
