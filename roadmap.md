# AI-IDE Advanced Upgrades Roadmap

This document outlines future advanced features to build into AI-IDE.

## 1. Semantic Codebase Search (Vector RAG) 🔍
- **Description**: Natural language semantic code indexing.
- **Goal**: Perform cosine similarity queries on embedding vectors for classes, methods, and files (utilizing `nomic-embed-text` via Ollama) to locate logic concepts without exact keyword matches.

## 2. Multi-File Agentic Coding Pipeline 🤖
- **Description**: Autonomous multi-file code editing and verification loops.
- **Goal**: Enable AI to plan changes, modify multiple headers/sources, build the codebase, parse compilation errors, and auto-correct itself iteratively until tests pass.

## 3. AST Structure Outline View 🌳
- **Description**: Visual classes/functions hierarchy browser.
- **Goal**: Query clangd LSP `textDocument/documentSymbol` to display a real-time navigation outline in the sidebar showing functions, class methods, and member variables.

## 4. Visual Debugger Inspector 📊
- **Description**: Graphical representation of memory variables during execution.
- **Goal**: Render C++ collection structures (matrices, graphs, arrays) as diagrams, heatmaps, or charts during debugger breakpoints.

## 5. Visual Git History Tree & Conflict Resolver 📈
- **Description**: Branch graphs and visual merge editors.
- **Goal**: Render visual graphs of commits and provide a side-by-side three-pane conflict resolver with single-click merge buttons.

## 6. Remote Container Compilation (Docker & WSL) 🐳
- **Description**: Sandbox build and execution environments.
- **Goal**: Direct compiler and runner actions to execute seamlessly inside target Docker containers or WSL systems.
