# AI-IDE Programming Guide

## Overview
AI-IDE is a Qt6-based integrated development environment with AI-powered features. This guide provides a comprehensive index of all components, their relationships, and development guidelines.

## Project Structure
```
ai-ide/
├── src/
│   ├── main.cpp              # Application entry point
│   ├── ui/                   # UI components
│   │   ├── EditorWindow.hpp/cpp    # Main window
│   │   ├── CustomEditor.hpp/cpp    # Code editor widget
│   │   ├── FileBrowser.hpp/cpp     # File browser widget
│   │   ├── AIChatPanel.hpp/cpp     # AI chat interface
│   │   ├── DiffView.hpp/cpp        # Code diff viewer
│   │   ├── AIPatchController.hpp/cpp # AI refactor controller
│   │   ├── AdminDialog.hpp/cpp     # Settings dialog
│   │   └── ClipboardListener.hpp/cpp # Clipboard monitoring
│   ├── ai/                   # AI integration layer
│   │   └── OllamaProvider.hpp/cpp   # AI provider interface
│   └── git/                  # Git integration
│       └── GitClient.hpp/cpp        # Git operations
├── CMakeLists.txt            # Build configuration
└── PROGRAMMING_GUIDE.md      # This file
```