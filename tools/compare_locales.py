import io
import os

# Base de cada archivo de localizacion (sin el sufijo _l_<lang>.yml).
# english es la referencia: cada idioma se compara contra ingles.
BASE_FILES = [
    "bt_main_3",
    "bca_intro",
    "bca_gui",
    "bac_colony_transform_events",
    "bca_gui_zone_icon",
]

REFERENCE_LANG = "english"
# Idiomas a validar contra la referencia.
LANGS = ["japanese", "russian", "simp_chinese", "spanish"]

root = os.path.dirname(os.path.dirname(__file__))


def loc_path(base, lang):
    return f"localisation/{lang}/{base}_l_{lang}.yml"


def read_keys(path):
    p = os.path.join(root, path.replace('/', os.sep))
    if not os.path.exists(p):
        return None, f"MISSING_FILE: {path}"
    with io.open(p, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
    keys = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        if s.startswith('#') or s.startswith('//'):
            continue
        # ignorar la cabecera tipo l_spanish: / l_english:
        if s.endswith(':') and s.split(':')[0].startswith('l_') and len(s.split()) == 1:
            continue
        # ignorar tags de plantilla Jinja por si se apunta a un .yml.j2
        if s.startswith('{%') or s.startswith('{{'):
            continue
        if ':' in s:
            key = s.split(':', 1)[0].strip()
            if key:
                keys.append(key)
    return set(keys), None


total_missing = {lang: 0 for lang in LANGS}
total_extra = {lang: 0 for lang in LANGS}

for base in BASE_FILES:
    ref_path = loc_path(base, REFERENCE_LANG)
    ref_keys, err = read_keys(ref_path)
    print('BASE FILE:', base)
    if ref_keys is None:
        print('  Reference (english) file missing:', err)
        print()
        continue
    print(f'  Reference (english) keys: {len(ref_keys)}')

    for lang in LANGS:
        lang_keys, lerr = read_keys(loc_path(base, lang))
        if lang_keys is None:
            print(f'  [{lang}] FILE MISSING')
            continue
        missing = sorted(ref_keys - lang_keys)   # presentes en ingles, ausentes en este idioma
        extra = sorted(lang_keys - ref_keys)      # presentes en este idioma, ausentes en ingles
        total_missing[lang] += len(missing)
        total_extra[lang] += len(extra)
        print(f'  [{lang}] missing: {len(missing)}  extra: {len(extra)}')
        for k in missing:
            print('      - missing:', k)
        for k in extra:
            print('      + extra  :', k)
    print()

print('==================== SUMMARY ====================')
for lang in LANGS:
    print(f'{lang:14s} total missing vs english: {total_missing[lang]:4d}   total extra: {total_extra[lang]:4d}')
