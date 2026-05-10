---
name: youtube-educational
description: "Pipeline educativo: YouTube → transcripción → notas profundas → Learning Vault (Obsidian) con conceptos, wikilinks automáticos, glosario acumulativo y auto-organización por temas."
version: 1.0.0
license: MIT
platforms: [macos, linux]
---

# 📚 YouTube Educational Pipeline

Pipeline multi-modelo para convertir videos de YouTube en notas educativas profundas dentro de un vault de Obsidian (Learning Vault), con extracción automática de conceptos, generación de wikilinks, glosario acumulativo y organización por temas.

## Cuando usar

- Cuando quieres extraer conocimiento profundo de un video educativo y almacenarlo en un vault de Obsidian
- Para construir una base de conocimiento interconectada a partir de contenido de YouTube
- Para generar notas de estudio con wikilinks automáticos entre conceptos

## Requisitos

```bash
pip install youtube-transcript-api
```

Opcional (para features avanzados):
```bash
pip install chromadb genanki
```

## Pipeline multi-modelo

| Etapa | Modelo | Tarea |
|---|---|---|
| 1 | Default | Detección de trigger y validación de URL |
| 2 | Default | Extracción de transcript (youtube-transcript-api) |
| 3 | Gemini 2.5-pro | Chunking inteligente (overlap 3K) |
| 4 | Gemini 2.5-pro | Procesamiento educativo (narrativa, conceptos, glosario) |
| 5 | GPT-5.5 | Merge + deduplicación de conceptos + generación de wikilinks |
| 6 | GPT-5.5 | Escritura en Learning Vault |

Fallback intra-etapa: si Gemini falla → GPT-5.5. Si GPT falla → Gemini.
Al finalizar, vuelve al modelo default y presenta resultado.

## Estructura del Learning Vault

```
~/Documents/Learning Vault/
├── Index.md                    ← Wikilinks a todos los temas
├── Concepts/                   ← Explicaciones semidetalladas de conceptos
│   ├── Machine-Learning.md     ← Con links a Glossary/
│   └── Transformer.md
├── Glossary/                   ← Entradas individuales del glosario
│   ├── Backpropagation.md
│   └── Attention-Mechanism.md
└── Courses/
    ├── Temas/                  ← Subcarpetas por área temática
    │   ├── IA/
    │   │   └── Video-Titulo.md
    │   ├── Trading/
    │   └── Criptografia/
    └── Conceptos/              ← Conceptos desde cursos (contextualizados)
        └── Concepto.md
```

Cascada: `Index → Temas → Videos → Conceptos → Glosario`

## Uso

```bash
# Paso 1: Extraer transcript y generar chunks
python3 pipeline/educational_pipeline.py fetch "https://youtube.com/watch?v=VIDEO_ID" -o chunks.json

# Paso 2: Escribir notas procesadas en el vault
python3 pipeline/educational_pipeline.py write processed_data.json --topic "Tema"
```

## Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `LEARNING_VAULT_PATH` | `~/Documents/Learning Vault` | Ruta al vault de Obsidian |
| `LEARNING_VAULT_DATE_FORMAT` | `dd/mm/aa` | Formato de fecha en frontmatter |

## Templates de notas

Ver carpeta `skill/templates/` para:
- `template-curso.md` — Nota principal de video
- `template-concepto.md` — Nota de concepto
- `template-glossary.md` — Entrada de glosario

## Referencias

Ver `skill/references/prompts.yaml` para los prompts exactos de cada etapa del pipeline.

---

## 🇬🇧 English

### When to use

- When you want to extract deep knowledge from an educational video and store it in an Obsidian vault
- To build an interconnected knowledge base from YouTube content
- To generate study notes with automatic wikilinks between concepts

### Requirements

```bash
pip install youtube-transcript-api
```

Optional (advanced features):
```bash
pip install chromadb genanki
```

### Multi-model pipeline

| Stage | Model | Task |
|---|---|---|
| 1 | Default | Trigger detection and YouTube URL validation |
| 2 | Default | Transcript extraction (youtube-transcript-api) |
| 3 | Gemini 2.5-pro | Intelligent chunking (3K overlap) |
| 4 | Gemini 2.5-pro | Educational processing (narrative, concepts, glossary) |
| 5 | GPT-5.5 | Merge + concept deduplication + wikilink generation |
| 6 | GPT-5.5 | Write to Learning Vault |

Intra-stage fallback: if Gemini fails → GPT-5.5. If GPT fails → Gemini.
On completion, restore default model and present results.

### Learning Vault structure

```
~/Documents/Learning Vault/
├── Index.md                    ← Wikilinks to all topics
├── Concepts/                   ← Semi-detailed concept explanations
│   ├── Machine-Learning.md     ← With links to Glossary/
│   └── Transformer.md
├── Glossary/                   ← Individual glossary entries
│   ├── Backpropagation.md
│   └── Attention-Mechanism.md
└── Courses/
    ├── Temas/                  ← Subfolders by subject area
    │   ├── IA/
    │   │   └── Video-Title.md
    │   ├── Trading/
    │   └── Cryptography/
    └── Conceptos/              ← Course-contextualized concepts
        └── Concept.md
```

Search cascade: `Index → Topics → Videos → Concepts → Glossary`

### Usage

```bash
# Step 1: Extract transcript and generate chunks
python3 pipeline/educational_pipeline.py fetch "https://youtube.com/watch?v=VIDEO_ID" -o chunks.json

# Step 2: Write processed notes into the vault
python3 pipeline/educational_pipeline.py write processed_data.json --topic "Topic"
```

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `LEARNING_VAULT_PATH` | `~/Documents/Learning Vault` | Path to Obsidian vault |
| `LEARNING_VAULT_DATE_FORMAT` | `dd/mm/aa` | Date format in frontmatter |

### Note templates

See `skill/templates/` folder for:
- `template-curso.md` — Main video note
- `template-concepto.md` — Concept note
- `template-glossary.md` — Glossary entry

### References

See `skill/references/prompts.yaml` for the exact prompts for each pipeline stage.
