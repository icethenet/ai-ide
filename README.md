# AI-IDE 🚀

An AI-augmented C++ desktop Integrated Development Environment (IDE) built with **Qt 6**, **CMake**, and **Ninja**. AI-IDE blends classical compiler tooling, LSP semantic indexers, and modern visualizers with autonomous agentic coding loops.

---

## Key Features

### 💻 Advanced Editor & Workspace
- **Sleek Dark Theme**: Designed with custom layouts, colors, and responsive toolbars.
- **Syntax Highlighting**: Real-time C++ token highlighters for enhanced readability.
- **Workspace Navigation**: Complete tree explorer browser and dynamic workspace file selector.

### 🧠 Agentic AI Coding Pipeline
- **Action Planner**: Checkbox lists detailing plans, complete with visual code diff overlays.
- **Multi-File Autocorrect Loop**: Autonomous debugging engine that captures compilation failures and feeds diagnostics back to the LLM agent to recursively repair code until builds pass.
- **Semantic LSP indexer**: Out-of-the-box integration with `clangd` for symbol outline lookups and references.

### 📊 Visual Debugging & Symbols Outline
- **AST Outline View**: Sidebar symbol hierarchies (namespaces, classes, methods, fields) with filter search and jump-to-line navigation.
- **Visual Debugger**: Render data structures as charts (arrays), heatmaps (matrices), or node-link layouts (JSON graphs) during breakpoint steps.

### 🐙 Visual Git & Merge Resolver
- **Visual Commit Tree**: History timeline delegate painting branches and commit tracks directly in the status table.
- **Three-Pane Conflict Resolver**: Interactive side-by-side conflict resolver (Local/Remote/Merged panels) with quick-accept helpers, auto-staging files on merge completion.

### 🐳 Sandbox & Remote Environments
- **Container Compilation**: Target environment switcher (Local Host, WSL Ubuntu, Docker Container) allowing files to compile within target sandbox containers seamlessly.
- **Remote Server Manager**: Asynchronous TCP socket latency ping testing and interactive native SSH terminal shell tabs.

---

## File Structure

- **`add_custom_editor_and_features.py`**: The single source of truth for generating all C++ UI, logic, and configuration files for the project.
- **`build.py`**: Clean, configure, compile, and run script.
- **`run-app.bat`**: Runs the compiled binary injecting the Qt library dependencies path.
- **`ai-ide/`**: CMake configuration workspace containing generated source code files.

---

## Getting Started

### Prerequisites
- Windows 10/11
- Qt 6.x (installed at `C:\Qt\6.11.1\llvm-mingw_64`)
- LLVM-MinGW Toolchain (installed at `C:\Qt\Tools\llvm-mingw_64`)
- CMake & Ninja

### Build and Run
To compile and launch the application:
```powershell
python build.py --run
```

---

## Release & Changelog History 📜

### v1.0 Release (Latest)
- **Visual Git Commit Graph**: Color-coded branch track lines and commit nodes.
- **Three-Pane Conflict Resolver**: Side-by-side local, remote, and editable merge view panels with accept actions.
- **Remote Container Compilation**: Selector to redirect builds natively to Local Host, WSL bash, or Docker workspace mounts.
- **Remote Server Manager**: Asynchronous TCP socket latency scanner and native SSH terminal pane integrations.

### v0.9 Update - Semantic Search (Vector RAG)
- **Local SQLite Database**: Caches metadata and float vectors index at `.antigravity/vector_index.db`.
- **Gemini / Ollama Client**: Dynamic embedding generations on file changes.
- **Similarity Ranking Engine**: Dot product similarity scoring directly in C++ for fast result matches.
- **Semantic Toggle Search UI**: Checkbox to toggle vector search with double-click navigation.

### v0.8 Update - AI Connections Settings & Editor Polish
- **Tabbed Settings Admin Panel**: Dynamic switching and API credential configurations for Ollama, Gemini, Claude, and Antigravity profiles.
- **Floating Find & Replace Dialog**: Regex, Case-Sensitive, Whole Word filters for scope or folder matches.
- **TLS/SSL Network backend registration**: Win64 MinGW plugin registration fixing request handshake exceptions.
- **Logo Resource Bundle & Dashboard styling**.

### v0.7 Update - Core IDE Subsystems (Phases A-E)
- **LSP Integration**: Hooked `clangd` JSON-RPC client to provide fuzzy autocompletion popup list, right-click go-to-definition, and symbols reference indexing.
- **Splittable Terminal Tiling**: ANSI colors terminal tab holding horizontal/vertical recursive command panes.
- **Auto-Fix Lightbulbs**: Editor gutter lightbulb signals offering automated C++ compile error fixes with one click.
- **Git Changes Sidebar & Gutter Diff markers**: Color code gutters matching current git modifications.
- **Syntax Highlighter & CodeEditor Gutters**: Synchronized lines number gutter highlights.
