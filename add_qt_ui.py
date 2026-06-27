import os

ROOT = "ai-ide"

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# --- Overwrite src/main.cpp with Qt entry point ---
write(f"{ROOT}/src/main.cpp", r"""#include <QApplication>
#include "ui/EditorWindow.hpp"

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);

    EditorWindow w;
    w.show();

    return app.exec();
}
""")

# --- Add Qt main window skeleton ---
write(f"{ROOT}/src/ui/EditorWindow.hpp", r"""#pragma once

#include <QMainWindow>

class EditorWindow : public QMainWindow {
    Q_OBJECT
public:
    explicit EditorWindow(QWidget *parent = nullptr);

private:
    void createMenus();
    void createDocks();
    void createCentralEditor();
};
""")

write(f"{ROOT}/src/ui/EditorWindow.cpp", r"""#include "EditorWindow.hpp"
#include <QMenuBar>
#include <QDockWidget>
#include <QTextEdit>
#include <QTreeView>
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
    // File browser dock
    auto *fileDock = new QDockWidget("Files", this);
    auto *fileView = new QTreeView(fileDock);
    fileDock->setWidget(fileView);
    addDockWidget(Qt::LeftDockWidgetArea, fileDock);

    // AI chat dock
    auto *aiDock = new QDockWidget("AI Chat", this);
    auto *aiView = new QTextEdit(aiDock);
    aiView->setReadOnly(false);
    aiDock->setWidget(aiView);
    addDockWidget(Qt::RightDockWidgetArea, aiDock);

    // Action history dock
    auto *historyDock = new QDockWidget("AI History", this);
    auto *historyView = new QListView(historyDock);
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

# --- Update src/CMakeLists.txt to use Qt6 Widgets ---
write(f"{ROOT}/src/CMakeLists.txt", r"""cmake_minimum_required(VERSION 3.16)

file(GLOB_RECURSE SOURCES *.cpp)

find_package(Qt6 REQUIRED COMPONENTS Widgets)

add_executable(ai-ide ${SOURCES})

target_link_libraries(ai-ide PRIVATE Qt6::Widgets)

target_compile_definitions(ai-ide PRIVATE
    QT_DEPRECATED_WARNINGS
)
""")

print("Qt UI skeleton added. Remember to configure CMake with Qt6 available.")
