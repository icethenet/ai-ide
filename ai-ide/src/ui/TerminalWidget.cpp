#include "TerminalWidget.hpp"
#include <QHBoxLayout>
#include <QPushButton>
#include <QKeyEvent>
#include <QRegularExpression>
#include <QTextCursor>
#include <QLabel>

TerminalPane::TerminalPane(const QString& shellPath, QPlainTextEdit* existingEdit, QProcess* existingProc, QWidget* parent)
    : TerminalPane(shellPath, QStringList(), existingEdit, existingProc, parent)
{
}

TerminalPane::TerminalPane(const QString& shellPath, const QStringList& shellArgs, QPlainTextEdit* existingEdit, QProcess* existingProc, QWidget* parent)
    : QWidget(parent),
      shell(shellPath),
      shellArgs(shellArgs),
      terminalEdit(existingEdit),
      process(existingProc),
      isSplit(false),
      splitter(nullptr),
      child1(nullptr),
      child2(nullptr)
{
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);
    mainLayout->setSpacing(0);

    // Create toolbar
    toolbar = new QWidget(this);
    toolbar->setStyleSheet("QWidget { background-color: #282c34; border-bottom: 1px solid #181a1f; }");
    auto* toolbarLayout = new QHBoxLayout(toolbar);
    toolbarLayout->setContentsMargins(10, 2, 10, 2);
    
    QString label = "Terminal";
    if (shellPath.contains("powershell")) label = "PowerShell";
    else if (shellPath.contains("bash")) label = "Bash";
    else if (shellPath.contains("ssh")) label = "SSH Connection";
    
    auto* shellLabel = new QLabel(label, this);
    shellLabel->setStyleSheet("QLabel { color: #abb2bf; font-weight: bold; font-family: 'Segoe UI', Arial; }");
    toolbarLayout->addWidget(shellLabel);
    toolbarLayout->addStretch();

    QString btnStyle = "QPushButton { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 2px 8px; font-family: 'Segoe UI', Arial; }"
                       "QPushButton:hover { background-color: #3e4452; color: #ffffff; }";
    
    auto* splitHBtn = new QPushButton("Split H", this);
    splitHBtn->setStyleSheet(btnStyle);
    connect(splitHBtn, &QPushButton::clicked, this, &TerminalPane::splitHorizontal);
    toolbarLayout->addWidget(splitHBtn);

    auto* splitVBtn = new QPushButton("Split V", this);
    splitVBtn->setStyleSheet(btnStyle);
    connect(splitVBtn, &QPushButton::clicked, this, &TerminalPane::splitVertical);
    toolbarLayout->addWidget(splitVBtn);

    auto* closeBtn = new QPushButton("Close", this);
    closeBtn->setStyleSheet("QPushButton { background-color: #e06c75; color: #1e1e1e; border: none; border-radius: 4px; padding: 2px 8px; font-family: 'Segoe UI', Arial; font-weight: bold; }"
                            "QPushButton:hover { background-color: #e5c07b; }");
    connect(closeBtn, &QPushButton::clicked, this, &TerminalPane::closePane);
    toolbarLayout->addWidget(closeBtn);

    // Show close button only if parent is a splitter
    auto* parentSplitter = qobject_cast<QSplitter*>(parent);
    closeBtn->setVisible(parentSplitter != nullptr);

    mainLayout->addWidget(toolbar);

    contentArea = new QWidget(this);
    contentLayout = new QVBoxLayout(contentArea);
    contentLayout->setContentsMargins(0, 0, 0, 0);
    contentLayout->setSpacing(0);
    mainLayout->addWidget(contentArea, 1);

    if (!terminalEdit && !process) {
        // Create new terminal session
        terminalEdit = new QPlainTextEdit(contentArea);
        QFont monoFont("Consolas", 10);
        if (monoFont.fixedPitch()) {
            terminalEdit->setFont(monoFont);
        }
        terminalEdit->setStyleSheet("QPlainTextEdit { background-color: #1e1e1e; color: #abb2bf; border: none; }");
        contentLayout->addWidget(terminalEdit);

        process = new QProcess(this);
        process->setProcessChannelMode(QProcess::MergedChannels);
        connect(process, &QProcess::readyReadStandardOutput, this, &TerminalPane::readOutput);
        
        terminalEdit->installEventFilter(this);

        QStringList args = shellArgs;
        if (args.isEmpty() && shellPath.contains("bash.exe")) {
            args << "--login" << "-i";
        }
        process->start(shellPath, args);
    } else {
        // Take ownership of existing session
        terminalEdit->setParent(contentArea);
        contentLayout->addWidget(terminalEdit);
        terminalEdit->installEventFilter(this);
        connect(process, &QProcess::readyReadStandardOutput, this, &TerminalPane::readOutput);
    }
}

TerminalPane::~TerminalPane() {
    if (process && process->state() != QProcess::NotRunning) {
        process->terminate();
        process->waitForFinished(1000);
    }
}

void TerminalPane::splitHorizontal() {
    split(Qt::Horizontal);
}

void TerminalPane::splitVertical() {
    split(Qt::Vertical);
}

void TerminalPane::split(Qt::Orientation orientation) {
    if (isSplit) return;

    if (process) {
        disconnect(process, &QProcess::readyReadStandardOutput, this, &TerminalPane::readOutput);
    }
    if (terminalEdit) {
        terminalEdit->removeEventFilter(this);
        contentLayout->removeWidget(terminalEdit);
    }

    isSplit = true;
    
    splitter = new QSplitter(orientation, contentArea);
    contentLayout->addWidget(splitter);

    child1 = new TerminalPane(shell, terminalEdit, process, splitter);
    child2 = new TerminalPane(shell, nullptr, nullptr, splitter);

    terminalEdit = nullptr;
    process = nullptr;
    if (toolbar) toolbar->hide();

    splitter->addWidget(child1);
    splitter->addWidget(child2);

    connect(child1, &TerminalPane::closed, this, &TerminalPane::onChildClosed);
    connect(child2, &TerminalPane::closed, this, &TerminalPane::onChildClosed);
}

void TerminalPane::closePane() {
    emit closed();
}

void TerminalPane::onChildClosed() {
    auto* closedChild = qobject_cast<TerminalPane*>(sender());
    if (!closedChild) return;

    TerminalPane* remainingChild = (closedChild == child1) ? child2 : child1;

    // Reparent remaining session
    terminalEdit = remainingChild->terminalEdit;
    process = remainingChild->process;

    if (terminalEdit) {
        terminalEdit->setParent(contentArea);
        contentLayout->addWidget(terminalEdit);
        terminalEdit->installEventFilter(this);
    }
    if (process) {
        process->setParent(this);
        connect(process, &QProcess::readyReadStandardOutput, this, &TerminalPane::readOutput);
    }

    child1->deleteLater();
    child2->deleteLater();
    splitter->deleteLater();

    child1 = nullptr;
    child2 = nullptr;
    splitter = nullptr;
    isSplit = false;

    if (toolbar) toolbar->show();
}

bool TerminalPane::eventFilter(QObject* obj, QEvent* event) {
    if (obj == terminalEdit && event->type() == QEvent::KeyPress) {
        auto* keyEvent = static_cast<QKeyEvent*>(event);
        QString txt = keyEvent->text();
        
        if (keyEvent->modifiers() & Qt::ControlModifier) {
            if (keyEvent->key() == Qt::Key_C) {
                if (process) process->write("\x03");
                return true;
            } else if (keyEvent->key() == Qt::Key_Z) {
                if (process) process->write("\x1A");
                return true;
            } else if (keyEvent->key() == Qt::Key_D) {
                if (process) process->write("\x04");
                return true;
            }
            return false;
        }

        if (keyEvent->key() == Qt::Key_Return || keyEvent->key() == Qt::Key_Enter) {
            if (process) process->write("\r\n");
            return true;
        } else if (keyEvent->key() == Qt::Key_Backspace) {
            if (process) process->write("\b");
            return true;
        } else if (keyEvent->key() == Qt::Key_Tab) {
            if (process) process->write("\t");
            return true;
        } else if (keyEvent->key() == Qt::Key_Escape) {
            if (process) process->write("\x1B");
            return true;
        } else if (keyEvent->key() == Qt::Key_Up) {
            if (process) process->write("\x1B[A");
            return true;
        } else if (keyEvent->key() == Qt::Key_Down) {
            if (process) process->write("\x1B[B");
            return true;
        } else if (keyEvent->key() == Qt::Key_Right) {
            if (process) process->write("\x1B[C");
            return true;
        } else if (keyEvent->key() == Qt::Key_Left) {
            if (process) process->write("\x1B[D");
            return true;
        }

        if (!txt.isEmpty()) {
            if (process) process->write(txt.toLocal8Bit());
            return true;
        }
    }
    return QWidget::eventFilter(obj, event);
}

void TerminalPane::readOutput() {
    if (!process || !terminalEdit) return;
    QByteArray data = process->readAllStandardOutput();
    if (data.isEmpty()) return;

    QString text = QString::fromLocal8Bit(data);
    if (text.contains('\b')) {
        static QRegularExpression ansiRegex("\x1B\\[[0-9;]*[a-zA-Z]");
        text.remove(ansiRegex);
        for (int i = 0; i < text.length(); ++i) {
            if (text[i] == '\b') {
                QTextCursor cursor = terminalEdit->textCursor();
                cursor.movePosition(QTextCursor::End);
                cursor.deletePreviousChar();
            } else {
                terminalEdit->insertPlainText(QString(text[i]));
            }
        }
    } else {
        QString html = ansiToHtml(text);
        terminalEdit->moveCursor(QTextCursor::End);
        terminalEdit->appendHtml(html);
    }
    terminalEdit->moveCursor(QTextCursor::End);
}

QString TerminalPane::ansiToHtml(const QString& ansiText) {
    QString html = ansiText;
    html.replace("&", "&amp;");
    html.replace("<", "&lt;");
    html.replace(">", "&gt;");
    html.replace("\r", "");

    QRegularExpression regex("\x1B\\[([0-9;]*)m");
    QRegularExpressionMatchIterator it = regex.globalMatch(html);

    int lastPos = 0;
    QString result;
    QString currentStyle;
    bool inSpan = false;

    while (it.hasNext()) {
        QRegularExpressionMatch match = it.next();
        int pos = match.capturedStart();

        QString textSegment = html.mid(lastPos, pos - lastPos);
        if (inSpan) {
            result += textSegment + "</span>";
            inSpan = false;
        } else {
            result += textSegment;
        }

        QString params = match.captured(1);
        if (params.isEmpty() || params == "0") {
            currentStyle = "";
        } else {
            QStringList codes = params.split(";");
            QString fgColor, bgColor;
            bool bold = false;

            for (const QString& code : codes) {
                int val = code.toInt();
                if (val == 1) {
                    bold = true;
                } else if (val >= 30 && val <= 37) {
                    switch (val) {
                        case 30: fgColor = "#282c34"; break;
                        case 31: fgColor = "#e06c75"; break;
                        case 32: fgColor = "#98c379"; break;
                        case 33: fgColor = "#d19a66"; break;
                        case 34: fgColor = "#61afef"; break;
                        case 35: fgColor = "#c678dd"; break;
                        case 36: fgColor = "#56b6c2"; break;
                        case 37: fgColor = "#abb2bf"; break;
                    }
                } else if (val >= 40 && val <= 47) {
                    switch (val) {
                        case 40: bgColor = "#282c34"; break;
                        case 41: bgColor = "#e06c75"; break;
                        case 42: bgColor = "#98c379"; break;
                        case 43: bgColor = "#d19a66"; break;
                        case 44: bgColor = "#61afef"; break;
                        case 45: bgColor = "#c678dd"; break;
                        case 46: bgColor = "#56b6c2"; break;
                        case 47: bgColor = "#abb2bf"; break;
                    }
                }
            }

            currentStyle = "";
            if (!fgColor.isEmpty()) currentStyle += QString("color: %1;").arg(fgColor);
            if (!bgColor.isEmpty()) currentStyle += QString("background-color: %1;").arg(bgColor);
            if (bold) currentStyle += "font-weight: bold;";
        }

        if (!currentStyle.isEmpty()) {
            result += QString("<span style=\"%1\">").arg(currentStyle);
            inSpan = true;
        }

        lastPos = match.capturedEnd();
    }

    QString remaining = html.mid(lastPos);
    if (inSpan) {
        result += remaining + "</span>";
    } else {
        result += remaining;
    }

    result.replace("\n", "<br>");
    return result;
}

TerminalWidget::TerminalWidget(const QString& shellPath, QWidget* parent)
    : TerminalWidget(shellPath, QStringList(), parent)
{
}

TerminalWidget::TerminalWidget(const QString& shellPath, const QStringList& shellArgs, QWidget* parent)
    : QWidget(parent)
{
    auto* layout = new QVBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);
    rootPane = new TerminalPane(shellPath, shellArgs, nullptr, nullptr, this);
    layout->addWidget(rootPane);
}
