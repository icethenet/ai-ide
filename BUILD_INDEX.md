# BUILD_INDEX.md - add_custom_editor_and_features.py

## Overview
This script generates C++ code for an AI-IDE application with custom editor, file browser, diff viewer, AI patch workflow, and Git integration.

## Generated Files

### Core Components
| File | Purpose | Lines Generated |
|------|---------|-----------------|
| [src/ui/SettingsManager.hpp](src/ui/SettingsManager.hpp) | Singleton for app configuration (endpoint, model, provider) | ~40 |
| [src/ui/SettingsManager.cpp](src/ui/SettingsManager.cpp) | Settings implementation using QSettings | ~15 |
| [src/ui/AdminDialog.hpp](src/ui/AdminDialog.cpp) | Settings UI dialog | ~20 |
| [src/ui/AdminDialog.cpp](src/ui/AdminDialog.cpp) | Admin dialog implementation | ~100+ |

### AI Components
| File | Purpose | Lines Generated |
|------|---------|-----------------|
| [src/ui/AIChatPanel.hpp](src/ui/AIChatPanel.hpp) | AI chat interface widget | ~30 |
| [src/ui/AIChatPanel.cpp](src/ui/AIChatPanel.cpp) | Chat panel implementation | ~150+ |
| [src/ai/OllamaProvider.hpp](src/ai/OllamaProvider.hpp) | AI provider interface | ~25 |
| [src/ai/OllamaProvider.cpp](src/ai/OllamaProvider.cpp) | Ollama API integration | ~80+ |
| [src/ui/AIPatchController.hpp](src/ui/AIPatchController.hpp) | AI patch workflow controller | ~20 |
| [src/ui/AIPatchController.cpp](src/ui/AIPatchController.cpp) | Patch controller implementation | ~60+ |

### Editor Components
| File | Purpose | Lines Generated |
|------|---------|-----------------|
| [src/ui/CustomEditor.hpp](src/ui/CustomEditor.hpp) | Custom text editor widget | ~20 |
| [src/ui/CustomEditor.cpp](src/ui/CustomEditor.cpp) | Editor implementation | ~80+ |

### Diff Components
| File | Purpose | Lines Generated |
|------|---------|-----------------|
| [src/ui/DiffView.hpp](src/ui/DiffView.hpp) | Diff viewer widget | ~15 |
| [src/ui/DiffView.cpp](src/ui/DiffView.cpp) | Diff viewer implementation | ~50+ |

### Git Components
| File | Purpose | Lines Generated |
|------|---------|-----------------|
| [src/git/GitClient.hpp](src/git/GitClient.hpp) | Git client interface | ~15 |
| [src/git/GitClient.cpp](src/git/GitClient.cpp) | Git client implementation | ~20+ |

### Utility Components
| File | Purpose | Lines Generated |
|------|---------|-----------------|
| [src/ui/ClipboardListener.hpp](src/ui/ClipboardListener.hpp) | Clipboard monitoring | ~15 |
| [src/ui/ClipboardListener.cpp](src/ui/ClipboardListener.cpp) | Clipboard listener implementation | ~20+ |

### Main Window
| File | Purpose | Lines Generated |
|------|---------|-----------------|
| [src/ui/EditorWindow.hpp](src/ui/EditorWindow.hpp) | Main application window | ~25 |
| [src/ui/EditorWindow.cpp](src/ui/EditorWindow.cpp) | Window implementation | ~100+ |

### Entry Point
| File | Purpose | Lines Generated |
|------|---------|-----------------|
| [src/main.cpp](src/main.cpp) | Application entry point | ~10 |
| [CMakeLists.txt](CMakeLists.txt) | Build configuration | ~15 |
| [src/CMakeLists.txt](src/CMakeLists.txt) | Source build configuration | ~20+ |

## Key Features

### 1. Custom Editor
- File open/save/save-as functionality
- Text editing with QPlainTextEdit
- File change notifications

### 2. AI Chat Panel
- Markdown rendering for AI responses
- Code block extraction
- Chat history management
- Apply code to editor
- Create new files

### 3. Diff Viewer
- Side-by-side comparison
- Color-coded differences (red=removals, green=additions)
- Monospace font for code

### 4. AI Patch Workflow
- Request refactor from AI
- Extract code blocks from Markdown
- Preview changes in diff view
- Apply approved patches

### 5. Git Integration
- Status checking
- Add files
- Commit changes
- Push to remote

### 6. Clipboard Monitoring
- Detect code copied to clipboard
- Show status bar notification

## Architecture

```
ai-ide/
├── src/
│   ├── ai/
│   │   ├── OllamaProvider.hpp
│   │   └── OllamaProvider.cpp
│   ├── git/
│   │   ├── GitClient.hpp
│   │   └── GitClient.cpp
│   ├── ui/
│   │   ├── SettingsManager.hpp
│   │   ├── SettingsManager.cpp
│   │   ├── AdminDialog.hpp
│   │   ├── AdminDialog.cpp
│   │   ├── AIChatPanel.hpp
│   │   ├── AIChatPanel.cpp
│   │   ├── CustomEditor.hpp
│   │   ├── CustomEditor.cpp
│   │   ├── DiffView.hpp
│   │   ├── DiffView.cpp
│   │   ├── AIPatchController.hpp
│   │   ├── AIPatchController.cpp
│   │   ├── ClipboardListener.hpp
│   │   ├── ClipboardListener.cpp
│   │   └── EditorWindow.hpp
│   └── main.cpp
├── CMakeLists.txt
└── src/CMakeLists.txt
```

## Dependencies
- Qt6 (Widgets, Network)
- C++17
- Ollama API (for AI provider)

## Usage
```bash
python add_custom_editor_and_features.py
```

## Generated Code Patterns

### Singleton Pattern
- `SettingsManager` uses Meyer's singleton

### Signal/Slot Connections
- Extensive use of Qt signals/slots for component communication

### Markdown Parsing
- Regex for code block extraction: `(?s)```(?:[a-zA-Z0-9+#]+)?\\s*\\n?(.*?)(?:```|$)`

### File Operations
- QFile/QTextStream for file I/O
- QFileDialog for user dialogs

## Quick Reference

### Settings Keys
- `endpoint`: AI service URL (default: `http://localhost:11434`)
- `model`: AI model name (default: `llama3`)
- `providerType`: Provider type (default: `Ollama`)

### AI Response Format
- Markdown with code blocks
- Code extracted for editor application

### Diff Colors
- Red background: removed lines
- Green background: added lines
- No background: unchanged lines

## Notes
- Script creates directories as needed
- Uses UTF-8 encoding
- Qt MOC (Meta-Object Compiler) enabled
- Auto-generated code uses modern C++17 features