"""
Gera o manifest.json escaneando todas as pastas e HTMLs dentro de previewtemplates/.

Estrutura esperada:
  previewtemplates/
    <categoria>/              ← cada subpasta vira uma categoria no menu
      <template_grupo>/       ← subpastas agrupam HTMLs relacionados
        index.html
        outro.html
        images/

Uso:
  python generate-manifest.py
"""

import os
import json
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT   = os.path.join(BASE_DIR, 'manifest.json')

SKIP_DIRS  = {'images', '.vscode', '.git', '__pycache__', 'node_modules', '.idea'}
SKIP_FILES = {'index.html'}  # nunca pular — incluir tudo
SKIP_SELF  = {'index.html'}  # o próprio index.html do previewtemplates, não das subpastas


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


def scan() -> dict:
    categories = []

    entries = sorted(os.listdir(BASE_DIR))
    for cat_name in entries:
        cat_path = os.path.join(BASE_DIR, cat_name)

        # Ignora arquivos, pastas ocultas, pastas de skip e a própria raiz
        if not os.path.isdir(cat_path):
            continue
        if cat_name.startswith('.') or cat_name in SKIP_DIRS:
            continue

        templates = {}  # group_id → {id, label, files[]}

        for root, dirs, files in os.walk(cat_path):
            # Prune dirs in-place to skip unwanted folders
            dirs[:] = sorted([
                d for d in dirs
                if d not in SKIP_DIRS and not d.startswith('.')
            ])

            html_files = sorted([f for f in files if f.endswith('.html')])
            if not html_files:
                continue

            # Determina o grupo a partir do primeiro nível de subpasta
            rel_root  = os.path.relpath(root, cat_path)
            parts     = rel_root.replace('\\', '/').split('/')

            if rel_root == '.':
                # HTMLs diretamente na pasta da categoria (raro)
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
                # Caminho relativo a BASE_DIR (ex: vitrines/basicos_burgundy_fem/index.html)
                rel    = os.path.relpath(full, BASE_DIR).replace('\\', '/')
                stem   = os.path.splitext(fname)[0]
                flabel = label_from_file(fname)

                templates[group_id]['files'].append({
                    'name':  stem,
                    'label': flabel,
                    'path':  rel
                })

        if templates:
            categories.append({
                'id':        cat_name,
                'label':     prettify(cat_name),
                'templates': list(templates.values())
            })

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
