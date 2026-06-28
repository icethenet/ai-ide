#pragma once
#include <QObject>
#include <QThread>
#include <QSqlDatabase>
#include <QVector>
#include <QStringList>
#include <QMutex>

struct SearchResult {
    QString filePath;
    int lineNumber;
    QString lineContent;
    float score;
};

struct IndexStats {
    int chunks;
    int files;
};

class VectorIndexManager : public QObject {
    Q_OBJECT
public:
    static VectorIndexManager& instance();

    void startIndexing(const QString& rootPath);
    void stopIndexing();
    bool isIndexing() const;

    QVector<SearchResult> search(const QString& queryText, float threshold = 0.5f);
    
    QSqlDatabase getDbForCurrentThread();
    
    IndexStats getIndexStats();
    QString getLastError();
    void setLastError(const QString& err);
    void clearLastError();

signals:
    void indexingProgress(int current, int total);
    void indexingFinished();

private:
    VectorIndexManager();
    ~VectorIndexManager();

    void initDb();
    bool m_indexing = false;
    QMutex mutex;
    QString lastError;
};

class IndexWorker : public QThread {
    Q_OBJECT
public:
    IndexWorker(const QString& rootPath, QObject* parent = nullptr);
signals:
    void progress(int current, int total);
protected:
    void run() override;
private:
    QString root;
    void processFile(const QString& path, QSqlDatabase& threadDb);
    QVector<float> getEmbedding(const QString& text);
};
