# AI-IDE Component Index

## Quick Reference

### Main Components

| Component | Purpose | Status |
|-----------|---------|--------|
| [EditorWindow](src/ui/EditorWindow.hpp) | Main application window | ✅ Complete |
| [CustomEditor](src/ui/CustomEditor.hpp) | Code editing widget | ✅ Complete |
| [FileBrowser](src/ui/FileBrowser.hpp) | File system browser | ✅ Complete |
| [AIChatPanel](src/ui/AIChatPanel.hpp) | AI chat interface | ✅ Complete |
| [DiffView](src/ui/DiffView.hpp) | Code diff viewer | ✅ Complete |
| [AIPatchController](src/ui/AIPatchController.hpp) | AI refactor controller | ✅ Complete |
| [AdminDialog](src/ui/AdminDialog.hpp) | Settings dialog | ✅ Complete |
| [ClipboardListener](src/ui/ClipboardListener.hpp) | Clipboard monitoring | ✅ Complete |

### AI Components

| Component | Purpose | Status |
|-----------|---------|--------|
| [OllamaProvider](ai/OllamaProvider.hpp) | AI API communication | ⚠️ Needs implementation |

### Git Components

| Component | Purpose | Status |
|-----------|---------|--------|
| [GitClient](src/git/GitClient.hpp) | Git operations | ⚠️ Needs implementation |

## Component Details

### EditorWindow
**Location**: [src/ui/EditorWindow.hpp](src/ui/EditorWindow.hpp)

**Responsibilities**:
- Main application window
- Coordinates all UI components
- Handles window events and layout
- Manages application state

**Signals**:
- `fileOpened(const QString& path)` - Emitted when a file is opened
- `editorChanged(const QString& path)` - Emitted when editor content changes
- `aiResponseReceived(const QString& response)` - Emitted when AI responds

**Slots**:
- `onFileOpened(const QString& path)` - Handles file opening
- `onEditorChanged()` - Handles editor changes
- `onAIResponse(const QString& response)` - Handles AI responses

### CustomEditor
**Location**: [src/ui/CustomEditor.hpp](src/ui/CustomEditor.hpp)

**Responsibilities**:
- Main code editing widget
- File operations (open, save, saveAs)
- Text editing and manipulation
- Line number display

**Signals**:
- `fileChanged(const QString& path)` - Emitted when file content changes
- `textChanged()` - Emitted when text changes

**Slots**:
- `openFile(const QString& path)` - Opens a file
- `saveFile()` - Saves current file
- `saveAsFile(const QString& path)` - Saves with new path
- `clear()` - Clears editor content

### FileBrowser
**Location**: [src/ui/FileBrowser.hpp](src/ui/FileBrowser.hpp)

**Responsibilities**:
- File system tree view
- Project folder navigation
- File selection and opening
- File icons and metadata

**Signals**:
- `fileSelected(const QString& path)` - Emitted when a file is selected
- `folderSelected(const QString& path)` - Emitted when a folder is selected

**Slots**:
- `setProjectPath(const QString& path)` - Sets the project root folder
- `refresh()` - Refreshes the file tree

### AIChatPanel
**Location**: [src/ui/AIChatPanel.hpp](src/ui/AIChatPanel.hpp)

**Responsibilities**:
- AI chat interface
- Code snippet extraction from Markdown
- Message history management
- User prompt handling

**Signals**:
- `promptSent(const QString& prompt)` - Emitted when user sends a prompt
- `codeExtracted(const QString& code)` - Emitted when code is extracted

**Slots**:
- `sendPrompt(const QString& prompt)` - Sends prompt to AI
- `extractCode(const QString& text)` - Extracts code from Markdown
- `saveCode(const QString& code, const QString& filename)` - Saves extracted code

### DiffView
**Location**: [src/ui/DiffView.hpp](src/ui/DiffView.hpp)

**Responsibilities**:
- Side-by-side code diff viewer
- Change highlighting
- Diff statistics display
- Apply/revert changes

**Signals**:
- `changesApplied()` - Emitted when changes are applied
- `changesReverted()` - Emitted when changes are reverted

**Slots**:
- `showDiff(const QString& original, const QString& modified)` - Displays diff
- `applyChanges()` - Applies changes from diff
- `revertChanges()` - Reverts changes

### AIPatchController
**Location**: [src/ui/AIPatchController.hpp](src/ui/AIPatchController.hpp)

**Responsibilities**:
- AI-powered code refactoring workflow
- Manages refactor requests
- Coordinates with AI and editor
- Handles diff display and application

**Signals**:
- `refactorRequested(const QString& instruction)` - Emitted when refactor is requested
- `refactorComplete(const QString& result)` - Emitted when refactor completes

**Slots**:
- `requestRefactor(const QString& instruction)` - Requests AI refactor
- `applyPatch(const QString& patch)` - Applies AI-generated patch
- `showDiff(const QString& original, const QString& modified)` - Shows diff

### AdminDialog
**Location**: [src/ui/AdminDialog.hpp](src/ui/AdminDialog.hpp)

**Responsibilities**:
- Settings management UI
- AI provider configuration
- Model selection and discovery
- Endpoint configuration

**Signals**:
- `settingsSaved(const Settings& settings)` - Emitted when settings are saved

**Slots**:
- `saveSettings()` - Saves current settings
- `loadSettings()` - Loads settings from storage
- `discoverModels()` - Discovers available AI models

### ClipboardListener
**Location**: [src/ui/ClipboardListener.hpp](src/ui/ClipboardListener.hpp)

**Responsibilities**:
- Monitors clipboard for code snippets
- Detects code changes
- Notifies AI panel when code is copied

**Signals**:
- `codeCopied(const QString& code)` - Emitted when code is copied

**Slots**:
- `startMonitoring()` - Starts clipboard monitoring
- `stopMonitoring()` - Stops clipboard monitoring

### OllamaProvider
**Location**: [ai/OllamaProvider.hpp](ai/OllamaProvider.hpp)

**Responsibilities**:
- AI API communication
- HTTP request handling
- JSON response parsing
- Error handling

**Methods**:
- `send(AIRequest request)` - Sends request to AI API
- `parseResponse(const QString& response)` - Parses AI response
- `handleError(const QString& error)` - Handles errors

**Status**: ⚠️ Needs implementation

### GitClient
**Location**: [src/git/GitClient.hpp](src/git/GitClient.hpp)

**Responsibilities**:
- Git status checking
- File staging
- Commit operations
- Push operations

**Methods**:
- `status()` - Gets git status
- `add(const QString& file)` - Stages a file
- `commit(const QString& message)` - Commits changes
- `push()` - Pushes changes to remote

**Status**: ⚠️ Needs implementation

## Component Dependencies

### EditorWindow Dependencies
- CustomEditor
- FileBrowser
- AIChatPanel
- DiffView
- AIPatchController
- ClipboardListener

### AIPatchController Dependencies
- OllamaProvider
- CustomEditor
- DiffView
- SettingsManager

### AIChatPanel Dependencies
- OllamaProvider
- SettingsManager

### AdminDialog Dependencies
- SettingsManager
- QNetworkAccessManager

## Signal Flow Diagram

```
User Action → Component → Signal → EditorWindow → Slot → Action
```

Example:
```
User clicks file in FileBrowser → fileSelected signal → EditorWindow.onFileOpened → CustomEditor.openFile
```

## Development Status

### ✅ Complete Components
- EditorWindow
- CustomEditor
- FileBrowser
- AIChatPanel
- DiffView
- AIPatchController
- AdminDialog
- ClipboardListener

### ⚠️ Needs Implementation
- OllamaProvider (High Priority)
- GitClient (High Priority)

### 📋 Future Enhancements
- Syntax highlighting in CustomEditor
- Streaming AI responses
- Code completion
- Project management
- Terminal integration
- Multi-provider support

## Quick Start

1. **Build the project**:
   ```bash
   mkdir build && cd build
   cmake ..
   cmake --build .
   ```

2. **Run the application**:
   ```bash
   ./ai-ide
   ```

3. **Open a project**:
   - File → Open Folder
   - Select your project directory

4. **Configure AI**:
   - Settings → Admin
   - Enter Ollama endpoint
   - Select model
   - Click "Discover Models"

5. **Use AI features**:
   - Chat with AI using AIChatPanel
   - Select code and use "Refactor with AI"
   - Monitor clipboard for code snippets

## Troubleshooting

### Build Issues
- Ensure Qt6 is installed and CMake can find it
- Check CMakeLists.txt for correct dependencies
- Verify C++17 compiler is available

### AI Not Working
- Verify Ollama is running
- Check AdminDialog settings
- Ensure endpoint is correct
- Check network connectivity

### File Browser Issues
- Ensure you've opened a project folder
- Check file permissions
- Verify project path is correct

---

*Last Updated: May 28, 2026*
*Version: 1.0*