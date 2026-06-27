#include "TerminalWidget.hpp"
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
