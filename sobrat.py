# -*- coding: utf-8 -*-
"""
Сборка сайта NFS Own Music — общий сайт серии (своя музыка во всех Need for Speed).

  shablon.html  — разметка и стиль (одна на все языки)
  teksty/*.txt  — тексты, по файлу на язык (ключ = текст)
  sajt.txt      — общее: адрес, программы (версия, ссылки), языки
  igry.txt      — все NFS: год | название | статус | программа
  static/       — иконка (копируется как есть)
  -> gotovo/    — готовый сайт: /index.html (главный язык), /en/, /de/, ... + sitemap.xml  (= ветка gh-pages)

  py sobrat.py               собрать
  py sobrat.py --prosmotr    собрать и открыть в браузере (http://localhost:8766/)
  py sobrat.py --opublikovat собрать и отправить на GitHub: исходник -> main, gotovo/ -> gh-pages
"""
import datetime
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "gotovo"
PORT = 8766
SITE_NAME = "NFS Own Music"
LABEL = {"uk": "UA"}                      # подпись кнопки языка (остальные — код большими буквами)
HTML_LANG = {"zh": "zh-Hans"}             # lang="" в html; в адресе и hreflang — код как есть
CJK = {"zh", "ja", "ko"}                  # без курсива
STATUS = ("ready", "soon", "wait")

warnings = []


def fail(msg):
    print("ОШИБКА: " + msg)
    sys.exit(1)


def read_kv(path):
    data = {}
    for n, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if " = " in s:
            k, v = s.split(" = ", 1)
        elif s.endswith(" ="):
            k, v = s[:-2], ""
        else:
            fail(f"{path.name}, строка {n}: нет « = » — {s[:70]}")
        k = k.strip()
        if k in data:
            warnings.append(f"{path.name}: ключ «{k}» записан дважды — беру последний")
        data[k] = v.strip()
    return data


def read_games(path, cfg):
    games = []
    for n, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        p = [x.strip() for x in s.split("|")]
        if len(p) < 3 or not p[0].isdigit():
            fail(f"igry.txt, строка {n}: нужно «год | название | статус» — {s[:70]}")
        year, name, st = p[0], p[1], p[2]
        prog = p[3] if len(p) > 3 else ""
        if st not in STATUS:
            fail(f"igry.txt, строка {n}: статус «{st}» — бывает только ready / soon / wait")
        if st in ("ready", "soon") and not prog:
            fail(f"igry.txt, строка {n}: для {st} нужен 4-й столбец — ключ программы (unbound, heat…)")
        if prog and f"{prog}_name" not in cfg:
            fail(f"igry.txt, строка {n}: программы «{prog}» нет в sajt.txt (нужен {prog}_name)")
        games.append({"year": year, "name": name, "st": st, "prog": prog})
    return games


def split_name(name):
    """«Need for Speed: Carbon» -> («Need for Speed», «Carbon»); «Shift 2: Unleashed» -> («», «Shift 2: Unleashed»)."""
    for pre in ("Need for Speed: ", "Need for Speed "):
        if name.startswith(pre):
            return "Need for Speed", name[len(pre):]
    return "", name


def esc(s):
    return html.escape(s, quote=True)


def main():
    if not (ROOT / "sajt.txt").exists():
        fail("нет sajt.txt рядом со скриптом")
    cfg = read_kv(ROOT / "sajt.txt")
    games = read_games(ROOT / "igry.txt", cfg)
    langs = [x.strip() for x in cfg["languages"].split(";") if x.strip()]
    main_lang = langs[0]
    base = cfg["base_url"].rstrip("/") + "/"

    texts = {}
    for L in langs:
        p = ROOT / "teksty" / f"{L}.txt"
        if not p.exists():
            fail(f"нет файла teksty/{L}.txt")
        texts[L] = read_kv(p)

    template = (ROOT / "shablon.html").read_text(encoding="utf-8")
    need = sorted(set(re.findall(r"\{\{([\w .-]+?)(?:\|attr)?\}\}", template)) |
                  {"seo_title", "seo_desc", "og_locale", "lang_name", "suggest",
                   "st_ready", "st_soon", "st_wait", "b_site", "b_download", "b_code"})

    def path_of(L):
        return "" if L == main_lang else f"{L}/"

    def url_of(L):
        return base + path_of(L)

    def md(text, L, key):
        t = html.escape(text, quote=False)
        t = t.replace("\\n", "<br>")
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)

        def link(m):
            label, target = m.group(1), m.group(2)
            u = cfg.get(target, target)
            if not u.startswith(("http://", "https://")):
                fail(f"{L}.txt, «{key}»: ссылка [{label}]({target}) — нет такого ключа в sajt.txt и это не адрес")
            return f'<a href="{esc(u)}" target="_blank" rel="noopener">{label}</a>'
        return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, t)

    def plain(h):
        return html.unescape(re.sub(r"<[^>]+>", "", h))

    def get_text(L, key):
        for src in (L, "en", main_lang):
            if src in texts and texts[src].get(key):
                if src != L:
                    warnings.append(f"{L}.txt: нет «{key}» — взял из {src}.txt")
                return md(texts[src][key], L, key)
        fail(f"текста «{key}» нет ни в {L}.txt, ни в en.txt, ни в {main_lang}.txt")

    # чистим gotovo/, но не трогаем .git (это ветка gh-pages для публикации)
    OUT.mkdir(exist_ok=True)
    for p in OUT.iterdir():
        if p.name == ".git":
            continue
        shutil.rmtree(p) if p.is_dir() else p.unlink()
    shutil.copytree(ROOT / "static", OUT, dirs_exist_ok=True)
    today = datetime.date.today().isoformat()

    for L in langs:
        T = {k: get_text(L, k) for k in need if not k.startswith(("!", "@"))}
        rel = "" if L == main_lang else "../"
        me = url_of(L)
        title, desc = plain(T["seo_title"]), plain(T["seo_desc"])

        def href_to(X):
            return (rel + path_of(X)) or "./"

        # --- карточки игр ---
        cards = []
        for g in games:
            small, big = split_name(g["name"])
            st = g["st"]
            badge = (f'<span class="b {st}">' + ('<i aria-hidden="true">?</i>' if st == "wait" else "")
                     + f'{T["st_" + st]}</span>')
            prog = ""
            if g["prog"]:
                k = g["prog"]
                ver = cfg.get(f"{k}_version", "")
                btns = []
                if cfg.get(f"{k}_site"):
                    btns.append((cfg[f"{k}_site"].rstrip("/") + "/" + path_of(L), T["b_site"], "main"))
                if cfg.get(f"{k}_download"):
                    btns.append((cfg[f"{k}_download"], T["b_download"], ""))
                if cfg.get(f"{k}_code"):
                    btns.append((cfg[f"{k}_code"], T["b_code"], ""))
                if cfg.get(f"{k}_nfsmods"):   # 13.11: страница мода на nfsmods.xyz, подпись — имя сайта, не переводится
                    btns.append((cfg[f"{k}_nfsmods"], "NFSMods", ""))
                if cfg.get(f"{k}_nexus"):     # 13.11: страница на Nexus Mods, подпись тоже не переводится
                    btns.append((cfg[f"{k}_nexus"], "Nexus Mods", ""))
                prog = (f'<p class="prog">{esc(cfg[k + "_name"])}' + (f" <small>{esc(ver)}</small>" if ver else "") + "</p>"
                        + '<p class="btns">' + "".join(
                            f'<a class="btn {c}" href="{esc(u)}" target="_blank" rel="noopener">{lbl}</a>' for u, lbl, c in btns)
                        + "</p>")
            cards.append(
                f'<article class="card {st}"><p class="yr">{g["year"]}</p>'
                f'<h3>' + (f'<small>{esc(small)}</small>' if small else "") + f'{esc(big)}</h3>'
                f'{badge}{prog}</article>')

        # --- SEO в <head> ---
        head = [
            f"<title>{esc(title)}</title>",
            f'<meta name="description" content="{esc(desc)}">',
            f'<link rel="canonical" href="{esc(me)}">',
        ]
        head += [f'<link rel="alternate" hreflang="{X}" href="{esc(url_of(X))}">' for X in langs]
        head.append(f'<link rel="alternate" hreflang="x-default" href="{esc(url_of(cfg.get("x_default", main_lang)))}">')
        head += [
            '<meta property="og:type" content="website">',
            f'<meta property="og:site_name" content="{SITE_NAME}">',
            f'<meta property="og:title" content="{esc(title)}">',
            f'<meta property="og:description" content="{esc(desc)}">',
            f'<meta property="og:url" content="{esc(me)}">',
            f'<meta property="og:locale" content="{esc(plain(T["og_locale"]))}">',
        ]
        head += [f'<meta property="og:locale:alternate" content="{esc(plain(get_text(X, "og_locale")))}">'
                 for X in langs if X != L]
        head += [
            '<meta name="twitter:card" content="summary">',
            f'<meta name="twitter:title" content="{esc(title)}">',
            f'<meta name="twitter:description" content="{esc(desc)}">',
        ]
        if cfg.get("google_verify"):
            head.append(f'<meta name="google-site-verification" content="{esc(cfg["google_verify"])}">')
        apps = []
        for g in games:
            if g["st"] != "ready":
                continue
            k = g["prog"]
            app = {"@type": "SoftwareApplication", "name": cfg[k + "_name"],
                   "applicationCategory": "GameApplication", "operatingSystem": "Windows 10, Windows 11",
                   "url": cfg[k + "_site"].rstrip("/") + "/" + path_of(L),
                   "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
                   "license": "https://www.gnu.org/licenses/gpl-3.0.html"}
            if cfg.get(k + "_version"):
                app["softwareVersion"] = cfg[k + "_version"]
            if cfg.get(k + "_download"):
                app["downloadUrl"] = cfg[k + "_download"]
            apps.append(app)
        ld = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": SITE_NAME,
            "url": me,
            "inLanguage": HTML_LANG.get(L, L),
            "description": desc,
            "author": {"@type": "Person", "name": "Kitivski", "url": cfg["kitivski"]},
            "creditText": "Kitivski + Claude",
            "about": {"@type": "VideoGameSeries", "name": "Need for Speed"},
            "hasPart": apps,
            "sameAs": [cfg["github"]],
        }
        ld_txt = json.dumps(ld, ensure_ascii=False, indent=1).replace("</", "<\\/")
        head.append(f'<script type="application/ld+json">\n{ld_txt}\n</script>')

        langs_nav = "".join(
            f'<a href="{href_to(X)}" hreflang="{X}" lang="{HTML_LANG.get(X, X)}"'
            + (' aria-current="page"' if X == L else "")
            + f'><b>{LABEL.get(X, X.upper())}</b>{esc(plain(get_text(X, "lang_name")))}</a>'
            for X in langs)
        cur_label = f'{LABEL.get(L, L.upper())} · {esc(plain(T["lang_name"]))}'
        pages = {X: {"t": plain(get_text(X, "suggest")), "href": href_to(X)} for X in langs}
        n_ready = sum(1 for g in games if g["st"] == "ready")

        special = {
            "lang": HTML_LANG.get(L, L), "code": L, "cls": "cjk" if L in CJK else "", "rel": rel, "home": href_to(L),
            "head": "\n".join(head), "langs": langs_nav, "cur_label": cur_label, "games": "\n".join(cards),
            "count": f"{n_ready} / {len(games)}",
            "pages_json": json.dumps(pages, ensure_ascii=False).replace("</", "<\\/"),
        }

        def fill(m):
            kind, key, attr = m.group(1), m.group(2), m.group(3)
            if kind == "!":
                if key not in special:
                    fail(f"shablon.html: неизвестное {{{{!{key}}}}}")
                return special[key]
            if kind == "@":
                if key not in cfg:
                    fail(f"shablon.html: {{{{@{key}}}}} — нет такого ключа в sajt.txt")
                return esc(cfg[key])
            v = T[key]
            return esc(plain(v)) if attr else v
        page = re.sub(r"\{\{([!@]?)([\w .-]+?)(\|attr)?\}\}", fill, template)
        if "{{" in page:
            fail(f"{L}: в странице остались {{{{...}}}} — проверь shablon.html")
        dest = OUT / path_of(L) / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page, encoding="utf-8")
        print(f"  {L:3} -> gotovo/{path_of(L)}index.html   «{title}»")

    # --- sitemap.xml (отдать в Google Search Console / Bing Webmaster) ---
    xdef = cfg.get("x_default", main_lang)
    rows = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for L in langs:
        rows.append(f"  <url>\n    <loc>{esc(url_of(L))}</loc>\n    <lastmod>{today}</lastmod>")
        rows += [f'    <xhtml:link rel="alternate" hreflang="{X}" href="{esc(url_of(X))}"/>' for X in langs]
        rows.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{esc(url_of(xdef))}"/>')
        rows.append("  </url>")
    rows.append("</urlset>")
    (OUT / "sitemap.xml").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("  sitemap.xml   (robots.txt не нужен: для адреса с /NFSOwnMusic/ поисковики его не читают)")

    seen = set()
    for w in warnings:
        if w not in seen:
            seen.add(w)
            print("  ! " + w)
    print(f"Готово: {len(langs)} страниц, игр {len(games)}. Папка: {OUT}")
    return cfg


def prosmotr():
    import functools
    import http.server
    import webbrowser
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    print(f"Просмотр: http://localhost:{PORT}/  (закрой это окно — просмотр остановится)")
    webbrowser.open(f"http://localhost:{PORT}/")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


def opublikovat(cfg):
    if not (OUT / ".git").exists():
        fail("gotovo/ не подключена к GitHub (нет .git) — попроси Claude подключить ветку gh-pages")

    def git(where, *args, check=True):
        r = subprocess.run(["git", "-C", str(where), *args], capture_output=True, text=True, encoding="utf-8")
        if check and r.returncode != 0:
            fail("git " + " ".join(args) + "\n" + (r.stderr or r.stdout))
        return r
    # 1) исходник сайта (тексты, шаблон, списки) -> main: чтобы он тоже был на GitHub
    git(ROOT, "add", "-A", ".")
    if git(ROOT, "diff", "--cached", "--quiet", "--", ".", check=False).returncode:
        git(ROOT, "commit", "-q", "-m", "Site source update", "--", ".")
        git(ROOT, "push", "-q", "origin", "HEAD:main")
        print("Исходник -> GitHub (main)")
    # 2) готовый сайт -> gh-pages
    git(OUT, "add", "-A")
    if not git(OUT, "status", "--porcelain").stdout.strip():
        print("Сайт не изменился — на GitHub отправлять нечего.")
        return
    git(OUT, "commit", "-q", "-m", "Site update")
    git(OUT, "push", "-q", "origin", "gh-pages")
    print("Отправлено на GitHub. Сайт обновится через 1-2 минуты: " + cfg["base_url"])


if __name__ == "__main__":
    c = main()
    if "--prosmotr" in sys.argv:
        prosmotr()
    elif "--opublikovat" in sys.argv:
        opublikovat(c)
