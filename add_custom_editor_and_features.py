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
    void rootChanged(const QString& path);
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
    emit rootChanged(path);
}
""")

write(f"{ROOT}/src/ui/AIChatPanel.hpp", r"""#pragma once
#include <QWidget>
#include <QTextEdit>
#include <QPushButton>
#include <memory>
#include "SettingsManager.hpp"
#include "../ai/AIProvider.hpp"

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
# C++ Syntax Highlighter
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/CppHighlighter.hpp", r"""#pragma once
#include <QSyntaxHighlighter>
#include <QTextCharFormat>
#include <QRegularExpression>
#include <vector>

class CppHighlighter : public QSyntaxHighlighter {
    Q_OBJECT
public:
    explicit CppHighlighter(QTextDocument* parent = nullptr);

protected:
    void highlightBlock(const QString& text) override;

private:
    struct HighlightingRule {
        QRegularExpression pattern;
        QTextCharFormat format;
    };
    std::vector<HighlightingRule> highlightingRules;

    QTextCharFormat keywordFormat;
    QTextCharFormat classFormat;
    QTextCharFormat singleLineCommentFormat;
    QTextCharFormat multiLineCommentFormat;
    QTextCharFormat quotationFormat;
    QTextCharFormat functionFormat;
    QTextCharFormat preprocessorFormat;
    QTextCharFormat numberFormat;
    
    QRegularExpression commentStartExpression;
    QRegularExpression commentEndExpression;
};
""")

write(f"{ROOT}/src/ui/CppHighlighter.cpp", r"""#include "CppHighlighter.hpp"
#include <QColor>
#include <QFont>
#include <QStringList>

CppHighlighter::CppHighlighter(QTextDocument* parent)
    : QSyntaxHighlighter(parent)
{
    HighlightingRule rule;

    // Keywords (Purple-ish theme matching modern dark UI)
    keywordFormat.setForeground(QColor(198, 120, 221));
    keywordFormat.setFontWeight(QFont::Bold);
    QStringList keywordPatterns;
    keywordPatterns << "\\bchar\\b" << "\\bclass\\b" << "\\bconst\\b"
                    << "\\bdouble\\b" << "\\benum\\b" << "\\bexplicit\\b"
                    << "\\bfloat\\b" << "\\bint\\b" << "\\blong\\b"
                    << "\\boperator\\b" << "\\bprivate\\b" << "\\bprotected\\b"
                    << "\\bpublic\\b" << "\\bshort\\b" << "\\bsignals\\b"
                    << "\\bsigned\\b" << "\\bslots\\b" << "\\bstatic\\b"
                    << "\\bstruct\\b" << "\\btemplate\\b" << "\\btypedef\\b"
                    << "\\btypename\\b" << "\\bunion\\b" << "\\bunsigned\\b"
                    << "\\bvirtual\\b" << "\\bvoid\\b" << "\\bvolatile\\b"
                    << "\\bbool\\b" << "\\bif\\b" << "\\belse\\b"
                    << "\\bfor\\b" << "\\bwhile\\b" << "\\bdo\\b"
                    << "\\breturn\\b" << "\\bswitch\\b" << "\\bcase\\b"
                    << "\\bbreak\\b" << "\\bcontinue\\b" << "\\bdefault\\b"
                    << "\\bnew\\b" << "\\bdelete\\b" << "\\btry\\b"
                    << "\\bcatch\\b" << "\\bthrow\\b" << "\\bnamespace\\b"
                    << "\\busing\\b" << "\\bconstexpr\\b" << "\\bnullptr\\b";
    for (const QString& pattern : keywordPatterns) {
        rule.pattern = QRegularExpression(pattern);
        rule.format = keywordFormat;
        highlightingRules.push_back(rule);
    }

    // Classes / Types (Yellow)
    classFormat.setForeground(QColor(229, 192, 123));
    classFormat.setFontWeight(QFont::Bold);
    rule.pattern = QRegularExpression("\\b[A-Z][a-zA-Z0-9_]*\\b");
    rule.format = classFormat;
    highlightingRules.push_back(rule);

    // Preprocessor directives (Red)
    preprocessorFormat.setForeground(QColor(224, 108, 117));
    rule.pattern = QRegularExpression("^\\s*#\\s*[a-zA-Z]+");
    rule.format = preprocessorFormat;
    highlightingRules.push_back(rule);

    // Functions (Blue)
    functionFormat.setForeground(QColor(97, 175, 239));
    rule.pattern = QRegularExpression("\\b[A-Za-z0-9_]+(?=\\s*\\()");
    rule.format = functionFormat;
    highlightingRules.push_back(rule);

    // Strings (Green)
    quotationFormat.setForeground(QColor(152, 195, 121));
    rule.pattern = QRegularExpression("\".*?\"");
    rule.format = quotationFormat;
    highlightingRules.push_back(rule);

    // Numbers (Orange)
    numberFormat.setForeground(QColor(209, 154, 102));
    rule.pattern = QRegularExpression("\\b\\d+(\\.\\d+)?\\b");
    rule.format = numberFormat;
    highlightingRules.push_back(rule);

    // Single line comments (Gray)
    singleLineCommentFormat.setForeground(QColor(92, 99, 112));
    singleLineCommentFormat.setFontItalic(true);
    rule.pattern = QRegularExpression("//[^\n]*");
    rule.format = singleLineCommentFormat;
    highlightingRules.push_back(rule);

    // Multi-line comments
    multiLineCommentFormat.setForeground(QColor(92, 99, 112));
    multiLineCommentFormat.setFontItalic(true);
    commentStartExpression = QRegularExpression(R"(\/\*)");
    commentEndExpression = QRegularExpression(R"(\*\/)");
}

void CppHighlighter::highlightBlock(const QString& text) {
    for (const auto& rule : highlightingRules) {
        QRegularExpressionMatchIterator matchIterator = rule.pattern.globalMatch(text);
        while (matchIterator.hasNext()) {
            QRegularExpressionMatch match = matchIterator.next();
            setFormat(match.capturedStart(), match.capturedLength(), rule.format);
        }
    }

    setCurrentBlockState(0);

    int startIndex = 0;
    if (previousBlockState() != 1) {
        QRegularExpressionMatch startMatch = commentStartExpression.match(text);
        if (startMatch.hasMatch()) {
            startIndex = startMatch.capturedStart();
        } else {
            startIndex = -1;
        }
    }

    while (startIndex >= 0) {
        QRegularExpressionMatch endMatch = commentEndExpression.match(text, startIndex);
        int commentLength;
        if (!endMatch.hasMatch()) {
            setCurrentBlockState(1);
            commentLength = text.length() - startIndex;
        } else {
            commentLength = endMatch.capturedStart() - startIndex + endMatch.capturedLength();
        }
        setFormat(startIndex, commentLength, multiLineCommentFormat);
        
        if (currentBlockState() == 1) {
            break;
        }
        
        QRegularExpressionMatch nextStartMatch = commentStartExpression.match(text, startIndex + commentLength);
        if (nextStartMatch.hasMatch()) {
            startIndex = nextStartMatch.capturedStart();
        } else {
            startIndex = -1;
        }
    }
}
""")

# ---------------------------------------------------------
# Command Palette (Fuzzy command search)
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/CommandPalette.hpp", r"""#pragma once
#include <QWidget>
#include <QListWidget>
#include <vector>
#include <functional>

class CommandPalette : public QWidget {
    Q_OBJECT
public:
    explicit CommandPalette(QWidget* parent = nullptr);

    void addCommand(const QString& name, const QString& shortcut, const std::function<void()>& action);
    void filterCommands(const QString& text);
    void selectNext();
    void selectPrev();
    void executeCurrent();

private:
    struct PaletteCommand {
        QString name;
        QString shortcut;
        std::function<void()> action;
    };
    std::vector<PaletteCommand> commands;
    QListWidget* listWidget;
};
""")

write(f"{ROOT}/src/ui/CommandPalette.cpp", r"""#include "CommandPalette.hpp"
#include <QVBoxLayout>
#include <QVariant>

CommandPalette::CommandPalette(QWidget* parent)
    : QWidget(parent, Qt::FramelessWindowHint | Qt::Popup)
{
    setAttribute(Qt::WA_ShowWithoutActivating);
    setFocusPolicy(Qt::NoFocus);
    
    setMinimumWidth(550);
    setMaximumHeight(250);
    setStyleSheet("QWidget { background-color: #21252b; border: 1px solid #3e4452; border-radius: 8px; }"
                  "QListWidget { background-color: #21252b; color: #abb2bf; border: none; font-size: 13px; font-family: 'Segoe UI', Arial; }"
                  "QListWidget::item { padding: 10px; border-bottom: 1px solid #2c313c; border-radius: 4px; }"
                  "QListWidget::item:selected { background-color: #3e4452; color: #ffffff; }");

    auto* layout = new QVBoxLayout(this);
    layout->setContentsMargins(2, 2, 2, 2);
    listWidget = new QListWidget(this);
    listWidget->setFocusPolicy(Qt::NoFocus);
    layout->addWidget(listWidget);
}

void CommandPalette::addCommand(const QString& name, const QString& shortcut, const std::function<void()>& action) {
    commands.push_back({name, shortcut, action});
}

void CommandPalette::filterCommands(const QString& text) {
    listWidget->clear();
    for (size_t i = 0; i < commands.size(); ++i) {
        if (text.isEmpty() || commands[i].name.contains(text, Qt::CaseInsensitive)) {
            auto* item = new QListWidgetItem(listWidget);
            QString label = commands[i].name;
            if (!commands[i].shortcut.isEmpty()) {
                label += "   (" + commands[i].shortcut + ")";
            }
            item->setText(label);
            item->setData(Qt::UserRole, QVariant::fromValue(static_cast<int>(i)));
        }
    }
    if (listWidget->count() > 0) {
        listWidget->setCurrentRow(0);
    }
}

void CommandPalette::selectNext() {
    int row = listWidget->currentRow();
    if (row < listWidget->count() - 1) {
        listWidget->setCurrentRow(row + 1);
    }
}

void CommandPalette::selectPrev() {
    int row = listWidget->currentRow();
    if (row > 0) {
        listWidget->setCurrentRow(row - 1);
    }
}

void CommandPalette::executeCurrent() {
    auto* item = listWidget->currentItem();
    if (item) {
        int idx = item->data(Qt::UserRole).toInt();
        if (idx >= 0 && idx < static_cast<int>(commands.size())) {
            commands[idx].action();
        }
    }
    hide();
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

class CodeEditor;
class CppHighlighter;

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
    void closeRequested();

private:
    CodeEditor* editor;
    QPushButton* closeButton;
    QPushButton* saveAsButton;
    QString filePath;
    CppHighlighter* highlighter;
};

class CodeEditor : public QPlainTextEdit {
    Q_OBJECT
public:
    explicit CodeEditor(QWidget* parent = nullptr);

    void lineNumberAreaPaintEvent(QPaintEvent* event);
    int lineNumberAreaWidth();

protected:
    void resizeEvent(QResizeEvent* event) override;

private slots:
    void updateLineNumberAreaWidth(int newBlockCount);
    void highlightCurrentLine();
    void updateLineNumberArea(const QRect& rect, int dy);

private:
    QWidget* lineNumberArea;
};

class LineNumberArea : public QWidget {
public:
    explicit LineNumberArea(CodeEditor* editor) : QWidget(editor), codeEditor(editor) {}

    QSize sizeHint() const override {
        return QSize(codeEditor->lineNumberAreaWidth(), 0);
    }

protected:
    void paintEvent(QPaintEvent* event) override {
        codeEditor->lineNumberAreaPaintEvent(event);
    }

private:
    CodeEditor* codeEditor;
};
""")

write(f"{ROOT}/src/ui/CustomEditor.cpp", r"""#include "CustomEditor.hpp"
#include "CppHighlighter.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QPushButton>
#include <QFile>
#include <QTextStream>
#include <QFileDialog>
#include <QDir>
#include <QPainter>
#include <QPaintEvent>
#include <QTextBlock>

CustomEditor::CustomEditor(QWidget* parent)
    : QWidget(parent), closeButton(nullptr), saveAsButton(nullptr), highlighter(nullptr)
{
    auto* mainLayout = new QVBoxLayout(this);

    editor = new CodeEditor(this);
    mainLayout->addWidget(editor);

    highlighter = new CppHighlighter(editor->document());

    auto* buttonLayout = new QHBoxLayout();
    buttonLayout->addStretch();
    
    saveAsButton = new QPushButton("Save As", this);
    closeButton = new QPushButton("Close", this);
    
    buttonLayout->addWidget(saveAsButton);
    buttonLayout->addWidget(closeButton);
    mainLayout->addLayout(buttonLayout);

    connect(closeButton, &QPushButton::clicked, this, &CustomEditor::closeRequested);
    connect(saveAsButton, &QPushButton::clicked, this, &CustomEditor::saveAsFile);

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

// ---------------------------------------------------------
// CodeEditor Implementation
// ---------------------------------------------------------
CodeEditor::CodeEditor(QWidget* parent) : QPlainTextEdit(parent) {
    lineNumberArea = new LineNumberArea(this);

    connect(this, &CodeEditor::blockCountChanged, this, &CodeEditor::updateLineNumberAreaWidth);
    connect(this, &CodeEditor::updateRequest, this, &CodeEditor::updateLineNumberArea);
    connect(this, &CodeEditor::cursorPositionChanged, this, &CodeEditor::highlightCurrentLine);

    updateLineNumberAreaWidth(0);
    highlightCurrentLine();
    
    setStyleSheet("QPlainTextEdit { background-color: #1e1e1e; color: #abb2bf; font-family: 'Consolas', monospace; font-size: 11pt; border: none; }");
}

int CodeEditor::lineNumberAreaWidth() {
    int digits = 1;
    int max = std::max(1, blockCount());
    while (max >= 10) {
        max /= 10;
        digits++;
    }
    int space = 15 + fontMetrics().horizontalAdvance(QLatin1Char('9')) * digits;
    return space;
}

void CodeEditor::updateLineNumberAreaWidth(int /* newBlockCount */) {
    setViewportMargins(lineNumberAreaWidth(), 0, 0, 0);
}

void CodeEditor::updateLineNumberArea(const QRect& rect, int dy) {
    if (dy) {
        lineNumberArea->scroll(0, dy);
    } else {
        lineNumberArea->update(0, rect.y(), lineNumberArea->width(), rect.height());
    }

    if (rect.contains(viewport()->rect())) {
        updateLineNumberAreaWidth(0);
    }
}

void CodeEditor::resizeEvent(QResizeEvent* event) {
    QPlainTextEdit::resizeEvent(event);

    QRect cr = contentsRect();
    lineNumberArea->setGeometry(QRect(cr.left(), cr.top(), lineNumberAreaWidth(), cr.height()));
}

void CodeEditor::highlightCurrentLine() {
    QList<QTextEdit::ExtraSelection> extraSelections;

    if (!isReadOnly()) {
        QTextEdit::ExtraSelection selection;
        QColor lineColor = QColor(Qt::gray).darker(300);
        selection.format.setBackground(lineColor);
        selection.format.setProperty(QTextFormat::FullWidthSelection, true);
        selection.cursor = textCursor();
        selection.cursor.clearSelection();
        extraSelections.append(selection);
    }

    setExtraSelections(extraSelections);
}

void CodeEditor::lineNumberAreaPaintEvent(QPaintEvent* event) {
    QPainter painter(lineNumberArea);
    painter.fillRect(event->rect(), QColor(33, 37, 43));

    QTextBlock block = firstVisibleBlock();
    int blockNumber = block.blockNumber();
    int top = qRound(blockBoundingGeometry(block).translated(contentOffset()).y());
    int bottom = top + qRound(blockBoundingRect(block).height());

    while (block.isValid() && top <= event->rect().bottom()) {
        if (block.isVisible() && bottom >= event->rect().top()) {
            QString number = QString::number(blockNumber + 1);
            painter.setPen(QColor(92, 99, 112));
            painter.drawText(0, top, lineNumberArea->width() - 5, fontMetrics().height(),
                             Qt::AlignRight | Qt::AlignVCenter, number);
        }

        block = block.next();
        top = bottom;
        bottom = top + qRound(blockBoundingRect(block).height());
        blockNumber++;
    }
}
""")

# ---------------------------------------------------------
# Terminal Widget for Shells
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/TerminalWidget.hpp", r"""#pragma once
#include <QWidget>
#include <QPlainTextEdit>
#include <QProcess>

class TerminalWidget : public QWidget {
    Q_OBJECT
public:
    explicit TerminalWidget(const QString& shellPath, QWidget* parent = nullptr);
    ~TerminalWidget() override;

protected:
    bool eventFilter(QObject* obj, QEvent* event) override;

private slots:
    void readOutput();

private:
    QPlainTextEdit* terminalEdit;
    QProcess* process;
};
""")

write(f"{ROOT}/src/ui/TerminalWidget.cpp", r"""#include "TerminalWidget.hpp"
#include <QVBoxLayout>
#include <QKeyEvent>
#include <QRegularExpression>
#include <QTextCursor>

TerminalWidget::TerminalWidget(const QString& shellPath, QWidget* parent)
    : QWidget(parent)
{
    auto* layout = new QVBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);

    terminalEdit = new QPlainTextEdit(this);
    
    // Monospace Font
    QFont monoFont("Consolas", 10);
    if (monoFont.fixedPitch()) {
        terminalEdit->setFont(monoFont);
    }
    
    // Visual terminal styling (dark theme)
    terminalEdit->setStyleSheet("QPlainTextEdit { background-color: #1e1e1e; color: #d4d4d4; }");

    layout->addWidget(terminalEdit);

    process = new QProcess(this);
    process->setProcessChannelMode(QProcess::MergedChannels);

    connect(process, &QProcess::readyReadStandardOutput, this, &TerminalWidget::readOutput);

    // Install event filter to capture keyboard input
    terminalEdit->installEventFilter(this);

    // Start shell process
    QStringList args;
    if (shellPath.contains("bash.exe")) {
        args << "--login" << "-i";
    }
    process->start(shellPath, args);
}

TerminalWidget::~TerminalWidget() {
    if (process) {
        process->terminate();
        process->waitForFinished(1000);
    }
}

bool TerminalWidget::eventFilter(QObject* obj, QEvent* event) {
    if (obj == terminalEdit && event->type() == QEvent::KeyPress) {
        auto* keyEvent = static_cast<QKeyEvent*>(event);
        QString txt = keyEvent->text();
        
        // Handle Ctrl combinations
        if (keyEvent->modifiers() & Qt::ControlModifier) {
            if (keyEvent->key() == Qt::Key_C) {
                process->write("\x03");
                return true;
            } else if (keyEvent->key() == Qt::Key_Z) {
                process->write("\x1A");
                return true;
            } else if (keyEvent->key() == Qt::Key_D) {
                process->write("\x04");
                return true;
            }
            // Allow other Ctrl shortcuts to propagate (e.g. Ctrl+B, Ctrl+S)
            return false;
        }

        // Handle special control sequences
        if (keyEvent->key() == Qt::Key_Return || keyEvent->key() == Qt::Key_Enter) {
            process->write("\r\n");
            return true;
        } else if (keyEvent->key() == Qt::Key_Backspace) {
            process->write("\b");
            return true;
        } else if (keyEvent->key() == Qt::Key_Tab) {
            process->write("\t");
            return true;
        } else if (keyEvent->key() == Qt::Key_Escape) {
            process->write("\x1B");
            return true;
        } else if (keyEvent->key() == Qt::Key_Up) {
            process->write("\x1B[A");
            return true;
        } else if (keyEvent->key() == Qt::Key_Down) {
            process->write("\x1B[B");
            return true;
        } else if (keyEvent->key() == Qt::Key_Right) {
            process->write("\x1B[C");
            return true;
        } else if (keyEvent->key() == Qt::Key_Left) {
            process->write("\x1B[D");
            return true;
        }

        if (!txt.isEmpty()) {
            process->write(txt.toLocal8Bit());
            return true;
        }
    }
    return QWidget::eventFilter(obj, event);
}

void TerminalWidget::readOutput() {
    if (!process || !terminalEdit) return;
    QByteArray data = process->readAllStandardOutput();
    if (data.isEmpty()) return;

    QString text = QString::fromLocal8Bit(data);
    static QRegularExpression ansiRegex("\x1B\\[[0-9;]*[a-zA-Z]");
    text.remove(ansiRegex);

    QString buffer;
    for (int i = 0; i < text.length(); ++i) {
        if (text[i] == '\b') {
            if (!buffer.isEmpty()) {
                terminalEdit->moveCursor(QTextCursor::End);
                terminalEdit->insertPlainText(buffer);
                buffer.clear();
            }
            QTextCursor cursor = terminalEdit->textCursor();
            cursor.movePosition(QTextCursor::End);
            cursor.deletePreviousChar();
        } else {
            buffer.append(text[i]);
        }
    }
    if (!buffer.isEmpty()) {
        terminalEdit->moveCursor(QTextCursor::End);
        terminalEdit->insertPlainText(buffer);
    }
    terminalEdit->moveCursor(QTextCursor::End);
}
""")

# ---------------------------------------------------------
# Problems Widget
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/ProblemsWidget.hpp", r"""#pragma once
#include <QWidget>
#include <QString>

class QTableWidget;

class ProblemsWidget : public QWidget {
    Q_OBJECT
public:
    explicit ProblemsWidget(QWidget* parent = nullptr);
    void addProblem(const QString& severity, const QString& file, int line, int col, const QString& message);
    void clearProblems();

signals:
    void problemActivated(const QString& file, int line);

private:
    QTableWidget* table;
};
""")

write(f"{ROOT}/src/ui/ProblemsWidget.cpp", r"""#include "ProblemsWidget.hpp"
#include <QVBoxLayout>
#include <QTableWidget>
#include <QHeaderView>
#include <QTableWidgetItem>

ProblemsWidget::ProblemsWidget(QWidget* parent)
    : QWidget(parent)
{
    auto* layout = new QVBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);

    table = new QTableWidget(0, 4, this);
    table->setHorizontalHeaderLabels({"Severity", "File", "Line", "Message"});
    table->horizontalHeader()->setSectionResizeMode(3, QHeaderView::Stretch);
    table->horizontalHeader()->setSectionResizeMode(1, QHeaderView::ResizeToContents);
    table->setEditTriggers(QAbstractItemView::NoEditTriggers);
    table->setSelectionBehavior(QAbstractItemView::SelectRows);
    table->setAlternatingRowColors(true);
    table->verticalHeader()->setVisible(false);

    layout->addWidget(table);

    connect(table, &QTableWidget::itemDoubleClicked, this, [this](QTableWidgetItem* item) {
        int row = item->row();
        QString file = table->item(row, 1)->text();
        int line = table->item(row, 2)->text().toInt();
        emit problemActivated(file, line);
    });
}

void ProblemsWidget::clearProblems() {
    table->setRowCount(0);
}

void ProblemsWidget::addProblem(const QString& severity, const QString& file, int line, int col, const QString& message) {
    int row = table->rowCount();
    table->insertRow(row);

    auto* sevItem = new QTableWidgetItem(severity);
    if (severity.toLower() == "error") {
        sevItem->setForeground(QColor(220, 60, 60));
    } else if (severity.toLower() == "warning") {
        sevItem->setForeground(QColor(220, 160, 40));
    } else {
        sevItem->setForeground(QColor(100, 160, 240));
    }
    table->setItem(row, 0, sevItem);
    table->setItem(row, 1, new QTableWidgetItem(file));
    table->setItem(row, 2, new QTableWidgetItem(QString::number(line)));
    table->setItem(row, 3, new QTableWidgetItem(message));
    
    (void)col; // stored in item data if needed later
}
""")

# ---------------------------------------------------------
# Debug Widget (GDB/LLDB Wrapper Skeleton)
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/DebugWidget.hpp", r"""#pragma once
#include <QWidget>
#include <QProcess>
#include <QString>

class QPushButton;
class QPlainTextEdit;
class QTreeWidget;
class QLineEdit;
class QLabel;

class DebugWidget : public QWidget {
    Q_OBJECT
public:
    explicit DebugWidget(QWidget* parent = nullptr);
    ~DebugWidget() override;

private slots:
    void startDebugging();
    void stopDebugging();
    void stepOver();
    void stepInto();
    void continueDebug();
    void sendManualCommand();
    void readGdbOutput();
    void gdbFinished(int exitCode);

private:
    void sendGdbCommand(const QString& cmd);
    void updateVariables();
    void addVariable(const QString& name, const QString& type, const QString& val);
    
    // Simulation mode helpers
    void enterSimulationMode();
    void runSimulationStep();

    QProcess* gdbProcess;
    bool isSimulated;
    int simStepCount;

    QPushButton* startBtn;
    QPushButton* stopBtn;
    QPushButton* stepOverBtn;
    QPushButton* stepIntoBtn;
    QPushButton* continueBtn;
    QLabel* statusLabel;
    
    QPlainTextEdit* consoleLog;
    QLineEdit* cmdInput;
    QTreeWidget* variablesTree;
};
""")

write(f"{ROOT}/src/ui/DebugWidget.cpp", r"""#include "DebugWidget.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QSplitter>
#include <QTreeWidget>
#include <QTreeWidgetItem>
#include <QHeaderView>
#include <QPushButton>
#include <QLineEdit>
#include <QLabel>
#include <QPlainTextEdit>
#include <QDir>
#include <QFile>
#include <QRegularExpression>
#include <QDateTime>

DebugWidget::DebugWidget(QWidget* parent)
    : QWidget(parent),
      gdbProcess(nullptr),
      isSimulated(false),
      simStepCount(0)
{
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);

    // 1. Toolbar at the top
    auto* toolbar = new QHBoxLayout();
    startBtn = new QPushButton("Start Debugging", this);
    stopBtn = new QPushButton("Stop", this);
    stepOverBtn = new QPushButton("Step Over", this);
    stepIntoBtn = new QPushButton("Step Into", this);
    continueBtn = new QPushButton("Continue", this);
    statusLabel = new QLabel("Status: Idle", this);
    statusLabel->setStyleSheet("font-weight: bold; margin-left: 10px;");

    stopBtn->setEnabled(false);
    stepOverBtn->setEnabled(false);
    stepIntoBtn->setEnabled(false);
    continueBtn->setEnabled(false);

    toolbar->addWidget(startBtn);
    toolbar->addWidget(stopBtn);
    toolbar->addWidget(stepOverBtn);
    toolbar->addWidget(stepIntoBtn);
    toolbar->addWidget(continueBtn);
    toolbar->addWidget(statusLabel);
    toolbar->addStretch();
    mainLayout->addLayout(toolbar);

    // 2. Splitter for console output and variables inspector
    auto* splitter = new QSplitter(Qt::Horizontal, this);

    // Left container: Console output and manual command input
    auto* consoleContainer = new QWidget(this);
    auto* consoleLayout = new QVBoxLayout(consoleContainer);
    consoleLayout->setContentsMargins(0, 0, 0, 0);

    consoleLog = new QPlainTextEdit(this);
    consoleLog->setReadOnly(true);
    consoleLog->setStyleSheet("QPlainTextEdit { background-color: #1e1e1e; color: #d4d4d4; font-family: 'Consolas', monospace; }");
    consoleLayout->addWidget(consoleLog);

    auto* cmdLayout = new QHBoxLayout();
    cmdInput = new QLineEdit(this);
    cmdInput->setPlaceholderText("Enter GDB/debugger command...");
    cmdInput->setStyleSheet("QLineEdit { background-color: #2d2d2d; color: #ffffff; font-family: 'Consolas', monospace; }");
    cmdInput->setEnabled(false);
    cmdLayout->addWidget(cmdInput);
    consoleLayout->addLayout(cmdLayout);

    splitter->addWidget(consoleContainer);

    // Right container: Variables tree widget
    variablesTree = new QTreeWidget(this);
    variablesTree->setColumnCount(3);
    variablesTree->setHeaderLabels({"Name", "Type", "Value"});
    variablesTree->header()->setSectionResizeMode(QHeaderView::Stretch);
    variablesTree->setStyleSheet("QTreeWidget { background-color: #1e1e1e; color: #d4d4d4; } QHeaderView::section { background-color: #2d2d2d; color: #ffffff; }");
    splitter->addWidget(variablesTree);

    mainLayout->addWidget(splitter);

    // Connections
    connect(startBtn, &QPushButton::clicked, this, &DebugWidget::startDebugging);
    connect(stopBtn, &QPushButton::clicked, this, &DebugWidget::stopDebugging);
    connect(stepOverBtn, &QPushButton::clicked, this, &DebugWidget::stepOver);
    connect(stepIntoBtn, &QPushButton::clicked, this, &DebugWidget::stepInto);
    connect(continueBtn, &QPushButton::clicked, this, &DebugWidget::continueDebug);
    connect(cmdInput, &QLineEdit::returnPressed, this, &DebugWidget::sendManualCommand);
}

DebugWidget::~DebugWidget() {
    stopDebugging();
}

void DebugWidget::startDebugging() {
    consoleLog->clear();
    variablesTree->clear();
    simStepCount = 0;
    
    // Check if lldb-mi.exe exists in the toolchain directory
    QString lldbMiPath = "C:/Qt/Tools/llvm-mingw_64/bin/lldb-mi.exe";
    QString targetExe = QDir::currentPath() + "/ai-ide/build/src/ai-ide.exe";

    if (!QFile::exists(lldbMiPath)) {
        // Fallback: search system PATH for lldb-mi or gdb
        lldbMiPath = "lldb-mi.exe";
    }

    consoleLog->appendPlainText("--- Launching Debug Session ---");
    consoleLog->appendPlainText("Target Executable: " + targetExe);

    gdbProcess = new QProcess(this);
    gdbProcess->setProcessChannelMode(QProcess::MergedChannels);
    connect(gdbProcess, &QProcess::readyReadStandardOutput, this, &DebugWidget::readGdbOutput);
    connect(gdbProcess, static_cast<void(QProcess::*)(int, QProcess::ExitStatus)>(&QProcess::finished), this, [this](int exitCode) {
        this->gdbFinished(exitCode);
    });

    // Try to run lldb-mi or gdb
    QStringList args;
    args << targetExe;

    gdbProcess->start(lldbMiPath, args);
    if (!gdbProcess->waitForStarted(1500)) {
        // Debugger process failed to start, enter simulation fallback
        enterSimulationMode();
    } else {
        isSimulated = false;
        consoleLog->appendPlainText("Debugger process started successfully via: " + lldbMiPath);
        statusLabel->setText("Status: Running");
        startBtn->setEnabled(false);
        stopBtn->setEnabled(true);
        stepOverBtn->setEnabled(true);
        stepIntoBtn->setEnabled(true);
        continueBtn->setEnabled(true);
        cmdInput->setEnabled(true);
        
        // Initial setup commands
        sendGdbCommand("break main");
        sendGdbCommand("run");
    }
}

void DebugWidget::enterSimulationMode() {
    isSimulated = true;
    consoleLog->appendPlainText("\n[WARNING] lldb-mi.exe or gdb.exe not found in toolchain or system PATH.");
    consoleLog->appendPlainText("[INFO] Starting Panel in Debug Simulation Mode instead...\n");
    consoleLog->appendPlainText("[Sim] Process launched. Breakpoint hit at main() in src/main.cpp:5");
    
    statusLabel->setText("Status: Paused");
    startBtn->setEnabled(false);
    stopBtn->setEnabled(true);
    stepOverBtn->setEnabled(true);
    stepIntoBtn->setEnabled(true);
    continueBtn->setEnabled(true);
    cmdInput->setEnabled(true);

    updateVariables();
}

void DebugWidget::stopDebugging() {
    if (gdbProcess) {
        if (gdbProcess->state() != QProcess::NotRunning) {
            gdbProcess->write("quit\n");
            gdbProcess->waitForFinished(1000);
            if (gdbProcess->state() != QProcess::NotRunning) {
                gdbProcess->kill();
            }
        }
        gdbProcess->deleteLater();
        gdbProcess = nullptr;
    }

    isSimulated = false;
    statusLabel->setText("Status: Idle");
    startBtn->setEnabled(true);
    stopBtn->setEnabled(false);
    stepOverBtn->setEnabled(false);
    stepIntoBtn->setEnabled(false);
    continueBtn->setEnabled(false);
    cmdInput->setEnabled(false);
    consoleLog->appendPlainText("--- Debug Session Stopped ---");
}

void DebugWidget::stepOver() {
    if (isSimulated) {
        consoleLog->appendPlainText("[Sim] step over");
        runSimulationStep();
    } else {
        sendGdbCommand("next");
    }
}

void DebugWidget::stepInto() {
    if (isSimulated) {
        consoleLog->appendPlainText("[Sim] step into");
        runSimulationStep();
    } else {
        sendGdbCommand("step");
    }
}

void DebugWidget::continueDebug() {
    if (isSimulated) {
        consoleLog->appendPlainText("[Sim] continue");
        consoleLog->appendPlainText("[Sim] Program exited normally.");
        stopDebugging();
    } else {
        sendGdbCommand("continue");
    }
}

void DebugWidget::sendManualCommand() {
    QString cmd = cmdInput->text().trimmed();
    if (cmd.isEmpty()) return;

    consoleLog->appendPlainText("> " + cmd);
    cmdInput->clear();

    if (isSimulated) {
        if (cmd == "next" || cmd == "n") {
            stepOver();
        } else if (cmd == "step" || cmd == "s") {
            stepInto();
        } else if (cmd == "continue" || cmd == "c") {
            continueDebug();
        } else if (cmd == "info locals" || cmd == "info l") {
            updateVariables();
        } else {
            consoleLog->appendPlainText("[Sim Mode] Unsupported simulation command. Try 'next', 'step', 'continue', or 'info locals'.");
        }
    } else {
        sendGdbCommand(cmd);
    }
}

void DebugWidget::sendGdbCommand(const QString& cmd) {
    if (gdbProcess && gdbProcess->state() == QProcess::Running) {
        gdbProcess->write((cmd + "\n").toLocal8Bit());
    }
}

void DebugWidget::readGdbOutput() {
    if (!gdbProcess) return;
    QByteArray output = gdbProcess->readAllStandardOutput();
    if (!output.isEmpty()) {
        QString text = QString::fromLocal8Bit(output);
        consoleLog->appendPlainText(text);
        
        // Auto-refresh variables if we hit a stopping point
        if (text.contains("stopped") || text.contains("Breakpoint") || text.contains("step")) {
            sendGdbCommand("info locals");
        }
        
        // Parse simple locals from GDB output
        QStringList lines = text.split('\n');
        bool foundLocals = false;
        for (const QString& line : lines) {
            static QRegularExpression varRegex(R"(^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*)$)");
            auto match = varRegex.match(line.trimmed());
            if (match.hasMatch()) {
                if (!foundLocals) {
                    variablesTree->clear();
                    foundLocals = true;
                }
                QString name = match.captured(1);
                QString val = match.captured(2);
                addVariable(name, "auto", val);
            }
        }
    }
}

void DebugWidget::gdbFinished(int exitCode) {
    consoleLog->appendPlainText("Debugger process finished with exit code: " + QString::number(exitCode));
    stopDebugging();
}

void DebugWidget::addVariable(const QString& name, const QString& type, const QString& val) {
    auto* item = new QTreeWidgetItem(variablesTree);
    item->setText(0, name);
    item->setText(1, type);
    item->setText(2, val);
}

void DebugWidget::updateVariables() {
    variablesTree->clear();
    if (isSimulated) {
        if (simStepCount == 0) {
            addVariable("argc", "int", "1");
            addVariable("argv", "char**", "0x0000021a8d052a60");
            addVariable("app", "QApplication", "{...}");
            addVariable("isInitialized", "bool", "false");
        } else if (simStepCount == 1) {
            addVariable("argc", "int", "1");
            addVariable("argv", "char**", "0x0000021a8d052a60");
            addVariable("app", "QApplication", "{...}");
            addVariable("isInitialized", "bool", "true");
            addVariable("w", "EditorWindow", "{...}");
        } else if (simStepCount == 2) {
            addVariable("argc", "int", "1");
            addVariable("argv", "char**", "0x0000021a8d052a60");
            addVariable("app", "QApplication", "{...}");
            addVariable("isInitialized", "bool", "true");
            addVariable("w", "EditorWindow", "{...}");
            addVariable("loopCount", "int", "0");
        } else {
            addVariable("argc", "int", "1");
            addVariable("argv", "char**", "0x0000021a8d052a60");
            addVariable("app", "QApplication", "{...}");
            addVariable("isInitialized", "bool", "true");
            addVariable("w", "EditorWindow", "{...}");
            addVariable("loopCount", "int", QString::number(simStepCount - 2));
            addVariable("status", "QString", "\"Processing window event loop...\"");
        }
    }
}

void DebugWidget::runSimulationStep() {
    simStepCount++;
    statusLabel->setText("Status: Paused (Step " + QString::number(simStepCount) + ")");
    
    if (simStepCount == 1) {
        consoleLog->appendPlainText("[Sim] Stopped at main.cpp:6 - QApplication app(argc, argv);");
    } else if (simStepCount == 2) {
        consoleLog->appendPlainText("[Sim] Stopped at main.cpp:7 - EditorWindow w;");
    } else if (simStepCount == 3) {
        consoleLog->appendPlainText("[Sim] Stopped at main.cpp:8 - w.show();");
    } else {
        consoleLog->appendPlainText("[Sim] Stopped at main.cpp:9 - return app.exec(); (Iteration: " + QString::number(simStepCount - 3) + ")");
    }
    
    updateVariables();
}
""")

# ---------------------------------------------------------
# Welcome Widget (Dashboard Startup Screen)
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/WelcomeWidget.hpp", r"""#pragma once
#include <QWidget>

class WelcomeWidget : public QWidget {
    Q_OBJECT
public:
    explicit WelcomeWidget(QWidget* parent = nullptr);

signals:
    void newFileRequested();
    void openFileRequested();
    void openFolderRequested();
    void buildRequested();
    void settingsRequested();
};
""")

write(f"{ROOT}/src/ui/WelcomeWidget.cpp", r"""#include "WelcomeWidget.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QPushButton>
#include <QFrame>

WelcomeWidget::WelcomeWidget(QWidget* parent)
    : QWidget(parent)
{
    // Styling with visual theme matching VS Code dark welcoming styles
    setStyleSheet("QWidget { background-color: #1e1e1e; color: #abb2bf; }"
                  "QLabel#title { color: #61afef; font-family: 'Segoe UI', Arial, sans-serif; font-size: 36px; font-weight: bold; margin-bottom: 5px; }"
                  "QLabel#subtitle { color: #5c6370; font-family: 'Segoe UI', Arial, sans-serif; font-size: 15px; margin-bottom: 25px; }"
                  "QPushButton { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 6px; padding: 12px 24px; font-size: 14px; text-align: left; font-family: 'Segoe UI', Arial; min-width: 280px; margin-bottom: 10px; }"
                  "QPushButton:hover { background-color: #3e4452; color: #ffffff; border-color: #61afef; }"
                  "QPushButton:pressed { background-color: #4b5263; }");

    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setAlignment(Qt::AlignCenter);

    auto* container = new QWidget(this);
    auto* layout = new QVBoxLayout(container);
    layout->setContentsMargins(40, 40, 40, 40);
    layout->setAlignment(Qt::AlignCenter);

    auto* titleLabel = new QLabel("AI-IDE", this);
    titleLabel->setObjectName("title");
    titleLabel->setAlignment(Qt::AlignCenter);
    layout->addWidget(titleLabel);

    auto* subtitleLabel = new QLabel("Next-generation C++ development powered by LLVM and Local AI", this);
    subtitleLabel->setObjectName("subtitle");
    subtitleLabel->setAlignment(Qt::AlignCenter);
    layout->addWidget(subtitleLabel);

    // Dark separator line
    auto* line = new QFrame(this);
    line->setFrameShape(QFrame::HLine);
    line->setStyleSheet("background-color: #2c313c; max-height: 1px; margin-bottom: 20px;");
    layout->addWidget(line);

    // Setup action buttons
    auto* newFileBtn = new QPushButton("📄  Create New File", this);
    auto* openFileBtn = new QPushButton("📂  Open Existing File", this);
    auto* openFolderBtn = new QPushButton("📁  Open Project Folder", this);
    auto* buildBtn = new QPushButton("🛠️  Build C++ Project", this);
    auto* settingsBtn = new QPushButton("⚙️  AI Provider Settings", this);

    layout->addWidget(newFileBtn);
    layout->addWidget(openFileBtn);
    layout->addWidget(openFolderBtn);
    layout->addWidget(buildBtn);
    layout->addWidget(settingsBtn);

    mainLayout->addWidget(container);

    // Click mappings
    connect(newFileBtn, &QPushButton::clicked, this, &WelcomeWidget::newFileRequested);
    connect(openFileBtn, &QPushButton::clicked, this, &WelcomeWidget::openFileRequested);
    connect(openFolderBtn, &QPushButton::clicked, this, &WelcomeWidget::openFolderRequested);
    connect(buildBtn, &QPushButton::clicked, this, &WelcomeWidget::buildRequested);
    connect(settingsBtn, &QPushButton::clicked, this, &WelcomeWidget::settingsRequested);
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
            leftView->appendPlainText(" --- [Hunk Boundary] --- ");
            rightView->appendPlainText(" --- [Hunk Boundary] --- ");
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
#include <memory>
#include "SettingsManager.hpp"
#include "CustomEditor.hpp"

class AIProvider;

class AIPatchController : public QObject {
    Q_OBJECT
public:
    explicit AIPatchController(CustomEditor* editor, QObject* parent = nullptr);
    void setEditor(CustomEditor* ed);

public slots:
    void requestRefactor(const QString& instruction);

private:
    CustomEditor* editor;
    std::unique_ptr<AIProvider> provider;
};
""")

write(f"{ROOT}/src/ui/AIPatchController.cpp", r"""#include "AIPatchController.hpp"
#include "DiffView.hpp"
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

AIPatchController::AIPatchController(CustomEditor* ed, QObject* parent)
    : QObject(parent),
      editor(ed)
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

    DiffView diffView;
    diffView.setTexts(code, newCode);

    QDialog dlg;
    dlg.setWindowTitle("AI Patch Preview");
    auto* layout = new QVBoxLayout(&dlg);
    layout->addWidget(&diffView);

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
#include <QTabWidget>
#include <QStringListModel>

class CustomEditor;
class FileBrowser;
class WelcomeWidget;
class AIPatchController;
class CommandPalette;
class ClipboardListener;
class QShowEvent;
class QSplitter;
class QListView;
class QPlainTextEdit;
class QProcess;
class TerminalWidget;
class ProblemsWidget;
class DebugWidget;
class QLineEdit;

class EditorWindow : public QMainWindow {
    Q_OBJECT
public:
    explicit EditorWindow(QWidget *parent = nullptr);

private:
    void createMenus();
    void createDocks();
    void createCentralEditor();
    void showEvent(QShowEvent* event) override;
    void openFileInTab(const QString& path);
    CustomEditor* currentEditor() const;
    void runBuild();
    void readBuildOutput();
    void buildFinished(int exitCode, int exitStatus);
    void parseBuildLine(const QString& line);
    void gotoLine(const QString& file, int line);
    void openWelcomeTab();
    void showCommandPalette();
    bool eventFilter(QObject* obj, QEvent* event) override;

    QTabWidget* tabWidget;
    QTabWidget* bottomTabWidget;
    QSplitter* mainSplitter;
    TerminalWidget* powerShellTab;
    TerminalWidget* bashTab;
    DebugWidget* debugTab;
    ProblemsWidget* problemsTab;
    QPlainTextEdit* outputTab;
    QListView* historyView;

    QProcess* buildProcess;

    CustomEditor* editor;
    FileBrowser* fileBrowser;
    AIPatchController* aiPatchController;
    CommandPalette* commandPalette;
    QLineEdit* pathLineEdit;
    QLineEdit* cmdLineEdit;
    ClipboardListener* clipboardListener;
    QStringListModel* historyModel;
    QString buildBuffer;
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
#include "TerminalWidget.hpp"
#include "ProblemsWidget.hpp"
#include "DebugWidget.hpp"
#include "WelcomeWidget.hpp"
#include "CommandPalette.hpp"

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
      aiPatchController(nullptr),
      commandPalette(nullptr),
      pathLineEdit(nullptr),
      cmdLineEdit(nullptr),
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
    // File Browser (Left)
    auto* fileDock = new QDockWidget("Files", this);
    fileBrowser = new FileBrowser(fileDock);
    fileDock->setWidget(fileBrowser);
    fileDock->setMinimumWidth(250);
    addDockWidget(Qt::LeftDockWidgetArea, fileDock);

    connect(fileBrowser, &FileBrowser::fileOpened, this, [this](const QString& path) {
        openFileInTab(path);
    });

    connect(fileBrowser, &FileBrowser::rootChanged, this, [this](const QString& path) {
        if (pathLineEdit) pathLineEdit->setText(path);
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
