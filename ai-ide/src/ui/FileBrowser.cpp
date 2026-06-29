#include "FileBrowser.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QFileInfo>
#include <QDir>
#include <QHeaderView>
#include <QMenu>
#include <QAction>
#include <QInputDialog>
#include <QMessageBox>

FileBrowser::FileBrowser(QWidget* parent) : QWidget(parent) {
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);
    mainLayout->setSpacing(2);

    // Toolbar Layout
    auto* toolbar = new QWidget(this);
    toolbar->setStyleSheet(
        "QWidget { background-color: #21252b; border-bottom: 1px solid #181a1f; }"
        "QPushButton { background-color: transparent; border: none; color: #abb2bf; font-size: 14px; font-weight: bold; padding: 4px; border-radius: 4px; min-width: 24px; min-height: 24px; }"
        "QPushButton:hover { background-color: #2c313c; color: #ffffff; }"
        "QPushButton:disabled { color: #5c6370; background-color: transparent; }"
    );

    auto* tbLayout = new QHBoxLayout(toolbar);
    tbLayout->setContentsMargins(4, 4, 4, 4);
    tbLayout->setSpacing(4);

    backBtn = new QPushButton("←", this);
    backBtn->setToolTip("Back");
    
    forwardBtn = new QPushButton("→", this);
    forwardBtn->setToolTip("Forward");

    upBtn = new QPushButton("↑", this);
    upBtn->setToolTip("Up");

    refreshBtn = new QPushButton("⟳", this);
    refreshBtn->setToolTip("Refresh");

    newFolderBtn = new QPushButton("📁+", this);
    newFolderBtn->setToolTip("New Folder");

    newFileBtn = new QPushButton("📄+", this);
    newFileBtn->setToolTip("New File");

    tbLayout->addWidget(backBtn);
    tbLayout->addWidget(forwardBtn);
    tbLayout->addWidget(upBtn);
    tbLayout->addWidget(refreshBtn);
    tbLayout->addStretch();
    tbLayout->addWidget(newFolderBtn);
    tbLayout->addWidget(newFileBtn);

    mainLayout->addWidget(toolbar);

    model = new QFileSystemModel(this);
    model->setFilter(QDir::AllDirs | QDir::Files | QDir::NoDotAndDotDot);
    
    tree = new QTreeView(this);
    tree->setModel(model);
    tree->setContextMenuPolicy(Qt::CustomContextMenu);

    // Improve visibility: Hide metadata columns that crowd the sidebar
    tree->setColumnHidden(1, true); // Size
    tree->setColumnHidden(2, true); // Type
    tree->setColumnHidden(3, true); // Date Modified
    tree->header()->setSectionResizeMode(0, QHeaderView::Stretch);

    mainLayout->addWidget(tree);

    // Initial state
    currentRootPath = QDir::currentPath();
    setRootDirectory(currentRootPath);

    // Connections
    connect(tree, &QTreeView::doubleClicked, this, [this](const QModelIndex& idx) {
        QString path = model->filePath(idx);
        if (QFileInfo(path).isFile()) {
            emit fileOpened(path);
        } else if (QFileInfo(path).isDir()) {
            navigateTo(path);
        }
    });

    connect(tree, &QTreeView::customContextMenuRequested, this, &FileBrowser::showContextMenu);

    connect(backBtn, &QPushButton::clicked, this, &FileBrowser::goBack);
    connect(forwardBtn, &QPushButton::clicked, this, &FileBrowser::goForward);
    connect(upBtn, &QPushButton::clicked, this, &FileBrowser::goUp);
    connect(refreshBtn, &QPushButton::clicked, this, &FileBrowser::refreshView);
    connect(newFolderBtn, &QPushButton::clicked, this, &FileBrowser::createFolder);
    connect(newFileBtn, &QPushButton::clicked, this, &FileBrowser::createFile);

    updateButtonStates();
}

void FileBrowser::setRootDirectory(const QString& path) {
    navigateTo(path, false);
}

void FileBrowser::navigateTo(const QString& path, bool recordHistory) {
    if (path.isEmpty() || !QFileInfo(path).isDir()) return;

    QString cleanPath = QDir::cleanPath(path);
    if (recordHistory && !currentRootPath.isEmpty() && currentRootPath != cleanPath) {
        historyBack.push_back(currentRootPath);
        historyForward.clear();
    }

    currentRootPath = cleanPath;
    tree->setRootIndex(model->setRootPath(cleanPath));
    updateButtonStates();
    emit rootChanged(cleanPath);
}

void FileBrowser::goBack() {
    if (!historyBack.isEmpty()) {
        QString prev = historyBack.takeLast();
        historyForward.push_back(currentRootPath);
        navigateTo(prev, false);
    }
}

void FileBrowser::goForward() {
    if (!historyForward.isEmpty()) {
        QString nextPath = historyForward.takeLast();
        historyBack.push_back(currentRootPath);
        navigateTo(nextPath, false);
    }
}

void FileBrowser::goUp() {
    QDir dir(currentRootPath);
    if (dir.cdUp()) {
        navigateTo(dir.absolutePath());
    }
}

void FileBrowser::refreshView() {
    model->setRootPath("");
    model->setRootPath(currentRootPath);
    tree->setRootIndex(model->index(currentRootPath));
}

void FileBrowser::updateButtonStates() {
    backBtn->setEnabled(!historyBack.isEmpty());
    forwardBtn->setEnabled(!historyForward.isEmpty());
    
    QDir dir(currentRootPath);
    upBtn->setEnabled(dir.absolutePath() != dir.rootPath());
}

QString FileBrowser::getSelectedPath() const {
    QModelIndex idx = tree->currentIndex();
    if (idx.isValid()) {
        return model->filePath(idx);
    }
    return currentRootPath;
}

void FileBrowser::createFolder() {
    QString targetDir = getSelectedPath();
    if (QFileInfo(targetDir).isFile()) {
        targetDir = QFileInfo(targetDir).absolutePath();
    }

    bool ok;
    QString name = QInputDialog::getText(this, "Create Folder",
                                         "Folder Name:", QLineEdit::Normal,
                                         "", &ok);
    if (ok && !name.trimmed().isEmpty()) {
        QDir dir(targetDir);
        if (dir.mkdir(name.trimmed())) {
            refreshView();
        } else {
            QMessageBox::warning(this, "Error", "Failed to create directory. It may already exist or you lack permissions.");
        }
    }
}

void FileBrowser::createFile() {
    QString targetDir = getSelectedPath();
    if (QFileInfo(targetDir).isFile()) {
        targetDir = QFileInfo(targetDir).absolutePath();
    }

    bool ok;
    QString name = QInputDialog::getText(this, "Create File",
                                         "File Name:", QLineEdit::Normal,
                                         "", &ok);
    if (ok && !name.trimmed().isEmpty()) {
        QString filePath = QDir(targetDir).filePath(name.trimmed());
        QFile file(filePath);
        if (file.open(QIODevice::WriteOnly)) {
            file.close();
            refreshView();
            emit fileOpened(filePath);
        } else {
            QMessageBox::warning(this, "Error", "Failed to create file.");
        }
    }
}

void FileBrowser::showContextMenu(const QPoint& pos) {
    QModelIndex idx = tree->indexAt(pos);
    
    QMenu menu(this);
    menu.setStyleSheet(
        "QMenu { background-color: #21252b; color: #abb2bf; border: 1px solid #181a1f; }"
        "QMenu::item { padding: 6px 20px; }"
        "QMenu::item:selected { background-color: #3e4452; color: #ffffff; }"
    );

    QAction* newFileAct = menu.addAction("New File...");
    QAction* newFolderAct = menu.addAction("New Folder...");
    
    QAction* renameAct = nullptr;
    QAction* deleteAct = nullptr;

    if (idx.isValid()) {
        menu.addSeparator();
        renameAct = menu.addAction("Rename...");
        deleteAct = menu.addAction("Delete");
    }

    menu.addSeparator();
    QAction* refreshAct = menu.addAction("Refresh");

    QAction* selectedAct = menu.exec(tree->viewport()->mapToGlobal(pos));
    if (!selectedAct) return;

    if (selectedAct == newFileAct) {
        createFile();
    } else if (selectedAct == newFolderAct) {
        createFolder();
    } else if (selectedAct == renameAct) {
        renameItem();
    } else if (selectedAct == deleteAct) {
        deleteItem();
    } else if (selectedAct == refreshAct) {
        refreshView();
    }
}

void FileBrowser::renameItem() {
    QModelIndex idx = tree->currentIndex();
    if (!idx.isValid()) return;

    QString oldPath = model->filePath(idx);
    QFileInfo info(oldPath);

    bool ok;
    QString newName = QInputDialog::getText(this, "Rename Item",
                                            "New Name:", QLineEdit::Normal,
                                            info.fileName(), &ok);
    if (ok && !newName.trimmed().isEmpty() && newName != info.fileName()) {
        QString newPath = info.absoluteDir().filePath(newName.trimmed());
        if (QFile::rename(oldPath, newPath)) {
            refreshView();
        } else {
            QMessageBox::warning(this, "Error", "Failed to rename item.");
        }
    }
}

void FileBrowser::deleteItem() {
    QModelIndex idx = tree->currentIndex();
    if (!idx.isValid()) return;

    QString path = model->filePath(idx);
    QFileInfo info(path);

    QMessageBox::StandardButton reply = QMessageBox::question(
        this, "Confirm Delete",
        QString("Are you sure you want to delete '%1'? This action is permanent.").arg(info.fileName()),
        QMessageBox::Yes | QMessageBox::No
    );

    if (reply != QMessageBox::Yes) return;

    bool success = false;
    if (info.isDir()) {
        success = QDir(path).removeRecursively();
    } else {
        success = QFile::remove(path);
    }
    if (success) {
        refreshView();
    } else {
        QMessageBox::warning(this, "Error", "Failed to delete item.");
    }
}
