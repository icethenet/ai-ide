#include "CustomEditor.hpp"
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
    editor->setFilePath(path);
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
    editor->setFilePath(fileName);
}

QString CustomEditor::currentFilePath() const {
    return filePath;
}

#include <QTimer>
#include <QProcess>

// ---------------------------------------------------------
// CodeEditor Implementation
// ---------------------------------------------------------
CodeEditor::CodeEditor(QWidget* parent)
    : QPlainTextEdit(parent),
      lineNumberArea(nullptr),
      diffTimer(nullptr)
{
    lineNumberArea = new LineNumberArea(this);

    diffTimer = new QTimer(this);
    diffTimer->setSingleShot(true);
    connect(diffTimer, &QTimer::timeout, this, &CodeEditor::updateGitDiff);

    connect(this, &CodeEditor::blockCountChanged, this, &CodeEditor::updateLineNumberAreaWidth);
    connect(this, &CodeEditor::updateRequest, this, &CodeEditor::updateLineNumberArea);
    connect(this, &CodeEditor::cursorPositionChanged, this, &CodeEditor::highlightCurrentLine);

    connect(this, &QPlainTextEdit::textChanged, this, [this]() {
        if (diffTimer) diffTimer->start(2000);
    });

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

    // Draw Git diff color bars on the left edge of the gutter
    int markerWidth = 3;
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
            
            // Match git lines
            for (const auto& dl : diffLines) {
                if (dl.line == blockNumber + 1) {
                    QColor color;
                    if (dl.type == 'A') color = QColor(152, 195, 121); // Green
                    else if (dl.type == 'M') color = QColor(97, 175, 239); // Blue
                    else if (dl.type == 'D') color = QColor(224, 108, 117); // Red
                    
                    painter.fillRect(QRect(0, top, markerWidth, bottom - top), color);
                    break;
                }
            }
        }

        block = block.next();
        top = bottom;
        bottom = top + qRound(blockBoundingRect(block).height());
        blockNumber++;
    }
}

void CodeEditor::setFilePath(const QString& path) {
    filePath = path;
    updateGitDiff();
}

void CodeEditor::updateGitDiff() {
    diffLines.clear();
    if (filePath.isEmpty()) return;

    QFileInfo info(filePath);
    QString dir = info.dir().absolutePath();
    QString fileName = info.fileName();

    auto* proc = new QProcess();
    proc->setWorkingDirectory(dir);
    
    connect(proc, QOverload<int, QProcess::ExitStatus>::of(&QProcess::finished), this, [this, proc](int exitCode) {
        if (exitCode == 0) {
            QString out = proc->readAllStandardOutput();
            QStringList lines = out.split("\n", Qt::SkipEmptyParts);
            
            QRegularExpression regex("^@@ -(\\d+)(?:,(\\d+))? \\+(\\d+)(?:,(\\d+))? @@");
            for (const QString& line : lines) {
                auto match = regex.match(line);
                if (match.hasMatch()) {
                    int oldStart = match.captured(1).toInt();
                    int oldLen = match.captured(2).isEmpty() ? 1 : match.captured(2).toInt();
                    int newStart = match.captured(3).toInt();
                    int newLen = match.captured(4).isEmpty() ? 1 : match.captured(4).toInt();
                    
                    if (newLen == 0) {
                        diffLines.push_back({newStart, 'D'});
                    } else {
                        char type = (oldLen > 0) ? 'M' : 'A';
                        for (int l = 0; l < newLen; ++l) {
                            diffLines.push_back({newStart + l, type});
                        }
                    }
                }
            }
            if (lineNumberArea) lineNumberArea->update();
        }
        proc->deleteLater();
    });
    
    proc->start("git", QStringList() << "diff" << "-U0" << fileName);
}
