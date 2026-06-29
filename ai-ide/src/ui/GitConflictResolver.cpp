#include "GitConflictResolver.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QFile>
#include <QTextStream>
#include <QMessageBox>
#include <QFileInfo>
#include <QProcess>

GitConflictResolver::GitConflictResolver(const QString& path, QWidget* parent)
    : QWidget(parent), filePath(path)
{
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(8, 8, 8, 8);
    mainLayout->setSpacing(8);

    titleLabel = new QLabel(QString("Resolve Conflict: %1").arg(QFileInfo(path).fileName()), this);
    titleLabel->setStyleSheet("QLabel { color: #e06c75; font-family: 'Segoe UI', Arial; font-size: 14px; font-weight: bold; }");
    mainLayout->addWidget(titleLabel);

    // Three pane layout
    auto* paneLayout = new QHBoxLayout();
    
    // Left Pane (Local)
    auto* leftLayout = new QVBoxLayout();
    auto* leftLabel = new QLabel("Current Change (Local - HEAD)", this);
    leftLabel->setStyleSheet("color: #61afef; font-weight: bold;");
    leftEdit = new QPlainTextEdit(this);
    leftEdit->setReadOnly(true);
    leftEdit->setStyleSheet("QPlainTextEdit { background-color: #1e1e1e; color: #abb2bf; font-family: 'Consolas', monospace; }");
    auto* acceptLocalBtn = new QPushButton("Accept Local Change", this);
    acceptLocalBtn->setStyleSheet("QPushButton { background-color: #2c313c; color: #61afef; border: 1px solid #61afef; border-radius: 4px; padding: 6px; font-weight: bold; }"
                                  "QPushButton:hover { background-color: #61afef; color: #1e1e1e; }");
    leftLayout->addWidget(leftLabel);
    leftLayout->addWidget(leftEdit);
    leftLayout->addWidget(acceptLocalBtn);

    // Center Pane (Merged Result)
    auto* centerLayout = new QVBoxLayout();
    auto* centerLabel = new QLabel("Merged Result (Editable)", this);
    centerLabel->setStyleSheet("color: #98c379; font-weight: bold;");
    centerEdit = new QPlainTextEdit(this);
    centerEdit->setStyleSheet("QPlainTextEdit { background-color: #21252b; color: #ffffff; font-family: 'Consolas', monospace; border: 1px solid #3e4452; }");
    auto* acceptBothBtn = new QPushButton("Accept Both (Local + Remote)", this);
    acceptBothBtn->setStyleSheet("QPushButton { background-color: #2c313c; color: #98c379; border: 1px solid #98c379; border-radius: 4px; padding: 6px; font-weight: bold; }"
                                  "QPushButton:hover { background-color: #98c379; color: #1e1e1e; }");
    centerLayout->addWidget(centerLabel);
    centerLayout->addWidget(centerEdit);
    centerLayout->addWidget(acceptBothBtn);

    // Right Pane (Remote)
    auto* rightLayout = new QVBoxLayout();
    auto* rightLabel = new QLabel("Incoming Change (Remote)", this);
    rightLabel->setStyleSheet("color: #d19a66; font-weight: bold;");
    rightEdit = new QPlainTextEdit(this);
    rightEdit->setReadOnly(true);
    rightEdit->setStyleSheet("QPlainTextEdit { background-color: #1e1e1e; color: #abb2bf; font-family: 'Consolas', monospace; }");
    auto* acceptRemoteBtn = new QPushButton("Accept Remote Change", this);
    acceptRemoteBtn->setStyleSheet("QPushButton { background-color: #2c313c; color: #d19a66; border: 1px solid #d19a66; border-radius: 4px; padding: 6px; font-weight: bold; }"
                                   "QPushButton:hover { background-color: #d19a66; color: #1e1e1e; }");
    rightLayout->addWidget(rightLabel);
    rightLayout->addWidget(rightEdit);
    rightLayout->addWidget(acceptRemoteBtn);

    paneLayout->addLayout(leftLayout);
    paneLayout->addLayout(centerLayout);
    paneLayout->addLayout(rightLayout);
    mainLayout->addLayout(paneLayout);

    // Action button at the bottom
    auto* saveBtn = new QPushButton("Save & Mark Resolved", this);
    saveBtn->setStyleSheet("QPushButton { background-color: #98c379; color: #1e1e1e; border: none; border-radius: 4px; padding: 10px; font-weight: bold; font-size: 13px; }"
                           "QPushButton:hover { background-color: #a6db87; }");
    mainLayout->addWidget(saveBtn);

    connect(acceptLocalBtn, &QPushButton::clicked, this, &GitConflictResolver::acceptLocal);
    connect(acceptRemoteBtn, &QPushButton::clicked, this, &GitConflictResolver::acceptRemote);
    connect(acceptBothBtn, &QPushButton::clicked, this, &GitConflictResolver::acceptBoth);
    connect(saveBtn, &QPushButton::clicked, this, &GitConflictResolver::saveAndResolve);

    parseConflictData();
}

bool GitConflictResolver::parseConflictData() {
    QFile file(filePath);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) return false;

    QTextStream in(&file);
    QStringList localLines;
    QStringList remoteLines;
    QStringList rawLines;

    bool inConflict = false;
    bool inRemote = false;

    while (!in.atEnd()) {
        QString line = in.readLine();
        rawLines.append(line);

        if (line.startsWith("<<<<<<<")) {
            inConflict = true;
            inRemote = false;
            continue;
        } else if (line.startsWith("=======")) {
            inRemote = true;
            continue;
        } else if (line.startsWith(">>>>>>>")) {
            inConflict = false;
            inRemote = false;
            continue;
        }

        if (inConflict) {
            if (inRemote) {
                remoteLines.append(line);
            } else {
                localLines.append(line);
            }
        } else {
            localLines.append(line);
            remoteLines.append(line);
        }
    }
    file.close();

    localContent = localLines.join('\n');
    remoteContent = remoteLines.join('\n');
    rawConflictContent = rawLines.join('\n');

    leftEdit->setPlainText(localContent);
    rightEdit->setPlainText(remoteContent);
    centerEdit->setPlainText(rawConflictContent);
    return true;
}

void GitConflictResolver::acceptLocal() {
    centerEdit->setPlainText(localContent);
}

void GitConflictResolver::acceptRemote() {
    centerEdit->setPlainText(remoteContent);
}

void GitConflictResolver::acceptBoth() {
    centerEdit->setPlainText(localContent + "\n" + remoteContent);
}

void GitConflictResolver::saveAndResolve() {
    QFile file(filePath);
    if (!file.open(QIODevice::WriteOnly | QIODevice::Text)) {
        QMessageBox::critical(this, "Save Error", "Could not open file for writing.");
        return;
    }
    QTextStream out(&file);
    out << centerEdit->toPlainText();
    file.close();

    QProcess* gitAdd = new QProcess(this);
    gitAdd->setWorkingDirectory(QFileInfo(filePath).absolutePath());
    gitAdd->start("git", QStringList() << "add" << filePath);
    gitAdd->waitForFinished(2000);
    gitAdd->deleteLater();

    emit resolved(filePath);
}
