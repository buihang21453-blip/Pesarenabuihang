"""Read-only GĐ2 draw logo lookup from Supabase clubs_import and teams.

No changes to club assignments, Pot rules, imported rows or Storage objects.
clubs_import wins when both catalogs provide a usable URL.
"""

import os
import re
import unicodedata


_ALIASES = {
    'bayern munich': 'bayern', 'fc bayern munchen': 'bayern', 'bayern munchen': 'bayern',
    'fc bayern': 'bayern', 'fc bayern munich': 'bayern', 'real madrid cf': 'real madrid',
    'fc barcelona': 'barcelona', 'paris saint germain': 'psg', 'paris sg': 'psg',
    'paris saint germain fc': 'psg', 'liverpool fc': 'liverpool',
    'manchester city': 'man city', 'manchester city fc': 'man city',
    'arsenal fc': 'arsenal', 'inter milan': 'inter', 'internazionale': 'inter',
    'fc internazionale milano': 'inter', 'atletico de madrid': 'atletico madrid',
    'club atletico de madrid': 'atletico madrid', 'manchester united': 'man united',
    'manchester united fc': 'man united', 'aston villa fc': 'aston villa',
    'ssc napoli': 'napoli', 'as roma': 'roma', 'fenerbahce sk': 'fenerbahce',
    'galatasaray sk': 'galatasaray', 'borussia dortmund': 'dortmund',
    'bvb': 'dortmund', 'psv eindhoven': 'psv', 'villarreal cf': 'villarreal',
    'real betis balompie': 'real betis', 'lille osc': 'lille',
    'rc lens': 'lens', 'racing club de lens': 'lens', 'como 1907': 'como',
    'fc porto': 'porto', 'fcporto': 'porto', 'rb leipzig': 'rb leipzig',
    'rasenballsport leipzig': 'rb leipzig',
}


def normalize_club(name):
    name = unicodedata.normalize('NFKD', str(name or '').casefold())
    name = ''.join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r'[^a-z0-9]+', ' ', name).strip()
    return _ALIASES.get(name, name)


def _valid_url(url):
    url = str(url or '').strip()
    return url if url.startswith(('https://', 'http://', '/static/')) else ''


def _logo_url(row, db, supabase_url):
    for field in ('logo_url', 'crest_url', 'image_url', 'logo', 'crest'):
        result = _valid_url(row.get(field))
        if result:
            return result
    # A filename alone does not identify a Storage bucket. The established
    # team-logos bucket may be overridden for clubs_import deployments.
    path = next((str(row.get(key)).strip() for key in ('logo_path', 'logo_file', 'storage_path')
                 if row.get(key)), '')
    if not path or path.startswith(('/', '../')) or '..' in path.split('/'):
        return ''
    bucket = os.getenv('CLUBS_IMPORT_LOGO_BUCKET', 'team-logos').strip()
    if not bucket or not supabase_url:
        return ''
    try:
        result = db.storage.from_(bucket).get_public_url(path)
        if isinstance(result, dict):
            result = result.get('publicUrl') or result.get('public_url') or ''
        return _valid_url(result)
    except Exception:
        return ''


def _row_name(row):
    for field in ('club_name', 'team_name', 'team', 'name', 'club', 'display', 'slug'):
        if row.get(field):
            return str(row[field]).strip()
    return ''


def load_draw_club_logos(db, execute_query, supabase_url, clubs, team_loader=None, logger=None):
    """Return (canonical-name -> URL, source info) for only the 24 approved clubs."""
    canonical = {normalize_club(name): name for name in clubs}
    found = {}
    sources = {}
    imported = set()
    import_available = False
    try:
        result = execute_query(db.table('clubs_import').select('*').limit(1000),
                               'draw_clubs_import_logos', attempts=2)
        import_available = True
        for row in result.data or []:
            name = normalize_club(_row_name(row))
            if name not in canonical:
                continue
            imported.add(name)
            url = _logo_url(row, db, supabase_url)
            if url:
                found[name], sources[name] = url, 'clubs_import'
    except Exception as exc:
        if logger:
            logger.warning('clubs_import logo lookup unavailable; using teams fallback: %s', exc)
    try:
        for row in (team_loader() if team_loader else []):
            name = normalize_club(_row_name(row))
            if name in canonical and name not in found:
                url = _logo_url(row, db, supabase_url)
                if url:
                    found[name], sources[name] = url, 'teams'
    except Exception as exc:
        if logger:
            logger.warning('Draw teams logo fallback unavailable: %s', exc)
    urls = {name: found.get(normalize_club(name), '') for name in clubs}
    info = {
        'clubs_import': sum(source == 'clubs_import' for source in sources.values()),
        'teams_fallback': sum(source == 'teams' for source in sources.values()),
        'without_logo': [name for name in clubs if not urls[name]],
        'missing_in_import': ([name for name in clubs if normalize_club(name) not in imported]
                              if import_available else None),
        'import_available': import_available,
    }
    return urls, info
