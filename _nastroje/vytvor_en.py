"""Vytvoří anglickou verzi webu do složky en/ z českých stránek.

Použití (z kořene repozitáře):  python3 _nastroje/vytvor_en.py
Překlady jsou v _nastroje/preklad_en.py. Když se změní český text,
doplňte jeho překlad tam – skript vypíše texty, které překlad nemají.
Složky začínající podtržítkem GitHub Pages nezveřejňuje.
"""
import glob, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from preklad_en import EN, JS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEEP = {'Brno', 'Ostrava', 'Plzeň', 'Liberec', 'Hradec Králové', 'České Budějovice', 'Olomouc', 'Ústí nad Labem', 'vse', 'realizace', 'projekce', 'false', 'EN', 'English', 'DP', 'OV', 'Facebook', 'Instagram',
        'info@owax.cz', 'Bc. David Pivoňka', 'Bc. Ondřej Vlček', 'OWAX – Bc. David Pivoňka & Bc. Ondřej Vlček',
        '&nbsp; +420 723 557 807', '&nbsp;·&nbsp;'}   # hodnoty pro skripty, nepřekládat
TEXT_ATTRS = ('alt', 'title', 'aria-label', 'placeholder', 'content', 'value')
LANG_CSS = """
/* Přepínač jazyka CZ / EN v hlavičce */
.lang-switch {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 48px;
    height: 40px;
    padding: 0 0.8rem;
    border: 1px solid rgba(255, 255, 255, 0.35);
    border-radius: 50px;
    color: #ffffff;
    font-weight: 700;
    font-size: 0.85rem;
    letter-spacing: 0.06em;
    text-decoration: none;
    transition: var(--transition);
}

.lang-switch:hover {
    background: rgba(255, 255, 255, 0.12);
    border-color: #ffffff;
}
"""

missing = set()

def tr(s):
    core = s.strip()
    if not core or not re.search(r'[A-Za-zÁ-ž]', core) or core in KEEP:
        return s
    if core in EN:
        return s.replace(core, EN[core])
    missing.add(core)
    return s

def tr_tag(tag):
    def attr(m):
        name, q, val = m.group(1), m.group(2), m.group(3)
        if name in TEXT_ATTRS:
            if name == 'content' and not re.search(r'[A-Za-zÁ-ž]{3}', val) or val.startswith('http'):
                return m.group(0)
            return f'{name}={q}{tr(val)}{q}'
        return m.group(0)
    if re.match(r'<meta[^>]+(name="(viewport|robots)"|property="og:(type|url|image|locale)")', tag):
        return tag
    return re.sub(r'([\w-]+)=(["\'])(.*?)\2', attr, tag)

ASSET = re.compile(r'^(foto/|video/|vendor/|logo\.png|favicon\.png|apple-touch-icon\.png)')

def fix_paths(t):
    t = re.sub(r'(src|href|poster|data-bg)="([^"#:]+?)"',
               lambda m: f'{m.group(1)}="../{m.group(2)}"' if ASSET.match(m.group(2)) else m.group(0), t)
    t = re.sub(r"url\('((?:foto/|video/)[^']*)'\)", r"url('../\1')", t)
    return t

def page_url(name, en):
    base = 'https://owax.cz/' + ('en/' if en else '')
    return base if name == 'index.html' else base + name

def add_switch(t, name, en):
    """Přepínač jazyka + odkazy hreflang (bezpečné spustit opakovaně)."""
    t = re.sub(r'\n    <link rel="alternate" hreflang="[^"]+" href="[^"]+">', '', t)
    t = re.sub(r'\n                <a href="[^"]*" class="lang-switch".*?</a>', '', t)
    if '.lang-switch {' not in t:
        t = t.replace('\n    </style>', LANG_CSS + '\n    </style>', 1)
    alt = ''.join(f'\n    <link rel="alternate" hreflang="{l}" href="{u}">' for l, u in
                  (('cs', page_url(name, False)), ('en', page_url(name, True)), ('x-default', page_url(name, False))))
    t = re.sub(r'(\n    <link rel="canonical" href="[^"]+">)', lambda m: m.group(1) + alt, t, count=1)
    other = '' if name == 'index.html' else name
    if en:
        link = f'<a href="../{other or "./"}" class="lang-switch" hreflang="cs" lang="cs" title="Česky">CZ</a>'
    else:
        link = f'<a href="en/{other}" class="lang-switch" hreflang="en" lang="en" title="English">EN</a>'
    t = t.replace('\n                <button class="hamburger"', '\n                ' + link + '\n                <button class="hamburger"', 1)
    return t

def to_en(t, name):
    t = t.replace('<html lang="cs">', '<html lang="en">')
    t = t.replace('content="cs_CZ"', 'content="en_GB"')
    t = re.sub(r'(<link rel="canonical" href=")[^"]+', lambda m: m.group(1) + page_url(name, True), t, count=1)
    t = re.sub(r'(<meta property="og:url" content=")[^"]+', lambda m: m.group(1) + page_url(name, True), t, count=1)
    parts = re.split(r'(<style>.*?</style>|<script[^>]*>.*?</script>|<!--.*?-->|<[^>]+>)', t, flags=re.S)
    out = []
    for p in parts:
        if p.startswith('<script'):
            for a, b in JS.items():
                p = p.replace(a, b)
            out.append(p)
        elif p.startswith('<style') or p.startswith('<!--'):
            out.append(p)
        elif p.startswith('<'):
            out.append(tr_tag(p))
        else:
            out.append(tr(p))
    return fix_paths(''.join(out)).replace('&amp;hl=cs&amp;', '&amp;hl=en&amp;')

os.makedirs(os.path.join(ROOT, 'en'), exist_ok=True)
for path in sorted(glob.glob(os.path.join(ROOT, '*.html'))):
    name = os.path.basename(path)
    with open(path, encoding='utf8', newline='') as f:
        cz = f.read()
    cz = add_switch(cz, name, False)
    with open(path, 'w', encoding='utf8', newline='') as f:
        f.write(cz)
    en = add_switch(to_en(cz, name), name, True)
    with open(os.path.join(ROOT, 'en', name), 'w', encoding='utf8', newline='') as f:
        f.write(en)

# sitemap s oběma jazyky
names = [os.path.basename(p) for p in sorted(glob.glob(os.path.join(ROOT, '*.html')))]
names.sort(key=lambda n: n != 'index.html')
rows = ''.join(f'    <url><loc>{page_url(n, e)}</loc></url>\n' for e in (False, True) for n in names)
with open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf8') as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + rows + '</urlset>\n')

if missing:
    print('Chybí překlad pro:')
    for m in sorted(missing):
        print('  -', m)
else:
    print('Hotovo – vše přeloženo.')
