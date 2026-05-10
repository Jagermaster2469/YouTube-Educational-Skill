#!/usr/bin/env python3
"""
YouTube Educational Pipeline

Pipeline multi-modelo para convertir videos de YouTube en notas educativas
profundas dentro de un vault de Obsidian (Learning Vault).

Uso:
    # Paso 1: Fetch transcript + chunking
    python3 educational_pipeline.py fetch "URL" [--output chunks.json]

    # Paso 2: Escribir notas procesadas en vault
    python3 educational_pipeline.py write processed_data.json --topic "Tema"

Compatibilidad: macOS / Linux, Python 3.9+
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# ─── Configuración ───────────────────────────────────────────────────────────

LEARNING_VAULT = os.environ.get(
    "LEARNING_VAULT_PATH",
    os.path.expanduser("~/Documents/Learning Vault")
)
DATE_FORMAT = os.environ.get("LEARNING_VAULT_DATE_FORMAT", "dd/mm/aa")

# ─── Sanitización ────────────────────────────────────────────────────────────

def yaml_quote(value: str) -> str:
    """
    Escapa un valor para ser usado dentro de un campo YAML (frontmatter).
    Si contiene comillas, saltos de línea o caracteres especiales,
    lo envuelve en comillas escapando las internas.
    """
    if not isinstance(value, str):
        value = str(value)
    # Si ya está entre comillas, las removemos para re-escapar
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    # Escapar comillas dobles internas
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    # Si contiene caracteres riesgosos, siempre entrecomillar
    risky = re.search(r'["\n\r:#{}\[\],&*?|<>=!%@`]', escaped)
    if risky or not escaped.strip():
        return f'"{escaped}"'
    return escaped

def md_sanitize(text: str) -> str:
    """
    Sanitiza texto para incrustar en Markdown de forma segura.
    Escapa secuencias que romperían el frontmatter (---).
    """
    if not isinstance(text, str):
        text = str(text)
    # Reemplazar --- dentro del texto por - - - (evita romper frontmatter)
    text = re.sub(r'(?m)^---\s*$', '- - -', text)
    # Escapar wikilinks crudos que puedan interferir
    return text

def wikilink_safe(target: str, label: str = None) -> str:
    """
    Genera un wikilink Obsidian seguro: [[target|label]]
    Escapa caracteres especiales en el target.
    """
    target = sanitize_filename(target)
    if label:
        # Escapar pipes y corchetes en el label
        label_clean = label.replace('[', '(').replace(']', ')').replace('|', '/')
        return f"[[{target}|{label_clean}]]"
    return f"[[{target}]]"

def validate_url(url: str) -> str:
    """Valida y limpia una URL. Retorna string vacío si es inválida."""
    if not url or not isinstance(url, str):
        return ""
    # Solo permitir http/https
    if re.match(r'^https?://', url.strip()):
        return url.strip()
    return ""

# ─── Utilidades de video ─────────────────────────────────────────────────────

def extract_video_id(url_or_id: str) -> str:
    """Extrae el video ID de 11 chars de cualquier URL de YouTube."""
    url_or_id = url_or_id.strip()
    patterns = [
        r'(?:v=|youtu\.be/|shorts/|embed/|live/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return url_or_id  # fallback — asume que ya es un ID

# ─── Transcript ──────────────────────────────────────────────────────────────

def fetch_transcript(video_id: str, languages: list = None) -> dict:
    """Obtiene el transcript usando youtube-transcript-api."""
    from youtube_transcript_api import YouTubeTranscriptApi

    api = YouTubeTranscriptApi()
    try:
        if languages:
            result = api.fetch(video_id, languages=languages)
        else:
            result = api.fetch(video_id)
    except Exception as e:
        return {"error": str(e), "video_id": video_id}

    segments = [
        {"text": seg.text.strip(), "start": seg.start, "duration": seg.duration}
        for seg in result
    ]

    if not segments:
        return {"error": "Empty transcript", "video_id": video_id}

    full_text = " ".join(seg["text"] for seg in segments)
    duration_sec = segments[-1]["start"] + segments[-1]["duration"]

    return {
        "video_id": video_id,
        "segments": segments,
        "full_text": full_text,
        "duration_sec": duration_sec,
        "duration_str": fmt_timestamp(duration_sec),
        "segment_count": len(segments),
    }

def fmt_timestamp(seconds: float) -> str:
    """Convierte segundos a MM:SS o HH:MM:SS."""
    total = int(seconds)
    h, remainder = divmod(total, 3600)
    m, s = divmod(remainder, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

# ─── Chunking ────────────────────────────────────────────────────────────────

def chunk_transcript(data: dict, max_chars: int = 30000, overlap: int = 3000) -> list:
    """
    Divide el transcript en chunks de ~max_chars con overlap.
    Respeta cortes naturales (párrafos, oraciones).
    """
    segments = data.get("segments", [])
    if not segments:
        return []

    # Construir texto plano con timestamps
    lines = []
    for seg in segments:
        ts = fmt_timestamp(seg["start"])
        lines.append(f"[{ts}] {seg['text']}")

    full = "\n".join(lines)
    total = len(full)

    if total <= max_chars:
        return [{
            "index": 0,
            "text": full,
            "start_ts": fmt_timestamp(segments[0]["start"]),
            "end_ts": fmt_timestamp(segments[-1]["start"] + segments[-1]["duration"]),
            "char_count": total,
        }]

    # Necesita chunking
    chunks = []
    start = 0
    chunk_idx = 0

    while start < total:
        end = min(start + max_chars, total)

        # Buscar corte natural (doble salto de línea o salto de línea)
        if end < total:
            natural_end = full.rfind("\n\n", start + max_chars // 2, end)
            if natural_end > 0:
                end = natural_end + 2
            else:
                natural_end = full.rfind("\n", start + max_chars // 2, end)
                if natural_end > 0:
                    end = natural_end + 1

        chunk_text = full[start:end].strip()

        # Encontrar timestamp inicial y final del chunk
        first_line = chunk_text.split("\n")[0] if chunk_text else ""
        last_line = chunk_text.split("\n")[-1] if chunk_text else ""
        start_ts = re.search(r'\[(\d+:\d+(?::\d+)?)\]', first_line)
        end_ts = re.search(r'\[(\d+:\d+(?::\d+)?)\]', last_line)

        chunks.append({
            "index": chunk_idx,
            "text": chunk_text,
            "start_ts": start_ts.group(1) if start_ts else "00:00",
            "end_ts": end_ts.group(1) if end_ts else "00:00",
            "char_count": len(chunk_text),
        })

        # Avanzar con overlap
        start = end - overlap
        chunk_idx += 1

    return chunks

# ─── Vault Writer ────────────────────────────────────────────────────────────

def sanitize_filename(name: str) -> str:
    """Limpia un string para usarlo como nombre de archivo."""
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[-\s]+', '-', name)
    return name.strip('-').strip()

def write_curso_nota(data: dict, topic: str = None):
    """Escribe la nota principal del video en Courses/Temas/{tema}/"""
    video_title = sanitize_filename(data.get("title", "Untitled"))
    auto_topic = data.get("auto_topic", topic or "General")
    tema = topic if topic else auto_topic

    tema_dir = Path(LEARNING_VAULT) / "Courses" / "Temas" / sanitize_filename(tema)
    tema_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{video_title}.md"
    filepath = tema_dir / filename
    created = data.get("created", DATE_FORMAT)

    # Sanitizar campos del frontmatter
    safe_title = yaml_quote(data.get('title', 'Untitled'))
    safe_url = validate_url(data.get('url', ''))
    safe_duration = yaml_quote(data.get('duration', ''))
    safe_topic = sanitize_filename(tema).lower()
    safe_narrative = md_sanitize(data.get('narrative', ''))

    content = f"""---
title: {safe_title}
created: {created}
modified: {created}
tags: [course, {safe_topic}]
video: {yaml_quote(safe_url)}
duration: {safe_duration}
tema: {tema}
source: youtube
---

# {data.get('title', 'Untitled')}

> **Video:** [{data.get('title', 'Untitled')}]({safe_url})
> **Tema:** {tema}
> **Duración:** {safe_duration}

---

## 📝 Notas principales

{safe_narrative}

---

## 🧠 Conceptos clave

"""
    for concept in data.get("concepts", []):
        name = concept.get("name", "")
        definition = concept.get("definition", "")
        timestamp = concept.get("timestamp", "")
        wl = wikilink_safe(f"Concepts/{sanitize_filename(name)}", name)
        content += f"- **{wl}** ({timestamp}): {md_sanitize(definition)}\n"

    content += f"""

---

## 📖 Glosario

"""
    for term in data.get("glossary", []):
        term_name = term.get("term", "")
        term_def = term.get("definition", "")
        wl = wikilink_safe(f"Glossary/{sanitize_filename(term_name)}", term_name)
        content += f"- **{wl}**: {md_sanitize(term_def)}\n"

    content += f"""

---

## 🔗 Conexiones

"""
    for rel in data.get("connections", []):
        content += f"- [[{md_sanitize(rel)}]]\n"

    content += f"""

---

*Nota generada automáticamente — {created}*
"""

    with open(filepath, "w") as f:
        f.write(content)

    print(f"✅ Nota de curso creada: {filepath}")
    return filepath

def write_concepto_nota(concept: dict, video_url: str, video_title: str, created: str):
    """Escribe o actualiza una nota de concepto en Concepts/"""
    name = concept.get("name", "Untitled")
    area = sanitize_filename(concept.get("area", "general"))
    related = concept.get("related", [])
    filename = f"{sanitize_filename(name)}.md"
    filepath = Path(LEARNING_VAULT) / "Concepts" / filename

    if filepath.exists():
        print(f"  ⏩ Concepto ya existe: Concepts/{filename}")
        return filepath

    # Sanitizar campos
    safe_name = yaml_quote(name)
    safe_url = validate_url(video_url)
    safe_ts = yaml_quote(concept.get('timestamp', '00:00'))
    safe_area = yaml_quote(concept.get('area', 'General'))
    safe_definition = md_sanitize(concept.get('definition', ''))
    safe_explanation = md_sanitize(concept.get('explanation', ''))
    safe_applications = md_sanitize(concept.get('applications', ''))

    rel_links = ", ".join(
        wikilink_safe(f"Concepts/{sanitize_filename(r)}", r)
        for r in related
    ) if related else "\u2014"

    content = f"""---
title: {safe_name}
created: {created}
modified: {created}
tags: [concept, {area}]
source: {yaml_quote(safe_url)}
timestamp: {safe_ts}
related: [{rel_links}]
---

# {name}

> **Source:** [{video_title}]({safe_url}) \u2014 {safe_ts}
> **Area:** {safe_area}

---

## Definition

{safe_definition}

---

## Explanation

{safe_explanation}

---

## Applications

{safe_applications}

---

## Links

""" + "\n".join(
    f"- {wikilink_safe(f'Glossary/{sanitize_filename(t)}', t)}"
    for t in concept.get("glossary_terms", [])
) + """

---

*Generated automatically*
"""

    with open(filepath, "w") as f:
        f.write(content)

    print(f"  ✅ Concepto creado: Concepts/{filename}")
    return filepath

def write_glossary_term(term: dict, video_note_path: str, created: str):
    """Escribe o actualiza una entrada del glosario en Glossary/"""
    term_name = term.get("term", "Untitled")
    filename = f"{sanitize_filename(term_name)}.md"
    filepath = Path(LEARNING_VAULT) / "Glossary" / filename

    if filepath.exists():
        print(f"  ⏩ Término ya existe en glosario: Glossary/{filename}")
        return filepath

    vault = Path(LEARNING_VAULT)
    try:
        rel_path = str(Path(str(video_note_path)).relative_to(vault))
    except ValueError:
        rel_path = Path(str(video_note_path)).name

    # Sanitizar campos
    safe_name = yaml_quote(term_name)
    safe_ts = yaml_quote(term.get('timestamp', '00:00'))
    safe_def = md_sanitize(term.get('definition', ''))

    content = f"""---
title: {safe_name}
created: {created}
modified: {created}
tags: [glossary]
---

# {term_name}

{safe_def}

**Source:** [[{rel_path}]] \u2014 {safe_ts}
"""

    with open(filepath, "w") as f:
        f.write(content)

    print(f"  ✅ Glosario: Glossary/{filename}")
    return filepath

def update_index(video_title: str, tema: str, video_path: str):
    """Actualiza Index.md con el nuevo video y tema si es nuevo."""
    index_path = Path(LEARNING_VAULT) / "Index.md"
    if not index_path.exists():
        return

    with open(index_path) as f:
        content = f.read()

    tema_sanitized = sanitize_filename(tema)
    tema_link = f"[[Courses/Temas/{tema_sanitized}|{tema}]]"

    if tema_link not in content:
        new_entry = f"### [[Courses/Temas/{tema_sanitized}|{tema}]] 📘\n"
        insert_pos = content.find("## 📖 Conceptos destacados")
        if insert_pos > 0:
            content = content[:insert_pos] + new_entry + content[insert_pos:]

    with open(index_path, "w") as f:
        f.write(content)
    print(f"  ✅ Index actualizado")

# ─── CLI ─────────────────────────────────────────────────────────────────────

def cmd_fetch(args):
    """Fetch transcript y chunking."""
    url = args.url
    video_id = extract_video_id(url)

    print(f"[Stage 1-2] Extrayendo transcript de video {video_id}...")
    data = fetch_transcript(video_id, languages=args.language)

    if "error" in data:
        print(f"❌ Error: {data['error']}")
        sys.exit(1)

    print(f"  ✅ Transcript obtenido: {data['segment_count']} segmentos, {data['duration_str']}")

    print(f"\n[Stage 3] Chunking (overlap 3K)...")
    chunks = chunk_transcript(data)
    print(f"  ✅ {len(chunks)} chunk(s) generados")

    output = {
        "video_id": video_id,
        "url": url,
        "duration": data["duration_str"],
        "chunks": chunks,
        "full_text": data["full_text"],
    }

    if args.output:
        with open(args.output, "w") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\n📄 Datos guardados en: {args.output}")
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))

def cmd_write(args):
    """Escribe notas procesadas en el vault."""
    with open(args.data) as f:
        data = json.load(f)

    created = data.get("created", DATE_FORMAT)

    print(f"[Stage 6] Escribiendo en Learning Vault...")
    print(f"  Tema: {args.topic or 'auto-detect'}")

    video_path = write_curso_nota(data, topic=args.topic)
    print(f"  📝 Nota principal: {video_path.name}")

    for c in data.get("concepts", []):
        write_concepto_nota(c, data.get("url", ""), data.get("title", ""), created)

    for t in data.get("glossary", []):
        write_glossary_term(t, video_path, created)

    theme = args.topic or data.get("auto_topic", "General")
    update_index(data.get("title", "Untitled"), theme, video_path)
    print(f"\n✅ Pipeline completado — Learning Vault actualizado")

def main():
    parser = argparse.ArgumentParser(
        description="YouTube Educational Pipeline — Learning Vault",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python3 educational_pipeline.py fetch "https://youtube.com/watch?v=VIDEO_ID" -o chunks.json
  python3 educational_pipeline.py write chunks.json --topic "Inteligencia Artificial"
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos")

    fetch_parser = subparsers.add_parser("fetch", help="Extraer transcript y chunking")
    fetch_parser.add_argument("url", help="YouTube URL o video ID")
    fetch_parser.add_argument("--language", "-l", default=None, help="Código de idioma (en, es)")
    fetch_parser.add_argument("--output", "-o", default=None, help="Archivo JSON de salida")

    write_parser = subparsers.add_parser("write", help="Escribir notas procesadas en vault")
    write_parser.add_argument("data", help="Archivo JSON con datos procesados")
    write_parser.add_argument("--topic", "-t", default=None, help="Forzar tema específico")

    args = parser.parse_args()

    if args.command == "fetch":
        cmd_fetch(args)
    elif args.command == "write":
        cmd_write(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
