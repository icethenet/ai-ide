#include "EditorWindow.hpp"
#include "FileBrowser.hpp"
#include "AIChatPanel.hpp"
#include "CustomEditor.hpp"
#include "DiffView.hpp"
#include "AIPatchController.hpp"
#include "AdminDialog.hpp"
#include "ClipboardListener.hpp"
#include "FindReplaceDialog.hpp"
#include "TerminalWidget.hpp"
#include "ProblemsWidget.hpp"
#include "DebugWidget.hpp"
#include "WelcomeWidget.hpp"
#include "CommandPalette.hpp"
#include "SearchWidget.hpp"
#include "GitWidget.hpp"
#include "LspClient.hpp"
#include <QComboBox>
#include <QLabel>
#include <QTableWidget>
#include <QHeaderView>
#include <QUrl>
#include <QIcon>
#include <QPixmap>

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
#include <QDir>
#include <QShowEvent>
#include <QTimer>
#include <QMessageBox>
#include <QKeyEvent>
#include <QLineEdit>
#include <QHBoxLayout>
#include <QVBoxLayout>
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
      searchWidget(nullptr),
      gitWidget(nullptr),
      aiPatchController(nullptr),
      commandPalette(nullptr),
      pathLineEdit(nullptr),
      cmdLineEdit(nullptr),
      cmakeTargetCombo(nullptr),
      cmakeBuildTypeCombo(nullptr),
      clipboardListener(nullptr),
      historyModel(new QStringListModel(this)),
      findReplaceDialog(nullptr)
{
    setWindowTitle("AI-IDE");
    setWindowIcon(QIcon(":/idelogo.png"));

    // Application-wide styling (Sleek dark theme)
    setStyleSheet(
        "QMainWindow { background-color: #21252b; color: #abb2bf; }"
        "QWidget { background-color: #21252b; color: #abb2bf; font-family: 'Segoe UI', Arial; }"
        "QScrollBar:vertical { background-color: #21252b; width: 12px; margin: 0px; }"
        "QScrollBar::handle:vertical { background-color: #3e4452; min-height: 20px; border-radius: 6px; border: 2px solid #21252b; }"
        "QScrollBar::handle:vertical:hover { background-color: #5c6370; }"
        "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
        "QScrollBar:horizontal { background-color: #21252b; height: 12px; margin: 0px; }"
        "QScrollBar::handle:horizontal { background-color: #3e4452; min-width: 20px; border-radius: 6px; border: 2px solid #21252b; }"
        "QScrollBar::handle:horizontal:hover { background-color: #5c6370; }"
        "QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }"
        "QTabWidget::pane { border: 1px solid #181a1f; background-color: #1e1e1e; }"
        "QTabBar::tab { background-color: #21252b; color: #abb2bf; padding: 8px 12px; border-top-left-radius: 4px; border-top-right-radius: 4px; border: 1px solid #181a1f; border-bottom: none; margin-right: 2px; }"
        "QTabBar::tab:selected { background-color: #1e1e1e; color: #ffffff; border-bottom: 2px solid #61afef; }"
        "QTabBar::tab:hover { background-color: #2c313c; color: #ffffff; }"
        "QTableWidget { background-color: #1e1e1e; color: #abb2bf; border: none; gridline-color: #282c34; selection-background-color: #3e4452; selection-color: #ffffff; }"
        "QTableWidget::item { padding: 4px; }"
        "QHeaderView::section { background-color: #21252b; color: #abb2bf; padding: 4px; border: 1px solid #181a1f; }"
        "QMenuBar { background-color: #21252b; color: #abb2bf; border-bottom: 1px solid #181a1f; }"
        "QMenuBar::item { background-color: transparent; padding: 4px 10px; }"
        "QMenuBar::item:selected { background-color: #3e4452; color: #ffffff; border-radius: 4px; }"
        "QMenu { background-color: #21252b; color: #abb2bf; border: 1px solid #181a1f; border-radius: 4px; padding: 4px 0px; }"
        "QMenu::item { padding: 6px 20px; }"
        "QMenu::item:selected { background-color: #3e4452; color: #ffffff; }"
        "QStatusBar { background-color: #21252b; color: #abb2bf; border-top: 1px solid #181a1f; }"
    );

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
    // Top Control Bar
    auto* topControlBar = new QWidget(this);
    topControlBar->setStyleSheet("QWidget { background-color: #21252b; border-bottom: 1px solid #181a1f; }");
    auto* topLayout = new QHBoxLayout(topControlBar);
    topLayout->setContentsMargins(10, 4, 10, 4);
    topLayout->setSpacing(20);

    // Left half: Path/Folder Browser
    auto* leftLayout = new QHBoxLayout();
    leftLayout->setSpacing(5);
    
    auto* browseBtn = new QPushButton("Browse...", this);
    browseBtn->setStyleSheet("QPushButton { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 4px 8px; font-family: 'Segoe UI', Arial; }"
                             "QPushButton:hover { background-color: #3e4452; color: #ffffff; }");
    
    pathLineEdit = new QLineEdit(this);
    pathLineEdit->setPlaceholderText("Enter folder or file path to browse...");
    pathLineEdit->setStyleSheet("QLineEdit { background-color: #1e1e1e; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 4px 8px; font-family: 'Segoe UI', Arial; }");
    
    leftLayout->addWidget(pathLineEdit, 1);
    leftLayout->addWidget(browseBtn);
    topLayout->addLayout(leftLayout, 1);

    // Right half: Command line edit
    cmdLineEdit = new QLineEdit(this);
    cmdLineEdit->setPlaceholderText("Type command (Ctrl+Shift+P)...");
    cmdLineEdit->setStyleSheet("QLineEdit { background-color: #1e1e1e; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 4px 8px; font-family: 'Segoe UI', Arial; }");
    topLayout->addWidget(cmdLineEdit, 1);

    // Path line edit triggers
    connect(pathLineEdit, &QLineEdit::returnPressed, this, [this]() {
        QString path = pathLineEdit->text().trimmed();
        if (!path.isEmpty()) {
            QFileInfo info(path);
            if (info.isDir()) {
                if (fileBrowser) fileBrowser->setRootDirectory(path);
            } else {
                openFileInTab(path);
            }
        }
    });

    connect(browseBtn, &QPushButton::clicked, this, [this]() {
        QString dir = QFileDialog::getExistingDirectory(this, "Open Project Folder", pathLineEdit->text());
        if (!dir.isEmpty()) {
            pathLineEdit->setText(dir);
            if (fileBrowser) fileBrowser->setRootDirectory(dir);
        }
    });

    // Command line edit event filtering and connections
    cmdLineEdit->installEventFilter(this);
    connect(cmdLineEdit, &QLineEdit::textChanged, this, [this](const QString& text) {
        if (commandPalette) {
            if (!commandPalette->isVisible()) showCommandPalette();
            commandPalette->filterCommands(text);
        }
    });

    tabWidget = new QTabWidget(this);
    tabWidget->setTabsClosable(true);
    connect(tabWidget, &QTabWidget::tabCloseRequested, this, [this](int index) {
        QWidget* w = tabWidget->widget(index);
        tabWidget->removeTab(index);
        if (w) w->deleteLater();
    });

    // Synchronize pathLineEdit with active tab changes
    connect(tabWidget, &QTabWidget::currentChanged, this, [this](int index) {
        if (index != -1) {
            auto* ed = qobject_cast<CustomEditor*>(tabWidget->widget(index));
            if (ed) {
                pathLineEdit->setText(ed->currentFilePath());
            } else if (qobject_cast<SearchWidget*>(tabWidget->widget(index))) {
                pathLineEdit->setText("Workspace Search");
            } else {
                pathLineEdit->setText("Welcome Page");
            }
        }
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
        if (QFile::exists("C:/Windows/System32/wsl.exe")) {
            bashExe = "C:/Windows/System32/wsl.exe";
        } else {
            bashExe = "powershell.exe";
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

    auto* container = new QWidget(this);
    auto* containerLayout = new QVBoxLayout(container);
    containerLayout->setContentsMargins(0, 0, 0, 0);
    containerLayout->setSpacing(0);
    containerLayout->addWidget(topControlBar);
    containerLayout->addWidget(mainSplitter);

    // Bottom Status Bar selectors
    cmakeBuildTypeCombo = new QComboBox(this);
    cmakeBuildTypeCombo->addItems(QStringList() << "Debug" << "Release" << "RelWithDebInfo" << "MinSizeRel");
    cmakeBuildTypeCombo->setStyleSheet("QComboBox { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 2px 6px; font-family: 'Segoe UI', Arial; font-size: 11px; }"
                                       "QComboBox::drop-down { border: none; }"
                                       "QComboBox QAbstractItemView { background-color: #2c313c; color: #abb2bf; selection-background-color: #3e4452; }");

    cmakeTargetCombo = new QComboBox(this);
    cmakeTargetCombo->addItems(QStringList() << "ai-ide" << "clean" << "rebuild");
    cmakeTargetCombo->setStyleSheet("QComboBox { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 2px 6px; font-family: 'Segoe UI', Arial; font-size: 11px; }"
                                    "QComboBox::drop-down { border: none; }"
                                    "QComboBox QAbstractItemView { background-color: #2c313c; color: #abb2bf; selection-background-color: #3e4452; }");

    if (statusBar()) {
        auto* buildLabel = new QLabel("  Config: ", this);
        buildLabel->setStyleSheet("QLabel { color: #abb2bf; font-family: 'Segoe UI', Arial; font-size: 11px; }");
        auto* targetLabel = new QLabel("  Target: ", this);
        targetLabel->setStyleSheet("QLabel { color: #abb2bf; font-family: 'Segoe UI', Arial; font-size: 11px; }");
        
        statusBar()->addPermanentWidget(buildLabel);
        statusBar()->addPermanentWidget(cmakeBuildTypeCombo);
        statusBar()->addPermanentWidget(targetLabel);
        statusBar()->addPermanentWidget(cmakeTargetCombo);
    }

    referencesTable = new QTableWidget(this);
    referencesTable->setColumnCount(3);
    referencesTable->setHorizontalHeaderLabels(QStringList() << "File" << "Line" << "Match");
    referencesTable->setStyleSheet("QTableWidget { background-color: #1e1e1e; color: #abb2bf; border: none; font-family: 'Segoe UI', Arial; font-size: 12px; }"
                                   "QTableWidget::item:hover { background-color: #2c313c; }"
                                   "QTableWidget::item:selected { background-color: #3e4452; color: #ffffff; }");
    referencesTable->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    
    connect(referencesTable, &QTableWidget::itemDoubleClicked, this, [this](QTableWidgetItem* item) {
        int row = item->row();
        auto* fileItem = referencesTable->item(row, 0);
        auto* lineItem = referencesTable->item(row, 1);
        if (fileItem && lineItem) {
            gotoLine(fileItem->toolTip(), lineItem->text().toInt());
        }
    });

    bottomTabWidget->addTab(referencesTable, "References");

    setCentralWidget(container);
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

    if (pathLineEdit) pathLineEdit->setText(path);

    QString title = path.isEmpty() ? "Untitled" : QFileInfo(path).fileName();
    int idx = tabWidget->addTab(newEditor, title);
    tabWidget->setCurrentIndex(idx);

    updateDocumentDiagnostics();
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

void EditorWindow::openSearchTab() {
    int searchIdx = -1;
    for (int i = 0; i < tabWidget->count(); ++i) {
        if (qobject_cast<SearchWidget*>(tabWidget->widget(i))) {
            searchIdx = i;
            break;
        }
    }
    
    if (searchIdx != -1) {
        tabWidget->setCurrentIndex(searchIdx);
    } else {
        auto* sWidget = new SearchWidget(this);
        if (fileBrowser) {
            sWidget->setRootPath(fileBrowser->rootPath());
        }
        connect(sWidget, &SearchWidget::matchActivated, this, &EditorWindow::gotoLine);
        
        int idx = tabWidget->addTab(sWidget, "Workspace Search");
        tabWidget->setCurrentIndex(idx);
    }
}

void EditorWindow::showCommandPalette() {
    if (!commandPalette) {
        commandPalette = new CommandPalette(this);
        commandPalette->addCommand("File: New File", "Ctrl+N", [this]() { openFileInTab(""); });
        commandPalette->addCommand("File: Open File", "Ctrl+O", [this]() {
            QString path = QFileDialog::getOpenFileName(this, "Open File");
            if (!path.isEmpty()) openFileInTab(path);
        });
        commandPalette->addCommand("File: Search in Workspace", "Ctrl+Shift+F", [this]() { openSearchTab(); });
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
    
    if (cmdLineEdit) {
        commandPalette->filterCommands(cmdLineEdit->text());
        QPoint pos = cmdLineEdit->mapToGlobal(QPoint(0, cmdLineEdit->height()));
        commandPalette->setGeometry(pos.x(), pos.y(), cmdLineEdit->width(), 200);
        commandPalette->show();
        cmdLineEdit->setFocus();
    }
}

bool EditorWindow::eventFilter(QObject* obj, QEvent* event) {
    if (obj == cmdLineEdit) {
        if (event->type() == QEvent::KeyPress) {
            auto* keyEvent = static_cast<QKeyEvent*>(event);
            if (commandPalette && commandPalette->isVisible()) {
                if (keyEvent->key() == Qt::Key_Down) {
                    commandPalette->selectNext();
                    return true;
                } else if (keyEvent->key() == Qt::Key_Up) {
                    commandPalette->selectPrev();
                    return true;
                } else if (keyEvent->key() == Qt::Key_Enter || keyEvent->key() == Qt::Key_Return) {
                    commandPalette->executeCurrent();
                    cmdLineEdit->clear();
                    return true;
                } else if (keyEvent->key() == Qt::Key_Escape) {
                    commandPalette->hide();
                    return true;
                }
            } else if (keyEvent->key() == Qt::Key_Down || keyEvent->key() == Qt::Key_Up) {
                showCommandPalette();
                return true;
            }
        } else if (event->type() == QEvent::FocusIn) {
            showCommandPalette();
        } else if (event->type() == QEvent::FocusOut) {
            QTimer::singleShot(200, this, [this]() {
                if (commandPalette && !cmdLineEdit->hasFocus()) {
                    commandPalette->hide();
                }
            });
        }
    }
    return QMainWindow::eventFilter(obj, event);
}

void EditorWindow::createDocks() {
    // File Browser / Explorer Dock (Left)
    auto* fileDock = new QDockWidget("Explorer", this);
    fileDock->setMinimumWidth(280);
    
    auto* leftTabs = new QTabWidget(fileDock);
    leftTabs->setStyleSheet("QTabWidget::pane { border: none; }"
                            "QTabBar::tab { background-color: #21252b; color: #abb2bf; padding: 8px 12px; font-family: 'Segoe UI', Arial; }"
                            "QTabBar::tab:selected { background-color: #1e1e1e; color: #ffffff; border-bottom: 2px solid #61afef; }");

    fileBrowser = new FileBrowser(leftTabs);
    gitWidget = new GitWidget(leftTabs);

    leftTabs->addTab(fileBrowser, "Files");
    leftTabs->addTab(gitWidget, "Git");
 
    fileDock->setWidget(leftTabs);
    addDockWidget(Qt::LeftDockWidgetArea, fileDock);
 
    connect(fileBrowser, &FileBrowser::fileOpened, this, [this](const QString& path) {
        openFileInTab(path);
    });
 
    connect(fileBrowser, &FileBrowser::rootChanged, this, [this](const QString& path) {
        if (pathLineEdit) pathLineEdit->setText(path);
        if (gitWidget) gitWidget->setRootPath(path);
        if (!path.isEmpty()) {
            VectorIndexManager::instance().startIndexing(path);
        }
        for (int i = 0; i < tabWidget->count(); ++i) {
            auto* sWidget = qobject_cast<SearchWidget*>(tabWidget->widget(i));
            if (sWidget) sWidget->setRootPath(path);
        }
    });
 
    // Initialize initial paths on startup
    QString initialPath = QDir::currentPath();
    if (pathLineEdit) pathLineEdit->setText(initialPath);
    if (gitWidget) gitWidget->setRootPath(initialPath);
    if (!initialPath.isEmpty()) {
        VectorIndexManager::instance().startIndexing(initialPath);
    }

    LspClient::instance().startServer(initialPath);

    connect(&LspClient::instance(), &LspClient::definitionReady, this, [this](int id, const QString& path, int line) {
        if (!path.isEmpty()) {
            gotoLine(path, line);
        }
    });

    connect(&LspClient::instance(), &LspClient::referencesReady, this, [this](int id, const QJsonArray& locations) {
        showSymbolReferences(locations);
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

    auto *editMenu = menuBar()->addMenu("&Edit");
    auto *findAction = editMenu->addAction("Find & Replace...", [this]() {
        if (!findReplaceDialog) {
            findReplaceDialog = new FindReplaceDialog(this);
        }
        findReplaceDialog->showReplace();
    });
    findAction->setShortcut(QKeySequence(Qt::CTRL | Qt::Key_F));

    auto *folderSearchAction = editMenu->addAction("Search in Folder...", [this]() {
        if (!findReplaceDialog) {
            findReplaceDialog = new FindReplaceDialog(this);
        }
        findReplaceDialog->showFolderSearch(QDir::currentPath());
    });
    folderSearchAction->setShortcut(QKeySequence(Qt::CTRL | Qt::SHIFT | Qt::Key_F));

    auto *buildMenu = menuBar()->addMenu("&Build");
    buildMenu->addAction("Build Project", QKeySequence(Qt::CTRL | Qt::Key_B), this, &EditorWindow::runBuild);

    auto *searchAction = menuBar()->addAction("Search Workspace", this, &EditorWindow::openSearchTab);
    searchAction->setShortcut(QKeySequence(Qt::CTRL | Qt::SHIFT | Qt::Key_F));

    auto *helpMenu = menuBar()->addMenu("&Help");
    helpMenu->addAction("About", [this]() {
        QMessageBox msgBox(this);
        msgBox.setWindowTitle("About AI-IDE");
        msgBox.setText("<h3>AI-IDE v1.0</h3><p>Next-generation C++ development powered by LLVM and Local AI.</p>");
        QPixmap logo(":/idelogo.png");
        if (!logo.isNull()) {
            msgBox.setIconPixmap(logo.scaled(64, 64, Qt::KeepAspectRatio, Qt::SmoothTransformation));
        }
        msgBox.exec();
    });

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
    activeDiagnostics.clear();

    // Clear diagnostics on all open editors
    for (int i = 0; i < tabWidget->count(); ++i) {
        if (auto* ed = qobject_cast<CustomEditor*>(tabWidget->widget(i))) {
            auto* codeEd = ed->findChild<CodeEditor*>();
            if (codeEd) codeEd->clearDiagnostics();
        }
    }

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

    QStringList args;
    args << "build.py";
    if (cmakeBuildTypeCombo) {
        args << "--build-type" << cmakeBuildTypeCombo->currentText();
    }
    if (cmakeTargetCombo) {
        QString tgt = cmakeTargetCombo->currentText();
        if (tgt != "ai-ide") {
            args << "--target" << tgt;
        }
    }
    buildProcess->start("python", args);
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

        // Cache diagnostics
        bool isError = severity.contains("error", Qt::CaseInsensitive);
        activeDiagnostics.push_back({file, lineNum, message, isError});
        updateDocumentDiagnostics();
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

void EditorWindow::updateDocumentDiagnostics() {
    for (int i = 0; i < tabWidget->count(); ++i) {
        if (auto* ed = qobject_cast<CustomEditor*>(tabWidget->widget(i))) {
            QString edPath = ed->currentFilePath();
            if (edPath.isEmpty()) continue;
            
            auto* codeEd = ed->findChild<CodeEditor*>();
            if (!codeEd) continue;
            
            std::vector<CodeEditor::Diagnostic> fileDiags;
            for (const auto& diag : activeDiagnostics) {
                if (QFileInfo(diag.file).absoluteFilePath() == QFileInfo(edPath).absoluteFilePath()) {
                    fileDiags.push_back({diag.line, diag.message, diag.isError});
                }
            }
            codeEd->setDiagnostics(fileDiags);
        }
    }
}

void EditorWindow::showSymbolReferences(const QJsonArray& locations) {
    if (!referencesTable) return;

    referencesTable->setRowCount(0);
    for (const auto& val : locations) {
        QJsonObject loc = val.toObject();
        QString uri = loc["uri"].toString();
        QString path = QUrl(uri).toLocalFile();
        int line = loc["range"].toObject()["start"].toObject()["line"].toInt() + 1;

        int row = referencesTable->rowCount();
        referencesTable->insertRow(row);

        auto* fileItem = new QTableWidgetItem(QFileInfo(path).fileName());
        fileItem->setToolTip(path);
        fileItem->setFlags(fileItem->flags() & ~Qt::ItemIsEditable);

        auto* lineItem = new QTableWidgetItem(QString::number(line));
        lineItem->setFlags(lineItem->flags() & ~Qt::ItemIsEditable);

        QString lineContent = "Code reference";
        QFile file(path);
        if (file.open(QIODevice::ReadOnly | QIODevice::Text)) {
            QTextStream in(&file);
            int currentLine = 0;
            while (!in.atEnd()) {
                currentLine++;
                QString content = in.readLine();
                if (currentLine == line) {
                    lineContent = content.trimmed();
                    break;
                }
            }
        }

        auto* codeItem = new QTableWidgetItem(lineContent);
        codeItem->setFlags(codeItem->flags() & ~Qt::ItemIsEditable);

        referencesTable->setItem(row, 0, fileItem);
        referencesTable->setItem(row, 1, lineItem);
        referencesTable->setItem(row, 2, codeItem);
    }

    if (bottomTabWidget) {
        int refIdx = bottomTabWidget->indexOf(referencesTable);
        if (refIdx != -1) {
            bottomTabWidget->setCurrentIndex(refIdx);
        }
    }
}

void EditorWindow::fixProblemWithAI(const QString& filePath, int line, const QString& message) {
    if (filePath.isEmpty() || !aiPatchController) return;

    QString codeContent;
    QFile file(filePath);
    if (file.open(QIODevice::ReadOnly | QIODevice::Text)) {
        codeContent = QTextStream(&file).readAll();
    }
    
    if (codeContent.isEmpty()) return;

    QString prompt = QString("Here is a compiler diagnostic on line %1: \"%2\"\n\n"
                             "Please review this code from the file \"%3\" and rewrite it to fix the compiler warning or error:\n\n"
                             "```cpp\n%4\n```")
                             .arg(line)
                             .arg(message)
                             .arg(QFileInfo(filePath).fileName())
                             .arg(codeContent);

    aiPatchController->setEditor(currentEditor());
    aiPatchController->requestRefactor(prompt);
}
