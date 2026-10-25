#!/usr/bin/env python3
"""Footer, Recent nav, leader shop notes, and info pages."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path("/workspace")
SITE = "https://onepiecedecklists.com"
DISCLAIMER = (
    "Fan site for the Bandai ONE PIECE CARD GAME (OPTCG). "
    "Not affiliated with Bandai or Shueisha."
)

spec = importlib.util.spec_from_file_location("seocommon", ROOT / "scripts/seo_common.py")
seo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seo)

FOOTER_RE = re.compile(r"<footer>\s*.*?\s*</footer>", re.S)
NAV_RE = re.compile(r'<nav aria-label="Primary">.*?</nav>', re.S)


def page(title: str, desc: str, crumb: str, body: str, path: str) -> str:
    url = f"{SITE}/{path}"
    nav = seo.primary_nav_html()
    social = seo.social_tags(title, desc, url, seo.DEFAULT_OG)
    crumbs = seo.breadcrumb_jsonld([("Home", "/"), (crumb, "/" + path)])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{title}</title>
  <meta name="description" content="{desc}" />
  <link rel="canonical" href="{url}" />
  {seo.THEME_BOOT_SCRIPT}<link rel="stylesheet" href="/css/site.css?v=home-pro25" />
  {seo.google_head_tags(url)}
{social}{crumbs}</head>
<body>
  <div class="wrap">
    <header>
      <a class="brand" href="/">
        <img class="logo" src="/img/opdl-avatar.png" width="56" height="56" alt="One Piece Decklists" />
        <div>
          <h1>One Piece Decklists</h1>
          <div class="subtitle">OPTCG decklists</div>
        </div>
      </a>
      {seo.THEME_TOGGLE_HTML}
{nav}
    </header>
    <main class="single">
      <div class="card hero policy">
        <div class="crumb"><a href="/">Home</a> / {crumb}</div>
        <h2>{crumb}</h2>
{body}
        <p>{DISCLAIMER}</p>
      </div>
    </main>
    <footer>
      © <span id="year"></span> One Piece Decklists - {DISCLAIMER}
      {seo.FOOTER_LINKS}
    </footer>
  </div>
  <script>document.getElementById('year').textContent = new Date().getFullYear();</script>
  <script src="/js/site.js?v=deck-tools1"></script>
</body>
</html>
"""


def write_info_pages() -> None:
    about = page(
        "About | One Piece Decklists",
        "About One Piece Decklists, a fan site for OPTCG decklists, tier lists, and guides.",
        "About",
        """
        <p>One Piece Decklists publishes OPTCG decklists, a tier list, leader pages, and guides for the Bandai ONE PIECE CARD GAME.</p>
        <p>Tournament lists are sourced from Limitless Play and labeled on each page. Community lists are labeled with their public source. This is a fan project.</p>
        <p>Questions and deck corrections go through the <a href="/contact.html">contact page</a>. Advertising and partnership notes are on the <a href="/advertise.html">media kit</a>.</p>
""",
        "about.html",
    )
    contact = page(
        "Contact | One Piece Decklists",
        "Contact One Piece Decklists about a decklist, a correction, or a partnership.",
        "Contact",
        """
        <p>The public contact channel is the site Discord: <a href="https://discord.gg/adZ2WUQ3D" target="_blank" rel="noopener">discord.gg/adZ2WUQ3D</a>.</p>
        <p>Use that channel for a wrong list, a missing event, or a partnership question. There is no separate email address published on this site.</p>
""",
        "contact.html",
    )
    advertise = page(
        "Advertise | One Piece Decklists",
        "Media kit for One Piece Decklists. Traffic figures are placeholders until the publisher fills them in.",
        "Advertise",
        """
        <p>One Piece Decklists is an OPTCG fan site: decklists, a tier list, leader pages, guides, and an Amazon shop. Brands can reach readers next to that coverage.</p>
        <h3>Audience numbers</h3>
        <p>These figures are placeholders. They are not measurements.</p>
        <ul>
          <li>Monthly pageviews: [fill in]</li>
          <li>Monthly visitors: [fill in]</li>
          <li>Top countries: [fill in]</li>
          <li>Share of mobile visits: [fill in]</li>
          <li>Email or Discord audience: [fill in]</li>
        </ul>
        <h3>What is already on the site</h3>
        <ul>
          <li>Google AdSense auto ads, client <code>ca-pub-1074015774205047</code>. No manual ad units are placed in the layout.</li>
          <li>TCGplayer partner links on decklists, with a disclosure next to the button.</li>
          <li>Amazon Associates shop links (tag <code>opdl07-20</code>) with the Associates disclosure on shop pages.</li>
        </ul>
        <h3>Ad layout</h3>
        <p>The AdSense script is in the page head and loads asynchronously. The site does not reserve empty boxes for ads, and ads are not drawn as navigation items. Auto ads can still insert units after load and move content. If that shows up on a phone, turn off anchor and vignette formats in AdSense rather than adding a fake slot.</p>
        <h3>Consent</h3>
        <p>A Google-certified consent message is not turned on in the repo. Configure it in AdSense under Privacy &amp; messaging, as described on the <a href="/privacy.html">privacy page</a>.</p>
        <p>Partnership notes: <a href="/contact.html">contact</a>.</p>
""",
        "advertise.html",
    )
    (ROOT / "about.html").write_text(about)
    (ROOT / "contact.html").write_text(contact)
    (ROOT / "advertise.html").write_text(advertise)


def fix_footer(text: str) -> str:
    match = FOOTER_RE.search(text)
    if not match:
        return text
    inner = match.group(0)
    inner = inner.replace("Built with community in mind.", DISCLAIMER)
    if "Not affiliated with Bandai or Shueisha." in inner and DISCLAIMER not in inner:
        inner = inner.replace(
            "Fan site, not affiliated with Bandai or Shueisha.",
            DISCLAIMER,
        )
        inner = inner.replace(
            "not affiliated with Bandai or Shueisha.",
            DISCLAIMER[0].lower() + DISCLAIMER[1:],
        )
    inner = re.sub(
        r'(<a href="/eb05-lists.html"[^>]*>)EB05 lists(</a>)',
        r"\1EB05 Lists\2",
        inner,
    )
    inner = re.sub(
        r'(<a href="/eb05-spoilers.html"[^>]*>)EB05(</a>)',
        r"\1EB05 Spoilers\2",
        inner,
    )
    for href, label in (
        ("/about.html", "About"),
        ("/contact.html", "Contact"),
        ("/advertise.html", "Advertise"),
    ):
        if href not in inner and 'href="/privacy.html"' in inner:
            inner = inner.replace(
                '<a href="/privacy.html"',
                f'<a href="{href}">{label}</a> · <a href="/privacy.html"',
                1,
            )
    return text[: match.start()] + inner + text[match.end() :]


def fix_nav(text: str) -> str:
    match = NAV_RE.search(text)
    if not match:
        return text
    nav = match.group(0).replace('href="#recent"', 'href="/recent.html"')
    return text[: match.start()] + nav + text[match.end() :]


def fix_leader_shop(text: str, path: Path) -> str:
    if path.parent != ROOT / "decklists":
        return text
    if "leader-hero" not in text or "shop-note" in text:
        return text
    note = (
        '<p class="shop-note">Sleeves, playmats, and deck boxes are in the '
        '<a href="/shop/">shop</a>. As an Amazon Associate I earn from qualifying purchases.</p>\n        '
    )
    needle = "<!-- TOURNAMENT_DECKLISTS -->"
    if needle in text:
        return text.replace(needle, note + needle, 1)
    return text


def unlazy_leader_art(text: str) -> str:
    return re.sub(
        r'(<section class="leader-block"[\s\S]*?<img\b[^>]*?)\sloading="lazy"',
        r"\1",
        text,
        count=1,
    )


def fix_shueisha(text: str) -> str:
    return text.replace("Not affiliated with Bandai.", "Not affiliated with Bandai or Shueisha.")


def main() -> None:
    write_info_pages()
    changed = 0
    for path in ROOT.rglob("*.html"):
        if any(part in {".git", "img"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "Moved" in text[:300] and "http-equiv" in text[:800]:
            continue
        updated = fix_footer(fix_nav(fix_shueisha(text)))
        updated = fix_leader_shop(updated, path)
        if "leader-block" in updated:
            updated = unlazy_leader_art(updated)
        if updated != text:
            path.write_text(updated)
            changed += 1
    index = ROOT / "index.html"
    hero = index.read_text()
    imgs = list(re.finditer(r'<img class="home-splash-bg[^"]*"[^>]*>', hero))
    hero2 = hero
    for i, match in enumerate(imgs):
        if i == 0 or "loading=" in match.group(0) or "data-src=" in match.group(0):
            continue
        tag = match.group(0).replace("<img ", '<img loading="lazy" ', 1)
        hero2 = hero2.replace(match.group(0), tag, 1)
    if hero2 != hero:
        index.write_text(hero2)
        changed += 1
    privacy = (ROOT / "privacy.html").read_text()
    cmp_block = """
        <section>
          <h3>Ads in the EEA and the UK</h3>
          <p>Pages load Google AdSense (client ca-pub-1074015774205047). A Google-certified consent message is not shipped in this site's code.</p>
          <p>To turn one on: open AdSense, go to Privacy &amp; messaging, create a European regulations message, choose Google's Funding Choices message, select this AdSense account, and publish it. After it is published, the existing AdSense tag shows the message to EEA and UK visitors. Leave the CMP id blank in <code>data/affiliates.json</code> until that message exists. Do not paste a stand-in banner.</p>
        </section>
"""
    if "Ads in the EEA and the UK" not in privacy:
        privacy = privacy.replace("<section>\n          <h3>Contact Us</h3>", cmp_block + "        <section>\n          <h3>Contact Us</h3>", 1)
        (ROOT / "privacy.html").write_text(privacy)
    sitemap = (ROOT / "sitemap-core.xml").read_text()
    for loc in ("about.html", "contact.html", "advertise.html"):
        url = f"https://onepiecedecklists.com/{loc}"
        if url not in sitemap:
            sitemap = sitemap.replace(
                "</urlset>",
                f"  <url><loc>{url}</loc><lastmod>2026-10-25</lastmod></url>\n</urlset>",
            )
    (ROOT / "sitemap-core.xml").write_text(sitemap)
    shop = ROOT / "shop/index.html"
    shop_text = shop.read_text()
    note = (
        '<p class="amazon-disclosure-line">Links open Amazon.com through this site\'s Associates short links. '
        "An Amazon OneLink ID is not configured, so the shop is not localized by country yet.</p>\n"
    )
    if "not localized" not in shop_text and "amazon-disclosure-line" in shop_text:
        shop_text = shop_text.replace(
            '<p class="amazon-disclosure-line">As an Amazon Associate I earn from qualifying purchases.</p>',
            '<p class="amazon-disclosure-line">As an Amazon Associate I earn from qualifying purchases.</p>\n        ' + note,
            1,
        )
        shop.write_text(shop_text)
    print("chrome files", changed)


if __name__ == "__main__":
    main()
