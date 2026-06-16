"""
Gera o manifest.json escaneando todas as pastas e HTMLs dentro de previewtemplates/.

Estrutura esperada:
  previewtemplates/
    <categoria>/              ← cada subpasta vira uma categoria no menu
      <template_grupo>/       ← subpastas agrupam HTMLs relacionados
        index.html
        outro.html
        images/

Ordem das categorias no menu (edite conforme necessário):
  banner_principal → Banner Principal
  vitrines         → Vitrines
  banners_diversos → Banners Diversos

Uso:
  python generate-manifest.py
"""

import os
import json
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT   = os.path.join(BASE_DIR, 'manifest.json')

SKIP_DIRS = {'images', 'assets', '.vscode', '.git', '__pycache__', 'node_modules', '.idea'}

# Ordem fixa das categorias no menu lateral.
# Pastas não listadas aqui aparecem ao final em ordem alfabética.
CATEGORY_ORDER = [
    'banner_principal',
    'vitrines',
    'banners_diversos',
    'emails_completos',
]


def prettify(name: str) -> str:
    """Converte nome de pasta/arquivo em label legível."""
    # Remove prefixo numérico de data (ex: 12052026_nome → nome)
    name = re.sub(r'^\d{6,8}[_-]', '', name)
    # Substitui separadores por espaço
    name = name.replace('_', ' ').replace('-', ' ')
    # Capitaliza cada palavra
    return ' '.join(w.capitalize() for w in name.split() if w)


def label_from_file(filename: str) -> str:
    """Gera label a partir do nome do arquivo sem extensão."""
    stem = os.path.splitext(filename)[0]
    if stem == 'index':
        return 'index'
    return prettify(stem)


def scan_category(cat_name: str, cat_path: str) -> dict:
    """Escaneia uma pasta de categoria e retorna seu objeto com templates."""
    templates = {}  # group_id → {id, label, files[]}

    for root, dirs, files in os.walk(cat_path):
        dirs[:] = sorted([
            d for d in dirs
            if d not in SKIP_DIRS and not d.startswith('.')
        ])

        html_files = sorted([f for f in files if f.endswith('.html')])
        if not html_files:
            continue

        rel_root = os.path.relpath(root, cat_path)
        parts    = rel_root.replace('\\', '/').split('/')

        if rel_root == '.':
            group_id    = cat_name
            group_label = prettify(cat_name)
        else:
            group_id    = parts[0]
            group_label = prettify(parts[0])

        if group_id not in templates:
            templates[group_id] = {
                'id':    group_id,
                'label': group_label,
                'files': []
            }

        for fname in html_files:
            full   = os.path.join(root, fname)
            rel    = os.path.relpath(full, BASE_DIR).replace('\\', '/')
            stem   = os.path.splitext(fname)[0]
            templates[group_id]['files'].append({
                'name':  stem,
                'label': label_from_file(fname),
                'path':  rel
            })

    return {
        'id':        cat_name,
        'label':     prettify(cat_name),
        'templates': list(templates.values())
    }


def scan() -> dict:
    # Descobre todas as pastas de categoria válidas
    all_dirs = {
        name for name in os.listdir(BASE_DIR)
        if os.path.isdir(os.path.join(BASE_DIR, name))
        and not name.startswith('.')
        and name not in SKIP_DIRS
    }

    # Ordena: primeiro as da lista fixa, depois o restante alfabético
    ordered = [d for d in CATEGORY_ORDER if d in all_dirs]
    extras  = sorted(all_dirs - set(CATEGORY_ORDER))
    ordered += extras

    categories = []
    for cat_name in ordered:
        cat_path = os.path.join(BASE_DIR, cat_name)
        categories.append(scan_category(cat_name, cat_path))

    return {'categories': categories}


if __name__ == '__main__':
    import sys
    # Garante saida UTF-8 no terminal Windows
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    data = scan()

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f'[OK] manifest.json gerado em {OUTPUT}\n')

    total_templates = 0
    for cat in data['categories']:
        total_files = sum(len(t['files']) for t in cat['templates'])
        total_templates += total_files
        print(f'  [{cat["label"]}]')
        for t in cat['templates']:
            for file in t['files']:
                marker = '+-' if file != t['files'][-1] else '\\-'
                label  = t['label'] if file['name'] == 'index' else f'{t["label"]} -- {file["label"]}'
                print(f'     {marker} {label}')
                print(f'        {file["path"]}')

    print(f'\n[OK] Total: {total_templates} template(s) em {len(data["categories"])} categoria(s)')
