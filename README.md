# gh-repo-review

**English** · [Português](README.pt-BR.md)

A small local web page to **review all your GitHub repositories in one place** — see language, dates and whether each one is cloned on your machine, then **clone, archive, unarchive or delete** them with a click.

Built with Python's standard library and the official [GitHub CLI](https://cli.github.com/). No `pip install`, no database, no account other than your own GitHub login.

![gh-repo-review screenshot](docs/screenshot.png)

> The interface is available in **English** and **Portuguese (Brazil)** — switch with the flags at the top of the page.

## Features

- Lists every repository you own (public and private) — optionally also your organizations' repositories
- **Active** and **Archived** tabs, summary cards and filters (name, language, mark, "stale" repos, "not cloned")
- Mark repositories to **archive** or **delete**, with a free-text note — saved automatically
- **Clone** with one click into `<projects folder>/<language>/<repo>`, with a folder picker; the clone is verified at the end
- **Apply review** to archive/delete on GitHub, with confirmation
- **Unarchive** from the Archived tab
- **HTML report** of what was deleted, archived and cloned, reflecting the current state (e.g. "folder removed", "unarchived on ...")
- Interface and reports in **English** or **Portuguese (Brazil)**, switchable with one click
- Works on **Windows, macOS and Linux**

## Requirements

| Tool | Why |
|---|---|
| Python 3.8+ | Runs the local server |
| GitHub CLI (`gh`) | Talks to GitHub using your login |
| Git | Used to clone repositories |

### 1. Install Python

- **Windows:** download from [python.org/downloads](https://www.python.org/downloads/) and run the installer. Keep **"py launcher"** checked and tick **"Add python.exe to PATH"**. Or in a terminal: `winget install Python.Python.3.12`
- **macOS:** `brew install python` (with [Homebrew](https://brew.sh)) or the installer from [python.org](https://www.python.org/downloads/)
- **Linux (Debian/Ubuntu):** `sudo apt install python3 python3-tk` — `python3-tk` enables the folder picker (optional)

Check: `python --version` (Windows) or `python3 --version` (macOS/Linux).

### 2. Install Git

- **Windows:** [git-scm.com/download/win](https://git-scm.com/download/win) or `winget install Git.Git`
- **macOS:** `xcode-select --install` or `brew install git`
- **Linux:** `sudo apt install git`

### 3. Install and log in to the GitHub CLI

- **Windows:** `winget install GitHub.cli`
- **macOS:** `brew install gh`
- **Linux:** follow the [official instructions](https://github.com/cli/cli/blob/trunk/docs/install_linux.md)

Then log in (opens the browser):

```
gh auth login
```

Choose **GitHub.com**, **HTTPS** or **SSH** (whichever you use with git) and **Login with a web browser**. Check with `gh auth status`.

**Only if you want to delete repositories**, add the extra permission once:

```
gh auth refresh -h github.com -s delete_repo
```

## Getting started

```
git clone https://github.com/cristopherlima-dev/gh-repo-review.git
cd gh-repo-review
```

Run it:

- **Windows:** double-click `abrir.bat` (you can create a desktop shortcut to it)
- **macOS / Linux:** `./abrir.sh`
- **Any system:** `python servidor.py` (or `python3 servidor.py`)

On the first run a `config.json` is created from `config.example.json`. **Open it and set `pasta_projetos`** to the folder where you keep your clones, then run again. The page opens at `http://localhost:8765`. To stop, close the terminal window or press `Ctrl+C`.

## Configuration (`config.json`)

| Key | Default | Description |
|---|---|---|
| `pasta_projetos` | `~/projetos` | Folder with your clones, organized by language (e.g. `D:\\PROJETOS` on Windows — use double backslashes) |
| `pasta_dados` | `dados` | Where your review, history and reports are stored. Relative = inside the project. Point it to a synced folder (Google Drive, OneDrive...) for backup |
| `porta` | `8765` | Local server port |
| `anos_parado` | `2` | Repositories without a push for longer than this are highlighted |
| `permitir_excluir` | `false` | **Delete is off by default.** When `false`, the Delete button is hidden and the server refuses deletions |
| `incluir_organizacoes` | `false` | Also list repositories from organizations you belong to |
| `abrir_navegador` | `true` | Open the browser automatically on start |
| `idioma` | `en` | Language on first open: `en` or `pt-BR`. After that, the page remembers the flag you clicked |
| `pasta_sem_linguagem` | `outros` | Folder used for repositories with no detected language |
| `apelidos` | see file | GitHub language → folder name (e.g. `"C#": "csharp"`). Others become lowercase (`Python` → `python`) |

`config.json` and the data folder are in `.gitignore` — your settings and data are never committed.

## How to use

1. In the **Active** tab, mark repositories as **Archive** or **Delete** and add notes. No mark = keep.
2. Click **Clone** to clone a repository that isn't on your machine yet.
3. Click **Apply review** to archive/delete on GitHub. Deletions require typing `DELETE`.
4. In the **Archived** tab, click **Unarchive** to undo an archive.
5. Click **Report** to generate the HTML report in `<pasta_dados>/relatorios/` (in the language currently selected).

| Action | Effect | Reversible? |
|---|---|---|
| Archive | Repository becomes read-only on GitHub | Yes — Unarchive |
| Delete | Repository, code and history are removed | **No** |
| Unarchive | Repository accepts changes again | Yes — archive again |

When in doubt, **archive**.

## Your data

Everything stays on your machine, inside `pasta_dados`:

| File | Content |
|---|---|
| `revisao.json` | Your marks and notes |
| `historico.json` | Log of every action (cloned, archived, unarchived, deleted) — never erased |
| `relatorios/` | Generated reports |

## Security

- The server only listens on `127.0.0.1` (your own computer).
- Each session uses a random token: only the page opened by the server can send commands.
- Deleting is off by default, needs the `delete_repo` permission in `gh` and the word `DELETE` (or `EXCLUIR` in Portuguese) to confirm.
- All GitHub actions go through `gh` with **your** login; nothing is sent anywhere else.

## Troubleshooting

| Problem | Solution |
|---|---|
| `gh` not found / not logged in | Install the GitHub CLI and run `gh auth login` |
| Error parsing `config.json` | On Windows paths use double backslashes: `"D:\\PROJETOS"` |
| Port already in use | Close the other server window or change `porta` |
| "Choose folder" button shows a tkinter error (Linux) | `sudo apt install python3-tk`, or type the path in the field |
| Delete fails with `delete_repo` | `gh auth refresh -h github.com -s delete_repo` |
| `abrir.sh: Permission denied` | `chmod +x abrir.sh` |

## Project structure

| File | Role |
|---|---|
| `servidor.py` | Local server and actions (clone, archive, unarchive, delete, report) |
| `gerar_lista.py` | Fetches repositories via `gh` and builds the page. Run alone, it generates a static, read-only version in `saida/` |
| `relatorio.py` | Action history and HTML report |
| `config.py` | Loads `config.json` |
| `i18n.py` | Server and report messages in English and Portuguese |
| `template.html` | The page (HTML/CSS/JS, no frameworks) |
| `abrir.bat` / `abrir.sh` | Launchers for Windows / macOS-Linux |

## How it was built

This project was created by **Cristopher Lima** together with **Claude**, an AI assistant by Anthropic. I defined the problem, the rules and the design decisions, and tested every step on my own machine; the AI proposed solutions and wrote most of the code. I'm sharing this openly because I think it's an honest picture of how software can be built today.

## Author

**Cristopher Lima** — [linkedin.com/in/cristopherlima-dev](https://www.linkedin.com/in/cristopherlima-dev)

## License

[MIT](LICENSE)
