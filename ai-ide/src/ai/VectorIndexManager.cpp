#include "VectorIndexManager.hpp"
#include "../ui/SettingsManager.hpp"
#include <QDirIterator>
#include <QFile>
#include <QTextStream>
#include <QFileInfo>
#include <QDateTime>
#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QEventLoop>
#include <QJsonObject>
#include <QJsonDocument>
#include <QJsonArray>
#include <QSqlQuery>
#include <QSqlError>
#include <QDir>
#include <QCoreApplication>
#include <cmath>
#include <iostream>

VectorIndexManager& VectorIndexManager::instance() {
    static VectorIndexManager inst;
    return inst;
}

VectorIndexManager::VectorIndexManager() {
    initDb();
}

VectorIndexManager::~VectorIndexManager() {
    stopIndexing();
}

QSqlDatabase VectorIndexManager::getDbForCurrentThread() {
    QString connectionName = "vector_connection";
    if (QThread::currentThread() != qApp->thread()) {
        connectionName = QString("vector_connection_thread_%1").arg(quintptr(QThread::currentThreadId()));
    }
    
    QSqlDatabase threadDb;
    if (QSqlDatabase::contains(connectionName)) {
        threadDb = QSqlDatabase::database(connectionName);
    } else {
        threadDb = QSqlDatabase::addDatabase("QSQLITE", connectionName);
        QDir().mkpath(".antigravity");
        threadDb.setDatabaseName(".antigravity/vector_index.db");
    }
    
    if (!threadDb.isOpen()) {
        if (!threadDb.open()) {
            std::cerr << "[VectorIndex] Failed to open database: " << threadDb.lastError().text().toStdString() << std::endl;
        } else {
            // Enable WAL mode and set busy timeout for multi-threading safety
            QSqlQuery q(threadDb);
            q.exec("PRAGMA journal_mode = WAL;");
            q.exec("PRAGMA busy_timeout = 5000;");
        }
    }
    return threadDb;
}

void VectorIndexManager::initDb() {
    QSqlDatabase db = getDbForCurrentThread();
    QSqlQuery q(db);
    bool ok = q.exec(
        "CREATE TABLE IF NOT EXISTS codebase_embeddings ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  file_path TEXT NOT NULL,"
        "  chunk_index INTEGER NOT NULL,"
        "  chunk_text TEXT NOT NULL,"
        "  start_line INTEGER NOT NULL,"
        "  end_line INTEGER NOT NULL,"
        "  embedding BLOB NOT NULL,"
        "  last_modified INTEGER NOT NULL,"
        "  UNIQUE(file_path, chunk_index)"
        ")"
    );
    if (!ok) {
        std::cerr << "[VectorIndex] Error creating table: " 
                  << q.lastError().text().toStdString() << std::endl;
    }
}

void VectorIndexManager::startIndexing(const QString& rootPath) {
    QMutexLocker locker(&mutex);
    if (m_indexing) return;
    m_indexing = true;

    std::cout << "[VectorIndex] Indexing started in background for path: " << rootPath.toStdString() << std::endl;

    auto* worker = new IndexWorker(rootPath, this);
    connect(worker, &IndexWorker::progress, this, &VectorIndexManager::indexingProgress);
    connect(worker, &IndexWorker::finished, this, [this, worker]() {
        QMutexLocker l(&mutex);
        m_indexing = false;
        worker->deleteLater();
        std::cout << "[VectorIndex] Indexing completed successfully." << std::endl;
        emit indexingFinished();
    });
    worker->start();
}

void VectorIndexManager::stopIndexing() {
    // Handled by worker checks
}

bool VectorIndexManager::isIndexing() const {
    return m_indexing;
}

static float cosineSimilarity(const QVector<float>& a, const QVector<float>& b) {
    if (a.size() != b.size() || a.isEmpty()) return 0.0f;
    float dot = 0.0f;
    float normA = 0.0f;
    float normB = 0.0f;
    for (int i = 0; i < a.size(); ++i) {
        dot += a[i] * b[i];
        normA += a[i] * a[i];
        normB += b[i] * b[i];
    }
    if (normA == 0.0f || normB == 0.0f) return 0.0f;
    return dot / (std::sqrt(normA) * std::sqrt(normB));
}

static QVector<float> queryEmbedding(const QString& text) {
    auto& settings = SettingsManager::instance();
    QString provider = QString::fromStdString(settings.getProviderType());
    
    QString apiUrl;
    QJsonObject json;

    if (provider == "Gemini" || provider == "Antigravity AI" || provider == "Claude") {
        QString key = QString::fromStdString(settings.getGeminiApiKey());
        if (key.isEmpty()) key = QString::fromStdString(settings.getAntigravityApiKey());
        if (key.isEmpty()) key = QString::fromStdString(settings.getClaudeApiKey());

        apiUrl = "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-2:embedContent?key=" + key;
        
        QJsonObject contentPart;
        contentPart["text"] = text;
        QJsonArray partsArray;
        partsArray.append(contentPart);
        QJsonObject contentObj;
        contentObj["parts"] = partsArray;

        json["model"] = "models/gemini-embedding-2";
        json["content"] = contentObj;
    } else {
        QString endpoint = QString::fromStdString(settings.getOllamaEndpoint());
        if (endpoint.isEmpty()) endpoint = "http://localhost:11434";
        apiUrl = endpoint + "/api/embeddings";
        
        json["model"] = "nomic-embed-text";
        json["prompt"] = text;
    }

    QNetworkAccessManager manager;
    QNetworkRequest request{QUrl(apiUrl)};
    request.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");

    QNetworkReply* reply = manager.post(request, QJsonDocument(json).toJson());
    QEventLoop loop;
    QObject::connect(reply, &QNetworkReply::finished, &loop, &QEventLoop::quit);
    loop.exec();

    QVector<float> vec;
    if (reply->error() == QNetworkReply::NoError) {
        QJsonDocument resDoc = QJsonDocument::fromJson(reply->readAll());
        QJsonObject resObj = resDoc.object();
        
        if (provider == "Gemini" || provider == "Antigravity AI" || provider == "Claude") {
            if (resObj.contains("embedding")) {
                QJsonArray values = resObj["embedding"].toObject()["values"].toArray();
                for (const auto& v : values) vec.append(v.toDouble());
            }
        } else {
            if (resObj.contains("embedding")) {
                QJsonArray values = resObj["embedding"].toArray();
                for (const auto& v : values) vec.append(v.toDouble());
            }
        }
    } else {
        std::cerr << "[VectorIndex] Network error: " << reply->errorString().toStdString() << " (Code: " << reply->error() << ")" << std::endl;
        std::cerr << "[VectorIndex] Error payload: " << reply->readAll().toStdString() << std::endl;
    }
    reply->deleteLater();
    return vec;
}

QVector<SearchResult> VectorIndexManager::search(const QString& queryText, float threshold) {
    QVector<SearchResult> results;
    
    QVector<float> qVec = queryEmbedding(queryText);
    if (qVec.isEmpty()) {
        std::cerr << "[VectorIndex] Failed to get query embedding" << std::endl;
        return results;
    }

    QSqlDatabase db = getDbForCurrentThread();
    QSqlQuery query(db);
    query.exec("SELECT file_path, start_line, chunk_text, embedding FROM codebase_embeddings");
    while (query.next()) {
        QString filePath = query.value(0).toString();
        int startLine = query.value(1).toInt();
        QString chunkText = query.value(2).toString();
        QByteArray blob = query.value(3).toByteArray();

        QVector<float> recordVec;
        recordVec.resize(blob.size() / sizeof(float));
        memcpy(recordVec.data(), blob.constData(), blob.size());

        float score = cosineSimilarity(qVec, recordVec);
        if (score >= threshold) {
            SearchResult r;
            r.filePath = filePath;
            r.lineNumber = startLine;
            r.lineContent = chunkText.left(100).replace("\n", " ");
            r.score = score;
            results.append(r);
        }
    }

    std::sort(results.begin(), results.end(), [](const SearchResult& a, const SearchResult& b) {
        return a.score > b.score;
    });

    return results;
}

IndexWorker::IndexWorker(const QString& rootPath, QObject* parent)
    : QThread(parent), root(rootPath) {}

void IndexWorker::run() {
    if (root.isEmpty()) return;

    QSqlDatabase threadDb = VectorIndexManager::instance().getDbForCurrentThread();

    QStringList files;
    QDirIterator it(root, QDir::Files, QDirIterator::Subdirectories);
    while (it.hasNext()) {
        QString path = it.next();
        QString cleanPath = QDir::cleanPath(path);
        if (cleanPath.contains("/.git/") || cleanPath.contains("/build/") || cleanPath.contains("/.agents/") || cleanPath.contains("/.antigravity/")) {
            continue;
        }
        QFileInfo info(path);
        QString ext = info.suffix().toLower();
        if (ext == "cpp" || ext == "hpp" || ext == "h" || ext == "py" || ext == "md" || ext == "txt") {
            files.append(cleanPath);
        }
    }

    int total = files.size();
    for (int i = 0; i < total; ++i) {
        if (isInterruptionRequested()) break;
        emit progress(i + 1, total);
        processFile(files[i], threadDb);
    }
}

void IndexWorker::processFile(const QString& path, QSqlDatabase& threadDb) {
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) return;

    QFileInfo info(path);
    qint64 lastMod = info.lastModified().toSecsSinceEpoch();

    QSqlQuery check(threadDb);
    check.prepare("SELECT last_modified FROM codebase_embeddings WHERE file_path = :path LIMIT 1");
    check.bindValue(":path", path);
    check.exec();
    if (check.next()) {
        qint64 dbMod = check.value(0).toLongLong();
        if (dbMod == lastMod) {
            return; 
        }
        
        QSqlQuery del(threadDb);
        del.prepare("DELETE FROM codebase_embeddings WHERE file_path = :path");
        del.bindValue(":path", path);
        del.exec();
    }

    QTextStream in(&file);
    QString text = in.readAll();
    file.close();

    QStringList lines = text.split("\n");
    int chunkLineSize = 25;
    int chunkOverlap = 5;

    int chunkIndex = 0;
    for (int start = 0; start < lines.size(); start += (chunkLineSize - chunkOverlap)) {
        if (isInterruptionRequested()) break;

        int end = qMin(start + chunkLineSize, lines.size());
        QStringList chunkLines = lines.mid(start, end - start);
        QString chunkText = chunkLines.join("\n").trimmed();
        if (chunkText.isEmpty()) continue;

        QVector<float> vec = getEmbedding(chunkText);
        if (vec.isEmpty()) continue; 

        QByteArray blob;
        blob.resize(vec.size() * sizeof(float));
        memcpy(blob.data(), vec.constData(), blob.size());

        QSqlQuery insert(threadDb);
        insert.prepare(
            "INSERT OR REPLACE INTO codebase_embeddings "
            "(file_path, chunk_index, chunk_text, start_line, end_line, embedding, last_modified) "
            "VALUES (:path, :idx, :txt, :start, :end, :embed, :mod)"
        );
        insert.bindValue(":path", path);
        insert.bindValue(":idx", chunkIndex++);
        insert.bindValue(":txt", chunkText);
        insert.bindValue(":start", start + 1);
        insert.bindValue(":end", end);
        insert.bindValue(":embed", blob);
        insert.bindValue(":mod", lastMod);
        insert.exec();
    }
}

QVector<float> IndexWorker::getEmbedding(const QString& text) {
    return queryEmbedding(text);
}
