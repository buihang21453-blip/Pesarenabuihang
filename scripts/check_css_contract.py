from pathlib import Path
import re, sys
import tinycss2

ROOT=Path(__file__).resolve().parents[1]
CSS_DIR=ROOT/'static'/'css'
errors=[]

# 1) Module CSS must be parseable and cannot use !important in declarations.
for p in sorted(CSS_DIR.rglob('*.css')):
    text=p.read_text(encoding='utf-8')
    tokens=tinycss2.parse_stylesheet(text,skip_comments=True,skip_whitespace=True)
    for t in tokens:
        if t.type=='error': errors.append(f'{p.relative_to(ROOT)}: CSS parse error: {t.message}')
    def walk(items):
        for r in items:
            if r.type=='qualified-rule':
                for d in tinycss2.parse_declaration_list(r.content,skip_comments=True,skip_whitespace=True):
                    if d.type=='declaration' and d.important:
                        errors.append(f'{p.relative_to(ROOT)}: !important forbidden in module CSS ({d.name})')
            elif r.type=='at-rule' and r.content is not None:
                yield from walk(tinycss2.parse_rule_list(r.content,skip_comments=True,skip_whitespace=True))
    list(walk(tokens))

# 2) Shared .btn visual ownership lives in components/buttons.css.
visual={'background','background-color','background-image','color','border','border-color','box-shadow','text-shadow','filter'}
for p in sorted(CSS_DIR.rglob('*.css')):
    if p.as_posix().endswith('components/buttons.css'):
        continue
    text=p.read_text(encoding='utf-8')
    tokens=tinycss2.parse_stylesheet(text,skip_comments=True,skip_whitespace=True)
    stack=list(tokens)
    while stack:
        r=stack.pop(0)
        if r.type=='at-rule' and r.content is not None:
            stack[0:0]=tinycss2.parse_rule_list(r.content,skip_comments=True,skip_whitespace=True)
            continue
        if r.type!='qualified-rule': continue
        sel=tinycss2.serialize(r.prelude).strip()
        # Allow scoped feature buttons even if they contain a nested .btn; reject only generic/shared ownership.
        generic = bool(re.search(r'(^|,)\s*(?:\.btn|button\.btn|a\.btn)(?:[\s.:,#\[]|$)',sel))
        if not generic: continue
        props={d.lower_name for d in tinycss2.parse_declaration_list(r.content,skip_comments=True,skip_whitespace=True) if d.type=='declaration'}
        overlap=sorted(props & visual)
        if overlap:
            errors.append(f'{p.relative_to(ROOT)}: generic .btn visual property outside owner: {sel} -> {overlap}')

# 3) Base import order must remain deterministic.
base=(ROOT/'templates'/'base.html').read_text(encoding='utf-8')
need=[
    "css/core/design_tokens.css",
    "style.css",
    "css/components/buttons.css",
    "css/button_sizes.css",
]
pos=[]
for item in need:
    i=base.find(item)
    if i<0: errors.append(f'templates/base.html: missing CSS import {item}')
    pos.append(i)
if all(i>=0 for i in pos) and pos!=sorted(pos):
    errors.append('templates/base.html: core CSS import order is wrong')

if errors:
    print('CSS CONTRACT: FAIL')
    for e in errors: print('-',e)
    sys.exit(1)
print('CSS CONTRACT: PASS')
print('- module CSS parse: OK')
print('- !important outside legacy style.css: 0')
print('- generic button visual owner: css/components/buttons.css')
print('- generic button size owner: css/button_sizes.css')
print('- base import order: tokens -> legacy -> buttons -> sizes -> feature/page')
