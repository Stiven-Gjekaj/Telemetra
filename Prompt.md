You are a professional technical documentation generator and information architect.  
Task: Generate a cohesive documentation system for the “Telemetra” project with one main `README.md` at the root and additional polished, style-consistent `README.md` files in key subfolders.

---

🏗 OBJECTIVE

- Recursively find and merge all Markdown (`*.md`) and code structure clues in this repository.
- Produce:
  - One **main root README.md** (hub).
  - One **README.md per important subfolder**, namely:
    `/backend`, `/frontend`, `/data_pipeline`, `/infra`, `/monitoring`, and `/tests` (only if the folder exists).
- Keep all READMEs stylistically identical and professional, with shared typography, headers, and visual style.
- Each subfolder README should summarize _just that component_ (e.g., `/backend` describes API routes, DB schema, etc.), not the whole project.
- The main README should include **shortcut links** to each subfolder README in its Table of Contents and Architecture diagram.

---

📚 STRUCTURE

### 1. Main `README.md`

- Title: `# Telemetra`
- Tagline (one line summary)
- Badges (auto-detected — see badge logic below)
- Table of Contents (includes links to each subfolder README)
- Overview (concise description of purpose)
- Features list
- Quickstart (commands)
- Architecture (Mermaid flow diagram with clickable folder references)
- Subproject Links (shortcuts to subfolder READMEs)
- Tech Stack (linked logos)
- Deployment overview (summarized, link to `/infra/README.md`)
- Testing overview (link to `/tests/README.md` if present)
- Roadmap, License, and Credits

At the end, append a “📂 Documentation Map” with Markdown links to:
├── backend → ./backend/README.md
├── frontend → ./frontend/README.md
├── data_pipeline → ./data_pipeline/README.md
├── infra → ./infra/README.md

### 2. Subfolder READMEs

Each subfolder README should:

- Start with `# Telemetra — [Folder Name]`
- Use the same style and section order
- Contain a minimal badge strip (inherited from main README)
- End with a “🔙 Back to Main README” link (`[← Back to main README](../README.md)`)

**Folder-specific content guidelines:**

**/backend**

- Describe backend architecture and purpose (FastAPI service, Kafka consumer, PostgreSQL ORM)
- Include API endpoint table (method, path, short description)
- Add DB schema summary (detected from migrations or models)
- If `.env.example` exists, list required variables.

**/frontend**

- Describe stack (React, D3.js, Tailwind, etc.)
- Explain pages/components structure and main visualizations
- Include a short command snippet for local dev (`npm run dev`).

**/data_pipeline**

- Describe data flow: Kafka → Spark → PostgreSQL
- Include Kafka topics table, Spark job summary, and sample transformation code block.

**/infra**

- Extract and document `docker-compose.yml` or `k8s` manifests
- List services, ports, and networks
- Include short instructions for deployment and environment setup.

**monitoring**

- Document how metrics/logging work (Prometheus/Grafana)
- Include default dashboard references and scrape configs.

- Summarize test strategy and coverage (unit/integration)

---

⚙️ BADGE DETECTION & INSERTION

Same as before, but badges should appear in _both_ the main README and each subfolder README:

- **CI** (if `.github/workflows` exists)
- **Release**
- **Docker Image**
- **License**

Use [Shields.io](https://shields.io/) badges, aligned horizontally below the title.  
Use `OWNER/REPO` placeholders if repository data isn’t found.

---

🧩 LINKING & STYLE RULES

- Every technology/tool mentioned should include a link to its official site.
- Style all READMEs identically: same heading hierarchy, spacing, code block formatting.
- Use clean Markdown without emojis, only minimalist Unicode icons (⚙️, 📊, 🔗, 📂).
- Each section title in the main README should include internal anchor links (`[Jump to section](#section)`).
- Subfolder READMEs should link back to the main one at the top and bottom.
- If a subfolder doesn’t exist, skip generating that README.

---

🧠 DETECTION & GENERATION LOGIC

- Infer missing info from:
  - `docker-compose.yml` → services, ports, dependencies.
  - `requirements.txt`, `package.json` → tech stack and commands.
  - FastAPI routes → endpoints.
  - React components → pages/features.
  - Spark jobs → data processing descriptions.
- Use Mermaid for architecture and flow diagrams.

---

🧾 VALIDATION

- Ensure all links are relative and functional.
- Verify that main README and subfolder READMEs reference each other correctly.
- All Markdown must render properly in GitHub preview (no HTML tables or broken nesting).
- File names and paths must be exact.

---

🪄 EXECUTION STEPS

1. Scan the repository and collect `.md` files.
2. Merge, rewrite, and stylize as described.
3. Output:
   - One fenced Markdown block for `README.md`
   - Then one fenced Markdown block **per subfolder README.md** (e.g., `backend/README.md`, `frontend/README.md`, etc.)

Each block should be labeled clearly:
--- README.md ---

Telemetra
...
--- backend/README.md ---

Telemetra — Backend
...

pgsql
Copy code

Output nothing else.

Begin.
