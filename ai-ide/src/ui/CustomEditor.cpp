#include "CustomEditor.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QPushButton>
#include <QFile>
#include <QTextStream>
#include <QFileDialog>
#include <QDir>

CustomEditor::CustomEditor(QWidget* parent)
    : QWidget(parent), closeButton(nullptr), saveAsButton(nullptr)
{
    auto* mainLayout = new QVBoxLayout(this);

    editor = new QPlainTextEdit(this);
    mainLayout->addWidget(editor);

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
