#pragma once
#include <QWidget>
#include <QFileSystemModel>
#include <QTreeView>
#include <QStringList>
#include <QPushButton>
#include <QModelIndex>

class FileBrowser : public QWidget {
    Q_OBJECT
public:
    explicit FileBrowser(QWidget* parent = nullptr);

    void setRootDirectory(const QString& path);
    QString rootPath() const { return currentRootPath; }

signals:
    void fileOpened(const QString& path);
    void rootChanged(const QString& path);

private slots:
    void goBack();
    void goForward();
    void goUp();
    void refreshView();
    void createFolder();
    void createFile();
    void showContextMenu(const QPoint& pos);
    void renameItem();
    void deleteItem();

private:
    void navigateTo(const QString& path, bool recordHistory = true);
    void updateButtonStates();
    QString getSelectedPath() const;

    QFileSystemModel* model;
    QTreeView* tree;

    // Navigation buttons
    QPushButton* backBtn;
    QPushButton* forwardBtn;
    QPushButton* upBtn;
    QPushButton* refreshBtn;
    QPushButton* newFolderBtn;
    QPushButton* newFileBtn;

    // History state
    QString currentRootPath;
    QStringList historyBack;
    QStringList historyForward;
};
