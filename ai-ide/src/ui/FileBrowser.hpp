#pragma once
#include <QWidget>
#include <QFileSystemModel>
#include <QTreeView>

class FileBrowser : public QWidget {
    Q_OBJECT
public:
    explicit FileBrowser(QWidget* parent = nullptr);

    void setRootDirectory(const QString& path);

signals:
    void fileOpened(const QString& path);
    void rootChanged(const QString& path);
private:
    QFileSystemModel* model;
    QTreeView* tree;
};
