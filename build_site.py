"""Build the static homfaxtm.com marketing site for GitHub Pages.

Source: H:\HomFax-Core\public (identical to what was live on homfax-vm1).
Output: <scratchpad>\site

Owner directive 2026-11-14: the front page must remain the same, but every link
to information, services, property reports or other services sends an email to
homfaxtm@homfaxtm.com, because the backend (homfax-vm1) is offline.

What changes and what does not:
  - index.html, inspection.html, privacy.html, terms.html are kept, pixel for
    pixel, except for link targets and the two lead forms.
  - Nine destinations that no longer exist become mailto: links with a subject
    that tells the inbox what was asked for.
  - The two forms (claim review on the front page, free assessment on the QR
    landing page) open the visitor's email app with their details pre-filled
    instead of POSTing to /api/public/leads. The success message says exactly
    that; the old "a confirmation email is on its way" would now be false.
  - Root-absolute asset paths become relative so the same files render at
    https://bodhinath.github.io/homfaxtm-site/ (preview) and at homfaxtm.com.
"""
import os, re, shutil, sys

SRC = r"H:\HomFax-Core\public"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")
MAIL = "homfaxtm@homfaxtm.com"

def mailto(subject):
    from urllib.parse import quote
    return f"mailto:{MAIL}?subject={quote(subject)}"

# dead destinations -> email, with a subject the inbox can triage on
LINKS = {
    '/report.html':       mailto("Property Report Request"),
    '/contact.html':      mailto("Contact HomFax"),
    '/contractors.html':  mailto("Contractor Network Inquiry"),
    '/siu.html':          mailto("SIU / Claim Verification Inquiry"),
    '/app.html':          mailto("Platform Access Request"),
    '/warranty.html':     mailto("Warranty Inquiry"),
    'https://go.homfaxtmarlingtontx.com/': mailto("Storm Check Request"),
}
# pages that stay pages (relative so the preview URL works too)
KEEP = {
    'href="/"': 'href="./"',
    'href="/inspection.html"': 'href="inspection.html"',
    'href="/privacy.html"': 'href="privacy.html"',
    'href="/terms.html"': 'href="terms.html"',
}

OK_MSG = ('&#10004; Your email app should now be open with your request pre-filled &mdash; just press <b>Send</b>.<br>'
          '<span style="font-weight:500">If it didn&rsquo;t open, email '
          f'<a href="mailto:{MAIL}" style="color:inherit">{MAIL}</a> or call '
          '<a href="tel:+18444663290" style="color:inherit">(844) 466-3290</a>. We reply the same business day.</span>')

def handler(form_id, subject, extra_lines, button_text):
    return f"""document.getElementById('{form_id}').addEventListener('submit', (e) => {{
    e.preventDefault();
    const f = e.target;
    if (f.website && f.website.value) return;   // honeypot
    const v = (n) => (f[n] && f[n].value ? f[n].value.trim() : '');
    const lines = [
      '{subject}',
      '',
      'Name: ' + v('fullName'),
      'Email: ' + v('email'),
      'Property: ' + [v('addressLine1'), v('city'), v('zip')].filter(Boolean).join(', '),
{extra_lines}
      '',
      'Sent from homfaxtm.com',
    ];
    window.location.href = 'mailto:{MAIL}?subject=' + encodeURIComponent('{subject}')
      + '&body=' + encodeURIComponent(lines.join('\\n'));
    f.style.display = 'none';
    const ok = document.getElementById('okMsg');
    ok.style.display = 'block';
    setTimeout(() => ok.scrollIntoView({{ block: 'center', behavior: 'instant' }}), 120);
  }});"""

HANDLER_RE = re.compile(r"document\.getElementById\('(\w+)'\)\.addEventListener\('submit', async \(e\) => \{.*?\n  \}\);", re.S)
OKMSG_RE = re.compile(r'(<div class="ok-msg" id="okMsg">).*?(</div>)', re.S)

def rewrite(name, html):
    report = []
    for old, new in LINKS.items():
        n = html.count(f'href="{old}"')
        if n:
            html = html.replace(f'href="{old}"', f'href="{new}"'); report.append(f"{old} -> mailto x{n}")
    for old, new in KEEP.items():
        html = html.replace(old, new)
    # relative assets
    html = re.sub(r'(src|href)="/(ads/|logo\.jpg)', r'\1="\2', html)
    html = html.replace("url('/ads/", "url('ads/")
    # forms
    def sub_handler(m):
        fid = m.group(1)
        if fid == 'reviewForm':
            extra = ("      'Claim situation: ' + (f.situation && f.situation.selectedIndex > 0 ? f.situation.options[f.situation.selectedIndex].text : 'not stated'),\n"
                     "      'Details: ' + v('details'),")
            return handler(fid, 'Free Claim Review Request', extra, 'Request my free claim review')
        if fid == 'leadForm':
            return handler(fid, 'Free Storm Damage Assessment Request', "      'Source: inspection landing page',", 'Get my free assessment')
        return m.group(0)
    html, nh = HANDLER_RE.subn(sub_handler, html)
    if nh: report.append(f"form handler(s) replaced x{nh}")
    html, nk = OKMSG_RE.subn(lambda m: m.group(1) + OK_MSG + m.group(2), html)
    if nk: report.append(f"okMsg rewritten x{nk}")
    left = re.findall(r"fetch\(|href=\"/(?!/)[^\"]+\"", html)
    if left: report.append(f"REMAINING root links/fetch: {sorted(set(left))}")
    return html, report

if os.path.isdir(OUT): shutil.rmtree(OUT)
os.makedirs(os.path.join(OUT, "ads"))
for p in ["index.html", "inspection.html", "privacy.html", "terms.html"]:
    html = open(os.path.join(SRC, p), encoding="utf-8").read()
    html, rep = rewrite(p, html)
    open(os.path.join(OUT, p), "w", encoding="utf-8", newline="\n").write(html)
    print(f"{p}: " + ("; ".join(rep) if rep else "no changes"))

# assets actually referenced
refs = set()
for p in ["index.html", "inspection.html", "privacy.html", "terms.html"]:
    t = open(os.path.join(OUT, p), encoding="utf-8").read()
    refs |= set(re.findall(r'(?:src=|href=|url\()\s*[\'"]?((?:ads/)?[\w.-]+\.(?:jpg|jpeg|png|webp|svg|gif))', t))
n = 0
for r in sorted(refs):
    s, d = os.path.join(SRC, r.replace("/", os.sep)), os.path.join(OUT, r.replace("/", os.sep))
    if os.path.exists(s): shutil.copy2(s, d); n += 1
    else: print("  MISSING asset:", r)
print(f"assets copied: {n}")

open(os.path.join(OUT, ".nojekyll"), "w").write("")
open(os.path.join(OUT, "404.html"), "w", encoding="utf-8").write(f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HomFax&trade; &mdash; Page moved</title>
<style>body{{font-family:'Segoe UI',system-ui,sans-serif;background:#f6f8fb;color:#14213a;display:grid;place-items:center;min-height:100vh;margin:0;text-align:center;padding:24px}}
a.b{{display:inline-block;margin:8px;padding:13px 22px;border-radius:10px;font-weight:800;text-decoration:none;color:#fff;background:linear-gradient(135deg,#3ea82c,#23761d)}}a.o{{background:#1553a4}}</style></head>
<body><div><img src="logo.jpg" alt="HomFax" style="height:64px;border-radius:12px"><h1>That page has moved.</h1>
<p>Tell us what you need and we&rsquo;ll reply the same business day.</p>
<a class="b" href="mailto:{MAIL}?subject=HomFax%20Inquiry">Email {MAIL}</a><a class="b o" href="./">Back to homfaxtm.com</a>
<p style="color:#5b6b85;font-size:.85rem">or call <a href="tel:+18444663290">(844) 466-3290</a></p></div></body></html>""")
print("wrote .nojekyll, 404.html ->", OUT)
