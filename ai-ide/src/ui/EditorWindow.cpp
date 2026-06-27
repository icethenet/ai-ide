#include "EditorWindow.hpp"
#include "FileBrowser.hpp"
#include "AIChatPanel.hpp"
#include "CustomEditor.hpp"
#include "DiffView.hpp"
#include "AIPatchController.hpp"
#include "AdminDialog.hpp"
#include "ClipboardListener.hpp"
#include "TerminalWidget.hpp"
#include "ProblemsWidget.hpp"
#include "DebugWidget.hpp"
#include "WelcomeWidget.hpp"
#include "CommandPalette.hpp"

#include <QRegularExpression>

#include <QMenuBar>
#include <QDockWidget>
#include <QListView>
#include <QSplitter>
#include <QPlainTextEdit>
#include <QProcess>
#include <QAction>
#include <QInputDialog>
#include <QFile>
#include <QFileDialog>
#include <QShowEvent>
#include <QTimer>
#include <QStatusBar>
#include <QStringListModel>
#include <QTextBlock>
#include <QTextCursor>
#include <QTextDocument>
#include <QMessageBox>

EditorWindow::EditorWindow(QWidget *parent)
    : QMainWindow(parent),
      tabWidget(nullptr),
      bottomTabWidget(nullptr),
      mainSplitter(nullptr),
      powerShellTab(nullptr),
      bashTab(nullptr),
      debugTab(nullptr),
      problemsTab(nullptr),
      outputTab(nullptr),
      historyView(nullptr),
      buildProcess(nullptr),
      fileBrowser(nullptr),
      aiPatchController(nullptr),
      commandPalette(nullptr),
      clipboardListener(nullptr),
      historyModel(new QStringListModel(this))
{
    setWindowTitle("AI-IDE");

    createCentralEditor();
    createDocks();
    createMenus();
    openWelcomeTab();
    
    // Defer ClipboardListener initialization until after the window is shown
    // to ensure the native window handle is fully initialized for AddClipboardFormatListener.
    // This is handled in showEvent.
}

void EditorWindow::showEvent(QShowEvent* event) {
    QMainWindow::showEvent(event); // Call base class implementation
    
    if (!clipboardListener && isVisible()) {
        // Ensure handle is created
        (void)winId();
        
        QTimer::singleShot(1000, this, [this]() {
            if (clipboardListener) return;
            clipboardListener = new ClipboardListener(this);
            connect(clipboardListener, &ClipboardListener::codeCopied, this, [this](const QString& text) {
                if (statusBar()) statusBar()->showMessage("Code detected in clipboard", 3000);
            });
        });
    }
}
void EditorWindow::createCentralEditor() {
    tabWidget = new QTabWidget(this);
    tabWidget->setTabsClosable(true);
    connect(tabWidget, &QTabWidget::tabCloseRequested, this, [this](int index) {
        QWidget* w = tabWidget->widget(index);
        tabWidget->removeTab(index);
        if (w) w->deleteLater();
    });

    bottomTabWidget = new QTabWidget(this);

    // Create PowerShell terminal tab
    powerShellTab = new TerminalWidget("powershell.exe", this);

    // Create Bash terminal tab - detect Git Bash or fall back to wsl.exe
    QString bashExe;
    QStringList bashCandidates = {
        "C:/Program Files/Git/bin/bash.exe",
        "C:/Program Files (x86)/Git/bin/bash.exe",
        "C:/msys64/usr/bin/bash.exe",
    };
    for (const QString& candidate : bashCandidates) {
        if (QFile::exists(candidate)) { bashExe = candidate; break; }
    }
    if (bashExe.isEmpty()) {
        // Fallback: check if wsl.exe exists (WSL Bash)
        if (QFile::exists("C:/Windows/System32/wsl.exe")) {
            bashExe = "C:/Windows/System32/wsl.exe";
        } else {
            bashExe = "powershell.exe"; // Last resort: use PS if no bash found
        }
    }
    bashTab = new TerminalWidget(bashExe, this);

    debugTab = new DebugWidget(this);
    problemsTab = new ProblemsWidget(this);
    connect(problemsTab, &ProblemsWidget::problemActivated, this, &EditorWindow::gotoLine);
    
    // Create read-only output terminal text edit
    outputTab = new QPlainTextEdit(this);
    outputTab->setReadOnly(true);
    QFont monoFont("Consolas", 10);
    if (monoFont.fixedPitch()) {
        outputTab->setFont(monoFont);
    }

    bottomTabWidget->addTab(powerShellTab, "PowerShell");
    bottomTabWidget->addTab(bashTab, "Bash");
    bottomTabWidget->addTab(debugTab, "Debug");
    bottomTabWidget->addTab(problemsTab, "Problems");
    bottomTabWidget->addTab(outputTab, "Output");

    // Add AI History view tab
    historyView = new QListView(this);
    historyView->setModel(historyModel);
    bottomTabWidget->addTab(historyView, "AI History");

    mainSplitter = new QSplitter(Qt::Vertical, this);
    mainSplitter->addWidget(tabWidget);
    mainSplitter->addWidget(bottomTabWidget);

    mainSplitter->setStretchFactor(0, 3);
    mainSplitter->setStretchFactor(1, 1);

    setCentralWidget(mainSplitter);
}

void EditorWindow::openFileInTab(const QString& path) {
    auto* newEditor = new CustomEditor(this);
    if (!path.isEmpty()) newEditor->openFile(path);
    
    connect(newEditor, &CustomEditor::closeRequested, this, [this, newEditor]() {
        int idx = tabWidget->indexOf(newEditor);
        if (idx != -1) {
            tabWidget->removeTab(idx);
            newEditor->deleteLater();
        }
    });

    QString title = path.isEmpty() ? "Untitled" : QFileInfo(path).fileName();
    int idx = tabWidget->addTab(newEditor, title);
    tabWidget->setCurrentIndex(idx);
}

void EditorWindow::openWelcomeTab() {
    auto* welcome = new WelcomeWidget(this);
    connect(welcome, &WelcomeWidget::newFileRequested, this, [this]() { openFileInTab(""); });
    connect(welcome, &WelcomeWidget::openFileRequested, this, [this]() {
        QString path = QFileDialog::getOpenFileName(this, "Open File");
        if (!path.isEmpty()) openFileInTab(path);
    });
    connect(welcome, &WelcomeWidget::openFolderRequested, this, [this]() {
        QString dir = QFileDialog::getExistingDirectory(this, "Open Project Folder");
        if (!dir.isEmpty() && fileBrowser) {
            fileBrowser->setRootDirectory(dir);
        }
    });
    connect(welcome, &WelcomeWidget::buildRequested, this, &EditorWindow::runBuild);
    connect(welcome, &WelcomeWidget::settingsRequested, this, [this]() {
        AdminDialog dlg(this);
        dlg.exec();
    });

    int idx = tabWidget->addTab(welcome, "Welcome");
    tabWidget->setCurrentIndex(idx);
}

void EditorWindow::showCommandPalette() {
    if (!commandPalette) {
        commandPalette = new CommandPalette(this);
        commandPalette->addCommand("File: New File", "Ctrl+N", [this]() { openFileInTab(""); });
        commandPalette->addCommand("File: Open File", "Ctrl+O", [this]() {
            QString path = QFileDialog::getOpenFileName(this, "Open File");
            if (!path.isEmpty()) openFileInTab(path);
        });
        commandPalette->addCommand("File: Open Folder", "", [this]() {
            QString dir = QFileDialog::getExistingDirectory(this, "Open Project Folder");
            if (!dir.isEmpty() && fileBrowser) {
                fileBrowser->setRootDirectory(dir);
            }
        });
        commandPalette->addCommand("Build: Build Project", "Ctrl+B", [this]() { runBuild(); });
        commandPalette->addCommand("AI: Refactor with AI", "", [this]() {
            bool ok = false;
            QString instr = QInputDialog::getText(this, "AI Refactor",
                                                  "Describe the refactor:",
                                                  QLineEdit::Normal,
                                                  "", &ok);
            if (ok && !instr.trimmed().isEmpty()) {
                aiPatchController->setEditor(currentEditor());
                aiPatchController->requestRefactor(instr.trimmed());
            }
        });
        commandPalette->addCommand("AI: Provider Settings", "", [this]() {
            AdminDialog dlg(this);
            dlg.exec();
        });
        commandPalette->addCommand("Debugger: Start/Stop", "", [this]() {
            if (bottomTabWidget && debugTab) {
                bottomTabWidget->setCurrentWidget(debugTab);
                auto* startBtn = debugTab->findChild<QPushButton*>();
                if (startBtn) startBtn->click();
            }
        });
        commandPalette->addCommand("Help: About", "", [this]() {
            QMessageBox::about(this, "About AI-IDE", "AI-IDE\nNext-generation C++ development powered by LLVM and Local AI.");
        });
    }
    commandPalette->showPalette();
}

void EditorWindow::createDocks() {
    // File Browser (Left)
    auto* fileDock = new QDockWidget("Files", this);
    fileBrowser = new FileBrowser(fileDock);
    fileDock->setWidget(fileBrowser);
    fileDock->setMinimumWidth(250);
    addDockWidget(Qt::LeftDockWidgetArea, fileDock);

    connect(fileBrowser, &FileBrowser::fileOpened, this, [this](const QString& path) {
        openFileInTab(path);
    });

    // AI Chat (Right)
    auto* aiDock = new QDockWidget("AI Chat", this);
    auto* aiPanel = new AIChatPanel(aiDock);
    aiDock->setWidget(aiPanel);
    addDockWidget(Qt::RightDockWidgetArea, aiDock);

    // Connect AI Chat signals to the Central Editor
    connect(aiPanel, &AIChatPanel::applyToEditor, this, [this](const QString& code) {
        if (auto* ed = currentEditor()) {
            auto* textEdit = ed->findChild<QPlainTextEdit*>();
            if (textEdit) textEdit->setPlainText(code);
        }
    });

    connect(aiPanel, &AIChatPanel::createNewFile, this, [this](const QString& code) {
        openFileInTab("");
        if (auto* ed = currentEditor()) {
            auto* textEdit = ed->findChild<QPlainTextEdit*>();
            if (textEdit) textEdit->setPlainText(code);
        }
    });

    connect(aiPanel, &AIChatPanel::promptArchived, this, [this](const QString& summary) {
        QStringList list = historyModel->stringList();
        list.prepend(summary);
        historyModel->setStringList(list);
    });

    aiPatchController = new AIPatchController(nullptr, this);
}

CustomEditor* EditorWindow::currentEditor() const {
    return qobject_cast<CustomEditor*>(tabWidget->currentWidget());
}

void EditorWindow::createMenus() {
    auto *fileMenu = menuBar()->addMenu("&File");
    
    fileMenu->addAction("New File", [this]() {
        openFileInTab("");
    });
    
    fileMenu->addSeparator();

    fileMenu->addAction("Open File", [this]() {
        QString path = QFileDialog::getOpenFileName(this, "Open File");
        if (!path.isEmpty()) openFileInTab(path);
    });

    fileMenu->addAction("Open Folder", [this]() {
        QString dir = QFileDialog::getExistingDirectory(this, "Open Project Folder");
        if (!dir.isEmpty() && fileBrowser) {
            fileBrowser->setRootDirectory(dir);
        }
    });

    fileMenu->addAction("Close", [this]() {
        tabWidget->removeTab(tabWidget->currentIndex());
    });

    fileMenu->addAction("Save", [this]() {
        if (auto* ed = currentEditor()) ed->saveFile();
    });

    fileMenu->addAction("Save As", [this]() {
        if (auto* ed = currentEditor()) ed->saveAsFile();
    });

    fileMenu->addSeparator();
    fileMenu->addAction("Exit", this, SLOT(close()));

    auto *aiMenu = menuBar()->addMenu("&AI");
    auto *refactorAction = aiMenu->addAction("Refactor with AI");
    connect(refactorAction, &QAction::triggered, this, [this]() {
        bool ok = false;
        QString instr = QInputDialog::getText(this, "AI Refactor",
                                              "Describe the refactor:",
                                              QLineEdit::Normal,
                                              "", &ok);
        if (ok && !instr.trimmed().isEmpty()) {
            aiPatchController->setEditor(currentEditor());
            aiPatchController->requestRefactor(instr.trimmed());
        }
    });

    aiMenu->addAction("AI Settings (Admin)", [this]() {
        AdminDialog dlg(this);
        dlg.exec();
    });

    auto *buildMenu = menuBar()->addMenu("&Build");
    buildMenu->addAction("Build Project", QKeySequence(Qt::CTRL | Qt::Key_B), this, &EditorWindow::runBuild);

    auto *helpMenu = menuBar()->addMenu("&Help");
    helpMenu->addAction("About");

    auto *paletteAction = new QAction("Command Palette", this);
    paletteAction->setShortcut(QKeySequence(Qt::CTRL | Qt::SHIFT | Qt::Key_P));
    connect(paletteAction, &QAction::triggered, this, &EditorWindow::showCommandPalette);
    addAction(paletteAction);
}

void EditorWindow::runBuild() {
    if (buildProcess && buildProcess->state() != QProcess::NotRunning) {
        if (statusBar()) statusBar()->showMessage("Build is already running!", 3000);
        return;
    }

    if (!outputTab) return;
    outputTab->clear();
    
    if (problemsTab) {
        problemsTab->clearProblems();
    }
    
    buildBuffer.clear();

    // Switch to Output Tab
    if (bottomTabWidget) {
        int outputIndex = bottomTabWidget->indexOf(outputTab);
        if (outputIndex != -1) {
            bottomTabWidget->setCurrentIndex(outputIndex);
        }
    }

    if (statusBar()) statusBar()->showMessage("Building project...");

    if (!buildProcess) {
        buildProcess = new QProcess(this);
        buildProcess->setProcessChannelMode(QProcess::MergedChannels);
        connect(buildProcess, &QProcess::readyReadStandardOutput, this, &EditorWindow::readBuildOutput);
        connect(buildProcess, &QProcess::finished, this, [this](int exitCode, QProcess::ExitStatus status) {
            this->buildFinished(exitCode, static_cast<int>(status));
        });
    }
    
    buildProcess->setWorkingDirectory(QDir::currentPath());
    buildProcess->start("python", QStringList() << "build.py");
}

void EditorWindow::readBuildOutput() {
    if (!buildProcess || !outputTab) return;
    
    QByteArray data = buildProcess->readAllStandardOutput();
    if (data.isEmpty()) return;
    
    QString text = QString::fromLocal8Bit(data);
    outputTab->insertPlainText(text);
    outputTab->moveCursor(QTextCursor::End);
    
    buildBuffer.append(text);
    
    int newlineIdx;
    while ((newlineIdx = buildBuffer.indexOf('\n')) != -1) {
        QString line = buildBuffer.left(newlineIdx).trimmed();
        buildBuffer.remove(0, newlineIdx + 1);
        if (!line.isEmpty()) {
            parseBuildLine(line);
        }
    }
}

void EditorWindow::buildFinished(int exitCode, int exitStatus) {
    // Process any leftover text in the buffer
    if (!buildBuffer.isEmpty()) {
        QString line = buildBuffer.trimmed();
        if (!line.isEmpty()) {
            parseBuildLine(line);
        }
        buildBuffer.clear();
    }

    if (statusBar()) {
        if (exitCode == 0 && exitStatus == 0) {
            statusBar()->showMessage("Build Successful!", 5000);
        } else {
            statusBar()->showMessage("Build Failed (Exit Code: " + QString::number(exitCode) + ")", 5000);
        }
    }
}

void EditorWindow::parseBuildLine(const QString& line) {
    static QRegularExpression regex(R"(^(.+?):(\d+):(\d+):\s*(error|warning|note|fatal error):\s*(.*)$)", QRegularExpression::CaseInsensitiveOption);
    QRegularExpressionMatch match = regex.match(line);
    if (match.hasMatch()) {
        QString file = match.captured(1).trimmed();
        int lineNum = match.captured(2).toInt();
        int colNum = match.captured(3).toInt();
        QString severity = match.captured(4).trimmed();
        QString message = match.captured(5).trimmed();
        
        if (problemsTab) {
            problemsTab->addProblem(severity, file, lineNum, colNum, message);
        }
    }
}

void EditorWindow::gotoLine(const QString& file, int line) {
    openFileInTab(file);
    if (auto* ed = currentEditor()) {
        auto* textEdit = ed->findChild<QPlainTextEdit*>();
        if (textEdit) {
            QTextDocument* doc = textEdit->document();
            QTextBlock block = doc->findBlockByLineNumber(line - 1);
            if (block.isValid()) {
                QTextCursor cursor(block);
                cursor.movePosition(QTextCursor::StartOfLine);
                cursor.movePosition(QTextCursor::EndOfLine, QTextCursor::KeepAnchor);
                textEdit->setTextCursor(cursor);
                textEdit->setFocus();
            }
        }
    }
}
