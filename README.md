# 🎓 YouTube Educational Pipeline Skill for Personal AI Agents

🇬🇧 English below

> Convierte videos de YouTube en notas educativas profundas dentro de un vault de Obsidian, con extracción automática de conceptos, generación de wikilinks y glosario acumulativo.
>
> Turns YouTube videos into deep educational notes inside an Obsidian vault, with automatic concept extraction, wikilink generation, and a cumulative glossary.

---

## 🇪🇸 Español

### 🧠 ¿Qué hace?

1. Toma una URL de YouTube
2. Extrae la transcripción del video
3. Divide el contenido en chunks con overlap para procesamiento eficiente
4. Genera **notas educativas profundas** (tipo "clase universitaria") usando modelos de lenguaje
5. Extrae conceptos clave con definiciones, explicaciones y aplicaciones
6. Crea entradas de glosario para términos técnicos
7. **Todo interconectado con wikilinks** estilo Obsidian

### 🏗️ Pipeline de 6 etapas

| Etapa | Modelo | Función |
|---|---|---|
| 1 | Default | Detección del trigger y validación de la URL de YouTube |
| 2 | Default | Extracción de la transcripción completa vía `youtube-transcript-api` |
| 3 | Gemini 2.5-pro | Chunking inteligente con solapamiento de 3K caracteres entre fragmentos |
| 4 | Gemini 2.5-pro | Procesamiento educativo profundo: narrativa, conceptos clave y glosario |
| 5 | GPT-5.5 | Merge y deduplicación de conceptos + generación de wikilinks |
| 6 | GPT-5.5 | Escritura final en el Learning Vault con la estructura de carpetas |

**Fallback:** si un modelo falla en su etapa, se usa el otro automáticamente. Al finalizar, se restaura el modelo default.

### 🤖 ¿Por qué estos modelos?

- **Etapas 1 y 2 → Modelo default** — Son tareas mecánicas (validar URL, extraer transcript) que no requieren razonamiento avanzado. Usar un modelo económico aquí mantiene el costo total bajo sin sacrificar calidad.
- **Etapas 3 y 4 → Gemini 2.5-pro** — Su approach pedagógico y ventana de contexto masiva (1M tokens) lo hacen ideal para procesar chunks largos y generar contenido con profundidad educativa, como si un profesor preparara su clase.
- **Etapas 5 y 6 → GPT-5.5** — Su capacidad de razonamiento avanzado brilla en tareas de organización: merge semántico, deduplicación de conceptos similares, generación precisa de wikilinks y estructuración del markdown final.

> 💡 **Tips para empezar:**
>
> - 🔑 **Google AI Studio** ofrece una API key gratuita para Gemini con cuotas generosas. Consíguela en [aistudio.google.com](https://aistudio.google.com).
> - 🌐 **GPT-5.5** está disponible vía [OpenRouter](https://openrouter.ai) sin necesidad de suscripción directa a OpenAI — pagas solo por uso.
> - 🔄 No estás atado a estos modelos: podés usar **cualquier LLM** que prefieras (Claude, Llama, DeepSeek, etc.). Sin embargo, **esta combinación (Default + Gemini 2.5-pro + GPT-5.5) es la que mejor resultados ofrece en relación costo-beneficio**, balanceando profundidad educativa, precisión estructural y eficiencia económica.

### 📂 Estructura del vault

```
Learning Vault/
├── Index.md                    ← Wikilinks a todos los temas
├── Concepts/                   ← Explicaciones semidetalladas de conceptos
├── Glossary/                   ← Entradas individuales del glosario
└── Courses/
    ├── Temas/{tema}/           ← Notas de video organizadas por área
    └── Conceptos/              ← Conceptos contextualizados por curso
```

Cascada de búsqueda: `Index → Tema → Video → Concepto → Glosario`

### 🚀 Quick start

```bash
# 1. Clonar
git clone https://github.com/Jagermaster2469/YouTube-Educational.git
cd youtube-educational-pipeline

# 2. Instalar dependencias
pip install youtube-transcript-api

# 3. Crear vault (opcional — usa el template)
cp -r vault-structure ~/Documents/Learning\ Vault

# 4. Fetch transcript
python3 pipeline/educational_pipeline.py fetch "https://youtube.com/watch?v=VIDEO_ID" -o chunks.json

# 5. Procesar con LLM (ver prompts en skill/references/prompts.yaml)
# El archivo chunks.json contiene el transcript listo para procesar

# 6. Escribir en vault
python3 pipeline/educational_pipeline.py write processed_data.json --topic "Tu Tema"
```

### ⚙️ Configuración vía entorno

| Variable | Default | Descripción |
|---|---|---|
| `LEARNING_VAULT_PATH` | `~/Documents/Learning Vault` | Ruta al vault |
| `LEARNING_VAULT_DATE_FORMAT` | `dd/mm/aa` | Formato de fecha |

### 🔧 Dependencias

- **Requerido:** `youtube-transcript-api`
- **Opcional:** `chromadb` (deduplicación semántica), `genanki` (exportar a Anki), `obsidian` (vault)

### 📝 Templates

Los templates de las notas están en `skill/templates/`:
- `template-curso.md` — Nota principal de video
- `template-concepto.md` — Nota de concepto individual
- `template-glossary.md` — Entrada de glosario

### 📜 Prompts de IA

Los prompts exactos para cada etapa del pipeline están en `skill/references/prompts.yaml`.

---

## 🇬🇧 English

### 🧠 What it does

1. Takes a YouTube URL
2. Extracts the video transcript
3. Splits content into chunks with overlap for efficient processing
4. Generates **deep educational notes** (college-lecture style) using language models
5. Extracts key concepts with definitions, explanations, and applications
6. Creates glossary entries for technical terms
7. **Everything interconnected with Obsidian-style wikilinks**

### 🏗️ 6-Stage Pipeline

| Stage | Model | Function |
|---|---|---|
| 1 | Default | Trigger detection and YouTube URL validation |
| 2 | Default | Full transcript extraction via `youtube-transcript-api` |
| 3 | Gemini 2.5-pro | Intelligent chunking with 3K-character overlap between fragments |
| 4 | Gemini 2.5-pro | Deep educational processing: narrative, key concepts, and glossary |
| 5 | GPT-5.5 | Concept merge + deduplication + wikilink generation |
| 6 | GPT-5.5 | Final write into the Learning Vault with folder structure |

**Fallback:** if a model fails during its stage, the other one takes over automatically. The default model is restored upon completion.

### 🤖 Why these models?

- **Stages 1 & 2 → Default model** — These are mechanical tasks (URL validation, transcript fetching) that require no advanced reasoning. Using a cost-efficient model here keeps total spend low with zero quality loss.
- **Stages 3 & 4 → Gemini 2.5-pro** — Its pedagogical approach and massive context window (1M tokens) make it ideal for processing long chunks and generating content with genuine educational depth — like a professor preparing a lecture.
- **Stages 5 & 6 → GPT-5.5** — Its advanced reasoning capabilities shine in organizational tasks: semantic merging, deduplication of similar concepts, precise wikilink generation, and final markdown structuring.

> 💡 **Tips to get started:**
>
> - 🔑 **Google AI Studio** provides a free API key for Gemini with generous quotas. Grab yours at [aistudio.google.com](https://aistudio.google.com).
> - 🌐 **GPT-5.5** is available via [OpenRouter](https://openrouter.ai) — no direct OpenAI subscription needed, pay only for what you use.
> - 🔄 You're not locked into these models: you can use **any LLM** you prefer (Claude, Llama, DeepSeek, etc.). However, **this combination (Default + Gemini 2.5-pro + GPT-5.5) delivers the best cost-to-quality ratio**, balancing educational depth, structural precision, and economic efficiency.

### 📂 Vault structure

```
Learning Vault/
├── Index.md                    ← Wikilinks to all topics
├── Concepts/                   ← Semi-detailed concept explanations
├── Glossary/                   ← Individual glossary entries
└── Courses/
    ├── Temas/{topic}/          ← Video notes organized by subject area
    └── Conceptos/              ← Course-contextualized concepts
```

Search cascade: `Index → Topic → Video → Concept → Glossary`

### 🚀 Quick start

```bash
# 1. Clone
git clone https://github.com/Jagermaster2469/YouTube-Educational.git
cd youtube-educational-pipeline

# 2. Install dependencies
pip install youtube-transcript-api

# 3. Create vault (optional — use the template)
cp -r vault-structure ~/Documents/Learning\ Vault

# 4. Fetch transcript
python3 pipeline/educational_pipeline.py fetch "https://youtube.com/watch?v=VIDEO_ID" -o chunks.json

# 5. Process with LLM (see prompts in skill/references/prompts.yaml)
# The chunks.json file contains the transcript ready for processing

# 6. Write to vault
python3 pipeline/educational_pipeline.py write processed_data.json --topic "Your Topic"
```

### ⚙️ Environment configuration

| Variable | Default | Description |
|---|---|---|
| `LEARNING_VAULT_PATH` | `~/Documents/Learning Vault` | Path to vault |
| `LEARNING_VAULT_DATE_FORMAT` | `dd/mm/aa` | Date format |

### 🔧 Dependencies

- **Required:** `youtube-transcript-api`
- **Optional:** `chromadb` (semantic deduplication), `genanki` (export to Anki), `obsidian` (vault)

### 📝 Templates

Note templates are in `skill/templates/`:
- `template-curso.md` — Main video note
- `template-concepto.md` — Individual concept note
- `template-glossary.md` — Glossary entry

### 📜 AI Prompts

Exact prompts for each pipeline stage are in `skill/references/prompts.yaml`.

---

## 📄 License

MIT
