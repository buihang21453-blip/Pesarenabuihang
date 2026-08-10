from __future__ import annotations
from pathlib import Path
from collections import Counter, defaultdict
import re
import tinycss2

ROOT = Path(__file__).resolve().parents[1]
CSS_ROOT = ROOT / 'static'
VISUAL_PROPS = {'background','background-color','background-image','color','border','border-color','box-shadow','text-shadow','filter'}
BUTTON_RE = re.compile(r'(?i)(\.btn(?:[.\s:#\[,]|$)|button\b|\.room-neon-btn\b|\.parsec-action-btn\b|\.rui-actions\b|\.game-notice-button\b)')


def walk_rules(tokens, media=''):
    for r in tokens:
        if r.type == 'qualified-rule':
            yield media, r
        elif r.type == 'at-rule' and r.content is not None:
            name = r.lower_at_keyword
            pre = tinycss2.serialize(r.prelude).strip()
            child = tinycss2.parse_rule_list(r.content, skip_comments=True, skip_whitespace=True)
            yield from walk_rules(child, f'{media} @{name} {pre}'.strip())


def audit_file(path: Path):
    text = path.read_text(encoding='utf-8')
    tokens = tinycss2.parse_stylesheet(text, skip_comments=True, skip_whitespace=True)
    errors = [x for x in tokens if x.type == 'error']
    selectors = Counter()
    important = 0
    button_visual_rules = []
    for media, rule in walk_rules(tokens):
        sel = tinycss2.serialize(rule.prelude).strip()
        selectors[(media, sel)] += 1
        decls = tinycss2.parse_declaration_list(rule.content, skip_comments=True, skip_whitespace=True)
        vis=[]
        for d in decls:
            if d.type != 'declaration':
                continue
            if d.important:
                important += 1
            if d.lower_name in VISUAL_PROPS:
                vis.append(d.lower_name)
        if vis and BUTTON_RE.search(sel):
            button_visual_rules.append((media, sel, sorted(set(vis))))
    return {
        'errors': errors,
        'important': important,
        'selectors': selectors,
        'button_visual_rules': button_visual_rules,
        'lines': text.count('\n')+1,
    }


def main():
    files=sorted(CSS_ROOT.rglob('*.css'))
    all_selectors=defaultdict(list)
    totals={'important':0,'lines':0,'errors':0}
    rows=[]
    btn=[]
    for p in files:
        a=audit_file(p)
        rel=p.relative_to(ROOT).as_posix()
        totals['important'] += a['important']; totals['lines'] += a['lines']; totals['errors'] += len(a['errors'])
        rows.append((rel,a['lines'],a['important'],len(a['errors'])))
        for key,count in a['selectors'].items():
            if count>1:
                all_selectors[(rel,key[0],key[1])].append(count)
        for media,sel,props in a['button_visual_rules']:
            btn.append((rel,media,sel,props))

    print('CSS files:',len(files))
    print('CSS lines:',totals['lines'])
    print('!important declarations:',totals['important'])
    print('parse errors:',totals['errors'])
    print('\nPer-file:')
    for r in rows: print(f'{r[0]}\tlines={r[1]}\timportant={r[2]}\terrors={r[3]}')
    print('\nRepeated selector blocks inside same file/context:',len(all_selectors))
    for (rel,media,sel),counts in list(all_selectors.items())[:80]:
        print(f'{rel}\t{media}\t{sel}\tcount={sum(counts)}')
    print('\nButton visual owners:')
    for rel,media,sel,props in btn:
        print(f'{rel}\t{media}\t{sel}\t{",".join(props)}')

if __name__=='__main__': main()
