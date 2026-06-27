#include "FileBrowser.hpp"
#include <QVBoxLayout>
#include <QFileInfo>
#include <QDir>
#include <QHeaderView>

FileBrowser::FileBrowser(QWidget* parent) : QWidget(parent) {
    auto* layout = new QVBoxLayout(this);
    model = new QFileSystemModel(this);
    
    tree = new QTreeView(this);
    tree->setModel(model);

    // Improve visibility: Hide metadata columns that crowd the sidebar
    tree->setColumnHidden(1, true); // Size
    tree->setColumnHidden(2, true); // Type
    tree->setColumnHidden(3, true); // Date Modified
    
    // Ensure the file name column takes up the available space
    tree->header()->setSectionResizeMode(0, QHeaderView::Stretch);

    setRootDirectory(QDir::currentPath());

    layout->addWidget(tree);
    connect(tree, &QTreeView::doubleClicked, this, [this](const QModelIndex& idx) {
        QString path = model->filePath(idx);
        if (QFileInfo(path).isFile()) emit fileOpened(path);
    });
}

void FileBrowser::setRootDirectory(const QString& path) {
    model->setRootPath(path);
    tree->setRootIndex(model->index(path));
}
