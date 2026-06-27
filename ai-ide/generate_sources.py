import os

SRC_DIR = "src"

FILES = {
    "main.cpp": """
#include <QApplication>
#include "EditorWindow.h"

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    EditorWindow w;
    w.show();
    return app.exec();
}
""",

    "EditorWindow.h": """
#pragma once
#include <QMainWindow>

class CustomEditor;
class DiffView;

class EditorWindow : public QMainWindow
{
    Q_OBJECT
public:
    explicit EditorWindow(QWidget *parent = nullptr);

private:
    CustomEditor* editor;
    DiffView* diffView;

    void setupMenus();
};
""",

    "EditorWindow.cpp": """
#include "EditorWindow.h"
#include "CustomEditor.h"
#include "DiffView.h"
#include <QMenuBar>
#include <QFileDialog>
#include <QMessageBox>
#include <QFile>
#include <QTextStream>

EditorWindow::EditorWindow(QWidget *parent)
    : QMainWindow(parent)
{
    editor = new CustomEditor(this);
    diffView = new DiffView(this);

    setCentralWidget(editor);
    setupMenus();
}

void EditorWindow::setupMenus()
{
    QMenu* fileMenu = menuBar()->addMenu("File");

    QAction* openAct = new QAction("Open", this);
    connect(openAct, &QAction::triggered, this, [this]() {
        QString path = QFileDialog::getOpenFileName(this, "Open File");
        if (path.isEmpty()) return;

        QFile f(path);
        if (!f.open(QIODevice::ReadOnly | QIODevice::Text)) {
            QMessageBox::warning(this, "Error", "Failed to open file");
            return;
        }

        QTextStream in(&f);
        editor->setPlainText(in.readAll());
    });

    fileMenu->addAction(openAct);
}
""",

    "CustomEditor.h": """
#pragma once
#include <QPlainTextEdit>

class CustomEditor : public QPlainTextEdit
{
    Q_OBJECT
public:
    explicit CustomEditor(QWidget* parent = nullptr);
};
""",

    "CustomEditor.cpp": """
#include "CustomEditor.h"

CustomEditor::CustomEditor(QWidget* parent)
    : QPlainTextEdit(parent)
{
    setLineWrapMode(QPlainTextEdit::NoWrap);
}
""",

    "DiffView.h": """
#pragma once
#include <QWidget>
#include <QString>

class DiffView : public QWidget
{
    Q_OBJECT
public:
    explicit DiffView(QWidget* parent = nullptr);
    void showDiff(const QString& a, const QString& b);
};
""",

    "DiffView.cpp": """
#include "DiffView.h"
#include <QVBoxLayout>
#include <QLabel>

DiffView::DiffView(QWidget* parent)
    : QWidget(parent)
{
    auto* layout = new QVBoxLayout(this);
    layout->addWidget(new QLabel("Diff view placeholder"));
}

void DiffView::showDiff(const QString& a, const QString& b)
{
    // Placeholder for future diff logic
}
""",

    "GitClient.h": """
#pragma once
#include <QString>

class GitClient
{
public:
    GitClient();
    bool initRepo(const QString& path);
    bool commit(const QString& message);
};
""",

    "GitClient.cpp": """
#include "GitClient.h"

GitClient::GitClient() {}

bool GitClient::initRepo(const QString& path)
{
    // Placeholder
    return true;
}

bool GitClient::commit(const QString& message)
{
    // Placeholder
    return true;
}
"""
}

def ensure_src_dir():
    if not os.path.exists(SRC_DIR):
        os.makedirs(SRC_DIR)
        print(f"Created directory: {SRC_DIR}")

def write_files():
    for filename, content in FILES.items():
        path = os.path.join(SRC_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
        print(f"Created: {path}")

if __name__ == "__main__":
    ensure_src_dir()
    write_files()
    print("\nAll source files generated successfully.")
