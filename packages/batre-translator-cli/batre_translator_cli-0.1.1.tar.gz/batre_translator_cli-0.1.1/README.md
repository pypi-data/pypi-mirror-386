# 🧩 Batre Translator CLI

**Batre Translator CLI** is a lightweight command-line tool for automating localization workflows.  
It clones your frontend project, aggregates translation files, commits them to Git, and uploads updates to the **Batre Translator API** — with full GitLab/GitHub merge request automation.

---

## 🚀 Features

- 🔄 Automatically clones **full repositories** (no sparse-checkout)
- 📁 Aggregates `.js` and `.json` locale files into a unified structure
- 🧠 Encodes and uploads translations to the Batre Translator API (Base64)
- 🪄 Automatically creates **Merge Requests** for exported translations
- 🧰 Fully scriptable via `make` or direct CLI commands
- 💾 Safe local `.batre.yml` configuration per project

---

## ⚙️ Configuration (`.batre.yml`)

Create a `.batre.yml` file in your project root:

```yaml
# Project configuration for Batre Translator CLI
project_id: project-app
repo_url: git@gitlab.com:yourcompany/project/project-app.git
branch: develop
repo_path: tmp/project-app

base_path: src/locales/en-GB
export_path: src/locales/dist

api_url: https://translator.batre.io/api/v1
api_token: <CLIENT_TOKEN>
gitlab_token: <GITLAB_PAT>

vcs: gitlab   # or github / bitbucket
```

### Explanation
| Key | Description |
|-----|--------------|
| `project_id` | ID of the project in Batre Translator |
| `repo_url` | Git repository URL (SSH or HTTPS) |
| `branch` | Branch to pull from |
| `repo_path` | Local folder for temporary clone |
| `base_path` | Path to your localization source files |
| `export_path` | Folder where new translations are written |
| `api_url` | Batre Translator API endpoint |
| `api_token` | Client API token for authentication |
| `gitlab_token` | Personal Access Token for creating merge requests |
| `vcs` | Repository provider (`gitlab`, `github`, or `bitbucket`) |

---

## 🧩 Usage

### 1️⃣ Aggregate translations locally
Collect and combine all translation files into a single `aggregated.json`.  
The aggregated file is now saved **one level above the language folder** — e.g.:

```
src/locales/aggregated.json
```

Run manually:
```bash
batre aggregate
```

Or via `make`:
```bash
make aggregate
```

Example output:
```
📁 Using base path from .batre.yml: src/locales/en-GB
✅ Parsed: auth/login.js
✅ Parsed: auth/reset-password.js
✅ Aggregated file saved to: src/locales/aggregated.json
```

---

### 2️⃣ Full sync (clone → aggregate → upload)
This command:
1. Clones or updates the full Git repository (no sparse-checkout)
2. Aggregates all translation files
3. Uploads them as Base64 to the Batre Translator API

```bash
batre sync
```

Or via Makefile:
```bash
make sync
```

Example:
```
🔄 Updating repo at tmp/project-app...
📦 Aggregating translations from src/locales/en-GB...
✅ Aggregated file saved to: src/locales/aggregated.json
🌍 Sending en-GB translation data to https://translator.batre.io/api/v1 (Base64 mode)...
✅ Upload successful!
```

---

### 3️⃣ Export from API → Git → Merge Request
The `batre export` command fetches translations from the API, writes them into your repo,  
and automatically creates a **Git branch + Merge Request**.

```bash
batre export
```

Example:
```
📦 Processing en-GB...
✅ Wrote en-GB/auth/login.js
✅ Wrote en-GB/auth/reset-password.js
🌿 Creating branch: batre/export/20251024-2142
✅ Commit created successfully.
🚀 Pushing branch to remote...
✅ Merge Request created successfully!
🔗 https://gitlab.com/yourcompany/project/-/merge_requests/12
```

**Developers only need to review and merge the MR.**

---

## 🧱 Developer setup

Clone the CLI project locally and use `make` commands:

```bash
git clone https://gitlab.com/collabwire/batre-translator-cli.git
cd batre-translator-cli
make install-dev
```

Available commands:
```
make venv          - create Python virtual environment
make install       - install runtime dependencies
make install-dev   - install dev tools (black, isort, build, twine)
make lint          - format code
make aggregate     - run local aggregator
make sync          - full clone + aggregate + upload
make export        - export from API to repo + create MR
make build         - build wheel and sdist packages
make publish       - publish to PyPI or GitLab
make clean         - remove venv and caches
```

---

## 🧪 Build & Publish

### Build package
```bash
make build
```

### Publish to PyPI
```bash
make publish
```

or manually:
```bash
twine upload dist/*
```

---

## 🔧 Developer Notes

- Full Git clone is now used — **no sparse-checkout logic** remains.
- Aggregated files are saved to `src/locales/aggregated.json`.
- The CLI automatically commits translation exports and opens a **Merge Request**.
- Merge Requests are created using your configured `gitlab_token` (PAT).
- The tool can also work with GitHub or Bitbucket if configured under `vcs`.

---

## 🧰 Requirements

- Python **3.12+**
- Git (CLI)
- Access to your GitLab/GitHub repository
- Valid Batre Translator API credentials

---

## 🪪 License

MIT License © Collabwire

---

## 🧰 Authors

**Collabwire PSA**  
Architecture: *Alex Zmuda*  
AI Assistant: *Ania (GPT-5)*

## 🌍 Maintainer

**Collabwire P.S.A.**  
Warsaw, Poland  
📧 dev@collabwire.com  
🌐 https://collabwire.com
