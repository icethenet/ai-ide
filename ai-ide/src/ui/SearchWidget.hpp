#pragma once
#include <QWidget>
#include <QLineEdit>
#include <QTreeWidget>
#include <QThread>
#include <QCheckBox>
#include <QLabel>
#include <QPushButton>
#include "../ai/VectorIndexManager.hpp"

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

class SemanticSearchThread : public QThread {
    Q_OBJECT
public:
    SemanticSearchThread(const QString& query, QObject* parent = nullptr)
        : QThread(parent), q(query) {}
signals:
    void searchCompleted(const QVector<SearchResult>& results);
protected:
    void run() override {
        auto results = VectorIndexManager::instance().search(q, 0.4f);
        emit searchCompleted(results);
    }
private:
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
    
    void runSemanticSearch();
    void renderSemanticResults(const QVector<SearchResult>& results);
    void updateProgress(int current, int total);
    void indexingFinished();
    void startIndexing();

private:
    QString rootPath;
    QLineEdit* searchEdit;
    QTreeWidget* resultsTree;
    SearchThread* activeThread;
    SemanticSearchThread* activeSemanticThread = nullptr;
    
    QCheckBox* semanticSearchCheckbox;
    QLabel* progressLabel;
    QPushButton* indexBtn;
    QPushButton* searchBtn;
};
