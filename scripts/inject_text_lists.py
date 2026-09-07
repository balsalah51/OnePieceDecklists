#!/usr/bin/env python3
"""Insert or rebuild a hoverable text decklist above the picture summary."""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path("/workspace")

ARTICLE = re.compile(
    r'<article class="card-entry">\s*'
    r'<img src="([^"]+)" alt="([^"]*)"[^>]*>\s*'
    r'<div>\s*'
    r'<div class="id"><span class="qty">(\d+)x</span>\s*([A-Z0-9-]+) · ([^<]+)</div>\s*'
    r'<h4>([^<]+)</h4>',
    re.S,
)

PREVIEW_JS = """    document.getElementById('year').textContent = new Date().getFullYear();
    (function(){
      var lines = document.querySelectorAll('.text-line');
      if (!lines.length) return;
      function resetPop(pop){
        pop.style.position = '';
        pop.style.left = '';
        pop.style.top = '';
        pop.style.right = '';
        pop.style.bottom = '';
        pop.classList.remove('flip-left', 'flip-down');
      }
      function place(line){
        var pop = line.querySelector('.card-pop');
        var title = line.querySelector('.card-title');
        if (!pop || !title) return;
        resetPop(pop);
        var tr = title.getBoundingClientRect();
        var width = pop.offsetWidth || 220;
        var height = pop.offsetHeight || 308;
        var left = tr.left;
        var top = tr.top - height - 10;
        if (left + width > window.innerWidth - 12) left = window.innerWidth - width - 12;
        if (left < 12) left = 12;
        if (top < 12) top = tr.bottom + 10;
        if (top + height > window.innerHeight - 12) top = Math.max(12, window.innerHeight - height - 12);
        pop.style.position = 'fixed';
        pop.style.left = left + 'px';
        pop.style.top = top + 'px';
        pop.style.bottom = 'auto';
        pop.style.right = 'auto';
      }
      lines.forEach(function(line){
        line.addEventListener('mouseenter', function(){ place(line); });
        line.addEventListener('focus', function(){ place(line); });
        line.addEventListener('click', function(e){
          if (window.matchMedia('(hover: hover)').matches) return;
          e.stopPropagation();
          lines.forEach(function(other){ if (other !== line) other.classList.remove('is-open'); });
          line.classList.toggle('is-open');
          place(line);
        });
      });
      document.addEventListener('click', function(e){
        if (!e.target.closest('.text-line')) {
          lines.forEach(function(line){ line.classList.remove('is-open'); });
        }
      });
    })();"""


def collect_groups(page: str) -> list[tuple[str, list[dict]]]:
    groups: list[tuple[str, list[dict]]] = []
    for m in re.finditer(
        r'<h3>(Leader|Characters|Events|Stages)</h3>.*?<div class="card-grid">(.*?)</div>\s*</section>',
        page,
        re.S,
    ):
        group = m.group(1)
        items = []
        for art in ARTICLE.finditer(m.group(2)):
            src, _alt, qty, cid, _cat, name = art.groups()
            items.append(
                {
                    "src": src,
                    "qty": int(qty),
                    "id": cid.strip(),
                    "name": html.unescape(name.strip()),
                }
            )
        if items:
            groups.append((group, items))
    return groups


def render_text_deck(groups: list[tuple[str, list[dict]]]) -> str:
    total = sum(item["qty"] for _, items in groups for item in items)
    cols = []
    for group, items in groups:
        lines = []
        for item in items:
            name = html.escape(item["name"])
            lines.append(
                f"""            <li class="text-line" tabindex="0">
              <span class="qty">{item['qty']}x</span>
              <span class="card-title">{name}</span>
              <span class="muted card-id">{html.escape(item['id'])}</span>
              <img class="card-pop" src="{html.escape(item['src'])}" alt="{name}" />
            </li>"""
            )
        cols.append(
            f"""          <div>
            <h4>{html.escape(group)}</h4>
            <ul class="text-lines">
{chr(10).join(lines)}
            </ul>
          </div>"""
        )
    return f"""        <section class="text-deck">
          <div class="section-title">
            <h3>Text list</h3>
            <div class="muted">{total} cards</div>
          </div>
          <div class="text-deck-cols">
{chr(10).join(cols)}
          </div>
        </section>"""


def ensure_picture_wrap(page: str) -> str:
    if 'class="picture-summary"' in page:
        return page
    page = re.sub(
        r"(<section class=\"text-deck\">.*?</section>)",
        r"""\1
        <section class="picture-summary">
          <div class="section-title">
            <h3>Card pictures</h3>
            <div class="muted">Full card text</div>
          </div>
""",
        page,
        count=1,
        flags=re.S,
    )
    src = '        <p class="muted" style="margin-top:22px">'
    if src in page:
        page = page.replace(src, "        </section>\n" + src, 1)
    return page


def transform(page: str) -> str:
    if "/ Decklist</div>" not in page:
        return page
    groups = collect_groups(page)
    if not groups:
        return page
    text = render_text_deck(groups)
    if 'class="text-deck"' in page:
        page = re.sub(
            r"        <section class=\"text-deck\">.*?</section>\n",
            text + "\n",
            page,
            count=1,
            flags=re.S,
        )
    else:
        page = re.sub(
            r"(<h2>.*?</h2>\s*<p>.*?</p>)",
            r"\1\n" + text,
            page,
            count=1,
            flags=re.S,
        )
    page = ensure_picture_wrap(page)
    page = re.sub(
        r"<script>.*?</script>\s*</body>",
        "<script>\n" + PREVIEW_JS + "\n  </script>\n</body>",
        page,
        count=1,
        flags=re.S,
    )
    return page


def main() -> None:
    files = [
        p
        for p in ROOT.glob("decklists/**/*.html")
        if "/ Decklist</div>" in p.read_text()
    ]
    print("list pages", len(files))
    ok = 0
    for path in files:
        old = path.read_text()
        new = transform(old)
        if 'class="text-deck"' not in new:
            print("FAILED", path)
            continue
        if "&amp;#" in new or "&amp;amp;" in new:
            print("STILL ENCODED", path)
        path.write_text(new)
        ok += 1
    print("wrote", ok)


if __name__ == "__main__":
    main()
