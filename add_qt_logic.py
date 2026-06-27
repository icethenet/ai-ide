import os

ROOT = "ai-ide"

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# ---------------------------------------------------------
# 1. FILE BROWSER (LEFT DOCK)
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/FileBrowser.hpp", r"""#pragma once
#include <QWidget>
#include <QFileSystemModel>
#include <QTreeView>

class FileBrowser : public QWidget {
    Q_OBJECT
public:
    explicit FileBrowser(QWidget* parent = nullptr);

    void setRootPath(const QString& path);

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

FileBrowser::FileBrowser(QWidget* parent)
    : QWidget(parent)
{
    auto* layout = new QVBoxLayout(this);

    model = new QFileSystemModel(this);
    model->setRootPath(QDir::currentPath());
    model->setFilter(QDir::AllEntries | QDir::NoDotAndDotDot);

    tree = new QTreeView(this);
    tree->setModel(model);
    tree->setHeaderHidden(true);

    layout->addWidget(tree);

    connect(tree, &QTreeView::doubleClicked, this, [this](const QModelIndex& idx) {
        QString path = model->filePath(idx);
        if (QFileInfo(path).isFile()) {
            emit fileOpened(path);
        }
    });
}

void FileBrowser::setRootPath(const QString& path) {
    tree->setRootIndex(model->index(path));
}
""")

# ---------------------------------------------------------
# 2. AI CHAT PANEL (RIGHT DOCK)
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/AIChatPanel.hpp", r"""#pragma once
#include <QWidget>
#include <QTextEdit>
#include <QPushButton>

#include "../ai/OllamaProvider.hpp"

class AIChatPanel : public QWidget {
    Q_OBJECT
public:
    explicit AIChatPanel(QWidget* parent = nullptr);

private slots:
    void sendPrompt();

private:
    QTextEdit* chatHistory;
    QTextEdit* inputBox;
    QPushButton* sendButton;

    OllamaProvider* provider;
};
""")

write(f"{ROOT}/src/ui/AIChatPanel.cpp", r"""#include "AIChatPanel.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>

AIChatPanel::AIChatPanel(QWidget* parent)
    : QWidget(parent)
{
    auto* layout = new QVBoxLayout(this);

    chatHistory = new QTextEdit(this);
    chatHistory->setReadOnly(true);

    inputBox = new QTextEdit(this);
    inputBox->setFixedHeight(80);

    sendButton = new QPushButton("Send", this);

    provider = new OllamaProvider("http://192.168.1.161:11434");

    layout->addWidget(chatHistory);
    layout->addWidget(inputBox);
    layout->addWidget(sendButton);

    connect(sendButton, &QPushButton::clicked, this, &AIChatPanel::sendPrompt);
}

void AIChatPanel::sendPrompt() {
    QString prompt = inputBox->toPlainText().trimmed();
    if (prompt.isEmpty()) return;

    chatHistory->append("You: " + prompt);

    AIRequest req;
    req.mode = "chat";
    req.prompt = prompt.toStdString();

    AIResponse res = provider->send(req);

    chatHistory->append("AI: " + QString::fromStdString(res.text));

    inputBox->clear();
}
""")

# ---------------------------------------------------------
# 3. UPDATE EditorWindow.cpp TO USE NEW PANELS
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/EditorWindow.cpp", r"""#include "EditorWindow.hpp"
#include "FileBrowser.hpp"
#include "AIChatPanel.hpp"

#include <QMenuBar>
#include <QDockWidget>
#include <QTextEdit>
#include <QListView>

EditorWindow::EditorWindow(QWidget *parent)
    : QMainWindow(parent)
{
    setWindowTitle("AI-IDE");

    createCentralEditor();
    createDocks();
    createMenus();
}

void EditorWindow::createCentralEditor() {
    auto *editor = new QTextEdit(this);
    setCentralWidget(editor);
}

void EditorWindow::createDocks() {
    // File Browser (Left)
    auto* fileDock = new QDockWidget("Files", this);
    auto* fileBrowser = new FileBrowser(fileDock);
    fileDock->setWidget(fileBrowser);
    addDockWidget(Qt::LeftDockWidgetArea, fileDock);

    // AI Chat (Right)
    auto* aiDock = new QDockWidget("AI Chat", this);
    auto* aiPanel = new AIChatPanel(aiDock);
    aiDock->setWidget(aiPanel);
    addDockWidget(Qt::RightDockWidgetArea, aiDock);

    // AI History (Right)
    auto* historyDock = new QDockWidget("AI History", this);
    auto* historyView = new QListView(historyDock);
    historyDock->setWidget(historyView);
    addDockWidget(Qt::RightDockWidgetArea, historyDock);
}

void EditorWindow::createMenus() {
    auto *fileMenu = menuBar()->addMenu("&File");
    fileMenu->addAction("Open");
    fileMenu->addAction("Save");
    fileMenu->addSeparator();
    fileMenu->addAction("Exit", this, SLOT(close()));

    auto *aiMenu = menuBar()->addMenu("&AI");
    aiMenu->addAction("Ask AI");
    aiMenu->addAction("Show AI History");

    auto *helpMenu = menuBar()->addMenu("&Help");
    helpMenu->addAction("About");
}
""")

# ---------------------------------------------------------
# 4. UPDATE CMakeLists FOR QT
# ---------------------------------------------------------
write(f"{ROOT}/src/CMakeLists.txt", r"""cmake_minimum_required(VERSION 3.16)

file(GLOB_RECURSE SOURCES *.cpp)

find_package(Qt6 REQUIRED COMPONENTS Widgets)

add_executable(ai-ide ${SOURCES})

target_link_libraries(ai-ide PRIVATE Qt6::Widgets)

target_compile_definitions(ai-ide PRIVATE
    QT_DEPRECATED_WARNINGS
)
""")

print("Qt File Browser + AI Chat Panel logic added successfully!")
