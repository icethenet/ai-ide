#pragma once
#include <QWidget>
#include <QLineEdit>
#include <QTreeWidget>
#include <QThread>

class SearchThread : public QThread {
    Q_OBJECT
public:
    SearchThread(const QString& rootPath, const QString& query, QObject* parent = nullptr);
protected:
    void run() override;
signals:
    void matchFound(const QString& filePath, int lineNumber, const QString& lineContent);
private:
    QString root;
    QString q;
};

class SearchWidget : public QWidget {
    Q_OBJECT
public:
    explicit SearchWidget(QWidget* parent = nullptr);
    void setRootPath(const QString& path);

signals:
    void matchActivated(const QString& filePath, int lineNumber);

private slots:
    void startSearch();
    void addMatch(const QString& filePath, int lineNumber, const QString& lineContent);
    void onDoubleClicked(QTreeWidgetItem* item, int column);

private:
    QString rootPath;
    QLineEdit* searchEdit;
    QTreeWidget* resultsTree;
    SearchThread* activeThread;
};
