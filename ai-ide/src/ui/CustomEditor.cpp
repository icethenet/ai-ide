#include "CustomEditor.hpp"
#include "CppHighlighter.hpp"
#include "LspClient.hpp"
#include "CompletionPopup.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QPushButton>
#include <QFile>
#include <QTextStream>
#include <QFileDialog>
#include <QDir>
#include <QDesktopServices>
#include <QUrl>
#include <QMessageBox>
#include <QPainter>
#include <QPaintEvent>
#include <QTextBlock>
#include <QMenu>
#include <QContextMenuEvent>
#include <QTimer>
#include <QProcess>
#include <QMainWindow>

CustomEditor::CustomEditor(QWidget* parent)
    : QWidget(parent), saveButton(nullptr), saveAsButton(nullptr), closeButton(nullptr), openHtmlButton(nullptr), highlighter(nullptr)
{
    auto* mainLayout = new QVBoxLayout(this);

    editor = new CodeEditor(this);
    mainLayout->addWidget(editor);

    highlighter = new CppHighlighter(editor->document());

    auto* buttonLayout = new QHBoxLayout();
    buttonLayout->addStretch();
    
    saveButton = new QPushButton("Save", this);
    saveButton->setStyleSheet("QPushButton { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 4px 12px; font-family: 'Segoe UI', Arial; font-size: 11px; font-weight: bold; }"
                           "QPushButton:hover { background-color: #3e4452; color: #ffffff; }");

    saveAsButton = new QPushButton("Save As", this);
    saveAsButton->setStyleSheet("QPushButton { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 4px 12px; font-family: 'Segoe UI', Arial; font-size: 11px; font-weight: bold; }"
                             "QPushButton:hover { background-color: #3e4452; color: #ffffff; }");

    closeButton = new QPushButton("Close", this);
    closeButton->setStyleSheet("QPushButton { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 4px 12px; font-family: 'Segoe UI', Arial; font-size: 11px; font-weight: bold; }"
                            "QPushButton:hover { background-color: #e06c75; color: #ffffff; border-color: #d15a63; }");

    openHtmlButton = new QPushButton("Open HTML", this);
    openHtmlButton->setStyleSheet("QPushButton { background-color: #98c379; color: #1e1e1e; border: 1px solid #7cb057; border-radius: 4px; padding: 4px 12px; font-family: 'Segoe UI', Arial; font-size: 11px; font-weight: bold; }"
                               "QPushButton:hover { background-color: #a6db87; color: #111111; }");
    
    buttonLayout->addWidget(saveButton);
    buttonLayout->addWidget(saveAsButton);
    buttonLayout->addWidget(closeButton);
    buttonLayout->addWidget(openHtmlButton);
    mainLayout->addLayout(buttonLayout);

    connect(saveButton, &QPushButton::clicked, this, &CustomEditor::saveFile);
    connect(saveAsButton, &QPushButton::clicked, this, &CustomEditor::saveAsFile);
    connect(closeButton, &QPushButton::clicked, this, &CustomEditor::closeRequested);

    connect(openHtmlButton, &QPushButton::clicked, this, [this]() {
        QString path = currentFilePath();
        if (path.endsWith(".html", Qt::CaseSensitivity::CaseInsensitive) || path.endsWith(".htm", Qt::CaseSensitivity::CaseInsensitive)) {
            saveFile();
            QDesktopServices::openUrl(QUrl::fromLocalFile(path));
        } else {
            QString baseDir = path.isEmpty() ? QDir::currentPath() : QFileInfo(path).absolutePath();
            QString tempPath = QDir(baseDir).absoluteFilePath("preview_temp.html");
            QFile file(tempPath);
            if (file.open(QIODevice::WriteOnly | QIODevice::Text)) {
                QTextStream out(&file);
                out << editor->toPlainText();
                file.close();
                QDesktopServices::openUrl(QUrl::fromLocalFile(tempPath));
            } else {
                QMessageBox::warning(this, "Open HTML", "Please save the file first.");
            }
        }
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
    QString content = in.readAll();
    editor->setPlainText(content);
    filePath = path;
    editor->setFilePath(path);
    
    LspClient::instance().didOpen(path, content);
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
    f.close();
    emit fileSaved(filePath);
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
    f.close();
    editor->setFilePath(fileName);
    emit fileSaved(filePath);
}

QString CustomEditor::currentFilePath() const {
    return filePath;
}

// ---------------------------------------------------------
// CodeEditor Implementation
// ---------------------------------------------------------
CodeEditor::CodeEditor(QWidget* parent)
    : QPlainTextEdit(parent),
      lineNumberArea(nullptr),
      diffTimer(nullptr),
      completionPopup(nullptr),
      activeCompletionId(-1)
{
    lineNumberArea = new LineNumberArea(this);

    diffTimer = new QTimer(this);
    diffTimer->setSingleShot(true);
    connect(diffTimer, &QTimer::timeout, this, &CodeEditor::updateGitDiff);

    completionPopup = new CompletionPopup(this);
    connect(&LspClient::instance(), &LspClient::completionReady, this, &CodeEditor::onCompletionReady);

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

void CodeEditor::setDiagnostics(const std::vector<Diagnostic>& diags) {
    diagnostics = diags;
    highlightCurrentLine();
}

void CodeEditor::clearDiagnostics() {
    diagnostics.clear();
    highlightCurrentLine();
}

void CodeEditor::highlightDiagnostics(QList<QTextEdit::ExtraSelection>& selections) {
    for (const auto& diag : diagnostics) {
        QTextBlock block = document()->findBlockByNumber(diag.line - 1);
        if (block.isValid()) {
            QTextEdit::ExtraSelection selection;
            selection.cursor = QTextCursor(block);
            selection.cursor.select(QTextCursor::LineUnderCursor);
            
            QTextCharFormat format;
            format.setUnderlineStyle(QTextCharFormat::WaveUnderline);
            format.setUnderlineColor(diag.isError ? Qt::red : QColor(209, 154, 102));
            selection.format = format;
            
            selections.append(selection);
        }
    }
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

    highlightDiagnostics(extraSelections);

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
            
            // Draw Git diff color bars
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

            // Draw lightbulb emoji 💡 slightly to the left of the line number if diagnostic exists
            bool hasDiag = false;
            for (const auto& diag : diagnostics) {
                if (diag.line == blockNumber + 1) {
                    hasDiag = true;
                    break;
                }
            }
            if (hasDiag) {
                painter.drawText(2, top, lineNumberArea->width() - 5, fontMetrics().height(),
                                 Qt::AlignLeft | Qt::AlignVCenter, "💡");
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

void CodeEditor::keyPressEvent(QKeyEvent* event) {
    if (completionPopup && completionPopup->isVisible()) {
        if (event->key() == Qt::Key_Down) {
            int r = completionPopup->currentRow();
            if (r < completionPopup->count() - 1) completionPopup->setCurrentRow(r + 1);
            return;
        } else if (event->key() == Qt::Key_Up) {
            int r = completionPopup->currentRow();
            if (r > 0) completionPopup->setCurrentRow(r - 1);
            return;
        } else if (event->key() == Qt::Key_Enter || event->key() == Qt::Key_Return || event->key() == Qt::Key_Tab) {
            auto* item = completionPopup->currentItem();
            if (item) {
                QString replacement = item->data(Qt::UserRole).toString();
                QTextCursor tc = textCursor();
                tc.select(QTextCursor::WordUnderCursor);
                tc.removeSelectedText();
                tc.insertText(replacement);
            }
            completionPopup->hide();
            return;
        } else if (event->key() == Qt::Key_Escape) {
            completionPopup->hide();
            return;
        }
    }

    bool triggerAutocomplete = false;
    if (event->key() == Qt::Key_Space && (event->modifiers() & Qt::ControlModifier)) {
        triggerAutocomplete = true;
        event->accept();
    } else {
        QPlainTextEdit::keyPressEvent(event);
        QString text = event->text();
        if (text == "." || text == ">" || text == ":") {
            triggerAutocomplete = true;
        }
    }

    if (!filePath.isEmpty() && !event->text().isEmpty()) {
        LspClient::instance().didChange(filePath, toPlainText());
    }

    if (triggerAutocomplete && !filePath.isEmpty()) {
        QTextCursor tc = textCursor();
        int line = tc.blockNumber();
        int col = tc.columnNumber();
        activeCompletionId = LspClient::instance().requestCompletion(filePath, line, col);
    }
}

void CodeEditor::onCompletionReady(int id, const QJsonArray& items) {
    if (id == activeCompletionId) {
        if (items.isEmpty()) {
            completionPopup->hide();
        } else {
            completionPopup->setCompletions(items);
            QPoint pos = mapToGlobal(cursorRect().bottomLeft());
            completionPopup->setGeometry(pos.x(), pos.y() + 5, 250, 150);
            completionPopup->show();
        }
    }
}

void CodeEditor::contextMenuEvent(QContextMenuEvent* event) {
    QMenu* menu = createStandardContextMenu();
    menu->addSeparator();

    // Find if there is a diagnostic on the clicked line
    QTextCursor clickedCursor = cursorForPosition(event->pos());
    int clickedLine = clickedCursor.blockNumber() + 1;
    
    QString diagMessage;
    bool hasDiag = false;
    for (const auto& diag : diagnostics) {
        if (diag.line == clickedLine) {
            hasDiag = true;
            diagMessage = diag.message;
            break;
        }
    }

    QAction* aiFixAction = nullptr;
    if (hasDiag) {
        aiFixAction = menu->addAction("💡 Fix with AI...");
    }

    auto* gotoAction = menu->addAction("Go to Definition");
    auto* findRefAction = menu->addAction("Find References");

    QAction* selected = menu->exec(event->globalPos());
    if (selected == aiFixAction && hasDiag) {
        QWidget* w = parentWidget();
        while (w) {
            auto* mainWindow = qobject_cast<QMainWindow*>(w);
            if (mainWindow) {
                QMetaObject::invokeMethod(mainWindow, "fixProblemWithAI",
                                          Q_ARG(QString, filePath),
                                          Q_ARG(int, clickedLine),
                                          Q_ARG(QString, diagMessage));
                break;
            }
            w = w->parentWidget();
        }
    } else if (selected == gotoAction) {
        QTextCursor tc = cursorForPosition(event->pos());
        int line = tc.blockNumber();
        int col = tc.columnNumber();
        LspClient::instance().requestDefinition(filePath, line, col);
    } else if (selected == findRefAction) {
        QTextCursor tc = cursorForPosition(event->pos());
        int line = tc.blockNumber();
        int col = tc.columnNumber();
        LspClient::instance().requestReferences(filePath, line, col);
    }
    delete menu;
}

void CodeEditor::focusOutEvent(QFocusEvent* event) {
    QPlainTextEdit::focusOutEvent(event);
    if (completionPopup) {
        completionPopup->hide();
    }
}
