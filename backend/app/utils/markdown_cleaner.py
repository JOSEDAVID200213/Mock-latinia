"""
Convierte texto Markdown al formato limpio y legible para Google Docs.

El Apps Script inserta el texto como texto plano. Este módulo transforma
el Markdown generado por Gemini en un documento bien estructurado,
fácil de leer para un usuario final, sin ningún símbolo Markdown visible.

Transformaciones:
  # Título          → TÍTULO EN MAYÚSCULAS con línea de iguales
  ## Sección        → Sección con línea de guiones
  ### Subsección    → Subsección en negrita simulada (mayúsculas + dos puntos)
  **negrita**       → solo el texto (sin asteriscos)
  *cursiva*         → solo el texto
  `código`          → solo el texto
  | tabla 2 cols |  → Clave: Valor (una por línea, con sangría)
  | tabla N cols |  → Bloques numerados (un campo por línea, sangría clara)
  - item            → • item (con sangría)
  1. item           → 1. item (con sangría)
  > cita            → "cita entre comillas"
  ---               → espacio visual (línea en blanco)
"""

from __future__ import annotations

import re


# ─── Helpers de texto inline ──────────────────────────────────────────────────

def _strip_inline(text: str) -> str:
    """Quita marcadores inline de Markdown: **bold**, *italic*, `code`."""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)   # **bold**
    text = re.sub(r'\*(.+?)\*', r'\1', text)         # *italic*
    text = re.sub(r'`(.+?)`', r'\1', text)            # `code`
    return text.strip()


# ─── Renderizador de tablas ───────────────────────────────────────────────────

def _is_separator_row(row_line: str) -> bool:
    """Devuelve True si la fila es un separador Markdown (|---|---|)."""
    return bool(re.match(r'^\|[-|: ]+\|$', row_line))


def _parse_table_lines(lines: list[str], start: int) -> tuple[list[list[str]], int]:
    """
    Consume líneas de tabla desde `start` y devuelve (filas_de_datos, nuevo_índice).
    Excluye las filas separadoras (|---|---|).
    """
    rows: list[list[str]] = []
    i = start
    while i < len(lines):
        line = lines[i]
        if not (line.startswith('|') and line.endswith('|')):
            break
        if not _is_separator_row(line):
            cells = [_strip_inline(c) for c in line[1:-1].split('|')]
            rows.append(cells)
        i += 1
    return rows, i


def _format_table(rows: list[list[str]]) -> str:
    """
    Convierte filas de tabla a texto legible para Docs.

    • Tablas de 2 columnas  →  "  Clave: Valor" (una por línea)
    • Tablas de N columnas  →  bloques numerados, un campo por línea
    """
    if not rows:
        return ''

    headers = [h.strip() for h in rows[0]]
    data_rows = rows[1:]

    if not data_rows:
        # Solo hay encabezado, mostrarlo como lista de campos
        return '  ' + ' | '.join(headers)

    output_lines: list[str] = []

    if len(headers) == 2:
        # ── Tabla de 2 columnas: Clave: Valor ──────────────────────────────
        for row in data_rows:
            key = row[0] if len(row) > 0 else ''
            val = row[1] if len(row) > 1 else ''
            if key or val:
                output_lines.append(f'  {key}: {val}')

    else:
        # ── Tabla de N columnas: bloques numerados ─────────────────────────
        for idx, row in enumerate(data_rows, 1):
            # Línea de separación entre items para legibilidad
            if idx > 1:
                output_lines.append('')
            output_lines.append(f'  [{idx}]')
            for j, cell in enumerate(row):
                header = headers[j] if j < len(headers) else f'Campo {j + 1}'
                value = cell.strip()
                if value and value.lower() not in ('', '-', '—', 'n/a'):
                    output_lines.append(f'      {header}: {value}')

    return '\n'.join(output_lines)


# ─── Convertidor principal ─────────────────────────────────────────────────────

def markdown_to_docs_text(markdown: str) -> str:
    """
    Convierte Markdown a texto limpio, estructurado y legible para Google Docs.

    Args:
        markdown: Texto en formato Markdown generado por Gemini.

    Returns:
        Texto plano formateado, listo para insertar en un Google Doc sin
        que aparezca ningún símbolo Markdown (##, **, |---|, etc.).
    """
    lines = markdown.split('\n')
    output: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # ── H1: Título principal del documento ────────────────────────────────
        m = re.match(r'^#\s+(?!#)(.+)$', line)
        if m:
            title = _strip_inline(m.group(1))
            separator = '=' * min(len(title), 60)
            output.append('')
            output.append(title.upper())
            output.append(separator)
            output.append('')
            i += 1
            continue

        # ── H2: Sección principal ─────────────────────────────────────────────
        m = re.match(r'^##\s+(?!#)(.+)$', line)
        if m:
            section = _strip_inline(m.group(1))
            separator = '-' * min(len(section), 50)
            output.append('')
            output.append(section)
            output.append(separator)
            i += 1
            continue

        # ── H3: Subsección ────────────────────────────────────────────────────
        m = re.match(r'^###\s+(.+)$', line)
        if m:
            subsection = _strip_inline(m.group(1))
            output.append('')
            output.append(f'▸ {subsection}')
            i += 1
            continue

        # ── H4: Sub-subsección ────────────────────────────────────────────────
        m = re.match(r'^####\s+(.+)$', line)
        if m:
            label = _strip_inline(m.group(1))
            output.append(f'  → {label}')
            i += 1
            continue

        # ── Separador horizontal ──────────────────────────────────────────────
        if re.match(r'^-{3,}$', line.strip()) or re.match(r'^\*{3,}$', line.strip()):
            output.append('')
            i += 1
            continue

        # ── Tabla Markdown ────────────────────────────────────────────────────
        if line.startswith('|') and line.endswith('|'):
            table_rows, i = _parse_table_lines(lines, i)
            if table_rows:
                formatted = _format_table(table_rows)
                if formatted:
                    output.append(formatted)
            continue

        # ── Lista de viñetas (-, *, •) ────────────────────────────────────────
        m = re.match(r'^(\s*)[-*•]\s+(.+)$', line)
        if m:
            indent_spaces = len(m.group(1))
            indent = '  ' * (indent_spaces // 2 + 1)
            content = _strip_inline(m.group(2))
            output.append(f'{indent}• {content}')
            i += 1
            continue

        # ── Lista numerada ────────────────────────────────────────────────────
        m = re.match(r'^(\s*)(\d+)[.)]\s+(.+)$', line)
        if m:
            indent_spaces = len(m.group(1))
            indent = '  ' * (indent_spaces // 2 + 1)
            num = m.group(2)
            content = _strip_inline(m.group(3))
            output.append(f'{indent}{num}. {content}')
            i += 1
            continue

        # ── Cita / blockquote ─────────────────────────────────────────────────
        if line.startswith('> '):
            content = _strip_inline(line[2:])
            if content:
                output.append(f'  "{content}"')
            i += 1
            continue

        # ── Línea en blanco ───────────────────────────────────────────────────
        if not line.strip():
            output.append('')
            i += 1
            continue

        # ── Párrafo normal ────────────────────────────────────────────────────
        output.append(_strip_inline(line))
        i += 1

    # ── Post-proceso: colapsar más de 2 líneas vacías consecutivas ────────────
    result_lines: list[str] = []
    empty_count = 0
    for ln in output:
        if ln == '':
            empty_count += 1
            if empty_count <= 1:
                result_lines.append(ln)
        else:
            empty_count = 0
            result_lines.append(ln)

    # Quitar líneas vacías al inicio y al final
    final = '\n'.join(result_lines).strip()
    return final
