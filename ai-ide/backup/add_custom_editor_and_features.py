import os

ROOT = "ai-ide"

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# ---------------------------------------------------------
# Settings Manager (Singleton for App Configuration)
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/SettingsManager.hpp", r"""#pragma once
#include <string>
#include <QSettings>
#include <QString>

class SettingsManager {
public:
    static SettingsManager& instance() {
        static SettingsManager inst;
        return inst;
    }

    void setEndpoint(const std::string& ep) { 
        endpoint = ep; 
        QSettings s("Aide", "AI-IDE");
        s.setValue("endpoint", QString::fromStdString(ep));
    }
    std::string getEndpoint() const { return endpoint; }

    void setModel(const std::string& m) { 
        model = m; 
        QSettings s("Aide", "AI-IDE");
        s.setValue("model", QString::fromStdString(m));
    }
    std::string getModel() const { return model; }

    void setProviderType(const std::string& type) { 
        providerType = type; 
        QSettings s("Aide", "AI-IDE");
        s.setValue("providerType", QString::fromStdString(type));
    }
    std::string getProviderType() const { return providerType; }

private:
    SettingsManager() {
        QSettings s("Aide", "AI-IDE");
        endpoint = s.value("endpoint", "http://localhost:11434").toString().toStdString();
        model = s.value("model", "llama3").toString().toStdString();
        providerType = s.value("providerType", "Ollama").toString().toStdString();
    }

    std::string endpoint;
    std::string model;
    std::string providerType;
};
""")

# ---------------------------------------------------------
# Admin Dialog (UI for Settings and Model Management)
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/AdminDialog.hpp", r"""#pragma once
#include <QDialog>
#include <QLineEdit>
#include <QComboBox>

class AdminDialog : public QDialog {
    Q_OBJECT
public:
    explicit AdminDialog(QWidget* parent = nullptr);
private slots:
    void refreshModels();
    void saveSettings();
private:
    QLineEdit* endpointEdit;
    QComboBox* providerCombo;
    QComboBox* modelCombo;
};
""")

write(f"{ROOT}/src/ui/AdminDialog.cpp", r"""#include "AdminDialog.hpp"
#include "SettingsManager.hpp"
#include <QVBoxLayout>
#include <QFormLayout>
#include <QPushButton>
#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QUrl>
#include <QMessageBox>

AdminDialog::AdminDialog(QWidget* parent) : QDialog(parent) {
    setWindowTitle("AI Settings & Administration");
    setMinimumWidth(450);

    auto* layout = new QVBoxLayout(this);
    auto* form = new QFormLayout();

    providerCombo = new QComboBox(this);
    providerCombo->addItems({"Ollama", "Gemini", "Claude"});
    providerCombo->setCurrentText(QString::fromStdString(SettingsManager::instance().getProviderType()));

    endpointEdit = new QLineEdit(this);
    endpointEdit->setText(QString::fromStdString(SettingsManager::instance().getEndpoint()));

    modelCombo = new QComboBox(this);
    modelCombo->setEditable(true);
    modelCombo->setCurrentText(QString::fromStdString(SettingsManager::instance().getModel()));

    auto* refreshBtn = new QPushButton("Find Installed Models", this);
    connect(refreshBtn, &QPushButton::clicked, this, &AdminDialog::refreshModels);

    form->addRow("Provider:", providerCombo);
    form->addRow("AI IP/Endpoint:", endpointEdit);
    form->addRow("Current Model:", modelCombo);
    
    auto* btnLayout = new QHBoxLayout();
    btnLayout->addWidget(refreshBtn);
    form->addRow("Discovery:", btnLayout);

    layout->addLayout(form);
    
    auto* line = new QFrame();
    line->setFrameShape(QFrame::HLine);
    layout->addWidget(line);

    auto* saveBtn = new QPushButton("Save Changes", this);
    connect(saveBtn, &QPushButton::clicked, this, &AdminDialog::saveSettings);
    layout->addWidget(saveBtn, 0, Qt::AlignRight);
}

void AdminDialog::refreshModels() {
    QString url = endpointEdit->text() + "/api/tags";
    auto* manager = new QNetworkAccessManager(this);
    auto* reply = manager->get(QNetworkRequest(QUrl(url)));
    connect(reply, &QNetworkReply::finished, this, [this, reply]() {
        if (reply->error() == QNetworkReply::NoError) {
            modelCombo->clear();
            auto models = QJsonDocument::fromJson(reply->readAll()).object()["models"].toArray();
            for (const auto& m : models) modelCombo->addItem(m.toObject()["name"].toString());
        }
        reply->deleteLater();
    });
}

void AdminDialog::saveSettings() {
    auto& s = SettingsManager::instance();
    s.setEndpoint(endpointEdit->text().toStdString());
    s.setProviderType(providerCombo->currentText().toStdString());
    s.setModel(modelCombo->currentText().toStdString());
    accept();
}
""")

# ---------------------------------------------------------
# 0. File Browser and AI Chat Panel (Merged from qt_logic)
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/FileBrowser.hpp", r"""#pragma once
#include <QWidget>
#include <QFileSystemModel>
#include <QTreeView>

class FileBrowser : public QWidget {
    Q_OBJECT
public:
    explicit FileBrowser(QWidget* parent = nullptr);

    void setRootDirectory(const QString& path);

signals:
    void fileOpened(const QString& path);
private:
    QFileSystemModel* model;
    QTreeView* tree;
};
""")

write(f"{ROOT}/src/ui/FileBrowser.cpp", r"""#include "FileBrowser.hpp"
#include <QVBoxLayout>
#include <QFileInfo>
#include <QDir>
#include <QHeaderView>

FileBrowser::FileBrowser(QWidget* parent) : QWidget(parent) {
    auto* layout = new QVBoxLayout(this);
    model = new QFileSystemModel(this);
    
    tree = new QTreeView(this);
    tree->setModel(model);

    // Improve visibility: Hide metadata columns that crowd the sidebar
    tree->setColumnHidden(1, true); // Size
    tree->setColumnHidden(2, true); // Type
    tree->setColumnHidden(3, true); // Date Modified
    
    // Ensure the file name column takes up the available space
    tree->header()->setSectionResizeMode(0, QHeaderView::Stretch);

    setRootDirectory(QDir::currentPath());

    layout->addWidget(tree);
    connect(tree, &QTreeView::doubleClicked, this, [this](const QModelIndex& idx) {
        QString path = model->filePath(idx);
        if (QFileInfo(path).isFile()) emit fileOpened(path);
    });
}

void FileBrowser::setRootDirectory(const QString& path) {
    model->setRootPath(path);
    tree->setRootIndex(model->index(path));
}
""")

write(f"{ROOT}/src/ui/AIChatPanel.hpp", r"""#pragma once
#include <QWidget>
#include <QTextEdit>
#include <QPushButton>
#include <memory>
#include "SettingsManager.hpp"

class AIProvider;

class AIChatPanel : public QWidget {
    Q_OBJECT
public:
    explicit AIChatPanel(QWidget* parent = nullptr);

signals:
    void applyToEditor(const QString& code);
    void createNewFile(const QString& code);
    void promptArchived(const QString& summary);

private slots:
    void sendPrompt();
private:
    QTextEdit* chatHistory;
    QTextEdit* inputBox;
    QPushButton* sendButton;
    std::unique_ptr<AIProvider> provider;
    QString lastExtractedCode;
};
""")

write(f"{ROOT}/src/ui/AIChatPanel.cpp", r"""#include "AIChatPanel.hpp"
#include "../ai/GeminiProvider.hpp"
#include "../ai/OllamaProvider.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QRegularExpression>
#include <QFile>
#include <QTextStream>
#include <QDir>
#include <QMessageBox>
#include <QDateTime>

AIChatPanel::AIChatPanel(QWidget* parent) : QWidget(parent) {
    auto* layout = new QVBoxLayout(this);
    chatHistory = new QTextEdit(this);
    chatHistory->setReadOnly(true);
    chatHistory->setPlaceholderText("AI Chat History...");

    inputBox = new QTextEdit(this);
    inputBox->setFixedHeight(80);
    inputBox->setPlaceholderText("Type a message or instruction...");

    sendButton = new QPushButton("Send", this);
    
    auto& settings = SettingsManager::instance();
    if (settings.getProviderType() == "Gemini")
        provider = std::make_unique<GeminiProvider>(settings.getEndpoint());
    else
        provider = std::make_unique<OllamaProvider>(settings.getEndpoint());

    auto* actionLayout = new QHBoxLayout();
    auto* applyBtn = new QPushButton("Apply to Editor", this);
    auto* newPageBtn = new QPushButton("New Page", this);
    actionLayout->addWidget(applyBtn);
    actionLayout->addWidget(newPageBtn);

    layout->addWidget(chatHistory);
    layout->addWidget(inputBox);
    layout->addWidget(sendButton);
    layout->addLayout(actionLayout);

    connect(sendButton, &QPushButton::clicked, this, &AIChatPanel::sendPrompt);

    connect(applyBtn, &QPushButton::clicked, this, [this]() {
        if (!lastExtractedCode.isEmpty()) emit applyToEditor(lastExtractedCode);
        else QMessageBox::warning(this, "AI IDE", "No code detected in the AI's last response to apply.");
    });

    connect(newPageBtn, &QPushButton::clicked, this, [this]() {
        if (!lastExtractedCode.isEmpty()) emit createNewFile(lastExtractedCode);
        else QMessageBox::warning(this, "AI IDE", "No code detected in the AI's last response to create a page.");
    });
}

void AIChatPanel::sendPrompt() {
    QString prompt = inputBox->toPlainText().trimmed();
    if (prompt.isEmpty()) return;

    chatHistory->append("<b>You:</b> " + prompt);
    lastExtractedCode.clear();

    AIRequest req;
    req.prompt = prompt.toStdString();
    AIResponse res = provider->send(req);

    chatHistory->append("<b>AI:</b> " + QString::fromStdString(res.text));
    inputBox->clear();

    QString summary = QString("[%1] %2").arg(QDateTime::currentDateTime().toString("hh:mm")).arg(prompt.left(30) + "...");
    emit promptArchived(summary);

    // Extract code block from Markdown (Robust Regex)
    QRegularExpression codeRegex("(?s)```(?:[a-zA-Z0-9+#]+)?\\s*\\n?(.*?)(?:```|$)");
    QRegularExpressionMatch match = codeRegex.match(QString::fromStdString(res.text));
    if (match.hasMatch()) {
        lastExtractedCode = match.captured(1).trimmed();
        
        QString tempPath = QDir::tempPath() + "/ai_last_chat_code.txt";
        QFile tempFile(tempPath);
        if (tempFile.open(QIODevice::WriteOnly | QIODevice::Text)) {
            QTextStream out(&tempFile);
            out << lastExtractedCode;
            tempFile.close();
        }
    }
}
""")

# ---------------------------------------------------------
# 1. Custom editor widget
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/CustomEditor.hpp", r"""#pragma once
#include <QWidget>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QString>

class CustomEditor : public QWidget {
    Q_OBJECT
public:
    explicit CustomEditor(QWidget* parent = nullptr);

    void openFile(const QString& path);
    void saveFile();
    void saveAsFile();
    QString currentFilePath() const;

signals:
    void fileChanged(const QString& path);

private:
    QPlainTextEdit* editor;
    QPushButton* closeButton;
    QString filePath;
};
""")

write(f"{ROOT}/src/ui/CustomEditor.cpp", r"""#include "CustomEditor.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QPushButton>
#include <QFile>
#include <QTextStream>
#include <QFileDialog>
#include <QDir>

CustomEditor::CustomEditor(QWidget* parent)
    : QWidget(parent), closeButton(nullptr)
{
    auto* mainLayout = new QVBoxLayout(this);

    auto* buttonLayout = new QHBoxLayout();
    closeButton = new QPushButton("Close", this);
    buttonLayout->addWidget(closeButton);
    mainLayout->addLayout(buttonLayout);

    editor = new QPlainTextEdit(this);
    mainLayout->addWidget(editor);

    connect(closeButton, &QPushButton::clicked, this, [this]() {
        emit fileChanged("");
    });

    connect(editor, &QPlainTextEdit::textChanged, this, [this]() {
        if (!filePath.isEmpty()) {
            emit fileChanged(filePath);
        }
    });
}

void CustomEditor::openFile(const QString& path) {
    QFile f(path);
    if (!f.open(QIODevice::ReadOnly | QIODevice::Text)) {
        return;
    }
    QTextStream in(&f);
    editor->setPlainText(in.readAll());
    filePath = path;
}

void CustomEditor::saveFile() {
    if (filePath.isEmpty()) {
        saveAsFile();
        return;
    }
    QFile f(filePath);
    if (!f.open(QIODevice::WriteOnly | QIODevice::Text)) {
        return;
    }
    QTextStream out(&f);
    out << editor->toPlainText();
}

void CustomEditor::saveAsFile() {
    QString fileName = QFileDialog::getSaveFileName(
        this,
        "Save File",
        filePath.isEmpty() ? QDir::currentPath() : filePath,
        "Text Files (*.txt);;C++ Files (*.cpp *.hpp);;Header Files (*.h);;All Files (*.*)"
    );

    if (fileName.isEmpty()) return;

    filePath = fileName;
    QFile f(filePath);
    if (!f.open(QIODevice::WriteOnly | QIODevice::Text)) {
        return;
    }
    QTextStream out(&f);
    out << editor->toPlainText();
}

QString CustomEditor::currentFilePath() const {
    return filePath;
}
""")

# ---------------------------------------------------------
# 2. Diff viewer widget
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/DiffView.hpp", r"""#pragma once
#include <QWidget>
#include <QString>

class QPlainTextEdit;

class DiffView : public QWidget {
    Q_OBJECT
public:
    explicit DiffView(QWidget* parent = nullptr);

    void setTexts(const QString& original, const QString& modified);

private:
    QPlainTextEdit* leftView;
    QPlainTextEdit* rightView;
};
""")

write(f"{ROOT}/src/ui/DiffView.cpp", r"""#include "DiffView.hpp"
#include <QHBoxLayout>
#include <QPlainTextEdit>
#include <QStringList>

DiffView::DiffView(QWidget* parent)
    : QWidget(parent)
{
    auto* layout = new QHBoxLayout(this);
    leftView = new QPlainTextEdit(this);
    rightView = new QPlainTextEdit(this);

    leftView->setReadOnly(true);
    rightView->setReadOnly(true);
    
    // Set a monospace font for code clarity
    QFont monoFont("Consolas", 10);
    if (monoFont.fixedPitch()) {
        leftView->setFont(monoFont);
        rightView->setFont(monoFont);
    }

    layout->addWidget(leftView);
    layout->addWidget(rightView);
}

void DiffView::setTexts(const QString& original, const QString& modified) {
    leftView->clear();
    rightView->clear();

    QStringList leftLines = original.split('\n');
    QStringList rightLines = modified.split('\n');

    const int contextLines = 3;
    for (int i = 0; i < std::max(leftLines.size(), rightLines.size()); ++i) {
        bool isChanged = (i >= leftLines.size() || i >= rightLines.size() || leftLines[i] != rightLines[i]);
        bool nearChange = false;

        for (int j = i - contextLines; j <= i + contextLines; ++j) {
            if (j >= 0 && j < leftLines.size() && j < rightLines.size() && leftLines[j] != rightLines[j]) {
                nearChange = true; break;
            }
        }

        if (isChanged) {
            if (i < leftLines.size()) 
                leftView->appendHtml("<div style='background-color: #ffdce0;'>" + QString::number(i+1).rightJustified(4) + " | " + leftLines[i].toHtmlEscaped() + "</div>");
            if (i < rightLines.size())
                rightView->appendHtml("<div style='background-color: #e6ffed;'>" + QString::number(i+1).rightJustified(4) + " | " + rightLines[i].toHtmlEscaped() + "</div>");
        } else if (nearChange) {
            leftView->appendPlainText(QString::number(i+1).rightJustified(4) + " | " + leftLines[i]);
            rightView->appendPlainText(QString::number(i+1).rightJustified(4) + " | " + rightLines[i]);
        } else if (i > 0 && (i-1 < leftLines.size() && leftLines[i-1] != rightLines[i-1])) {
            leftView->appendPlainText(" --- [ Hunk Boundary ] --- ");
            rightView->appendPlainText(" --- [ Hunk Boundary ] --- ");
        }
    }
}
""")

# ---------------------------------------------------------
# 3. AI patch → diff → apply workflow (stub)
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/AIPatchController.hpp", r"""#pragma once
#include <QObject>
#include <QString>
#include "../ai/OllamaProvider.hpp"
#include "SettingsManager.hpp"
#include "CustomEditor.hpp"
#include "DiffView.hpp"

class AIPatchController : public QObject {
    Q_OBJECT
public:
    AIPatchController(CustomEditor* editor, DiffView* diffView, QObject* parent = nullptr);

public slots:
    void requestRefactor(const QString& instruction);

private:
    CustomEditor* editor;
    DiffView* diffView;
    std::unique_ptr<AIProvider> provider;
};
""")

write(f"{ROOT}/src/ui/AIPatchController.cpp", r"""#include "AIPatchController.hpp"
#include "../ai/GeminiProvider.hpp"
#include "../ai/OllamaProvider.hpp"
#include <QDialog>
#include <QVBoxLayout>
#include <QPushButton>
#include <QDialogButtonBox>
#include <QRegularExpression>
#include <QFile>
#include <QTextStream>
#include <QDir>

AIPatchController::AIPatchController(CustomEditor* ed, DiffView* dv, QObject* parent)
    : QObject(parent),
      editor(ed),
      diffView(dv)
{
    auto& settings = SettingsManager::instance();
    if (settings.getProviderType() == "Gemini")
        provider = std::make_unique<GeminiProvider>(settings.getEndpoint());
    else
        provider = std::make_unique<OllamaProvider>(settings.getEndpoint());
}

void AIPatchController::setEditor(CustomEditor* ed) {
    editor = ed;
}

void AIPatchController::requestRefactor(const QString& instruction) {
    if (!editor) return;
    QString code = editor->currentFilePath().isEmpty()
        ? QString()
        : editor->findChild<QPlainTextEdit*>()->toPlainText();

    AIRequest req;
    req.mode = "refactor";
    req.prompt = instruction.toStdString() + "\n\n" + code.toStdString();

    AIResponse res = provider->send(req);

    QString rawResponse = QString::fromStdString(res.text);
    QString newCode;

    // Extract the code block from the Markdown response
    QRegularExpression codeRegex("```(?:[a-zA-Z0-9+#]+)?\\n([\\s\\S]*?)```");
    QRegularExpressionMatch match = codeRegex.match(rawResponse);
    if (match.hasMatch()) {
        newCode = match.captured(1).trimmed();
    } else {
        newCode = rawResponse.trimmed();
    }

    // Persist the proposed code to a physical file
    QString tempPath = QDir::tempPath() + "/ai_proposed_patch.txt";
    QFile tempFile(tempPath);
    if (tempFile.open(QIODevice::WriteOnly | QIODevice::Text)) {
        QTextStream out(&tempFile);
        out << newCode;
        tempFile.close();
    }

    diffView->setTexts(code, newCode);

    QDialog dlg;
    dlg.setWindowTitle("AI Patch Preview");
    auto* layout = new QVBoxLayout(&dlg);
    layout->addWidget(diffView);

    auto* buttons = new QDialogButtonBox(QDialogButtonBox::Cancel | QDialogButtonBox::Ok, &dlg);
    layout->addWidget(buttons);

    QObject::connect(buttons, &QDialogButtonBox::accepted, &dlg, [&]() {
        auto* textEdit = editor->findChild<QPlainTextEdit*>();
        if (textEdit) {
            textEdit->setPlainText(newCode);
        }
        dlg.accept();
    });
    QObject::connect(buttons, &QDialogButtonBox::rejected, &dlg, [&]() {
        dlg.reject();
    });

    dlg.exec();
}
""")

# ---------------------------------------------------------
# 4. Git integration skeleton
# ---------------------------------------------------------
write(f"{ROOT}/src/git/GitClient.hpp", r"""#pragma once
#include <string>
#include <vector>

struct GitStatusEntry {
    std::string path;
    std::string status;
};

class GitClient {
public:
    explicit GitClient(const std::string& repoPath);

    std::vector<GitStatusEntry> status();
    void commit(const std::string& message);
    void add(const std::string& path);
    void push();

private:
    std::string repoPath;
};
""")

write(f"{ROOT}/src/git/GitClient.cpp", r"""#include "GitClient.hpp"
#include <iostream>

GitClient::GitClient(const std::string& path)
    : repoPath(path)
{
}

std::vector<GitStatusEntry> GitClient::status() {
    std::cout << "[Git] status in " << repoPath << std::endl;
    return {};
}

void GitClient::add(const std::string& path) {
    std::cout << "[Git] add " << path << std::endl;
}

void GitClient::commit(const std::string& message) {
    std::cout << "[Git] commit: " << message << std::endl;
}

void GitClient::push() {
    std::cout << "[Git] push from " << repoPath << std::endl;
}
""")

# ---------------------------------------------------------
# 5. Wire file browser → editor in EditorWindow
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/ClipboardListener.hpp", r"""#pragma once
#include <QObject>
#include <QClipboard>
#include <QMimeData>

class ClipboardListener : public QObject {
    Q_OBJECT
public:
    explicit ClipboardListener(QObject* parent = nullptr);

signals:
    void codeCopied(const QString& text);

private slots:
    void onClipboardChanged();
};
""")

write(f"{ROOT}/src/ui/ClipboardListener.cpp", r"""#include "ClipboardListener.hpp"
#include <QApplication>

ClipboardListener::ClipboardListener(QObject* parent) : QObject(parent) {
    connect(QApplication::clipboard(), &QClipboard::dataChanged, this, &ClipboardListener::onClipboardChanged);
}

void ClipboardListener::onClipboardChanged() {
    const QMimeData* mimeData = QApplication::clipboard()->mimeData();
    if (mimeData->hasText()) {
        QString text = mimeData->text();
        if (text.length() > 5) { // Basic heuristic to ignore tiny snippets
            emit codeCopied(text);
        }
    }
}
""")

write(f"{ROOT}/src/ui/EditorWindow.hpp", r"""#pragma once

#include <QMainWindow>

class CustomEditor;
class FileBrowser;
class DiffView;
class AIPatchController;
class ClipboardListener;
class QShowEvent; // Added for showEvent override

class EditorWindow : public QMainWindow {
    Q_OBJECT
public:
    explicit EditorWindow(QWidget *parent = nullptr);

private:
    void createMenus();
    void createDocks();
    void createCentralEditor();

    void showEvent(QShowEvent* event) override; // Declare showEvent override

    CustomEditor* editor;
    FileBrowser* fileBrowser;
    DiffView* diffView;
    AIPatchController* aiPatchController;
    ClipboardListener* clipboardListener;
};
""")

write(f"{ROOT}/src/ui/EditorWindow.cpp", r"""#include "EditorWindow.hpp"
#include "FileBrowser.hpp"
#include "AIChatPanel.hpp"
#include "CustomEditor.hpp"
#include "DiffView.hpp"
#include "AIPatchController.hpp"
#include "AdminDialog.hpp"
#include "ClipboardListener.hpp"

#include <QMenuBar>
#include <QDockWidget>
#include <QListView>
#include <QAction>
#include <QInputDialog>
#include <QFileDialog>
#include <QShowEvent> // Added for showEvent override
#include <QTimer>
#include <QStatusBar>
#include <QStringListModel>

EditorWindow::EditorWindow(QWidget *parent)
    : QMainWindow(parent),
      tabWidget(nullptr),
      fileBrowser(nullptr),
      diffView(nullptr),
      aiPatchController(nullptr),
      clipboardListener(nullptr),
      historyModel(new QStringListModel(this))
{
    setWindowTitle("AI-IDE");

    createCentralEditor();
    createDocks();
    createMenus();
    
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
    setCentralWidget(tabWidget);

    connect(tabWidget, &QTabWidget::tabCloseRequested, this, [this](int index) {
        tabWidget->removeTab(index);
    });
}

void EditorWindow::openFileInTab(const QString& path) {
    auto* newEditor = new CustomEditor(this);
    if (!path.isEmpty()) newEditor->openFile(path);
    
    QString title = path.isEmpty() ? "Untitled" : QFileInfo(path).fileName();
    int idx = tabWidget->addTab(newEditor, title);
    tabWidget->setCurrentIndex(idx);
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

    // Diff View (Right, tabbed with AI History)
    auto* diffDock = new QDockWidget("Diff", this);
    diffView = new DiffView(diffDock);
    diffDock->setWidget(diffView);
    addDockWidget(Qt::RightDockWidgetArea, diffDock);

    // AI History placeholder
    auto* historyDock = new QDockWidget("AI History", this);
    auto* historyView = new QListView(historyDock);
    historyView->setModel(historyModel);
    historyDock->setWidget(historyView);
    tabifyDockWidget(diffDock, historyDock);

    aiPatchController = new AIPatchController(nullptr, diffView, this);
}

CustomEditor* EditorWindow::currentEditor() const {
    return qobject_cast<CustomEditor*>(tabWidget->currentWidget());
}

void EditorWindow::createMenus() {
    auto *fileMenu = menuBar()->addMenu("&File");
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

    auto *helpMenu = menuBar()->addMenu("&Help");
    helpMenu->addAction("About");
}
""")

# ---------------------------------------------------------
# 6. Ensure CMake uses Qt and new files
# ---------------------------------------------------------
write(f"{ROOT}/src/main.cpp", r"""#include <QApplication>
#include "ui/EditorWindow.hpp"

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);
    EditorWindow w;
    w.show();
    return app.exec();
}
""")

write(f"{ROOT}/CMakeLists.txt", r"""cmake_minimum_required(VERSION 3.16)
project(AIIDE VERSION 1.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

add_subdirectory(src)
""")

write(f"{ROOT}/src/CMakeLists.txt", r"""cmake_minimum_required(VERSION 3.16)

file(GLOB_RECURSE SOURCES CONFIGURE_DEPENDS *.cpp *.hpp)

find_package(Qt6 REQUIRED COMPONENTS Widgets Network)

add_executable(ai-ide ${SOURCES})
target_link_libraries(ai-ide PRIVATE Qt6::Widgets Qt6::Network)

# Helps IntelliSense find headers in subdirectories like ui/ or ai/
target_include_directories(ai-ide PRIVATE 
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_compile_definitions(ai-ide PRIVATE
    QT_DEPRECATED_WARNINGS
)
""")

print("Custom editor, file browser wiring, diff view, AI patch workflow, and Git skeleton added successfully!")
