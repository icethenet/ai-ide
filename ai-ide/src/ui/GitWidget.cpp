#include "GitWidget.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QPushButton>
#include <QMessageBox>

GitWidget::GitWidget(QWidget* parent)
    : QWidget(parent), gitProcess(new QProcess(this))
{
    auto* layout = new QVBoxLayout(this);
    layout->setContentsMargins(5, 5, 5, 5);

    auto* toolbar = new QHBoxLayout();
    auto* refreshBtn = new QPushButton("🔄 Refresh", this);
    auto* syncBtn = new QPushButton("🚀 Sync", this);
    
    QString btnStyle = "QPushButton { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 6px; font-family: 'Segoe UI', Arial; }"
                       "QPushButton:hover { background-color: #3e4452; color: #ffffff; }";
    refreshBtn->setStyleSheet(btnStyle);
    syncBtn->setStyleSheet(btnStyle);

    toolbar->addWidget(refreshBtn);
    toolbar->addWidget(syncBtn);
    layout->addLayout(toolbar);

    statusList = new QListWidget(this);
    statusList->setStyleSheet("QListWidget { background-color: #1e1e1e; color: #abb2bf; border: none; font-family: 'Segoe UI', Arial; }"
                              "QListWidget::item { padding: 4px; }");
    layout->addWidget(statusList);

    commitMessageEdit = new QLineEdit(this);
    commitMessageEdit->setPlaceholderText("Commit message...");
    commitMessageEdit->setStyleSheet("QLineEdit { background-color: #1e1e1e; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 6px; font-family: 'Segoe UI', Arial; }");
    layout->addWidget(commitMessageEdit);

    auto* commitBtn = new QPushButton("Commit Staged Changes", this);
    commitBtn->setStyleSheet("QPushButton { background-color: #61afef; color: #1e1e1e; border: none; border-radius: 4px; padding: 8px; font-weight: bold; font-family: 'Segoe UI', Arial; }"
                             "QPushButton:hover { background-color: #528bff; }");
    layout->addWidget(commitBtn);

    connect(refreshBtn, &QPushButton::clicked, this, &GitWidget::refreshStatus);
    connect(syncBtn, &QPushButton::clicked, this, &GitWidget::syncChanges);
    connect(commitBtn, &QPushButton::clicked, this, &GitWidget::commitChanges);
    connect(gitProcess, &QProcess::finished, this, &GitWidget::onProcessFinished);
    connect(gitProcess, &QProcess::errorOccurred, this, [this](QProcess::ProcessError err) {
        statusList->clear();
        auto* item = new QListWidgetItem(statusList);
        item->setText("Git process error (not found on PATH?)");
    });
}

void GitWidget::setRootPath(const QString& path) {
    rootPath = path;
    refreshStatus();
}

void GitWidget::refreshStatus() {
    if (rootPath.isEmpty() || gitProcess->state() != QProcess::NotRunning) return;

    statusList->clear();
    currentMode = "status";
    gitProcess->setWorkingDirectory(rootPath);
    gitProcess->start("git", QStringList() << "status" << "--porcelain");
}

void GitWidget::commitChanges() {
    if (rootPath.isEmpty() || gitProcess->state() != QProcess::NotRunning) return;

    QString msg = commitMessageEdit->text().trimmed();
    if (msg.isEmpty()) {
        QMessageBox::warning(this, "Git Commit", "Please enter a commit message.");
        return;
    }

    filesToStage.clear();
    for (int i = 0; i < statusList->count(); ++i) {
        auto* item = statusList->item(i);
        if (item->checkState() == Qt::Checked) {
            filesToStage.append(item->text().mid(3).trimmed());
        }
    }

    if (filesToStage.isEmpty()) {
        QMessageBox::warning(this, "Git Commit", "No changes selected to stage/commit.");
        return;
    }

    currentMode = "add";
    gitProcess->setWorkingDirectory(rootPath);
    QStringList args;
    args << "add";
    args.append(filesToStage);
    gitProcess->start("git", args);
}

void GitWidget::syncChanges() {
    if (rootPath.isEmpty() || gitProcess->state() != QProcess::NotRunning) return;

    currentMode = "sync";
    gitProcess->setWorkingDirectory(rootPath);
    gitProcess->start("git", QStringList() << "pull" << "--rebase");
}

void GitWidget::onProcessFinished(int exitCode) {
    if (currentMode == "status") {
        if (exitCode == 0) {
            QString out = gitProcess->readAllStandardOutput();
            QStringList lines = out.split("\n", Qt::SkipEmptyParts);
            for (const QString& line : lines) {
                auto* item = new QListWidgetItem(statusList);
                item->setText(line);
                item->setFlags(item->flags() | Qt::ItemIsUserCheckable);
                item->setCheckState(Qt::Checked);
            }
        } else {
            auto* item = new QListWidgetItem(statusList);
            item->setText("Not a git repository (or git not found)");
        }
    } else if (currentMode == "add") {
        if (exitCode == 0) {
            currentMode = "commit";
            QString msg = commitMessageEdit->text().trimmed();
            gitProcess->start("git", QStringList() << "commit" << "-m" << msg);
        } else {
            QMessageBox::critical(this, "Git Add Error", gitProcess->readAllStandardError());
        }
    } else if (currentMode == "commit") {
        commitMessageEdit->clear();
        refreshStatus();
        QMessageBox::information(this, "Git Commit", "Commit completed successfully!");
    } else if (currentMode == "sync") {
        if (exitCode == 0) {
            currentMode = "push";
            gitProcess->start("git", QStringList() << "push");
        } else {
            QMessageBox::critical(this, "Git Sync Error", "Pull failed: " + gitProcess->readAllStandardError());
        }
    } else if (currentMode == "push") {
        refreshStatus();
        if (exitCode == 0) {
            QMessageBox::information(this, "Git Sync", "Push completed successfully! Repository is synchronized.");
        } else {
            QMessageBox::critical(this, "Git Sync Error", "Push failed: " + gitProcess->readAllStandardError());
        }
    }
}
