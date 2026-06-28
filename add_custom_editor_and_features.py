import os
import shutil

ROOT = "ai-ide"

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# Ensure src directory exists and copy the logo to it
os.makedirs(f"{ROOT}/src", exist_ok=True)
shutil.copy(os.path.join(os.path.dirname(__file__), "idelogo.png"), f"{ROOT}/src/idelogo.png")

# Create the Qt resource file
write(f"{ROOT}/src/resources.qrc", r"""<!DOCTYPE RCC><RCC version="1.0">
<qresource>
    <file>idelogo.png</file>
</qresource>
</RCC>
""")

# ---------------------------------------------------------
# AI Providers (Gemini, Claude & Antigravity)
# ---------------------------------------------------------
write(f"{ROOT}/src/ai/GeminiProvider.hpp", r"""#pragma once
#include "AIProvider.hpp"
#include <string>

class GeminiProvider : public AIProvider {
public:
    GeminiProvider(const std::string& apiKey, const std::string& customEndpoint = "");
    AIResponse send(const AIRequest& req) override;

private:
    std::string apiKey;
    std::string endpoint;
};
""")

write(f"{ROOT}/src/ai/GeminiProvider.cpp", r"""#include "GeminiProvider.hpp"
#include <iostream>
#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QEventLoop>
#include <QJsonObject>
#include <QJsonDocument>
#include <QJsonArray>
#include <QUrl>
#include "../ui/SettingsManager.hpp"

GeminiProvider::GeminiProvider(const std::string& key, const std::string& ep)
    : apiKey(key), endpoint(ep)
{
    if (endpoint.empty()) {
        endpoint = "https://generativelanguage.googleapis.com";
    }
}

AIResponse GeminiProvider::send(const AIRequest& req) {
    if (apiKey.empty()) {
        return {"Error: Gemini API key not configured. Please set API key in settings."};
    }

    QNetworkAccessManager manager;
    QString currentModel = QString::fromStdString(SettingsManager::instance().getModel());
    QString modelName = (currentModel.isEmpty() || currentModel == "antigravity-preview-05-2026") ? "gemini-2.5-pro" : currentModel;

    QString apiUrl = QString::fromStdString(
        endpoint + "/v1beta/models/" + modelName.toStdString() + ":generateContent?key=" + apiKey
    );
    
    QNetworkRequest request{QUrl(apiUrl)};
    request.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");

    QJsonObject content;
    content["role"] = "user";
    
    QJsonObject part;
    part["text"] = QString::fromStdString(req.prompt);
    
    QJsonArray parts;
    parts.append(part);
    content["parts"] = parts;
    
    QJsonArray contents;
    contents.append(content);
    
    QJsonObject json;
    json["contents"] = contents;
    
    QJsonObject generationConfig;
    generationConfig["temperature"] = 0.7;
    generationConfig["topP"] = 0.95;
    generationConfig["maxOutputTokens"] = 8192;
    json["generationConfig"] = generationConfig;

    QNetworkReply* reply = manager.post(request, QJsonDocument(json).toJson());

    QEventLoop loop;
    QObject::connect(reply, &QNetworkReply::finished, &loop, &QEventLoop::quit);
    loop.exec();

    AIResponse res;
    if (reply->error() == QNetworkReply::NoError) {
        QJsonDocument resDoc = QJsonDocument::fromJson(reply->readAll());
        QJsonObject obj = resDoc.object();
        
        if (obj.contains("candidates")) {
            QJsonArray candidates = obj["candidates"].toArray();
            if (!candidates.isEmpty()) {
                QJsonObject candidate = candidates[0].toObject();
                if (candidate.contains("content")) {
                    QJsonObject contentObj = candidate["content"].toObject();
                    if (contentObj.contains("parts")) {
                        QJsonArray parts = contentObj["parts"].toArray();
                        if (!parts.isEmpty()) {
                            QJsonObject partObj = parts[0].toObject();
                            if (partObj.contains("text")) {
                                res.text = partObj["text"].toString().toStdString();
                                reply->deleteLater();
                                return res;
                            }
                        }
                    }
                }
            }
        }
        
        if (obj.contains("error")) {
            QJsonObject error = obj["error"].toObject();
            res.text = "Error: " + error["message"].toString().toStdString();
        } else {
            res.text = "Error: Invalid response format from Gemini API";
        }
    } else {
        res.text = "Error: " + reply->errorString().toStdString();
    }

    reply->deleteLater();
    return res;
}
""")
write(f"{ROOT}/src/ai/ClaudeProvider.hpp", r"""#pragma once
#include "AIProvider.hpp"
#include <string>

class ClaudeProvider : public AIProvider {
public:
    ClaudeProvider(const std::string& apiKey, const std::string& customEndpoint = "");
    AIResponse send(const AIRequest& req) override;

private:
    std::string apiKey;
    std::string endpoint;
};
""")

write(f"{ROOT}/src/ai/ClaudeProvider.cpp", r"""#include "ClaudeProvider.hpp"
#include <iostream>
#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QEventLoop>
#include <QJsonObject>
#include <QJsonDocument>
#include <QJsonArray>
#include <QUrl>
#include "../ui/SettingsManager.hpp"

ClaudeProvider::ClaudeProvider(const std::string& key, const std::string& ep)
    : apiKey(key), endpoint(ep)
{
    if (endpoint.empty()) {
        endpoint = "https://api.anthropic.com";
    }
}

AIResponse ClaudeProvider::send(const AIRequest& req) {
    if (apiKey.empty()) {
        return {"Error: Claude API key not configured. Please set API key in settings."};
    }

    QNetworkAccessManager manager;
    QNetworkRequest request(QUrl(QString::fromStdString(endpoint + "/v1/messages")));
    request.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");
    request.setRawHeader("x-api-key", QByteArray::fromStdString(apiKey));
    request.setRawHeader("anthropic-version", "2023-06-01");

    QJsonObject message;
    message["role"] = "user";
    message["content"] = QString::fromStdString(req.prompt);

    QJsonArray messages;
    messages.append(message);

    QJsonObject json;
    QString currentModel = QString::fromStdString(SettingsManager::instance().getModel());
    json["model"] = currentModel.isEmpty() ? "claude-3-5-sonnet-20241022" : currentModel;
    json["max_tokens"] = 4096;
    json["messages"] = messages;
    json["system"] = "You are a world-class software engineer and IDE coding assistant. "
                     "Write complete, correct, and clean code inside markdown code blocks.";

    QNetworkReply* reply = manager.post(request, QJsonDocument(json).toJson());

    QEventLoop loop;
    QObject::connect(reply, &QNetworkReply::finished, &loop, &QEventLoop::quit);
    loop.exec();

    AIResponse res;
    if (reply->error() == QNetworkReply::NoError) {
        QJsonDocument resDoc = QJsonDocument::fromJson(reply->readAll());
        QJsonObject obj = resDoc.object();
        if (obj.contains("content")) {
            QJsonArray contentArray = obj["content"].toArray();
            if (!contentArray.isEmpty()) {
                QJsonObject contentObj = contentArray[0].toObject();
                if (contentObj.contains("text")) {
                    res.text = contentObj["text"].toString().toStdString();
                    reply->deleteLater();
                    return res;
                }
            }
        }
        res.text = "Error: Invalid response format from Claude API";
    } else {
        res.text = "Error: " + reply->errorString().toStdString();
    }

    reply->deleteLater();
    return res;
}
""")

write(f"{ROOT}/src/ai/AntigravityProvider.hpp", r"""#pragma once
#include "AIProvider.hpp"
#include <string>

class AntigravityProvider : public AIProvider {
public:
    AntigravityProvider(const std::string& apiKey, const std::string& customEndpoint = "");
    AIResponse send(const AIRequest& req) override;

private:
    std::string apiKey;
    std::string endpoint;
};
""")

write(f"{ROOT}/src/ai/AntigravityProvider.cpp", r"""#include "AntigravityProvider.hpp"
#include <iostream>
#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QEventLoop>
#include <QJsonObject>
#include <QJsonDocument>
#include <QJsonArray>
#include <QUrl>
#include "../ui/SettingsManager.hpp"

AntigravityProvider::AntigravityProvider(const std::string& key, const std::string& ep)
    : apiKey(key), endpoint(ep)
{
    if (endpoint.empty()) {
        endpoint = "https://generativelanguage.googleapis.com";
    }
}

AIResponse AntigravityProvider::send(const AIRequest& req) {
    if (apiKey.empty()) {
        return {"Error: Antigravity API key not configured. Please set API key in settings."};
    }

    QNetworkAccessManager manager;
    QString currentModel = QString::fromStdString(SettingsManager::instance().getModel());
    QString modelName = (currentModel.isEmpty() || currentModel == "antigravity-preview-05-2026") ? "gemini-2.5-flash" : currentModel;

    QString apiUrl = QString::fromStdString(endpoint + "/v1beta/models/" + modelName.toStdString() + ":generateContent?key=" + apiKey);
    
    QNetworkRequest request{QUrl(apiUrl)};
    request.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");

    QJsonObject systemInstruction;
    QJsonObject systemPart;
    systemPart["text"] = "You are Antigravity, a powerful agentic AI coding assistant designed by the Google DeepMind team working on Advanced Agentic Coding. "
                         "You specialize in C++ Qt development, LLVM toolchains, CMake, and advanced editor structures. "
                         "Write complete, robust, production-quality source code. "
                         "Wrap all code blocks in markdown formatting.";
    QJsonArray systemParts;
    systemParts.append(systemPart);
    systemInstruction["parts"] = systemParts;

    QJsonObject content;
    content["role"] = "user";
    QJsonObject part;
    part["text"] = QString::fromStdString(req.prompt);
    QJsonArray parts;
    parts.append(part);
    content["parts"] = parts;
    
    QJsonArray contents;
    contents.append(content);
    
    QJsonObject json;
    json["contents"] = contents;
    json["systemInstruction"] = systemInstruction;
    
    QJsonObject generationConfig;
    generationConfig["temperature"] = 0.5;
    generationConfig["maxOutputTokens"] = 8192;
    json["generationConfig"] = generationConfig;

    QNetworkReply* reply = manager.post(request, QJsonDocument(json).toJson());

    QEventLoop loop;
    QObject::connect(reply, &QNetworkReply::finished, &loop, &QEventLoop::quit);
    loop.exec();

    AIResponse res;
    if (reply->error() == QNetworkReply::NoError) {
        QJsonDocument resDoc = QJsonDocument::fromJson(reply->readAll());
        QJsonObject obj = resDoc.object();
        
        if (obj.contains("candidates")) {
            QJsonArray candidates = obj["candidates"].toArray();
            if (!candidates.isEmpty()) {
                QJsonObject candidate = candidates[0].toObject();
                if (candidate.contains("content")) {
                    QJsonObject contentObj = candidate["content"].toObject();
                    if (contentObj.contains("parts")) {
                        QJsonArray parts = contentObj["parts"].toArray();
                        if (!parts.isEmpty()) {
                            QJsonObject partObj = parts[0].toObject();
                            if (partObj.contains("text")) {
                                res.text = partObj["text"].toString().toStdString();
                                reply->deleteLater();
                                return res;
                            }
                        }
                    }
                }
            }
        }
        res.text = "Error: Invalid response format from Antigravity AI Engine";
    } else {
        res.text = "Error: " + reply->errorString().toStdString();
    }

    reply->deleteLater();
    return res;
}
""")

write(f"{ROOT}/src/ai/VectorIndexManager.hpp", r"""#pragma once
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
    void initDb();

signals:
    void indexingProgress(int current, int total);
    void indexingFinished();

private:
    VectorIndexManager();
    ~VectorIndexManager();

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
""")

write(f"{ROOT}/src/ai/VectorIndexManager.cpp", r"""#include "VectorIndexManager.hpp"
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
            // Set busy timeout for multi-threading safety before any other queries
            QSqlQuery q(threadDb);
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

IndexStats VectorIndexManager::getIndexStats() {
    initDb();
    IndexStats stats{0, 0};
    QSqlDatabase db = getDbForCurrentThread();
    QSqlQuery query(db);
    query.exec("SELECT COUNT(*), COUNT(DISTINCT file_path) FROM codebase_embeddings");
    if (query.next()) {
        stats.chunks = query.value(0).toInt();
        stats.files = query.value(1).toInt();
    }
    return stats;
}

QString VectorIndexManager::getLastError() {
    QMutexLocker locker(&mutex);
    return lastError;
}

void VectorIndexManager::setLastError(const QString& err) {
    QMutexLocker locker(&mutex);
    lastError = err;
}

void VectorIndexManager::clearLastError() {
    QMutexLocker locker(&mutex);
    lastError.clear();
}

void VectorIndexManager::startIndexing(const QString& rootPath) {
    QMutexLocker locker(&mutex);
    if (m_indexing) return;
    m_indexing = true;

    clearLastError();
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
        QString errStr = reply->errorString() + " - " + QString::fromUtf8(reply->readAll());
        VectorIndexManager::instance().setLastError(errStr);
        std::cerr << "[VectorIndex] Network error: " << errStr.toStdString() << std::endl;
    }
    reply->deleteLater();
    return vec;
}

QVector<SearchResult> VectorIndexManager::search(const QString& queryText, float threshold) {
    initDb();
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

    VectorIndexManager::instance().initDb();
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
""")

# ---------------------------------------------------------
# Settings Manager (Singleton for App Configuration)
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/SettingsManager.hpp", r"""#pragma once
#include <string>
#include <QSettings>
#include <QString>

class SettingsManager {
public:
    static SettingsManager& instance() {
        static SettingsManager inst;
        return inst;
    }

    // Active Profile Getters/Setters
    void setProviderType(const std::string& type) { 
        providerType = type; 
        QSettings s("Aide", "AI-IDE");
        s.setValue("providerType", QString::fromStdString(type));
    }
    std::string getProviderType() const { return providerType; }

    void setModel(const std::string& m) { 
        model = m; 
        QSettings s("Aide", "AI-IDE");
        s.setValue("model", QString::fromStdString(m));
    }
    std::string getModel() const { return model; }

    // Legacy method for backward compatibility
    std::string getEndpoint() const {
        if (providerType == "Gemini") return getGeminiApiKey();
        if (providerType == "Claude") return getClaudeApiKey();
        if (providerType == "Antigravity AI") return getAntigravityApiKey();
        return getOllamaEndpoint();
    }

    // Ollama Config
    void setOllamaEndpoint(const std::string& ep) {
        ollamaEndpoint = ep;
        QSettings s("Aide", "AI-IDE");
        s.setValue("ollama/endpoint", QString::fromStdString(ep));
    }
    std::string getOllamaEndpoint() const { return ollamaEndpoint; }

    // Gemini Config
    void setGeminiApiKey(const std::string& key) {
        geminiApiKey = key;
        QSettings s("Aide", "AI-IDE");
        s.setValue("gemini/apiKey", QString::fromStdString(key));
    }
    std::string getGeminiApiKey() const { return geminiApiKey; }

    void setGeminiEndpoint(const std::string& ep) {
        geminiEndpoint = ep;
        QSettings s("Aide", "AI-IDE");
        s.setValue("gemini/endpoint", QString::fromStdString(ep));
    }
    std::string getGeminiEndpoint() const { return geminiEndpoint; }

    // Claude Config
    void setClaudeApiKey(const std::string& key) {
        claudeApiKey = key;
        QSettings s("Aide", "AI-IDE");
        s.setValue("claude/apiKey", QString::fromStdString(key));
    }
    std::string getClaudeApiKey() const { return claudeApiKey; }

    void setClaudeEndpoint(const std::string& ep) {
        claudeEndpoint = ep;
        QSettings s("Aide", "AI-IDE");
        s.setValue("claude/endpoint", QString::fromStdString(ep));
    }
    std::string getClaudeEndpoint() const { return claudeEndpoint; }

    // Antigravity Config
    void setAntigravityApiKey(const std::string& key) {
        antigravityApiKey = key;
        QSettings s("Aide", "AI-IDE");
        s.setValue("antigravity/apiKey", QString::fromStdString(key));
    }
    std::string getAntigravityApiKey() const { return antigravityApiKey; }

    void setAntigravityEndpoint(const std::string& ep) {
        antigravityEndpoint = ep;
        QSettings s("Aide", "AI-IDE");
        s.setValue("antigravity/endpoint", QString::fromStdString(ep));
    }
    std::string getAntigravityEndpoint() const { return antigravityEndpoint; }

private:
    SettingsManager() {
        QSettings s("Aide", "AI-IDE");
        providerType = s.value("providerType", "Ollama").toString().toStdString();
        model = s.value("model", "llama3").toString().toStdString();

        ollamaEndpoint = s.value("ollama/endpoint", "http://localhost:11434").toString().toStdString();
        geminiApiKey = s.value("gemini/apiKey", "").toString().toStdString();
        geminiEndpoint = s.value("gemini/endpoint", "https://generativelanguage.googleapis.com").toString().toStdString();
        claudeApiKey = s.value("claude/apiKey", "").toString().toStdString();
        claudeEndpoint = s.value("claude/endpoint", "https://api.anthropic.com").toString().toStdString();
        antigravityApiKey = s.value("antigravity/apiKey", "").toString().toStdString();
        antigravityEndpoint = s.value("antigravity/endpoint", "https://generativelanguage.googleapis.com").toString().toStdString();
    }

    std::string providerType;
    std::string model;

    std::string ollamaEndpoint;
    std::string geminiApiKey;
    std::string geminiEndpoint;
    std::string claudeApiKey;
    std::string claudeEndpoint;
    std::string antigravityApiKey;
    std::string antigravityEndpoint;
};
""")

# ---------------------------------------------------------
# Admin Dialog (UI for Settings and Model Management)
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/AdminDialog.hpp", r"""#pragma once
#include <QDialog>
#include <QLineEdit>
#include <QComboBox>

class AdminDialog : public QDialog {
    Q_OBJECT
public:
    explicit AdminDialog(QWidget* parent = nullptr);
private slots:
    void refreshModels();
    void saveSettings();
private:
    QComboBox* providerCombo;
    QComboBox* modelCombo;

    QLineEdit* ollamaEndpointEdit;

    QLineEdit* geminiApiKeyEdit;
    QLineEdit* geminiEndpointEdit;

    QLineEdit* claudeApiKeyEdit;
    QLineEdit* claudeEndpointEdit;

    QLineEdit* antigravityApiKeyEdit;
    QLineEdit* antigravityEndpointEdit;
};
""")

write(f"{ROOT}/src/ui/AdminDialog.cpp", r"""#include "AdminDialog.hpp"
#include "SettingsManager.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QFormLayout>
#include <QPushButton>
#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QUrl>
#include <QMessageBox>
#include <QTabWidget>
#include <QFrame>

AdminDialog::AdminDialog(QWidget* parent) : QDialog(parent) {
    setWindowTitle("AI Settings & Administration");
    setMinimumWidth(500);
    setMinimumHeight(350);

    setStyleSheet(
        "QDialog { background-color: #21252b; color: #abb2bf; font-family: 'Segoe UI', Arial; }"
        "QLabel { color: #abb2bf; font-size: 12px; }"
        "QLineEdit { background-color: #1e1e1e; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 6px; font-size: 12px; }"
        "QLineEdit:focus { border: 1px solid #61afef; }"
        "QComboBox { background-color: #1e1e1e; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 4px; font-size: 12px; }"
        "QTabWidget::pane { border: 1px solid #181a1f; background-color: #21252b; }"
        "QTabBar::tab { background-color: #1e1e1e; color: #abb2bf; padding: 8px 12px; border: 1px solid #181a1f; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }"
        "QTabBar::tab:selected { background-color: #21252b; color: #ffffff; border-bottom: 2px solid #61afef; }"
        "QPushButton { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 6px 12px; font-size: 12px; min-width: 80px; }"
        "QPushButton:hover { background-color: #3e4452; color: #ffffff; border-color: #61afef; }"
    );

    auto* mainLayout = new QVBoxLayout(this);
    auto* tabWidget = new QTabWidget(this);
    auto& settings = SettingsManager::instance();

    // ---------------------------------------------------------
    // Tab 1: Active Profile
    // ---------------------------------------------------------
    auto* activeTab = new QWidget(this);
    auto* activeLayout = new QFormLayout(activeTab);
    activeLayout->setContentsMargins(15, 15, 15, 15);
    activeLayout->setSpacing(12);

    providerCombo = new QComboBox(this);
    providerCombo->addItems({"Ollama", "Gemini", "Claude", "Antigravity AI"});
    providerCombo->setCurrentText(QString::fromStdString(settings.getProviderType()));

    modelCombo = new QComboBox(this);
    modelCombo->setEditable(true);
    modelCombo->setCurrentText(QString::fromStdString(settings.getModel()));

    auto* refreshBtn = new QPushButton("Refresh Models", this);
    connect(refreshBtn, &QPushButton::clicked, this, &AdminDialog::refreshModels);

    activeLayout->addRow("Active AI Provider:", providerCombo);
    activeLayout->addRow("Selected AI Model:", modelCombo);
    
    auto* discoveryLayout = new QHBoxLayout();
    discoveryLayout->addWidget(refreshBtn);
    discoveryLayout->addStretch();
    activeLayout->addRow("Discovery:", discoveryLayout);

    tabWidget->addTab(activeTab, "Active Profile");

    // ---------------------------------------------------------
    // Tab 2: Ollama Settings
    // ---------------------------------------------------------
    auto* ollamaTab = new QWidget(this);
    auto* ollamaLayout = new QFormLayout(ollamaTab);
    ollamaLayout->setContentsMargins(15, 15, 15, 15);
    ollamaLayout->setSpacing(12);

    ollamaEndpointEdit = new QLineEdit(this);
    ollamaEndpointEdit->setText(QString::fromStdString(settings.getOllamaEndpoint()));
    ollamaLayout->addRow("Ollama IP/Endpoint URL:", ollamaEndpointEdit);

    tabWidget->addTab(ollamaTab, "Ollama");

    // ---------------------------------------------------------
    // Tab 3: Google Gemini Settings
    // ---------------------------------------------------------
    auto* geminiTab = new QWidget(this);
    auto* geminiLayout = new QFormLayout(geminiTab);
    geminiLayout->setContentsMargins(15, 15, 15, 15);
    geminiLayout->setSpacing(12);

    geminiApiKeyEdit = new QLineEdit(this);
    geminiApiKeyEdit->setEchoMode(QLineEdit::Password);
    geminiApiKeyEdit->setText(QString::fromStdString(settings.getGeminiApiKey()));

    geminiEndpointEdit = new QLineEdit(this);
    geminiEndpointEdit->setText(QString::fromStdString(settings.getGeminiEndpoint()));

    geminiLayout->addRow("Gemini API Key:", geminiApiKeyEdit);
    geminiLayout->addRow("Custom Endpoint URL:", geminiEndpointEdit);

    tabWidget->addTab(geminiTab, "Google Gemini");

    // ---------------------------------------------------------
    // Tab 4: Anthropic Claude Settings
    // ---------------------------------------------------------
    auto* claudeTab = new QWidget(this);
    auto* claudeLayout = new QFormLayout(claudeTab);
    claudeLayout->setContentsMargins(15, 15, 15, 15);
    claudeLayout->setSpacing(12);

    claudeApiKeyEdit = new QLineEdit(this);
    claudeApiKeyEdit->setEchoMode(QLineEdit::Password);
    claudeApiKeyEdit->setText(QString::fromStdString(settings.getClaudeApiKey()));

    claudeEndpointEdit = new QLineEdit(this);
    claudeEndpointEdit->setText(QString::fromStdString(settings.getClaudeEndpoint()));

    claudeLayout->addRow("Claude API Key:", claudeApiKeyEdit);
    claudeLayout->addRow("Custom Endpoint URL:", claudeEndpointEdit);

    tabWidget->addTab(claudeTab, "Anthropic Claude");

    // ---------------------------------------------------------
    // Tab 5: Antigravity AI Settings
    // ---------------------------------------------------------
    auto* antigravityTab = new QWidget(this);
    auto* antigravityLayout = new QFormLayout(antigravityTab);
    antigravityLayout->setContentsMargins(15, 15, 15, 15);
    antigravityLayout->setSpacing(12);

    antigravityApiKeyEdit = new QLineEdit(this);
    antigravityApiKeyEdit->setEchoMode(QLineEdit::Password);
    antigravityApiKeyEdit->setText(QString::fromStdString(settings.getAntigravityApiKey()));

    antigravityEndpointEdit = new QLineEdit(this);
    antigravityEndpointEdit->setText(QString::fromStdString(settings.getAntigravityEndpoint()));

    antigravityLayout->addRow("Antigravity AI Key/Code:", antigravityApiKeyEdit);
    antigravityLayout->addRow("Custom Endpoint URL:", antigravityEndpointEdit);

    tabWidget->addTab(antigravityTab, "Antigravity AI");

    mainLayout->addWidget(tabWidget);

    auto* buttonLayout = new QHBoxLayout();
    auto* saveBtn = new QPushButton("Save Changes", this);
    auto* cancelBtn = new QPushButton("Cancel", this);

    connect(saveBtn, &QPushButton::clicked, this, &AdminDialog::saveSettings);
    connect(cancelBtn, &QPushButton::clicked, this, &AdminDialog::reject);

    buttonLayout->addStretch();
    buttonLayout->addWidget(cancelBtn);
    buttonLayout->addWidget(saveBtn);
    mainLayout->addLayout(buttonLayout);
}

void AdminDialog::refreshModels() {
    QString provider = providerCombo->currentText();
    if (provider == "Ollama") {
        QString url = ollamaEndpointEdit->text() + "/api/tags";
        auto* manager = new QNetworkAccessManager(this);
        auto* reply = manager->get(QNetworkRequest(QUrl(url)));
        connect(reply, &QNetworkReply::finished, this, [this, reply]() {
            if (reply->error() == QNetworkReply::NoError) {
                modelCombo->clear();
                auto models = QJsonDocument::fromJson(reply->readAll()).object()["models"].toArray();
                for (const auto& m : models) {
                    modelCombo->addItem(m.toObject()["name"].toString());
                }
            } else {
                QMessageBox::warning(this, "Discovery Error", "Failed to connect to Ollama: " + reply->errorString());
            }
            reply->deleteLater();
        });
    } else if (provider == "Gemini" || provider == "Antigravity AI") {
        modelCombo->clear();
        modelCombo->addItems({"gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"});
    } else if (provider == "Claude") {
        modelCombo->clear();
        modelCombo->addItems({"claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"});
    }
}

void AdminDialog::saveSettings() {
    auto& s = SettingsManager::instance();
    s.setProviderType(providerCombo->currentText().toStdString());
    s.setModel(modelCombo->currentText().toStdString());
    s.setOllamaEndpoint(ollamaEndpointEdit->text().toStdString());
    s.setGeminiApiKey(geminiApiKeyEdit->text().toStdString());
    s.setGeminiEndpoint(geminiEndpointEdit->text().toStdString());
    s.setClaudeApiKey(claudeApiKeyEdit->text().toStdString());
    s.setClaudeEndpoint(claudeEndpointEdit->text().toStdString());
    s.setAntigravityApiKey(antigravityApiKeyEdit->text().toStdString());
    s.setAntigravityEndpoint(antigravityEndpointEdit->text().toStdString());
    accept();
}
""")

# ---------------------------------------------------------
# 0. File Browser and AI Chat Panel (Merged from qt_logic)
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/FileBrowser.hpp", r"""#pragma once
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
""")

write(f"{ROOT}/src/ui/FileBrowser.cpp", r"""#include "FileBrowser.hpp"
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
""")

write(f"{ROOT}/src/ui/AIChatPanel.hpp", r"""#pragma once
#include <QWidget>
#include <QTextEdit>
#include <QPushButton>
#include <memory>
#include "SettingsManager.hpp"
#include "../ai/AIProvider.hpp"

class AIChatPanel : public QWidget {
    Q_OBJECT
public:
    explicit AIChatPanel(QWidget* parent = nullptr);
signals:
    void applyToEditor(const QString& code);
    void createNewFile(const QString& code);
    void promptArchived(const QString& summary);

private slots:
    void sendPrompt();
private:
    QTextEdit* chatHistory;
    QTextEdit* inputBox;
    QPushButton* sendButton;
    std::unique_ptr<AIProvider> provider;
    QString lastExtractedCode;
};
""")

write(f"{ROOT}/src/ui/AIChatPanel.cpp", r"""#include "AIChatPanel.hpp"
#include "../ai/GeminiProvider.hpp"
#include "../ai/OllamaProvider.hpp"
#include "../ai/ClaudeProvider.hpp"
#include "../ai/AntigravityProvider.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QRegularExpression>
#include <QFile>
#include <QTextStream>
#include <QDir>
#include <QMessageBox>
#include <QDateTime>

AIChatPanel::AIChatPanel(QWidget* parent) : QWidget(parent) {
    auto* layout = new QVBoxLayout(this);
    chatHistory = new QTextEdit(this);
    chatHistory->setReadOnly(true);
    chatHistory->setPlaceholderText("AI Chat History...");

    inputBox = new QTextEdit(this);
    inputBox->setFixedHeight(80);
    inputBox->setPlaceholderText("Type a message or instruction...");

    sendButton = new QPushButton("Send", this);
    
    auto& settings = SettingsManager::instance();
    if (settings.getProviderType() == "Gemini") {
        provider = std::make_unique<GeminiProvider>(settings.getGeminiApiKey(), settings.getGeminiEndpoint());
    } else if (settings.getProviderType() == "Claude") {
        provider = std::make_unique<ClaudeProvider>(settings.getClaudeApiKey(), settings.getClaudeEndpoint());
    } else if (settings.getProviderType() == "Antigravity AI") {
        provider = std::make_unique<AntigravityProvider>(settings.getAntigravityApiKey(), settings.getAntigravityEndpoint());
    } else {
        provider = std::make_unique<OllamaProvider>(settings.getOllamaEndpoint());
    }

    auto* actionLayout = new QHBoxLayout();
    auto* applyBtn = new QPushButton("Apply to Editor", this);
    auto* newPageBtn = new QPushButton("New Page", this);
    actionLayout->addWidget(applyBtn);
    actionLayout->addWidget(newPageBtn);

    layout->addWidget(chatHistory);
    layout->addWidget(inputBox);
    layout->addWidget(sendButton);
    layout->addLayout(actionLayout);

    connect(sendButton, &QPushButton::clicked, this, &AIChatPanel::sendPrompt);

    connect(applyBtn, &QPushButton::clicked, this, [this]() {
        if (!lastExtractedCode.isEmpty()) emit applyToEditor(lastExtractedCode);
        else QMessageBox::warning(this, "AI IDE", "No code detected in the AI's last response to apply.");
    });

    connect(newPageBtn, &QPushButton::clicked, this, [this]() {
        if (!lastExtractedCode.isEmpty()) emit createNewFile(lastExtractedCode);
        else QMessageBox::warning(this, "AI IDE", "No code detected in the AI's last response to create a page.");
    });
}

void AIChatPanel::sendPrompt() {
    QString prompt = inputBox->toPlainText().trimmed();
    if (prompt.isEmpty()) return;

    chatHistory->append("<b>You:</b> " + prompt);
    lastExtractedCode.clear();

    // Re-initialize provider on the fly based on latest settings
    auto& settings = SettingsManager::instance();
    if (settings.getProviderType() == "Gemini") {
        provider = std::make_unique<GeminiProvider>(settings.getGeminiApiKey(), settings.getGeminiEndpoint());
    } else if (settings.getProviderType() == "Claude") {
        provider = std::make_unique<ClaudeProvider>(settings.getClaudeApiKey(), settings.getClaudeEndpoint());
    } else if (settings.getProviderType() == "Antigravity AI") {
        provider = std::make_unique<AntigravityProvider>(settings.getAntigravityApiKey(), settings.getAntigravityEndpoint());
    } else {
        provider = std::make_unique<OllamaProvider>(settings.getOllamaEndpoint());
    }

    AIRequest req;
    req.prompt = prompt.toStdString();
    AIResponse res = provider->send(req);

    chatHistory->append("<b>AI:</b> " + QString::fromStdString(res.text));
    inputBox->clear();

    QString summary = QString("[%1] %2").arg(QDateTime::currentDateTime().toString("hh:mm")).arg(prompt.left(30) + "...");
    emit promptArchived(summary);

    // Extract code block from Markdown (Robust Regex)
    QRegularExpression codeRegex("(?s)```(?:[a-zA-Z0-9+#]+)?\\s*\\n?(.*?)(?:```|$)");
    QRegularExpressionMatch match = codeRegex.match(QString::fromStdString(res.text));
    if (match.hasMatch()) {
        lastExtractedCode = match.captured(1).trimmed();
        
        QString tempPath = QDir::tempPath() + "/ai_last_chat_code.txt";
        QFile tempFile(tempPath);
        if (tempFile.open(QIODevice::WriteOnly | QIODevice::Text)) {
            QTextStream out(&tempFile);
            out << lastExtractedCode;
            tempFile.close();
        }
    }
}
""")

# ---------------------------------------------------------
# LSP Client Wrapper (talking to clangd Language Server)
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/LspClient.hpp", r"""#pragma once
#include <QObject>
#include <QProcess>
#include <QJsonObject>
#include <QJsonDocument>
#include <QJsonArray>
#include <QHash>
#include <QUrl>

class LspClient : public QObject {
    Q_OBJECT
public:
    static LspClient& instance();

    void startServer(const QString& rootPath);
    void stopServer();

    void didOpen(const QString& filePath, const QString& text);
    void didChange(const QString& filePath, const QString& text);
    
    int requestCompletion(const QString& filePath, int line, int character);
    int requestDefinition(const QString& filePath, int line, int character);
    int requestReferences(const QString& filePath, int line, int character);

signals:
    void completionReady(int id, const QJsonArray& items);
    void definitionReady(int id, const QString& filePath, int line);
    void referencesReady(int id, const QJsonArray& locations);

private slots:
    void readOutput();

private:
    explicit LspClient(QObject* parent = nullptr);
    void sendRequest(const QString& method, const QJsonObject& params, int id);
    void sendNotification(const QString& method, const QJsonObject& params);
    void parseMessage(const QByteArray& payload);

    QProcess* process;
    int nextId;
    QByteArray readBuffer;
    int expectedContentLength;
    QHash<int, QString> pendingRequests;
};
""")

write(f"{ROOT}/src/ui/LspClient.cpp", r"""#include "LspClient.hpp"
#include <QDir>
#include <QRegularExpression>
#include <QCoreApplication>

LspClient& LspClient::instance() {
    static LspClient inst;
    return inst;
}

LspClient::LspClient(QObject* parent)
    : QObject(parent), process(nullptr), nextId(1), expectedContentLength(-1) {}

void LspClient::startServer(const QString& rootPath) {
    if (process && process->state() == QProcess::Running) return;

    process = new QProcess(this);
    process->setProcessChannelMode(QProcess::SeparateChannels);

    connect(process, &QProcess::readyReadStandardOutput, this, &LspClient::readOutput);

    // Path to clangd executable inside the LLVM-MinGW toolchain
    QString clangdPath = "C:/Qt/Tools/llvm-mingw_64/bin/clangd.exe";
    
    QStringList args;
    args << "--log=verbose" << "--background-index" << QString("--project-root=%1").arg(rootPath);
    
    process->start(clangdPath, args);

    // Send initialize request
    QJsonObject params;
    params["processId"] = static_cast<int>(QCoreApplication::applicationPid());
    params["rootPath"] = rootPath;
    params["rootUri"] = QUrl::fromLocalFile(rootPath).toString();
    
    QJsonObject capabilities;
    params["capabilities"] = capabilities;

    sendRequest("initialize", params, nextId++);
}

void LspClient::stopServer() {
    if (process) {
        process->terminate();
        process->waitForFinished(1000);
        process->deleteLater();
        process = nullptr;
    }
}

void LspClient::sendRequest(const QString& method, const QJsonObject& params, int id) {
    QJsonObject request;
    request["jsonrpc"] = "2.0";
    request["id"] = id;
    request["method"] = method;
    request["params"] = params;

    QByteArray doc = QJsonDocument(request).toJson(QJsonDocument::Compact);
    QByteArray header = QString("Content-Length: %1\r\n\r\n").arg(doc.length()).toUtf8();

    if (process && process->state() == QProcess::Running) {
        process->write(header + doc);
    }
}

void LspClient::sendNotification(const QString& method, const QJsonObject& params) {
    QJsonObject request;
    request["jsonrpc"] = "2.0";
    request["method"] = method;
    request["params"] = params;

    QByteArray doc = QJsonDocument(request).toJson(QJsonDocument::Compact);
    QByteArray header = QString("Content-Length: %1\r\n\r\n").arg(doc.length()).toUtf8();

    if (process && process->state() == QProcess::Running) {
        process->write(header + doc);
    }
}

void LspClient::readOutput() {
    if (!process) return;
    readBuffer.append(process->readAllStandardOutput());

    while (true) {
        if (expectedContentLength == -1) {
            int headerEnd = readBuffer.indexOf("\r\n\r\n");
            if (headerEnd == -1) break;

            QString headerPart = QString::fromUtf8(readBuffer.left(headerEnd));
            QRegularExpression lenRegex("Content-Length:\\s*(\\d+)", QRegularExpression::CaseInsensitiveOption);
            QRegularExpressionMatch match = lenRegex.match(headerPart);
            if (match.hasMatch()) {
                expectedContentLength = match.captured(1).toInt();
            }
            readBuffer.remove(0, headerEnd + 4);
        }

        if (expectedContentLength != -1) {
            if (readBuffer.length() < expectedContentLength) break;

            QByteArray payload = readBuffer.left(expectedContentLength);
            readBuffer.remove(0, expectedContentLength);
            expectedContentLength = -1;

            parseMessage(payload);
        }
    }
}

void LspClient::parseMessage(const QByteArray& payload) {
    QJsonDocument doc = QJsonDocument::fromJson(payload);
    if (!doc.isObject()) return;

    QJsonObject obj = doc.object();
    
    if (obj.contains("id") && (obj.contains("result") || obj.contains("error"))) {
        int id = obj["id"].toInt();
        QString method = pendingRequests.take(id);
        
        if (method == "textDocument/completion") {
            QJsonArray items;
            if (obj["result"].isObject()) {
                items = obj["result"].toObject()["items"].toArray();
            } else if (obj["result"].isArray()) {
                items = obj["result"].toArray();
            }
            emit completionReady(id, items);
        } else if (method == "textDocument/definition") {
            QString targetPath;
            int targetLine = 1;
            
            QJsonValue res = obj["result"];
            if (res.isArray()) {
                QJsonArray arr = res.toArray();
                if (!arr.isEmpty()) {
                    QJsonObject loc = arr[0].toObject();
                    QString uri = loc["uri"].toString();
                    targetPath = QUrl(uri).toLocalFile();
                    targetLine = loc["range"].toObject()["start"].toObject()["line"].toInt() + 1;
                }
            } else if (res.isObject()) {
                QJsonObject loc = res.toObject();
                QString uri = loc["uri"].toString();
                targetPath = QUrl(uri).toLocalFile();
                targetLine = loc["range"].toObject()["start"].toObject()["line"].toInt() + 1;
            }
            emit definitionReady(id, targetPath, targetLine);
        } else if (method == "textDocument/references") {
            emit referencesReady(id, obj["result"].toArray());
        }
    }
}

void LspClient::didOpen(const QString& filePath, const QString& text) {
    QJsonObject params;
    QJsonObject textDocument;
    textDocument["uri"] = QUrl::fromLocalFile(filePath).toString();
    textDocument["languageId"] = "cpp";
    textDocument["version"] = 1;
    textDocument["text"] = text;
    params["textDocument"] = textDocument;
    sendNotification("textDocument/didOpen", params);
}

void LspClient::didChange(const QString& filePath, const QString& text) {
    QJsonObject params;
    QJsonObject textDocument;
    textDocument["uri"] = QUrl::fromLocalFile(filePath).toString();
    textDocument["version"] = 2;
    params["textDocument"] = textDocument;

    QJsonArray contentChanges;
    QJsonObject change;
    change["text"] = text;
    contentChanges.append(change);
    params["contentChanges"] = contentChanges;

    sendNotification("textDocument/didChange", params);
}

int LspClient::requestCompletion(const QString& filePath, int line, int character) {
    int id = nextId++;
    pendingRequests[id] = "textDocument/completion";

    QJsonObject params;
    QJsonObject textDocument;
    textDocument["uri"] = QUrl::fromLocalFile(filePath).toString();
    params["textDocument"] = textDocument;

    QJsonObject position;
    position["line"] = line;
    position["character"] = character;
    params["position"] = position;

    sendRequest("textDocument/completion", params, id);
    return id;
}

int LspClient::requestDefinition(const QString& filePath, int line, int character) {
    int id = nextId++;
    pendingRequests[id] = "textDocument/definition";

    QJsonObject params;
    QJsonObject textDocument;
    textDocument["uri"] = QUrl::fromLocalFile(filePath).toString();
    params["textDocument"] = textDocument;

    QJsonObject position;
    position["line"] = line;
    position["character"] = character;
    params["position"] = position;

    sendRequest("textDocument/definition", params, id);
    return id;
}

int LspClient::requestReferences(const QString& filePath, int line, int character) {
    int id = nextId++;
    pendingRequests[id] = "textDocument/references";

    QJsonObject params;
    QJsonObject textDocument;
    textDocument["uri"] = QUrl::fromLocalFile(filePath).toString();
    params["textDocument"] = textDocument;

    QJsonObject position;
    position["line"] = line;
    position["character"] = character;
    params["position"] = position;

    QJsonObject context;
    context["includeDeclaration"] = true;
    params["context"] = context;

    sendRequest("textDocument/references", params, id);
    return id;
}
""")

write(f"{ROOT}/src/ui/CompletionPopup.hpp", r"""#pragma once
#include <QListWidget>
#include <QJsonArray>

class CompletionPopup : public QListWidget {
    Q_OBJECT
public:
    explicit CompletionPopup(QWidget* parent = nullptr);
    void setCompletions(const QJsonArray& items);
    void showAt(const QPoint& pos);
};
""")

write(f"{ROOT}/src/ui/CompletionPopup.cpp", r"""#include "CompletionPopup.hpp"
#include <QJsonObject>

CompletionPopup::CompletionPopup(QWidget* parent)
    : QListWidget(parent)
{
    setWindowFlags(Qt::ToolTip | Qt::FramelessWindowHint);
    setAttribute(Qt::WA_ShowWithoutActivating);
    setFocusPolicy(Qt::NoFocus);
    
    setStyleSheet("QListWidget { background-color: #21252b; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; font-family: 'Segoe UI', Arial; font-size: 12px; }"
                  "QListWidget::item { padding: 4px 8px; }"
                  "QListWidget::item:selected { background-color: #3e4452; color: #ffffff; }");
    
    setMinimumWidth(250);
    setMaximumHeight(150);
}

void CompletionPopup::setCompletions(const QJsonArray& items) {
    clear();
    for (const auto& val : items) {
        QJsonObject item = val.toObject();
        QString label = item["label"].toString();
        QString detail = item["detail"].toString();
        QString insertText = item["insertText"].toString();
        if (insertText.isEmpty()) insertText = label;

        auto* listItem = new QListWidgetItem(this);
        listItem->setText(label);
        if (!detail.isEmpty()) {
            listItem->setToolTip(detail);
        }
        listItem->setData(Qt::UserRole, insertText);
    }
    if (count() > 0) {
        setCurrentRow(0);
    }
}

void CompletionPopup::showAt(const QPoint& pos) {
    move(pos);
    show();
}
""")

# ---------------------------------------------------------
# Find & Replace Dialog
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/FindReplaceDialog.hpp", r"""#pragma once
#include <QDialog>
#include <QLineEdit>
#include <QCheckBox>
#include <QPushButton>
#include <QRadioButton>
#include <QLabel>
#include <QString>

class EditorWindow;

class FindReplaceDialog : public QDialog {
    Q_OBJECT
public:
    explicit FindReplaceDialog(EditorWindow* parent = nullptr);
    void showFind();
    void showReplace();
    void showFolderSearch(const QString& defaultFolder);

private slots:
    void onFindNext();
    void onFindPrev();
    void onReplace();
    void onReplaceAll();
    void onBrowseFolder();
    void onScopeChanged();

private:
    void setupUI();
    bool doFind(bool forward);
    void performFolderReplace();

    EditorWindow* mainWin;

    QLineEdit* findEdit;
    QLineEdit* replaceEdit;
    QLineEdit* folderEdit;
    QLineEdit* filterEdit;
    QPushButton* browseBtn;

    QCheckBox* caseCheck;
    QCheckBox* wordCheck;
    QCheckBox* regexCheck;

    QRadioButton* currentFileRadio;
    QRadioButton* folderRadio;

    QPushButton* findNextBtn;
    QPushButton* findPrevBtn;
    QPushButton* replaceBtn;
    QPushButton* replaceAllBtn;

    QLabel* statusLabel;
};
""")

write(f"{ROOT}/src/ui/FindReplaceDialog.cpp", r"""#include "FindReplaceDialog.hpp"
#include "EditorWindow.hpp"
#include "CustomEditor.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QFormLayout>
#include <QFileDialog>
#include <QMessageBox>
#include <QTextDocument>
#include <QTextCursor>
#include <QDirIterator>
#include <QFile>
#include <QTextStream>
#include <QFileInfo>
#include <QRegularExpression>
#include <QDir>
#if QT_VERSION < QT_VERSION_CHECK(6, 0, 0)
#include <QRegExp>
#endif

FindReplaceDialog::FindReplaceDialog(EditorWindow* parent)
    : QDialog(parent), mainWin(parent)
{
    setWindowFlags(Qt::Tool | Qt::WindowTitleHint | Qt::WindowCloseButtonHint);
    setWindowTitle("Find & Replace");
    resize(480, 280);

    setupUI();
    onScopeChanged();
}

void FindReplaceDialog::setupUI() {
    // Dark modern styling matching EditorWindow
    setStyleSheet(
        "QDialog { background-color: #21252b; color: #abb2bf; font-family: 'Segoe UI', Arial; }"
        "QLabel { color: #abb2bf; font-size: 12px; }"
        "QLineEdit { background-color: #1e1e1e; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 6px; font-size: 12px; }"
        "QLineEdit:focus { border: 1px solid #61afef; }"
        "QCheckBox { color: #abb2bf; font-size: 12px; }"
        "QCheckBox::indicator { width: 14px; height: 14px; }"
        "QRadioButton { color: #abb2bf; font-size: 12px; }"
        "QPushButton { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 6px 12px; font-size: 12px; min-width: 80px; }"
        "QPushButton:hover { background-color: #3e4452; color: #ffffff; border-color: #61afef; }"
        "QPushButton:pressed { background-color: #4b5263; }"
    );

    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(15, 15, 15, 15);
    mainLayout->setSpacing(12);

    auto* formLayout = new QFormLayout();
    formLayout->setSpacing(8);

    findEdit = new QLineEdit(this);
    findEdit->setPlaceholderText("Text to search...");
    formLayout->addRow("Find:", findEdit);

    replaceEdit = new QLineEdit(this);
    replaceEdit->setPlaceholderText("Replacement text...");
    formLayout->addRow("Replace with:", replaceEdit);

    // Options layout (Case sensitive, Whole word, Regex)
    auto* optionsLayout = new QHBoxLayout();
    caseCheck = new QCheckBox("Match Case", this);
    wordCheck = new QCheckBox("Whole Word", this);
    regexCheck = new QCheckBox("Regex", this);
    optionsLayout->addWidget(caseCheck);
    optionsLayout->addWidget(wordCheck);
    optionsLayout->addWidget(regexCheck);
    optionsLayout->addStretch();
    formLayout->addRow("", optionsLayout);

    // Scope layout
    auto* scopeLayout = new QHBoxLayout();
    currentFileRadio = new QRadioButton("Current File", this);
    currentFileRadio->setChecked(true);
    folderRadio = new QRadioButton("Folder/Workspace", this);
    scopeLayout->addWidget(currentFileRadio);
    scopeLayout->addWidget(folderRadio);
    scopeLayout->addStretch();
    formLayout->addRow("Scope:", scopeLayout);

    // Folder and Filter layout
    auto* folderLayout = new QHBoxLayout();
    folderEdit = new QLineEdit(this);
    folderEdit->setText(QDir::currentPath());
    folderEdit->setPlaceholderText("Directory path...");
    browseBtn = new QPushButton("Browse...", this);
    browseBtn->setMaximumWidth(80);
    folderLayout->addWidget(folderEdit);
    folderLayout->addWidget(browseBtn);
    formLayout->addRow("Directory:", folderLayout);

    filterEdit = new QLineEdit(this);
    filterEdit->setPlaceholderText("e.g. *.cpp, *.hpp, *.txt");
    formLayout->addRow("File Filters:", filterEdit);

    mainLayout->addLayout(formLayout);

    // Buttons layout
    auto* btnLayout = new QHBoxLayout();
    findPrevBtn = new QPushButton("Find Prev", this);
    findNextBtn = new QPushButton("Find Next", this);
    replaceBtn = new QPushButton("Replace", this);
    replaceAllBtn = new QPushButton("Replace All", this);

    btnLayout->addWidget(findPrevBtn);
    btnLayout->addWidget(findNextBtn);
    btnLayout->addWidget(replaceBtn);
    btnLayout->addWidget(replaceAllBtn);
    mainLayout->addLayout(btnLayout);

    statusLabel = new QLabel(this);
    statusLabel->setStyleSheet("color: #98c379; font-style: italic;");
    mainLayout->addWidget(statusLabel);

    // Connect signals/slots
    connect(browseBtn, &QPushButton::clicked, this, &FindReplaceDialog::onBrowseFolder);
    connect(currentFileRadio, &QRadioButton::toggled, this, &FindReplaceDialog::onScopeChanged);
    connect(folderRadio, &QRadioButton::toggled, this, &FindReplaceDialog::onScopeChanged);
    
    connect(findNextBtn, &QPushButton::clicked, this, &FindReplaceDialog::onFindNext);
    connect(findPrevBtn, &QPushButton::clicked, this, &FindReplaceDialog::onFindPrev);
    connect(replaceBtn, &QPushButton::clicked, this, &FindReplaceDialog::onReplace);
    connect(replaceAllBtn, &QPushButton::clicked, this, &FindReplaceDialog::onReplaceAll);

    // Focus on find edit initially
    findEdit->setFocus();
}

void FindReplaceDialog::showFind() {
    replaceEdit->setVisible(false);
    replaceBtn->setVisible(false);
    replaceAllBtn->setText("Find All");
    findEdit->setFocus();
    findEdit->selectAll();
    show();
    raise();
    activateWindow();
}

void FindReplaceDialog::showReplace() {
    replaceEdit->setVisible(true);
    replaceBtn->setVisible(true);
    replaceAllBtn->setText("Replace All");
    findEdit->setFocus();
    findEdit->selectAll();
    show();
    raise();
    activateWindow();
}

void FindReplaceDialog::showFolderSearch(const QString& defaultFolder) {
    folderRadio->setChecked(true);
    if (!defaultFolder.isEmpty()) {
        folderEdit->setText(defaultFolder);
    }
    onScopeChanged();
    findEdit->setFocus();
    findEdit->selectAll();
    show();
    raise();
    activateWindow();
}

void FindReplaceDialog::onBrowseFolder() {
    QString dir = QFileDialog::getExistingDirectory(this, "Select Directory to Search", folderEdit->text());
    if (!dir.isEmpty()) {
        folderEdit->setText(dir);
    }
}

void FindReplaceDialog::onScopeChanged() {
    bool isFolder = folderRadio->isChecked();
    folderEdit->setEnabled(isFolder);
    browseBtn->setEnabled(isFolder);
    filterEdit->setEnabled(isFolder);

    findPrevBtn->setEnabled(!isFolder);
    replaceBtn->setEnabled(!isFolder);
}

bool FindReplaceDialog::doFind(bool forward) {
    if (!mainWin) return false;
    CustomEditor* activeEd = mainWin->currentEditor();
    if (!activeEd) {
        statusLabel->setText("No active file editor.");
        return false;
    }

    CodeEditor* codeEd = activeEd->getCodeEditor();
    if (!codeEd) return false;

    QString query = findEdit->text();
    if (query.isEmpty()) return false;

    QTextDocument::FindFlags flags;
    if (!forward) flags |= QTextDocument::FindBackward;
    if (caseCheck->isChecked()) flags |= QTextDocument::FindCaseSensitively;
    if (wordCheck->isChecked()) flags |= QTextDocument::FindWholeWords;

    bool found = false;
    if (regexCheck->isChecked()) {
#if QT_VERSION >= QT_VERSION_CHECK(6, 0, 0)
        QRegularExpression::PatternOptions options = QRegularExpression::NoPatternOption;
        if (!caseCheck->isChecked()) {
            options |= QRegularExpression::CaseInsensitiveOption;
        }
        QRegularExpression regex(query, options);
        if (regex.isValid()) {
            QTextCursor foundCursor = codeEd->document()->find(regex, codeEd->textCursor(), flags);
            if (!foundCursor.isNull()) {
                codeEd->setTextCursor(foundCursor);
                found = true;
            }
        } else {
            statusLabel->setText("Invalid regular expression.");
            return false;
        }
#else
        QRegExp regex(query, caseCheck->isChecked() ? Qt::CaseSensitive : Qt::CaseInsensitive);
        QTextCursor foundCursor = codeEd->document()->find(regex, codeEd->textCursor(), flags);
        if (!foundCursor.isNull()) {
            codeEd->setTextCursor(foundCursor);
            found = true;
        }
#endif
    } else {
        found = codeEd->find(query, flags);
    }

    if (found) {
        statusLabel->setText("Match found.");
    } else {
        // Wrap around search
        QTextCursor startCursor = codeEd->textCursor();
        if (forward) {
            startCursor.movePosition(QTextCursor::Start);
        } else {
            startCursor.movePosition(QTextCursor::End);
        }
        
        bool wrapFound = false;
        if (regexCheck->isChecked()) {
#if QT_VERSION >= QT_VERSION_CHECK(6, 0, 0)
            QRegularExpression regex(query, caseCheck->isChecked() ? QRegularExpression::NoPatternOption : QRegularExpression::CaseInsensitiveOption);
            QTextCursor foundCursor = codeEd->document()->find(regex, startCursor, flags);
            if (!foundCursor.isNull()) {
                codeEd->setTextCursor(foundCursor);
                wrapFound = true;
            }
#else
            QRegExp regex(query, caseCheck->isChecked() ? Qt::CaseSensitive : Qt::CaseInsensitive);
            QTextCursor foundCursor = codeEd->document()->find(regex, startCursor, flags);
            if (!foundCursor.isNull()) {
                codeEd->setTextCursor(foundCursor);
                wrapFound = true;
            }
#endif
        } else {
            QTextCursor wrapCursor = codeEd->document()->find(query, startCursor, flags);
            if (!wrapCursor.isNull()) {
                codeEd->setTextCursor(wrapCursor);
                wrapFound = true;
            }
        }

        if (wrapFound) {
            statusLabel->setText("Search wrapped around.");
            found = true;
        } else {
            statusLabel->setText("No match found.");
        }
    }
    return found;
}

void FindReplaceDialog::onFindNext() {
    if (folderRadio->isChecked()) {
        statusLabel->setText("Use 'Replace All' for folder scope.");
        return;
    }
    doFind(true);
}

void FindReplaceDialog::onFindPrev() {
    doFind(false);
}

void FindReplaceDialog::onReplace() {
    if (folderRadio->isChecked()) return;

    if (!mainWin) return;
    CustomEditor* activeEd = mainWin->currentEditor();
    if (!activeEd) return;

    CodeEditor* codeEd = activeEd->getCodeEditor();
    if (!codeEd) return;

    QTextCursor cursor = codeEd->textCursor();
    if (cursor.hasSelection()) {
        cursor.insertText(replaceEdit->text());
        codeEd->setTextCursor(cursor);
        statusLabel->setText("Replaced match.");
    }
    doFind(true);
}

void FindReplaceDialog::onReplaceAll() {
    QString query = findEdit->text();
    if (query.isEmpty()) return;

    if (currentFileRadio->isChecked()) {
        if (!mainWin) return;
        CustomEditor* activeEd = mainWin->currentEditor();
        if (!activeEd) return;

        CodeEditor* codeEd = activeEd->getCodeEditor();
        if (!codeEd) return;

        int count = 0;
        QTextCursor startCursor = codeEd->textCursor();
        startCursor.movePosition(QTextCursor::Start);
        codeEd->setTextCursor(startCursor);

        codeEd->setUpdatesEnabled(false);

        QTextDocument::FindFlags flags;
        if (caseCheck->isChecked()) flags |= QTextDocument::FindCaseSensitively;
        if (wordCheck->isChecked()) flags |= QTextDocument::FindWholeWords;

        while (true) {
            QTextCursor foundCursor;
            if (regexCheck->isChecked()) {
#if QT_VERSION >= QT_VERSION_CHECK(6, 0, 0)
                QRegularExpression regex(query, caseCheck->isChecked() ? QRegularExpression::NoPatternOption : QRegularExpression::CaseInsensitiveOption);
                foundCursor = codeEd->document()->find(regex, codeEd->textCursor(), flags);
#else
                QRegExp regex(query, caseCheck->isChecked() ? Qt::CaseSensitive : Qt::CaseInsensitive);
                foundCursor = codeEd->document()->find(regex, codeEd->textCursor(), flags);
#endif
            } else {
                foundCursor = codeEd->document()->find(query, codeEd->textCursor(), flags);
            }

            if (!foundCursor.isNull()) {
                foundCursor.insertText(replaceEdit->text());
                codeEd->setTextCursor(foundCursor);
                count++;
            } else {
                break;
            }
        }

        codeEd->setUpdatesEnabled(true);
        statusLabel->setText(QString("Replaced %1 occurrences in file.").arg(count));
    } else {
        performFolderReplace();
    }
}

void FindReplaceDialog::performFolderReplace() {
    QString query = findEdit->text();
    QString replacement = replaceEdit->text();
    QString root = folderEdit->text();
    if (query.isEmpty() || root.isEmpty()) {
        statusLabel->setText("Find query and directory path cannot be empty.");
        return;
    }

    QString filterStr = filterEdit->text().trimmed();
    QStringList filters;
    if (!filterStr.isEmpty()) {
        filters = filterStr.split(QRegularExpression("[,;\\s]+"), Qt::SkipEmptyParts);
    } else {
        filters << "*.cpp" << "*.hpp" << "*.h" << "*.txt" << "*.md" << "*.py" << "*.json" << "*.cmake";
    }

    QMessageBox::StandardButton reply = QMessageBox::question(
        this, "Confirm Replace All",
        QString("Are you sure you want to replace all occurrences of '%1' with '%2' in folder '%3'?")
            .arg(query).arg(replacement).arg(root),
        QMessageBox::Yes | QMessageBox::No
    );

    if (reply != QMessageBox::Yes) {
        statusLabel->setText("Folder replacement cancelled.");
        return;
    }

    int filesChanged = 0;
    int occurrencesReplaced = 0;

    QDirIterator it(root, QDir::Files, QDirIterator::Subdirectories);
    while (it.hasNext()) {
        QString path = it.next();
        QString cleanPath = QDir::cleanPath(path);
        if (cleanPath.contains("/.git/") || cleanPath.contains("/build/") || cleanPath.contains("/.agents/") || cleanPath.contains("/.antigravity/")) {
            continue;
        }

        QFileInfo info(path);
        bool matchesFilter = false;
        for (const QString& filter : filters) {
            QRegularExpression filterRegex(QRegularExpression::wildcardToRegularExpression(filter));
            if (filterRegex.match(info.fileName()).hasMatch()) {
                matchesFilter = true;
                break;
            }
        }
        if (!matchesFilter) continue;

        QFile file(path);
        if (file.open(QIODevice::ReadOnly | QIODevice::Text)) {
            QTextStream in(&file);
            QString content = in.readAll();
            file.close();

            bool contentChanged = false;
            int countInFile = 0;

            if (regexCheck->isChecked()) {
#if QT_VERSION >= QT_VERSION_CHECK(6, 0, 0)
                QRegularExpression::PatternOptions options = QRegularExpression::NoPatternOption;
                if (!caseCheck->isChecked()) {
                    options |= QRegularExpression::CaseInsensitiveOption;
                }
                QRegularExpression regex(query, options);
                
                auto matchIterator = regex.globalMatch(content);
                while (matchIterator.hasNext()) {
                    matchIterator.next();
                    countInFile++;
                }

                if (countInFile > 0) {
                    content.replace(regex, replacement);
                    contentChanged = true;
                }
#else
                QRegExp regex(query, caseCheck->isChecked() ? Qt::CaseSensitive : Qt::CaseInsensitive);
                int pos = 0;
                while ((pos = regex.indexIn(content, pos)) != -1) {
                    countInFile++;
                    pos += regex.matchedLength();
                }
                if (countInFile > 0) {
                    content.replace(regex, replacement);
                    contentChanged = true;
                }
#endif
            } else {
                Qt::CaseSensitivity cs = caseCheck->isChecked() ? Qt::CaseSensitive : Qt::CaseInsensitive;
                
                int pos = 0;
                while ((pos = content.indexOf(query, pos, cs)) != -1) {
                    countInFile++;
                    pos += query.length();
                }

                if (countInFile > 0) {
                    content.replace(query, replacement, cs);
                    contentChanged = true;
                }
            }

            if (contentChanged) {
                if (file.open(QIODevice::WriteOnly | QIODevice::Truncate | QIODevice::Text)) {
                    QTextStream out(&file);
                    out << content;
                    file.close();
                    filesChanged++;
                    occurrencesReplaced += countInFile;
                }
            }
        }
    }

    statusLabel->setText(QString("Replaced %1 occurrences in %2 files.").arg(occurrencesReplaced).arg(filesChanged));
    QMessageBox::information(this, "Replace All Complete", 
                             QString("Successfully replaced %1 occurrences in %2 files.").arg(occurrencesReplaced).arg(filesChanged));
}
""")

# ---------------------------------------------------------
# Workspace Search Widget (Asynchronous file scanning)
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/SearchWidget.hpp", r"""#pragma once
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
    void updateIndexStats();

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
""")

write(f"{ROOT}/src/ui/SearchWidget.cpp", r"""#include "SearchWidget.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QDirIterator>
#include <QFile>
#include <QTextStream>
#include <QFileInfo>

SearchThread::SearchThread(const QString& rootPath, const QString& query, QObject* parent)
    : QThread(parent), root(rootPath), q(query) {}

void SearchThread::run() {
    if (root.isEmpty() || q.isEmpty()) return;
    
    QDirIterator it(root, QDir::Files, QDirIterator::Subdirectories);
    while (it.hasNext()) {
        if (isInterruptionRequested()) break;
        QString path = it.next();
        
        QString cleanPath = QDir::cleanPath(path);
        if (cleanPath.contains("/.git/") || cleanPath.contains("/build/") || cleanPath.contains("/.agents/") || cleanPath.contains("/.antigravity/")) {
            continue;
        }
        
        QFileInfo info(path);
        QString ext = info.suffix().toLower();
        if (ext != "cpp" && ext != "hpp" && ext != "h" && ext != "txt" && ext != "md" && ext != "py" && ext != "json" && ext != "cmake") {
            continue;
        }

        QFile file(path);
        if (file.open(QIODevice::ReadOnly | QIODevice::Text)) {
            QTextStream in(&file);
            int lineNumber = 1;
            while (!in.atEnd()) {
                if (isInterruptionRequested()) break;
                QString line = in.readLine();
                if (line.contains(q, Qt::CaseInsensitive)) {
                    emit matchFound(path, lineNumber, line.trimmed());
                }
                lineNumber++;
            }
            file.close();
        }
    }
}

SearchWidget::SearchWidget(QWidget* parent)
    : QWidget(parent), activeThread(nullptr)
{
    auto* layout = new QVBoxLayout(this);
    layout->setContentsMargins(5, 5, 5, 5);

    auto* searchBar = new QHBoxLayout();
    searchEdit = new QLineEdit(this);
    searchEdit->setPlaceholderText("Search in workspace...");
    searchEdit->setStyleSheet("QLineEdit { background-color: #1e1e1e; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 4px; font-family: 'Segoe UI', Arial; }");
    
    searchBtn = new QPushButton("Find", this);
    searchBtn->setStyleSheet("QPushButton { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 4px 8px; font-family: 'Segoe UI', Arial; }"
                             "QPushButton:hover { background-color: #3e4452; color: #ffffff; }");
    
    searchBar->addWidget(searchEdit);
    searchBar->addWidget(searchBtn);
    layout->addLayout(searchBar);

    auto* semanticBar = new QHBoxLayout();
    semanticSearchCheckbox = new QCheckBox("Semantic (AI RAG)", this);
    semanticSearchCheckbox->setStyleSheet("QCheckBox { color: #abb2bf; font-size: 11px; }");
    
    indexBtn = new QPushButton("Rebuild Index", this);
    indexBtn->setStyleSheet("QPushButton { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 3px; padding: 2px 6px; font-size: 11px; }"
                            "QPushButton:hover { background-color: #3e4452; color: #ffffff; }");
    
    semanticBar->addWidget(semanticSearchCheckbox);
    semanticBar->addWidget(indexBtn);
    layout->addLayout(semanticBar);

    progressLabel = new QLabel(this);
    progressLabel->setStyleSheet("QLabel { color: #5c6370; font-size: 11px; padding: 2px; }");
    layout->addWidget(progressLabel);

    resultsTree = new QTreeWidget(this);
    resultsTree->setHeaderLabel("Search Results");
    resultsTree->setStyleSheet("QTreeWidget { background-color: #1e1e1e; color: #abb2bf; border: none; font-family: 'Segoe UI', Arial; }"
                               "QTreeWidget::item:hover { background-color: #2c313c; }"
                               "QTreeWidget::item:selected { background-color: #3e4452; color: #ffffff; }");
    layout->addWidget(resultsTree);

    connect(searchEdit, &QLineEdit::returnPressed, this, &SearchWidget::startSearch);
    connect(searchBtn, &QPushButton::clicked, this, &SearchWidget::startSearch);
    connect(indexBtn, &QPushButton::clicked, this, &SearchWidget::startIndexing);
    connect(resultsTree, &QTreeWidget::itemDoubleClicked, this, &SearchWidget::onDoubleClicked);

    connect(&VectorIndexManager::instance(), &VectorIndexManager::indexingProgress, this, &SearchWidget::updateProgress);
    connect(&VectorIndexManager::instance(), &VectorIndexManager::indexingFinished, this, &SearchWidget::indexingFinished);
    updateIndexStats();
}

void SearchWidget::setRootPath(const QString& path) {
    rootPath = path;
    updateIndexStats();
}

void SearchWidget::startIndexing() {
    if (rootPath.isEmpty()) return;
    indexBtn->setEnabled(false);
    progressLabel->setText("Building semantic index...");
    VectorIndexManager::instance().startIndexing(rootPath);
}

void SearchWidget::updateProgress(int current, int total) {
    QString lastErr = VectorIndexManager::instance().getLastError();
    if (!lastErr.isEmpty()) {
        progressLabel->setText(QString("Indexing codebase: %1 of %2 files... (Error: %3)")
                               .arg(current).arg(total).arg(lastErr.left(120)));
    } else {
        progressLabel->setText(QString("Indexing codebase: %1 of %2 files...").arg(current).arg(total));
    }
}

void SearchWidget::indexingFinished() {
    indexBtn->setEnabled(true);
    QString lastErr = VectorIndexManager::instance().getLastError();
    if (!lastErr.isEmpty()) {
        progressLabel->setText(QString("Indexing finished with errors. Last Error: %1").arg(lastErr.left(120)));
    } else {
        updateIndexStats();
    }
}

void SearchWidget::updateIndexStats() {
    auto stats = VectorIndexManager::instance().getIndexStats();
    progressLabel->setText(QString("Local Index: %1 chunks across %2 files indexed.")
                           .arg(stats.chunks)
                           .arg(stats.files));
}

void SearchWidget::startSearch() {
    if (semanticSearchCheckbox->isChecked()) {
        runSemanticSearch();
        return;
    }

    if (activeThread) {
        activeThread->requestInterruption();
        activeThread->wait();
        delete activeThread;
        activeThread = nullptr;
    }

    resultsTree->clear();
    progressLabel->clear();
    QString query = searchEdit->text().trimmed();
    if (query.isEmpty() || rootPath.isEmpty()) return;

    activeThread = new SearchThread(rootPath, query, this);
    connect(activeThread, &SearchThread::matchFound, this, &SearchWidget::addMatch);
    activeThread->start();
}

void SearchWidget::runSemanticSearch() {
    if (activeSemanticThread) {
        activeSemanticThread->requestInterruption();
        activeSemanticThread->wait();
        delete activeSemanticThread;
        activeSemanticThread = nullptr;
    }

    resultsTree->clear();
    QString query = searchEdit->text().trimmed();
    if (query.isEmpty() || rootPath.isEmpty()) return;

    progressLabel->setText("Querying vector model...");
    searchBtn->setEnabled(false);
    searchEdit->setEnabled(false);

    activeSemanticThread = new SemanticSearchThread(query, this);
    connect(activeSemanticThread, &SemanticSearchThread::searchCompleted, this, &SearchWidget::renderSemanticResults);
    connect(activeSemanticThread, &QThread::finished, this, [this]() {
        searchBtn->setEnabled(true);
        searchEdit->setEnabled(true);
    });
    activeSemanticThread->start();
}

void SearchWidget::renderSemanticResults(const QVector<SearchResult>& results) {
    progressLabel->setText(QString("Found %1 semantic matches.").arg(results.size()));
    for (const auto& r : results) {
        QList<QTreeWidgetItem*> items = resultsTree->findItems(r.filePath, Qt::MatchExactly, 0);
        QTreeWidgetItem* parentItem = nullptr;
        
        if (items.isEmpty()) {
            parentItem = new QTreeWidgetItem(resultsTree);
            parentItem->setText(0, r.filePath);
            parentItem->setToolTip(0, r.filePath);
        } else {
            parentItem = items.first();
        }

        auto* childItem = new QTreeWidgetItem(parentItem);
        childItem->setText(0, QString("[%1% Match] Line %2: %3").arg(qRound(r.score * 100)).arg(r.lineNumber).arg(r.lineContent));
        childItem->setData(0, Qt::UserRole, r.filePath);
        childItem->setData(0, Qt::UserRole + 1, r.lineNumber);
        
        parentItem->setExpanded(true);
    }
}

void SearchWidget::addMatch(const QString& filePath, int lineNumber, const QString& lineContent) {
    QList<QTreeWidgetItem*> items = resultsTree->findItems(filePath, Qt::MatchExactly, 0);
    QTreeWidgetItem* parentItem = nullptr;
    
    if (items.isEmpty()) {
        parentItem = new QTreeWidgetItem(resultsTree);
        parentItem->setText(0, filePath);
        parentItem->setToolTip(0, filePath);
    } else {
        parentItem = items.first();
    }

    auto* childItem = new QTreeWidgetItem(parentItem);
    childItem->setText(0, QString::number(lineNumber) + ": " + lineContent);
    childItem->setData(0, Qt::UserRole, filePath);
    childItem->setData(0, Qt::UserRole + 1, lineNumber);
    
    parentItem->setExpanded(true);
}

void SearchWidget::onDoubleClicked(QTreeWidgetItem* item, int /* column */) {
    QVariant fileVal = item->data(0, Qt::UserRole);
    QVariant lineVal = item->data(0, Qt::UserRole + 1);
    if (fileVal.isValid() && lineVal.isValid()) {
        emit matchActivated(fileVal.toString(), lineVal.toInt());
    }
}
""")

# ---------------------------------------------------------
# Git Control Widget (Visual staging and commits)
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/GitWidget.hpp", r"""#pragma once
#include <QWidget>
#include <QListWidget>
#include <QLineEdit>
#include <QProcess>

class GitWidget : public QWidget {
    Q_OBJECT
public:
    explicit GitWidget(QWidget* parent = nullptr);
    void setRootPath(const QString& path);

private slots:
    void refreshStatus();
    void commitChanges();
    void syncChanges();
    void onProcessFinished(int exitCode);

private:
    QString rootPath;
    QListWidget* statusList;
    QLineEdit* commitMessageEdit;
    QProcess* gitProcess;
    QString currentMode;
    QStringList filesToStage;
};
""")

write(f"{ROOT}/src/ui/GitWidget.cpp", r"""#include "GitWidget.hpp"
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
""")

# ---------------------------------------------------------
# C++ Syntax Highlighter
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/CppHighlighter.hpp", r"""#pragma once
#include <QSyntaxHighlighter>
#include <QTextCharFormat>
#include <QRegularExpression>
#include <vector>

class CppHighlighter : public QSyntaxHighlighter {
    Q_OBJECT
public:
    explicit CppHighlighter(QTextDocument* parent = nullptr);

protected:
    void highlightBlock(const QString& text) override;

private:
    struct HighlightingRule {
        QRegularExpression pattern;
        QTextCharFormat format;
    };
    std::vector<HighlightingRule> highlightingRules;

    QTextCharFormat keywordFormat;
    QTextCharFormat classFormat;
    QTextCharFormat singleLineCommentFormat;
    QTextCharFormat multiLineCommentFormat;
    QTextCharFormat quotationFormat;
    QTextCharFormat functionFormat;
    QTextCharFormat preprocessorFormat;
    QTextCharFormat numberFormat;
    
    QRegularExpression commentStartExpression;
    QRegularExpression commentEndExpression;
};
""")

write(f"{ROOT}/src/ui/CppHighlighter.cpp", r"""#include "CppHighlighter.hpp"
#include <QColor>
#include <QFont>
#include <QStringList>

CppHighlighter::CppHighlighter(QTextDocument* parent)
    : QSyntaxHighlighter(parent)
{
    HighlightingRule rule;

    // Keywords (Purple-ish theme matching modern dark UI)
    keywordFormat.setForeground(QColor(198, 120, 221));
    keywordFormat.setFontWeight(QFont::Bold);
    QStringList keywordPatterns;
    keywordPatterns << "\\bchar\\b" << "\\bclass\\b" << "\\bconst\\b"
                    << "\\bdouble\\b" << "\\benum\\b" << "\\bexplicit\\b"
                    << "\\bfloat\\b" << "\\bint\\b" << "\\blong\\b"
                    << "\\boperator\\b" << "\\bprivate\\b" << "\\bprotected\\b"
                    << "\\bpublic\\b" << "\\bshort\\b" << "\\bsignals\\b"
                    << "\\bsigned\\b" << "\\bslots\\b" << "\\bstatic\\b"
                    << "\\bstruct\\b" << "\\btemplate\\b" << "\\btypedef\\b"
                    << "\\btypename\\b" << "\\bunion\\b" << "\\bunsigned\\b"
                    << "\\bvirtual\\b" << "\\bvoid\\b" << "\\bvolatile\\b"
                    << "\\bbool\\b" << "\\bif\\b" << "\\belse\\b"
                    << "\\bfor\\b" << "\\bwhile\\b" << "\\bdo\\b"
                    << "\\breturn\\b" << "\\bswitch\\b" << "\\bcase\\b"
                    << "\\bbreak\\b" << "\\bcontinue\\b" << "\\bdefault\\b"
                    << "\\bnew\\b" << "\\bdelete\\b" << "\\btry\\b"
                    << "\\bcatch\\b" << "\\bthrow\\b" << "\\bnamespace\\b"
                    << "\\busing\\b" << "\\bconstexpr\\b" << "\\bnullptr\\b";
    for (const QString& pattern : keywordPatterns) {
        rule.pattern = QRegularExpression(pattern);
        rule.format = keywordFormat;
        highlightingRules.push_back(rule);
    }

    // Classes / Types (Yellow)
    classFormat.setForeground(QColor(229, 192, 123));
    classFormat.setFontWeight(QFont::Bold);
    rule.pattern = QRegularExpression("\\b[A-Z][a-zA-Z0-9_]*\\b");
    rule.format = classFormat;
    highlightingRules.push_back(rule);

    // Preprocessor directives (Red)
    preprocessorFormat.setForeground(QColor(224, 108, 117));
    rule.pattern = QRegularExpression("^\\s*#\\s*[a-zA-Z]+");
    rule.format = preprocessorFormat;
    highlightingRules.push_back(rule);

    // Functions (Blue)
    functionFormat.setForeground(QColor(97, 175, 239));
    rule.pattern = QRegularExpression("\\b[A-Za-z0-9_]+(?=\\s*\\()");
    rule.format = functionFormat;
    highlightingRules.push_back(rule);

    // Strings (Green)
    quotationFormat.setForeground(QColor(152, 195, 121));
    rule.pattern = QRegularExpression("\".*?\"");
    rule.format = quotationFormat;
    highlightingRules.push_back(rule);

    // Numbers (Orange)
    numberFormat.setForeground(QColor(209, 154, 102));
    rule.pattern = QRegularExpression("\\b\\d+(\\.\\d+)?\\b");
    rule.format = numberFormat;
    highlightingRules.push_back(rule);

    // Single line comments (Gray)
    singleLineCommentFormat.setForeground(QColor(92, 99, 112));
    singleLineCommentFormat.setFontItalic(true);
    rule.pattern = QRegularExpression("//[^\n]*");
    rule.format = singleLineCommentFormat;
    highlightingRules.push_back(rule);

    // Multi-line comments
    multiLineCommentFormat.setForeground(QColor(92, 99, 112));
    multiLineCommentFormat.setFontItalic(true);
    commentStartExpression = QRegularExpression(R"(\/\*)");
    commentEndExpression = QRegularExpression(R"(\*\/)");
}

void CppHighlighter::highlightBlock(const QString& text) {
    for (const auto& rule : highlightingRules) {
        QRegularExpressionMatchIterator matchIterator = rule.pattern.globalMatch(text);
        while (matchIterator.hasNext()) {
            QRegularExpressionMatch match = matchIterator.next();
            setFormat(match.capturedStart(), match.capturedLength(), rule.format);
        }
    }

    setCurrentBlockState(0);

    int startIndex = 0;
    if (previousBlockState() != 1) {
        QRegularExpressionMatch startMatch = commentStartExpression.match(text);
        if (startMatch.hasMatch()) {
            startIndex = startMatch.capturedStart();
        } else {
            startIndex = -1;
        }
    }

    while (startIndex >= 0) {
        QRegularExpressionMatch endMatch = commentEndExpression.match(text, startIndex);
        int commentLength;
        if (!endMatch.hasMatch()) {
            setCurrentBlockState(1);
            commentLength = text.length() - startIndex;
        } else {
            commentLength = endMatch.capturedStart() - startIndex + endMatch.capturedLength();
        }
        setFormat(startIndex, commentLength, multiLineCommentFormat);
        
        if (currentBlockState() == 1) {
            break;
        }
        
        QRegularExpressionMatch nextStartMatch = commentStartExpression.match(text, startIndex + commentLength);
        if (nextStartMatch.hasMatch()) {
            startIndex = nextStartMatch.capturedStart();
        } else {
            startIndex = -1;
        }
    }
}
""")

# ---------------------------------------------------------
# Command Palette (Fuzzy command search)
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/CommandPalette.hpp", r"""#pragma once
#include <QWidget>
#include <QListWidget>
#include <vector>
#include <functional>

class CommandPalette : public QWidget {
    Q_OBJECT
public:
    explicit CommandPalette(QWidget* parent = nullptr);

    void addCommand(const QString& name, const QString& shortcut, const std::function<void()>& action);
    void filterCommands(const QString& text);
    void selectNext();
    void selectPrev();
    void executeCurrent();

private:
    struct PaletteCommand {
        QString name;
        QString shortcut;
        std::function<void()> action;
    };
    std::vector<PaletteCommand> commands;
    QListWidget* listWidget;
};
""")

write(f"{ROOT}/src/ui/CommandPalette.cpp", r"""#include "CommandPalette.hpp"
#include <QVBoxLayout>
#include <QVariant>

CommandPalette::CommandPalette(QWidget* parent)
    : QWidget(parent, Qt::FramelessWindowHint | Qt::Popup)
{
    setAttribute(Qt::WA_ShowWithoutActivating);
    setFocusPolicy(Qt::NoFocus);
    
    setMinimumWidth(550);
    setMaximumHeight(250);
    setStyleSheet("QWidget { background-color: #21252b; border: 1px solid #3e4452; border-radius: 8px; }"
                  "QListWidget { background-color: #21252b; color: #abb2bf; border: none; font-size: 13px; font-family: 'Segoe UI', Arial; }"
                  "QListWidget::item { padding: 10px; border-bottom: 1px solid #2c313c; border-radius: 4px; }"
                  "QListWidget::item:selected { background-color: #3e4452; color: #ffffff; }");

    auto* layout = new QVBoxLayout(this);
    layout->setContentsMargins(2, 2, 2, 2);
    listWidget = new QListWidget(this);
    listWidget->setFocusPolicy(Qt::NoFocus);
    layout->addWidget(listWidget);
}

void CommandPalette::addCommand(const QString& name, const QString& shortcut, const std::function<void()>& action) {
    commands.push_back({name, shortcut, action});
}

void CommandPalette::filterCommands(const QString& text) {
    listWidget->clear();
    for (size_t i = 0; i < commands.size(); ++i) {
        if (text.isEmpty() || commands[i].name.contains(text, Qt::CaseInsensitive)) {
            auto* item = new QListWidgetItem(listWidget);
            QString label = commands[i].name;
            if (!commands[i].shortcut.isEmpty()) {
                label += "   (" + commands[i].shortcut + ")";
            }
            item->setText(label);
            item->setData(Qt::UserRole, QVariant::fromValue(static_cast<int>(i)));
        }
    }
    if (listWidget->count() > 0) {
        listWidget->setCurrentRow(0);
    }
}

void CommandPalette::selectNext() {
    int row = listWidget->currentRow();
    if (row < listWidget->count() - 1) {
        listWidget->setCurrentRow(row + 1);
    }
}

void CommandPalette::selectPrev() {
    int row = listWidget->currentRow();
    if (row > 0) {
        listWidget->setCurrentRow(row - 1);
    }
}

void CommandPalette::executeCurrent() {
    auto* item = listWidget->currentItem();
    if (item) {
        int idx = item->data(Qt::UserRole).toInt();
        if (idx >= 0 && idx < static_cast<int>(commands.size())) {
            commands[idx].action();
        }
    }
    hide();
}
""")

# ---------------------------------------------------------
# 1. Custom editor widget
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/CustomEditor.hpp", r"""#pragma once
#include <QWidget>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QString>

class CodeEditor;
class CppHighlighter;

class CustomEditor : public QWidget {
    Q_OBJECT
public:
    explicit CustomEditor(QWidget* parent = nullptr);

    void openFile(const QString& path);
    void saveFile();
    void saveAsFile();
    QString currentFilePath() const;
    CodeEditor* getCodeEditor() const { return editor; }

signals:
    void fileChanged(const QString& path);
    void closeRequested();

private:
    CodeEditor* editor;
    QPushButton* closeButton;
    QPushButton* saveAsButton;
    QString filePath;
    CppHighlighter* highlighter;
};

class CompletionPopup;

class CodeEditor : public QPlainTextEdit {
    Q_OBJECT
public:
    explicit CodeEditor(QWidget* parent = nullptr);

    void setFilePath(const QString& path);
    void updateGitDiff();
    void lineNumberAreaPaintEvent(QPaintEvent* event);
    int lineNumberAreaWidth();

    struct Diagnostic {
        int line;
        QString message;
        bool isError;
    };
    void setDiagnostics(const std::vector<Diagnostic>& diags);
    void clearDiagnostics();

protected:
    void resizeEvent(QResizeEvent* event) override;
    void keyPressEvent(QKeyEvent* event) override;
    void contextMenuEvent(QContextMenuEvent* event) override;
    void focusOutEvent(QFocusEvent* event) override;

private slots:
    void updateLineNumberAreaWidth(int newBlockCount);
    void highlightCurrentLine();
    void updateLineNumberArea(const QRect& rect, int dy);
    void onCompletionReady(int id, const QJsonArray& items);

private:
    void highlightDiagnostics(QList<QTextEdit::ExtraSelection>& selections);

    QWidget* lineNumberArea;
    QString filePath;
    QTimer* diffTimer;
    struct DiffLine {
        int line;
        char type; // 'A', 'M', 'D'
    };
    std::vector<DiffLine> diffLines;
    std::vector<Diagnostic> diagnostics;

    CompletionPopup* completionPopup;
    int activeCompletionId;
};

class LineNumberArea : public QWidget {
public:
    explicit LineNumberArea(CodeEditor* editor) : QWidget(editor), codeEditor(editor) {}

    QSize sizeHint() const override {
        return QSize(codeEditor->lineNumberAreaWidth(), 0);
    }

protected:
    void paintEvent(QPaintEvent* event) override {
        codeEditor->lineNumberAreaPaintEvent(event);
    }

private:
    CodeEditor* codeEditor;
};
""")

write(f"{ROOT}/src/ui/CustomEditor.cpp", r"""#include "CustomEditor.hpp"
#include "CppHighlighter.hpp"
#include "LspClient.hpp"
#include "CompletionPopup.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QPushButton>
#include <QFile>
#include <QTextStream>
#include <QFileDialog>
#include <QDir>
#include <QPainter>
#include <QPaintEvent>
#include <QTextBlock>
#include <QMenu>
#include <QContextMenuEvent>
#include <QTimer>
#include <QProcess>
#include <QMainWindow>

CustomEditor::CustomEditor(QWidget* parent)
    : QWidget(parent), closeButton(nullptr), saveAsButton(nullptr), highlighter(nullptr)
{
    auto* mainLayout = new QVBoxLayout(this);

    editor = new CodeEditor(this);
    mainLayout->addWidget(editor);

    highlighter = new CppHighlighter(editor->document());

    auto* buttonLayout = new QHBoxLayout();
    buttonLayout->addStretch();
    
    saveAsButton = new QPushButton("Save As", this);
    closeButton = new QPushButton("Close", this);
    
    buttonLayout->addWidget(saveAsButton);
    buttonLayout->addWidget(closeButton);
    mainLayout->addLayout(buttonLayout);

    connect(closeButton, &QPushButton::clicked, this, &CustomEditor::closeRequested);
    connect(saveAsButton, &QPushButton::clicked, this, &CustomEditor::saveAsFile);

    connect(editor, &QPlainTextEdit::textChanged, this, [this]() {
        if (!filePath.isEmpty()) {
            emit fileChanged(filePath);
        }
    });
}

void CustomEditor::openFile(const QString& path) {
    QFile f(path);
    if (!f.open(QIODevice::ReadOnly | QIODevice::Text)) {
        return;
    }
    QTextStream in(&f);
    QString content = in.readAll();
    editor->setPlainText(content);
    filePath = path;
    editor->setFilePath(path);
    
    LspClient::instance().didOpen(path, content);
}

void CustomEditor::saveFile() {
    if (filePath.isEmpty()) {
        saveAsFile();
        return;
    }
    QFile f(filePath);
    if (!f.open(QIODevice::WriteOnly | QIODevice::Text)) {
        return;
    }
    QTextStream out(&f);
    out << editor->toPlainText();
}

void CustomEditor::saveAsFile() {
    QString fileName = QFileDialog::getSaveFileName(
        this,
        "Save File",
        filePath.isEmpty() ? QDir::currentPath() : filePath,
        "Text Files (*.txt);;C++ Files (*.cpp *.hpp);;Header Files (*.h);;All Files (*.*)"
    );

    if (fileName.isEmpty()) return;

    filePath = fileName;
    QFile f(filePath);
    if (!f.open(QIODevice::WriteOnly | QIODevice::Text)) {
        return;
    }
    QTextStream out(&f);
    out << editor->toPlainText();
    editor->setFilePath(fileName);
}

QString CustomEditor::currentFilePath() const {
    return filePath;
}

// ---------------------------------------------------------
// CodeEditor Implementation
// ---------------------------------------------------------
CodeEditor::CodeEditor(QWidget* parent)
    : QPlainTextEdit(parent),
      lineNumberArea(nullptr),
      diffTimer(nullptr),
      completionPopup(nullptr),
      activeCompletionId(-1)
{
    lineNumberArea = new LineNumberArea(this);

    diffTimer = new QTimer(this);
    diffTimer->setSingleShot(true);
    connect(diffTimer, &QTimer::timeout, this, &CodeEditor::updateGitDiff);

    completionPopup = new CompletionPopup(this);
    connect(&LspClient::instance(), &LspClient::completionReady, this, &CodeEditor::onCompletionReady);

    connect(this, &CodeEditor::blockCountChanged, this, &CodeEditor::updateLineNumberAreaWidth);
    connect(this, &CodeEditor::updateRequest, this, &CodeEditor::updateLineNumberArea);
    connect(this, &CodeEditor::cursorPositionChanged, this, &CodeEditor::highlightCurrentLine);

    connect(this, &QPlainTextEdit::textChanged, this, [this]() {
        if (diffTimer) diffTimer->start(2000);
    });

    updateLineNumberAreaWidth(0);
    highlightCurrentLine();
    
    setStyleSheet("QPlainTextEdit { background-color: #1e1e1e; color: #abb2bf; font-family: 'Consolas', monospace; font-size: 11pt; border: none; }");
}

int CodeEditor::lineNumberAreaWidth() {
    int digits = 1;
    int max = std::max(1, blockCount());
    while (max >= 10) {
        max /= 10;
        digits++;
    }
    int space = 15 + fontMetrics().horizontalAdvance(QLatin1Char('9')) * digits;
    return space;
}

void CodeEditor::updateLineNumberAreaWidth(int /* newBlockCount */) {
    setViewportMargins(lineNumberAreaWidth(), 0, 0, 0);
}

void CodeEditor::updateLineNumberArea(const QRect& rect, int dy) {
    if (dy) {
        lineNumberArea->scroll(0, dy);
    } else {
        lineNumberArea->update(0, rect.y(), lineNumberArea->width(), rect.height());
    }

    if (rect.contains(viewport()->rect())) {
        updateLineNumberAreaWidth(0);
    }
}

void CodeEditor::resizeEvent(QResizeEvent* event) {
    QPlainTextEdit::resizeEvent(event);

    QRect cr = contentsRect();
    lineNumberArea->setGeometry(QRect(cr.left(), cr.top(), lineNumberAreaWidth(), cr.height()));
}

void CodeEditor::setDiagnostics(const std::vector<Diagnostic>& diags) {
    diagnostics = diags;
    highlightCurrentLine();
}

void CodeEditor::clearDiagnostics() {
    diagnostics.clear();
    highlightCurrentLine();
}

void CodeEditor::highlightDiagnostics(QList<QTextEdit::ExtraSelection>& selections) {
    for (const auto& diag : diagnostics) {
        QTextBlock block = document()->findBlockByNumber(diag.line - 1);
        if (block.isValid()) {
            QTextEdit::ExtraSelection selection;
            selection.cursor = QTextCursor(block);
            selection.cursor.select(QTextCursor::LineUnderCursor);
            
            QTextCharFormat format;
            format.setUnderlineStyle(QTextCharFormat::WaveUnderline);
            format.setUnderlineColor(diag.isError ? Qt::red : QColor(209, 154, 102));
            selection.format = format;
            
            selections.append(selection);
        }
    }
}

void CodeEditor::highlightCurrentLine() {
    QList<QTextEdit::ExtraSelection> extraSelections;

    if (!isReadOnly()) {
        QTextEdit::ExtraSelection selection;
        QColor lineColor = QColor(Qt::gray).darker(300);
        selection.format.setBackground(lineColor);
        selection.format.setProperty(QTextFormat::FullWidthSelection, true);
        selection.cursor = textCursor();
        selection.cursor.clearSelection();
        extraSelections.append(selection);
    }

    highlightDiagnostics(extraSelections);

    setExtraSelections(extraSelections);
}

void CodeEditor::lineNumberAreaPaintEvent(QPaintEvent* event) {
    QPainter painter(lineNumberArea);
    painter.fillRect(event->rect(), QColor(33, 37, 43));

    // Draw Git diff color bars on the left edge of the gutter
    int markerWidth = 3;
    QTextBlock block = firstVisibleBlock();
    int blockNumber = block.blockNumber();
    int top = qRound(blockBoundingGeometry(block).translated(contentOffset()).y());
    int bottom = top + qRound(blockBoundingRect(block).height());

    while (block.isValid() && top <= event->rect().bottom()) {
        if (block.isVisible() && bottom >= event->rect().top()) {
            QString number = QString::number(blockNumber + 1);
            painter.setPen(QColor(92, 99, 112));
            painter.drawText(0, top, lineNumberArea->width() - 5, fontMetrics().height(),
                             Qt::AlignRight | Qt::AlignVCenter, number);
            
            // Draw Git diff color bars
            for (const auto& dl : diffLines) {
                if (dl.line == blockNumber + 1) {
                    QColor color;
                    if (dl.type == 'A') color = QColor(152, 195, 121); // Green
                    else if (dl.type == 'M') color = QColor(97, 175, 239); // Blue
                    else if (dl.type == 'D') color = QColor(224, 108, 117); // Red
                    
                    painter.fillRect(QRect(0, top, markerWidth, bottom - top), color);
                    break;
                }
            }

            // Draw lightbulb emoji 💡 slightly to the left of the line number if diagnostic exists
            bool hasDiag = false;
            for (const auto& diag : diagnostics) {
                if (diag.line == blockNumber + 1) {
                    hasDiag = true;
                    break;
                }
            }
            if (hasDiag) {
                painter.drawText(2, top, lineNumberArea->width() - 5, fontMetrics().height(),
                                 Qt::AlignLeft | Qt::AlignVCenter, "💡");
            }
        }

        block = block.next();
        top = bottom;
        bottom = top + qRound(blockBoundingRect(block).height());
        blockNumber++;
    }
}

void CodeEditor::setFilePath(const QString& path) {
    filePath = path;
    updateGitDiff();
}

void CodeEditor::updateGitDiff() {
    diffLines.clear();
    if (filePath.isEmpty()) return;

    QFileInfo info(filePath);
    QString dir = info.dir().absolutePath();
    QString fileName = info.fileName();

    auto* proc = new QProcess();
    proc->setWorkingDirectory(dir);
    
    connect(proc, QOverload<int, QProcess::ExitStatus>::of(&QProcess::finished), this, [this, proc](int exitCode) {
        if (exitCode == 0) {
            QString out = proc->readAllStandardOutput();
            QStringList lines = out.split("\n", Qt::SkipEmptyParts);
            
            QRegularExpression regex("^@@ -(\\d+)(?:,(\\d+))? \\+(\\d+)(?:,(\\d+))? @@");
            for (const QString& line : lines) {
                auto match = regex.match(line);
                if (match.hasMatch()) {
                    int oldStart = match.captured(1).toInt();
                    int oldLen = match.captured(2).isEmpty() ? 1 : match.captured(2).toInt();
                    int newStart = match.captured(3).toInt();
                    int newLen = match.captured(4).isEmpty() ? 1 : match.captured(4).toInt();
                    
                    if (newLen == 0) {
                        diffLines.push_back({newStart, 'D'});
                    } else {
                        char type = (oldLen > 0) ? 'M' : 'A';
                        for (int l = 0; l < newLen; ++l) {
                            diffLines.push_back({newStart + l, type});
                        }
                    }
                }
            }
            if (lineNumberArea) lineNumberArea->update();
        }
        proc->deleteLater();
    });
    
    proc->start("git", QStringList() << "diff" << "-U0" << fileName);
}

void CodeEditor::keyPressEvent(QKeyEvent* event) {
    if (completionPopup && completionPopup->isVisible()) {
        if (event->key() == Qt::Key_Down) {
            int r = completionPopup->currentRow();
            if (r < completionPopup->count() - 1) completionPopup->setCurrentRow(r + 1);
            return;
        } else if (event->key() == Qt::Key_Up) {
            int r = completionPopup->currentRow();
            if (r > 0) completionPopup->setCurrentRow(r - 1);
            return;
        } else if (event->key() == Qt::Key_Enter || event->key() == Qt::Key_Return || event->key() == Qt::Key_Tab) {
            auto* item = completionPopup->currentItem();
            if (item) {
                QString replacement = item->data(Qt::UserRole).toString();
                QTextCursor tc = textCursor();
                tc.select(QTextCursor::WordUnderCursor);
                tc.removeSelectedText();
                tc.insertText(replacement);
            }
            completionPopup->hide();
            return;
        } else if (event->key() == Qt::Key_Escape) {
            completionPopup->hide();
            return;
        }
    }

    bool triggerAutocomplete = false;
    if (event->key() == Qt::Key_Space && (event->modifiers() & Qt::ControlModifier)) {
        triggerAutocomplete = true;
        event->accept();
    } else {
        QPlainTextEdit::keyPressEvent(event);
        QString text = event->text();
        if (text == "." || text == ">" || text == ":") {
            triggerAutocomplete = true;
        }
    }

    if (!filePath.isEmpty() && !event->text().isEmpty()) {
        LspClient::instance().didChange(filePath, toPlainText());
    }

    if (triggerAutocomplete && !filePath.isEmpty()) {
        QTextCursor tc = textCursor();
        int line = tc.blockNumber();
        int col = tc.columnNumber();
        activeCompletionId = LspClient::instance().requestCompletion(filePath, line, col);
    }
}

void CodeEditor::onCompletionReady(int id, const QJsonArray& items) {
    if (id == activeCompletionId) {
        if (items.isEmpty()) {
            completionPopup->hide();
        } else {
            completionPopup->setCompletions(items);
            QPoint pos = mapToGlobal(cursorRect().bottomLeft());
            completionPopup->setGeometry(pos.x(), pos.y() + 5, 250, 150);
            completionPopup->show();
        }
    }
}

void CodeEditor::contextMenuEvent(QContextMenuEvent* event) {
    QMenu* menu = createStandardContextMenu();
    menu->addSeparator();

    // Find if there is a diagnostic on the clicked line
    QTextCursor clickedCursor = cursorForPosition(event->pos());
    int clickedLine = clickedCursor.blockNumber() + 1;
    
    QString diagMessage;
    bool hasDiag = false;
    for (const auto& diag : diagnostics) {
        if (diag.line == clickedLine) {
            hasDiag = true;
            diagMessage = diag.message;
            break;
        }
    }

    QAction* aiFixAction = nullptr;
    if (hasDiag) {
        aiFixAction = menu->addAction("💡 Fix with AI...");
    }

    auto* gotoAction = menu->addAction("Go to Definition");
    auto* findRefAction = menu->addAction("Find References");

    QAction* selected = menu->exec(event->globalPos());
    if (selected == aiFixAction && hasDiag) {
        QWidget* w = parentWidget();
        while (w) {
            auto* mainWindow = qobject_cast<QMainWindow*>(w);
            if (mainWindow) {
                QMetaObject::invokeMethod(mainWindow, "fixProblemWithAI",
                                          Q_ARG(QString, filePath),
                                          Q_ARG(int, clickedLine),
                                          Q_ARG(QString, diagMessage));
                break;
            }
            w = w->parentWidget();
        }
    } else if (selected == gotoAction) {
        QTextCursor tc = cursorForPosition(event->pos());
        int line = tc.blockNumber();
        int col = tc.columnNumber();
        LspClient::instance().requestDefinition(filePath, line, col);
    } else if (selected == findRefAction) {
        QTextCursor tc = cursorForPosition(event->pos());
        int line = tc.blockNumber();
        int col = tc.columnNumber();
        LspClient::instance().requestReferences(filePath, line, col);
    }
    delete menu;
}

void CodeEditor::focusOutEvent(QFocusEvent* event) {
    QPlainTextEdit::focusOutEvent(event);
    if (completionPopup) {
        completionPopup->hide();
    }
}
""")

# ---------------------------------------------------------
# Terminal Widget for Shells
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/TerminalWidget.hpp", r"""#pragma once
#include <QWidget>
#include <QPlainTextEdit>
#include <QProcess>
#include <QSplitter>
#include <QVBoxLayout>

class TerminalPane : public QWidget {
    Q_OBJECT
public:
    explicit TerminalPane(const QString& shellPath, QPlainTextEdit* existingEdit = nullptr, QProcess* existingProc = nullptr, QWidget* parent = nullptr);
    ~TerminalPane() override;

signals:
    void closed();

protected:
    bool eventFilter(QObject* obj, QEvent* event) override;

private slots:
    void readOutput();
    void splitHorizontal();
    void splitVertical();
    void closePane();
    void onChildClosed();

private:
    void split(Qt::Orientation orientation);
    QString ansiToHtml(const QString& ansiText);

    QString shell;
    QPlainTextEdit* terminalEdit;
    QProcess* process;
    QWidget* toolbar;
    QWidget* contentArea;
    QVBoxLayout* contentLayout;
    
    bool isSplit;
    QSplitter* splitter;
    TerminalPane* child1;
    TerminalPane* child2;
};

class TerminalWidget : public QWidget {
    Q_OBJECT
public:
    explicit TerminalWidget(const QString& shellPath, QWidget* parent = nullptr);
private:
    TerminalPane* rootPane;
};
""")

write(f"{ROOT}/src/ui/TerminalWidget.cpp", r"""#include "TerminalWidget.hpp"
#include <QHBoxLayout>
#include <QPushButton>
#include <QKeyEvent>
#include <QRegularExpression>
#include <QTextCursor>
#include <QLabel>

TerminalPane::TerminalPane(const QString& shellPath, QPlainTextEdit* existingEdit, QProcess* existingProc, QWidget* parent)
    : QWidget(parent),
      shell(shellPath),
      terminalEdit(existingEdit),
      process(existingProc),
      isSplit(false),
      splitter(nullptr),
      child1(nullptr),
      child2(nullptr)
{
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);
    mainLayout->setSpacing(0);

    // Create toolbar
    toolbar = new QWidget(this);
    toolbar->setStyleSheet("QWidget { background-color: #282c34; border-bottom: 1px solid #181a1f; }");
    auto* toolbarLayout = new QHBoxLayout(toolbar);
    toolbarLayout->setContentsMargins(10, 2, 10, 2);
    
    QString label = shellPath.contains("powershell") ? "PowerShell" : "Bash";
    auto* shellLabel = new QLabel(label, this);
    shellLabel->setStyleSheet("QLabel { color: #abb2bf; font-weight: bold; font-family: 'Segoe UI', Arial; }");
    toolbarLayout->addWidget(shellLabel);
    toolbarLayout->addStretch();

    QString btnStyle = "QPushButton { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 2px 8px; font-family: 'Segoe UI', Arial; }"
                       "QPushButton:hover { background-color: #3e4452; color: #ffffff; }";
    
    auto* splitHBtn = new QPushButton("Split H", this);
    splitHBtn->setStyleSheet(btnStyle);
    connect(splitHBtn, &QPushButton::clicked, this, &TerminalPane::splitHorizontal);
    toolbarLayout->addWidget(splitHBtn);

    auto* splitVBtn = new QPushButton("Split V", this);
    splitVBtn->setStyleSheet(btnStyle);
    connect(splitVBtn, &QPushButton::clicked, this, &TerminalPane::splitVertical);
    toolbarLayout->addWidget(splitVBtn);

    auto* closeBtn = new QPushButton("Close", this);
    closeBtn->setStyleSheet("QPushButton { background-color: #e06c75; color: #1e1e1e; border: none; border-radius: 4px; padding: 2px 8px; font-family: 'Segoe UI', Arial; font-weight: bold; }"
                            "QPushButton:hover { background-color: #e5c07b; }");
    connect(closeBtn, &QPushButton::clicked, this, &TerminalPane::closePane);
    toolbarLayout->addWidget(closeBtn);

    // Show close button only if parent is a splitter
    auto* parentSplitter = qobject_cast<QSplitter*>(parent);
    closeBtn->setVisible(parentSplitter != nullptr);

    mainLayout->addWidget(toolbar);

    contentArea = new QWidget(this);
    contentLayout = new QVBoxLayout(contentArea);
    contentLayout->setContentsMargins(0, 0, 0, 0);
    contentLayout->setSpacing(0);
    mainLayout->addWidget(contentArea, 1);

    if (!terminalEdit && !process) {
        // Create new terminal session
        terminalEdit = new QPlainTextEdit(contentArea);
        QFont monoFont("Consolas", 10);
        if (monoFont.fixedPitch()) {
            terminalEdit->setFont(monoFont);
        }
        terminalEdit->setStyleSheet("QPlainTextEdit { background-color: #1e1e1e; color: #abb2bf; border: none; }");
        contentLayout->addWidget(terminalEdit);

        process = new QProcess(this);
        process->setProcessChannelMode(QProcess::MergedChannels);
        connect(process, &QProcess::readyReadStandardOutput, this, &TerminalPane::readOutput);
        
        terminalEdit->installEventFilter(this);

        QStringList args;
        if (shellPath.contains("bash.exe")) {
            args << "--login" << "-i";
        }
        process->start(shellPath, args);
    } else {
        // Take ownership of existing session
        terminalEdit->setParent(contentArea);
        contentLayout->addWidget(terminalEdit);
        terminalEdit->installEventFilter(this);
        connect(process, &QProcess::readyReadStandardOutput, this, &TerminalPane::readOutput);
    }
}

TerminalPane::~TerminalPane() {
    if (process && process->state() != QProcess::NotRunning) {
        process->terminate();
        process->waitForFinished(1000);
    }
}

void TerminalPane::splitHorizontal() {
    split(Qt::Horizontal);
}

void TerminalPane::splitVertical() {
    split(Qt::Vertical);
}

void TerminalPane::split(Qt::Orientation orientation) {
    if (isSplit) return;

    if (process) {
        disconnect(process, &QProcess::readyReadStandardOutput, this, &TerminalPane::readOutput);
    }
    if (terminalEdit) {
        terminalEdit->removeEventFilter(this);
        contentLayout->removeWidget(terminalEdit);
    }

    isSplit = true;
    
    splitter = new QSplitter(orientation, contentArea);
    contentLayout->addWidget(splitter);

    child1 = new TerminalPane(shell, terminalEdit, process, splitter);
    child2 = new TerminalPane(shell, nullptr, nullptr, splitter);

    terminalEdit = nullptr;
    process = nullptr;
    if (toolbar) toolbar->hide();

    splitter->addWidget(child1);
    splitter->addWidget(child2);

    connect(child1, &TerminalPane::closed, this, &TerminalPane::onChildClosed);
    connect(child2, &TerminalPane::closed, this, &TerminalPane::onChildClosed);
}

void TerminalPane::closePane() {
    emit closed();
}

void TerminalPane::onChildClosed() {
    auto* closedChild = qobject_cast<TerminalPane*>(sender());
    if (!closedChild) return;

    TerminalPane* remainingChild = (closedChild == child1) ? child2 : child1;

    // Reparent remaining session
    terminalEdit = remainingChild->terminalEdit;
    process = remainingChild->process;

    if (terminalEdit) {
        terminalEdit->setParent(contentArea);
        contentLayout->addWidget(terminalEdit);
        terminalEdit->installEventFilter(this);
    }
    if (process) {
        process->setParent(this);
        connect(process, &QProcess::readyReadStandardOutput, this, &TerminalPane::readOutput);
    }

    child1->deleteLater();
    child2->deleteLater();
    splitter->deleteLater();

    child1 = nullptr;
    child2 = nullptr;
    splitter = nullptr;
    isSplit = false;

    if (toolbar) toolbar->show();
}

bool TerminalPane::eventFilter(QObject* obj, QEvent* event) {
    if (obj == terminalEdit && event->type() == QEvent::KeyPress) {
        auto* keyEvent = static_cast<QKeyEvent*>(event);
        QString txt = keyEvent->text();
        
        if (keyEvent->modifiers() & Qt::ControlModifier) {
            if (keyEvent->key() == Qt::Key_C) {
                if (process) process->write("\x03");
                return true;
            } else if (keyEvent->key() == Qt::Key_Z) {
                if (process) process->write("\x1A");
                return true;
            } else if (keyEvent->key() == Qt::Key_D) {
                if (process) process->write("\x04");
                return true;
            }
            return false;
        }

        if (keyEvent->key() == Qt::Key_Return || keyEvent->key() == Qt::Key_Enter) {
            if (process) process->write("\r\n");
            return true;
        } else if (keyEvent->key() == Qt::Key_Backspace) {
            if (process) process->write("\b");
            return true;
        } else if (keyEvent->key() == Qt::Key_Tab) {
            if (process) process->write("\t");
            return true;
        } else if (keyEvent->key() == Qt::Key_Escape) {
            if (process) process->write("\x1B");
            return true;
        } else if (keyEvent->key() == Qt::Key_Up) {
            if (process) process->write("\x1B[A");
            return true;
        } else if (keyEvent->key() == Qt::Key_Down) {
            if (process) process->write("\x1B[B");
            return true;
        } else if (keyEvent->key() == Qt::Key_Right) {
            if (process) process->write("\x1B[C");
            return true;
        } else if (keyEvent->key() == Qt::Key_Left) {
            if (process) process->write("\x1B[D");
            return true;
        }

        if (!txt.isEmpty()) {
            if (process) process->write(txt.toLocal8Bit());
            return true;
        }
    }
    return QWidget::eventFilter(obj, event);
}

void TerminalPane::readOutput() {
    if (!process || !terminalEdit) return;
    QByteArray data = process->readAllStandardOutput();
    if (data.isEmpty()) return;

    QString text = QString::fromLocal8Bit(data);
    if (text.contains('\b')) {
        static QRegularExpression ansiRegex("\x1B\\[[0-9;]*[a-zA-Z]");
        text.remove(ansiRegex);
        for (int i = 0; i < text.length(); ++i) {
            if (text[i] == '\b') {
                QTextCursor cursor = terminalEdit->textCursor();
                cursor.movePosition(QTextCursor::End);
                cursor.deletePreviousChar();
            } else {
                terminalEdit->insertPlainText(QString(text[i]));
            }
        }
    } else {
        QString html = ansiToHtml(text);
        terminalEdit->moveCursor(QTextCursor::End);
        terminalEdit->appendHtml(html);
    }
    terminalEdit->moveCursor(QTextCursor::End);
}

QString TerminalPane::ansiToHtml(const QString& ansiText) {
    QString html = ansiText;
    html.replace("&", "&amp;");
    html.replace("<", "&lt;");
    html.replace(">", "&gt;");
    html.replace("\r", "");

    QRegularExpression regex("\x1B\\[([0-9;]*)m");
    QRegularExpressionMatchIterator it = regex.globalMatch(html);

    int lastPos = 0;
    QString result;
    QString currentStyle;
    bool inSpan = false;

    while (it.hasNext()) {
        QRegularExpressionMatch match = it.next();
        int pos = match.capturedStart();

        QString textSegment = html.mid(lastPos, pos - lastPos);
        if (inSpan) {
            result += textSegment + "</span>";
            inSpan = false;
        } else {
            result += textSegment;
        }

        QString params = match.captured(1);
        if (params.isEmpty() || params == "0") {
            currentStyle = "";
        } else {
            QStringList codes = params.split(";");
            QString fgColor, bgColor;
            bool bold = false;

            for (const QString& code : codes) {
                int val = code.toInt();
                if (val == 1) {
                    bold = true;
                } else if (val >= 30 && val <= 37) {
                    switch (val) {
                        case 30: fgColor = "#282c34"; break;
                        case 31: fgColor = "#e06c75"; break;
                        case 32: fgColor = "#98c379"; break;
                        case 33: fgColor = "#d19a66"; break;
                        case 34: fgColor = "#61afef"; break;
                        case 35: fgColor = "#c678dd"; break;
                        case 36: fgColor = "#56b6c2"; break;
                        case 37: fgColor = "#abb2bf"; break;
                    }
                } else if (val >= 40 && val <= 47) {
                    switch (val) {
                        case 40: bgColor = "#282c34"; break;
                        case 41: bgColor = "#e06c75"; break;
                        case 42: bgColor = "#98c379"; break;
                        case 43: bgColor = "#d19a66"; break;
                        case 44: bgColor = "#61afef"; break;
                        case 45: bgColor = "#c678dd"; break;
                        case 46: bgColor = "#56b6c2"; break;
                        case 47: bgColor = "#abb2bf"; break;
                    }
                }
            }

            currentStyle = "";
            if (!fgColor.isEmpty()) currentStyle += QString("color: %1;").arg(fgColor);
            if (!bgColor.isEmpty()) currentStyle += QString("background-color: %1;").arg(bgColor);
            if (bold) currentStyle += "font-weight: bold;";
        }

        if (!currentStyle.isEmpty()) {
            result += QString("<span style=\"%1\">").arg(currentStyle);
            inSpan = true;
        }

        lastPos = match.capturedEnd();
    }

    QString remaining = html.mid(lastPos);
    if (inSpan) {
        result += remaining + "</span>";
    } else {
        result += remaining;
    }

    result.replace("\n", "<br>");
    return result;
}

TerminalWidget::TerminalWidget(const QString& shellPath, QWidget* parent)
    : QWidget(parent)
{
    auto* layout = new QVBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);
    rootPane = new TerminalPane(shellPath, nullptr, nullptr, this);
    layout->addWidget(rootPane);
}
""")

# ---------------------------------------------------------
# Problems Widget
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/ProblemsWidget.hpp", r"""#pragma once
#include <QWidget>
#include <QString>

class QTableWidget;

class ProblemsWidget : public QWidget {
    Q_OBJECT
public:
    explicit ProblemsWidget(QWidget* parent = nullptr);
    void addProblem(const QString& severity, const QString& file, int line, int col, const QString& message);
    void clearProblems();

signals:
    void problemActivated(const QString& file, int line);

private:
    QTableWidget* table;
};
""")

write(f"{ROOT}/src/ui/ProblemsWidget.cpp", r"""#include "ProblemsWidget.hpp"
#include <QVBoxLayout>
#include <QTableWidget>
#include <QHeaderView>
#include <QTableWidgetItem>

ProblemsWidget::ProblemsWidget(QWidget* parent)
    : QWidget(parent)
{
    auto* layout = new QVBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);

    table = new QTableWidget(0, 4, this);
    table->setHorizontalHeaderLabels({"Severity", "File", "Line", "Message"});
    table->horizontalHeader()->setSectionResizeMode(3, QHeaderView::Stretch);
    table->horizontalHeader()->setSectionResizeMode(1, QHeaderView::ResizeToContents);
    table->setEditTriggers(QAbstractItemView::NoEditTriggers);
    table->setSelectionBehavior(QAbstractItemView::SelectRows);
    table->setAlternatingRowColors(true);
    table->verticalHeader()->setVisible(false);

    layout->addWidget(table);

    connect(table, &QTableWidget::itemDoubleClicked, this, [this](QTableWidgetItem* item) {
        int row = item->row();
        QString file = table->item(row, 1)->text();
        int line = table->item(row, 2)->text().toInt();
        emit problemActivated(file, line);
    });
}

void ProblemsWidget::clearProblems() {
    table->setRowCount(0);
}

void ProblemsWidget::addProblem(const QString& severity, const QString& file, int line, int col, const QString& message) {
    int row = table->rowCount();
    table->insertRow(row);

    auto* sevItem = new QTableWidgetItem(severity);
    if (severity.toLower() == "error") {
        sevItem->setForeground(QColor(220, 60, 60));
    } else if (severity.toLower() == "warning") {
        sevItem->setForeground(QColor(220, 160, 40));
    } else {
        sevItem->setForeground(QColor(100, 160, 240));
    }
    table->setItem(row, 0, sevItem);
    table->setItem(row, 1, new QTableWidgetItem(file));
    table->setItem(row, 2, new QTableWidgetItem(QString::number(line)));
    table->setItem(row, 3, new QTableWidgetItem(message));
    
    (void)col; // stored in item data if needed later
}
""")

# ---------------------------------------------------------
# Debug Widget (GDB/LLDB Wrapper Skeleton)
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/DebugWidget.hpp", r"""#pragma once
#include <QWidget>
#include <QProcess>
#include <QString>

class QPushButton;
class QPlainTextEdit;
class QTreeWidget;
class QLineEdit;
class QLabel;

class DebugWidget : public QWidget {
    Q_OBJECT
public:
    explicit DebugWidget(QWidget* parent = nullptr);
    ~DebugWidget() override;

private slots:
    void startDebugging();
    void stopDebugging();
    void stepOver();
    void stepInto();
    void continueDebug();
    void sendManualCommand();
    void readGdbOutput();
    void gdbFinished(int exitCode);

private:
    void sendGdbCommand(const QString& cmd);
    void updateVariables();
    void addVariable(const QString& name, const QString& type, const QString& val);
    
    // Simulation mode helpers
    void enterSimulationMode();
    void runSimulationStep();

    QProcess* gdbProcess;
    bool isSimulated;
    int simStepCount;

    QPushButton* startBtn;
    QPushButton* stopBtn;
    QPushButton* stepOverBtn;
    QPushButton* stepIntoBtn;
    QPushButton* continueBtn;
    QLabel* statusLabel;
    
    QPlainTextEdit* consoleLog;
    QLineEdit* cmdInput;
    QTreeWidget* variablesTree;
};
""")

write(f"{ROOT}/src/ui/DebugWidget.cpp", r"""#include "DebugWidget.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QSplitter>
#include <QTreeWidget>
#include <QTreeWidgetItem>
#include <QHeaderView>
#include <QPushButton>
#include <QLineEdit>
#include <QLabel>
#include <QPlainTextEdit>
#include <QDir>
#include <QFile>
#include <QRegularExpression>
#include <QDateTime>

DebugWidget::DebugWidget(QWidget* parent)
    : QWidget(parent),
      gdbProcess(nullptr),
      isSimulated(false),
      simStepCount(0)
{
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);

    // 1. Toolbar at the top
    auto* toolbar = new QHBoxLayout();
    startBtn = new QPushButton("Start Debugging", this);
    stopBtn = new QPushButton("Stop", this);
    stepOverBtn = new QPushButton("Step Over", this);
    stepIntoBtn = new QPushButton("Step Into", this);
    continueBtn = new QPushButton("Continue", this);
    statusLabel = new QLabel("Status: Idle", this);
    statusLabel->setStyleSheet("font-weight: bold; margin-left: 10px;");

    stopBtn->setEnabled(false);
    stepOverBtn->setEnabled(false);
    stepIntoBtn->setEnabled(false);
    continueBtn->setEnabled(false);

    toolbar->addWidget(startBtn);
    toolbar->addWidget(stopBtn);
    toolbar->addWidget(stepOverBtn);
    toolbar->addWidget(stepIntoBtn);
    toolbar->addWidget(continueBtn);
    toolbar->addWidget(statusLabel);
    toolbar->addStretch();
    mainLayout->addLayout(toolbar);

    // 2. Splitter for console output and variables inspector
    auto* splitter = new QSplitter(Qt::Horizontal, this);

    // Left container: Console output and manual command input
    auto* consoleContainer = new QWidget(this);
    auto* consoleLayout = new QVBoxLayout(consoleContainer);
    consoleLayout->setContentsMargins(0, 0, 0, 0);

    consoleLog = new QPlainTextEdit(this);
    consoleLog->setReadOnly(true);
    consoleLog->setStyleSheet("QPlainTextEdit { background-color: #1e1e1e; color: #d4d4d4; font-family: 'Consolas', monospace; }");
    consoleLayout->addWidget(consoleLog);

    auto* cmdLayout = new QHBoxLayout();
    cmdInput = new QLineEdit(this);
    cmdInput->setPlaceholderText("Enter GDB/debugger command...");
    cmdInput->setStyleSheet("QLineEdit { background-color: #2d2d2d; color: #ffffff; font-family: 'Consolas', monospace; }");
    cmdInput->setEnabled(false);
    cmdLayout->addWidget(cmdInput);
    consoleLayout->addLayout(cmdLayout);

    splitter->addWidget(consoleContainer);

    // Right container: Variables tree widget
    variablesTree = new QTreeWidget(this);
    variablesTree->setColumnCount(3);
    variablesTree->setHeaderLabels({"Name", "Type", "Value"});
    variablesTree->header()->setSectionResizeMode(QHeaderView::Stretch);
    variablesTree->setStyleSheet("QTreeWidget { background-color: #1e1e1e; color: #d4d4d4; } QHeaderView::section { background-color: #2d2d2d; color: #ffffff; }");
    splitter->addWidget(variablesTree);

    mainLayout->addWidget(splitter);

    // Connections
    connect(startBtn, &QPushButton::clicked, this, &DebugWidget::startDebugging);
    connect(stopBtn, &QPushButton::clicked, this, &DebugWidget::stopDebugging);
    connect(stepOverBtn, &QPushButton::clicked, this, &DebugWidget::stepOver);
    connect(stepIntoBtn, &QPushButton::clicked, this, &DebugWidget::stepInto);
    connect(continueBtn, &QPushButton::clicked, this, &DebugWidget::continueDebug);
    connect(cmdInput, &QLineEdit::returnPressed, this, &DebugWidget::sendManualCommand);
}

DebugWidget::~DebugWidget() {
    stopDebugging();
}

void DebugWidget::startDebugging() {
    consoleLog->clear();
    variablesTree->clear();
    simStepCount = 0;
    
    // Check if lldb-mi.exe exists in the toolchain directory
    QString lldbMiPath = "C:/Qt/Tools/llvm-mingw_64/bin/lldb-mi.exe";
    QString targetExe = QDir::currentPath() + "/ai-ide/build/src/ai-ide.exe";

    if (!QFile::exists(lldbMiPath)) {
        // Fallback: search system PATH for lldb-mi or gdb
        lldbMiPath = "lldb-mi.exe";
    }

    consoleLog->appendPlainText("--- Launching Debug Session ---");
    consoleLog->appendPlainText("Target Executable: " + targetExe);

    gdbProcess = new QProcess(this);
    gdbProcess->setProcessChannelMode(QProcess::MergedChannels);
    connect(gdbProcess, &QProcess::readyReadStandardOutput, this, &DebugWidget::readGdbOutput);
    connect(gdbProcess, static_cast<void(QProcess::*)(int, QProcess::ExitStatus)>(&QProcess::finished), this, [this](int exitCode) {
        this->gdbFinished(exitCode);
    });

    // Try to run lldb-mi or gdb
    QStringList args;
    args << targetExe;

    gdbProcess->start(lldbMiPath, args);
    if (!gdbProcess->waitForStarted(1500)) {
        // Debugger process failed to start, enter simulation fallback
        enterSimulationMode();
    } else {
        isSimulated = false;
        consoleLog->appendPlainText("Debugger process started successfully via: " + lldbMiPath);
        statusLabel->setText("Status: Running");
        startBtn->setEnabled(false);
        stopBtn->setEnabled(true);
        stepOverBtn->setEnabled(true);
        stepIntoBtn->setEnabled(true);
        continueBtn->setEnabled(true);
        cmdInput->setEnabled(true);
        
        // Initial setup commands
        sendGdbCommand("break main");
        sendGdbCommand("run");
    }
}

void DebugWidget::enterSimulationMode() {
    isSimulated = true;
    consoleLog->appendPlainText("\n[WARNING] lldb-mi.exe or gdb.exe not found in toolchain or system PATH.");
    consoleLog->appendPlainText("[INFO] Starting Panel in Debug Simulation Mode instead...\n");
    consoleLog->appendPlainText("[Sim] Process launched. Breakpoint hit at main() in src/main.cpp:5");
    
    statusLabel->setText("Status: Paused");
    startBtn->setEnabled(false);
    stopBtn->setEnabled(true);
    stepOverBtn->setEnabled(true);
    stepIntoBtn->setEnabled(true);
    continueBtn->setEnabled(true);
    cmdInput->setEnabled(true);

    updateVariables();
}

void DebugWidget::stopDebugging() {
    if (gdbProcess) {
        if (gdbProcess->state() != QProcess::NotRunning) {
            gdbProcess->write("quit\n");
            gdbProcess->waitForFinished(1000);
            if (gdbProcess->state() != QProcess::NotRunning) {
                gdbProcess->kill();
            }
        }
        gdbProcess->deleteLater();
        gdbProcess = nullptr;
    }

    isSimulated = false;
    statusLabel->setText("Status: Idle");
    startBtn->setEnabled(true);
    stopBtn->setEnabled(false);
    stepOverBtn->setEnabled(false);
    stepIntoBtn->setEnabled(false);
    continueBtn->setEnabled(false);
    cmdInput->setEnabled(false);
    consoleLog->appendPlainText("--- Debug Session Stopped ---");
}

void DebugWidget::stepOver() {
    if (isSimulated) {
        consoleLog->appendPlainText("[Sim] step over");
        runSimulationStep();
    } else {
        sendGdbCommand("next");
    }
}

void DebugWidget::stepInto() {
    if (isSimulated) {
        consoleLog->appendPlainText("[Sim] step into");
        runSimulationStep();
    } else {
        sendGdbCommand("step");
    }
}

void DebugWidget::continueDebug() {
    if (isSimulated) {
        consoleLog->appendPlainText("[Sim] continue");
        consoleLog->appendPlainText("[Sim] Program exited normally.");
        stopDebugging();
    } else {
        sendGdbCommand("continue");
    }
}

void DebugWidget::sendManualCommand() {
    QString cmd = cmdInput->text().trimmed();
    if (cmd.isEmpty()) return;

    consoleLog->appendPlainText("> " + cmd);
    cmdInput->clear();

    if (isSimulated) {
        if (cmd == "next" || cmd == "n") {
            stepOver();
        } else if (cmd == "step" || cmd == "s") {
            stepInto();
        } else if (cmd == "continue" || cmd == "c") {
            continueDebug();
        } else if (cmd == "info locals" || cmd == "info l") {
            updateVariables();
        } else {
            consoleLog->appendPlainText("[Sim Mode] Unsupported simulation command. Try 'next', 'step', 'continue', or 'info locals'.");
        }
    } else {
        sendGdbCommand(cmd);
    }
}

void DebugWidget::sendGdbCommand(const QString& cmd) {
    if (gdbProcess && gdbProcess->state() == QProcess::Running) {
        gdbProcess->write((cmd + "\n").toLocal8Bit());
    }
}

void DebugWidget::readGdbOutput() {
    if (!gdbProcess) return;
    QByteArray output = gdbProcess->readAllStandardOutput();
    if (!output.isEmpty()) {
        QString text = QString::fromLocal8Bit(output);
        consoleLog->appendPlainText(text);
        
        // Auto-refresh variables if we hit a stopping point
        if (text.contains("stopped") || text.contains("Breakpoint") || text.contains("step")) {
            sendGdbCommand("info locals");
        }
        
        // Parse simple locals from GDB output
        QStringList lines = text.split('\n');
        bool foundLocals = false;
        for (const QString& line : lines) {
            static QRegularExpression varRegex(R"(^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*)$)");
            auto match = varRegex.match(line.trimmed());
            if (match.hasMatch()) {
                if (!foundLocals) {
                    variablesTree->clear();
                    foundLocals = true;
                }
                QString name = match.captured(1);
                QString val = match.captured(2);
                addVariable(name, "auto", val);
            }
        }
    }
}

void DebugWidget::gdbFinished(int exitCode) {
    consoleLog->appendPlainText("Debugger process finished with exit code: " + QString::number(exitCode));
    stopDebugging();
}

void DebugWidget::addVariable(const QString& name, const QString& type, const QString& val) {
    auto* item = new QTreeWidgetItem(variablesTree);
    item->setText(0, name);
    item->setText(1, type);
    item->setText(2, val);
}

void DebugWidget::updateVariables() {
    variablesTree->clear();
    if (isSimulated) {
        if (simStepCount == 0) {
            addVariable("argc", "int", "1");
            addVariable("argv", "char**", "0x0000021a8d052a60");
            addVariable("app", "QApplication", "{...}");
            addVariable("isInitialized", "bool", "false");
        } else if (simStepCount == 1) {
            addVariable("argc", "int", "1");
            addVariable("argv", "char**", "0x0000021a8d052a60");
            addVariable("app", "QApplication", "{...}");
            addVariable("isInitialized", "bool", "true");
            addVariable("w", "EditorWindow", "{...}");
        } else if (simStepCount == 2) {
            addVariable("argc", "int", "1");
            addVariable("argv", "char**", "0x0000021a8d052a60");
            addVariable("app", "QApplication", "{...}");
            addVariable("isInitialized", "bool", "true");
            addVariable("w", "EditorWindow", "{...}");
            addVariable("loopCount", "int", "0");
        } else {
            addVariable("argc", "int", "1");
            addVariable("argv", "char**", "0x0000021a8d052a60");
            addVariable("app", "QApplication", "{...}");
            addVariable("isInitialized", "bool", "true");
            addVariable("w", "EditorWindow", "{...}");
            addVariable("loopCount", "int", QString::number(simStepCount - 2));
            addVariable("status", "QString", "\"Processing window event loop...\"");
        }
    }
}

void DebugWidget::runSimulationStep() {
    simStepCount++;
    statusLabel->setText("Status: Paused (Step " + QString::number(simStepCount) + ")");
    
    if (simStepCount == 1) {
        consoleLog->appendPlainText("[Sim] Stopped at main.cpp:6 - QApplication app(argc, argv);");
    } else if (simStepCount == 2) {
        consoleLog->appendPlainText("[Sim] Stopped at main.cpp:7 - EditorWindow w;");
    } else if (simStepCount == 3) {
        consoleLog->appendPlainText("[Sim] Stopped at main.cpp:8 - w.show();");
    } else {
        consoleLog->appendPlainText("[Sim] Stopped at main.cpp:9 - return app.exec(); (Iteration: " + QString::number(simStepCount - 3) + ")");
    }
    
    updateVariables();
}
""")

# ---------------------------------------------------------
# Welcome Widget (Dashboard Startup Screen)
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/WelcomeWidget.hpp", r"""#pragma once
#include <QWidget>

class WelcomeWidget : public QWidget {
    Q_OBJECT
public:
    explicit WelcomeWidget(QWidget* parent = nullptr);

signals:
    void newFileRequested();
    void openFileRequested();
    void openFolderRequested();
    void buildRequested();
    void settingsRequested();
};
""")

write(f"{ROOT}/src/ui/WelcomeWidget.cpp", r"""#include "WelcomeWidget.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QPushButton>
#include <QFrame>
#include <QPixmap>

WelcomeWidget::WelcomeWidget(QWidget* parent)
    : QWidget(parent)
{
    // Styling with visual theme matching VS Code dark welcoming styles
    setStyleSheet("QWidget { background-color: #1e1e1e; color: #abb2bf; }"
                  "QLabel#title { color: #61afef; font-family: 'Segoe UI', Arial, sans-serif; font-size: 36px; font-weight: bold; margin-bottom: 5px; }"
                  "QLabel#subtitle { color: #5c6370; font-family: 'Segoe UI', Arial, sans-serif; font-size: 15px; margin-bottom: 25px; }"
                  "QPushButton { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 6px; padding: 12px 24px; font-size: 14px; text-align: left; font-family: 'Segoe UI', Arial; min-width: 280px; margin-bottom: 10px; }"
                  "QPushButton:hover { background-color: #3e4452; color: #ffffff; border-color: #61afef; }"
                  "QPushButton:pressed { background-color: #4b5263; }");

    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setAlignment(Qt::AlignCenter);

    auto* container = new QWidget(this);
    auto* layout = new QVBoxLayout(container);
    layout->setContentsMargins(40, 40, 40, 40);
    layout->setAlignment(Qt::AlignCenter);

    auto* logoLabel = new QLabel(this);
    QPixmap logoPixmap(":/idelogo.png");
    if (!logoPixmap.isNull()) {
        logoLabel->setPixmap(logoPixmap.scaled(96, 96, Qt::KeepAspectRatio, Qt::SmoothTransformation));
    }
    logoLabel->setAlignment(Qt::AlignCenter);
    logoLabel->setStyleSheet("margin-bottom: 15px;");
    layout->addWidget(logoLabel);

    auto* titleLabel = new QLabel("AI-IDE", this);
    titleLabel->setObjectName("title");
    titleLabel->setAlignment(Qt::AlignCenter);
    layout->addWidget(titleLabel);

    auto* subtitleLabel = new QLabel("Next-generation C++ development powered by LLVM and Local AI", this);
    subtitleLabel->setObjectName("subtitle");
    subtitleLabel->setAlignment(Qt::AlignCenter);
    layout->addWidget(subtitleLabel);

    // Dark separator line
    auto* line = new QFrame(this);
    line->setFrameShape(QFrame::HLine);
    line->setStyleSheet("background-color: #2c313c; max-height: 1px; margin-bottom: 20px;");
    layout->addWidget(line);

    // Setup action buttons
    auto* newFileBtn = new QPushButton("📄  Create New File", this);
    auto* openFileBtn = new QPushButton("📂  Open Existing File", this);
    auto* openFolderBtn = new QPushButton("📁  Open Project Folder", this);
    auto* buildBtn = new QPushButton("🛠️  Build C++ Project", this);
    auto* settingsBtn = new QPushButton("⚙️  AI Provider Settings", this);

    layout->addWidget(newFileBtn);
    layout->addWidget(openFileBtn);
    layout->addWidget(openFolderBtn);
    layout->addWidget(buildBtn);
    layout->addWidget(settingsBtn);

    mainLayout->addWidget(container);

    // Click mappings
    connect(newFileBtn, &QPushButton::clicked, this, &WelcomeWidget::newFileRequested);
    connect(openFileBtn, &QPushButton::clicked, this, &WelcomeWidget::openFileRequested);
    connect(openFolderBtn, &QPushButton::clicked, this, &WelcomeWidget::openFolderRequested);
    connect(buildBtn, &QPushButton::clicked, this, &WelcomeWidget::buildRequested);
    connect(settingsBtn, &QPushButton::clicked, this, &WelcomeWidget::settingsRequested);
}
""")

# ---------------------------------------------------------
# 2. Diff viewer widget
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/DiffView.hpp", r"""#pragma once
#include <QWidget>
#include <QString>

class QPlainTextEdit;

class DiffView : public QWidget {
    Q_OBJECT
public:
    explicit DiffView(QWidget* parent = nullptr);

    void setTexts(const QString& original, const QString& modified);

private:
    QPlainTextEdit* leftView;
    QPlainTextEdit* rightView;
};
""")

write(f"{ROOT}/src/ui/DiffView.cpp", r"""#include "DiffView.hpp"
#include <QHBoxLayout>
#include <QPlainTextEdit>
#include <QStringList>

DiffView::DiffView(QWidget* parent)
    : QWidget(parent)
{
    auto* layout = new QHBoxLayout(this);
    leftView = new QPlainTextEdit(this);
    rightView = new QPlainTextEdit(this);

    leftView->setReadOnly(true);
    rightView->setReadOnly(true);
    
    // Set a monospace font for code clarity
    QFont monoFont("Consolas", 10);
    if (monoFont.fixedPitch()) {
        leftView->setFont(monoFont);
        rightView->setFont(monoFont);
    }

    layout->addWidget(leftView);
    layout->addWidget(rightView);
}

void DiffView::setTexts(const QString& original, const QString& modified) {
    leftView->clear();
    rightView->clear();

    QStringList leftLines = original.split('\n');
    QStringList rightLines = modified.split('\n');

    const int contextLines = 3;
    for (int i = 0; i < std::max(leftLines.size(), rightLines.size()); ++i) {
        bool isChanged = (i >= leftLines.size() || i >= rightLines.size() || leftLines[i] != rightLines[i]);
        bool nearChange = false;

        for (int j = i - contextLines; j <= i + contextLines; ++j) {
            if (j >= 0 && j < leftLines.size() && j < rightLines.size() && leftLines[j] != rightLines[j]) {
                nearChange = true; break;
            }
        }

        if (isChanged) {
            if (i < leftLines.size()) 
                leftView->appendHtml("<div style='background-color: #ffdce0;'>" + QString::number(i+1).rightJustified(4) + " | " + leftLines[i].toHtmlEscaped() + "</div>");
            if (i < rightLines.size())
                rightView->appendHtml("<div style='background-color: #e6ffed;'>" + QString::number(i+1).rightJustified(4) + " | " + rightLines[i].toHtmlEscaped() + "</div>");
        } else if (nearChange) {
            leftView->appendPlainText(QString::number(i+1).rightJustified(4) + " | " + leftLines[i]);
            rightView->appendPlainText(QString::number(i+1).rightJustified(4) + " | " + rightLines[i]);
        } else if (i > 0 && (i-1 < leftLines.size() && leftLines[i-1] != rightLines[i-1])) {
            leftView->appendPlainText(" --- [Hunk Boundary] --- ");
            rightView->appendPlainText(" --- [Hunk Boundary] --- ");
        }
    }
}
""")

# ---------------------------------------------------------
# 3. AI patch → diff → apply workflow (stub)
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/AIPatchController.hpp", r"""#pragma once
#include <QObject>
#include <QString>
#include <memory>
#include "SettingsManager.hpp"
#include "CustomEditor.hpp"

class AIProvider;

class AIPatchController : public QObject {
    Q_OBJECT
public:
    explicit AIPatchController(CustomEditor* editor, QObject* parent = nullptr);
    void setEditor(CustomEditor* ed);

public slots:
    void requestRefactor(const QString& instruction);

private:
    CustomEditor* editor;
    std::unique_ptr<AIProvider> provider;
};
""")

write(f"{ROOT}/src/ui/AIPatchController.cpp", r"""#include "AIPatchController.hpp"
#include "DiffView.hpp"
#include "../ai/GeminiProvider.hpp"
#include "../ai/OllamaProvider.hpp"
#include "../ai/ClaudeProvider.hpp"
#include "../ai/AntigravityProvider.hpp"
#include <QDialog>
#include <QVBoxLayout>
#include <QPushButton>
#include <QDialogButtonBox>
#include <QRegularExpression>
#include <QFile>
#include <QTextStream>
#include <QDir>

AIPatchController::AIPatchController(CustomEditor* ed, QObject* parent)
    : QObject(parent),
      editor(ed)
{
    auto& settings = SettingsManager::instance();
    if (settings.getProviderType() == "Gemini") {
        provider = std::make_unique<GeminiProvider>(settings.getGeminiApiKey(), settings.getGeminiEndpoint());
    } else if (settings.getProviderType() == "Claude") {
        provider = std::make_unique<ClaudeProvider>(settings.getClaudeApiKey(), settings.getClaudeEndpoint());
    } else if (settings.getProviderType() == "Antigravity AI") {
        provider = std::make_unique<AntigravityProvider>(settings.getAntigravityApiKey(), settings.getAntigravityEndpoint());
    } else {
        provider = std::make_unique<OllamaProvider>(settings.getOllamaEndpoint());
    }
}

void AIPatchController::setEditor(CustomEditor* ed) {
    editor = ed;
}

void AIPatchController::requestRefactor(const QString& instruction) {
    if (!editor) return;
    
    // Re-initialize provider on the fly based on latest settings
    auto& settings = SettingsManager::instance();
    if (settings.getProviderType() == "Gemini") {
        provider = std::make_unique<GeminiProvider>(settings.getGeminiApiKey(), settings.getGeminiEndpoint());
    } else if (settings.getProviderType() == "Claude") {
        provider = std::make_unique<ClaudeProvider>(settings.getClaudeApiKey(), settings.getClaudeEndpoint());
    } else if (settings.getProviderType() == "Antigravity AI") {
        provider = std::make_unique<AntigravityProvider>(settings.getAntigravityApiKey(), settings.getAntigravityEndpoint());
    } else {
        provider = std::make_unique<OllamaProvider>(settings.getOllamaEndpoint());
    }

    QString code = editor->currentFilePath().isEmpty()
        ? QString()
        : editor->findChild<QPlainTextEdit*>()->toPlainText();

    AIRequest req;
    req.mode = "refactor";
    req.prompt = instruction.toStdString() + "\n\n" + code.toStdString();

    AIResponse res = provider->send(req);

    QString rawResponse = QString::fromStdString(res.text);
    QString newCode;

    // Extract the code block from the Markdown response
    QRegularExpression codeRegex("```(?:[a-zA-Z0-9+#]+)?\\n([\\s\\S]*?)```");
    QRegularExpressionMatch match = codeRegex.match(rawResponse);
    if (match.hasMatch()) {
        newCode = match.captured(1).trimmed();
    } else {
        newCode = rawResponse.trimmed();
    }

    // Persist the proposed code to a physical file
    QString tempPath = QDir::tempPath() + "/ai_proposed_patch.txt";
    QFile tempFile(tempPath);
    if (tempFile.open(QIODevice::WriteOnly | QIODevice::Text)) {
        QTextStream out(&tempFile);
        out << newCode;
        tempFile.close();
    }

    DiffView diffView;
    diffView.setTexts(code, newCode);

    QDialog dlg;
    dlg.setWindowTitle("AI Patch Preview");
    auto* layout = new QVBoxLayout(&dlg);
    layout->addWidget(&diffView);

    auto* buttons = new QDialogButtonBox(QDialogButtonBox::Cancel | QDialogButtonBox::Ok, &dlg);
    layout->addWidget(buttons);

    QObject::connect(buttons, &QDialogButtonBox::accepted, &dlg, [&]() {
        auto* textEdit = editor->findChild<QPlainTextEdit*>();
        if (textEdit) {
            textEdit->setPlainText(newCode);
        }
        dlg.accept();
    });
    QObject::connect(buttons, &QDialogButtonBox::rejected, &dlg, [&]() {
        dlg.reject();
    });

    dlg.exec();
}
""")

# ---------------------------------------------------------
# 4. Git integration skeleton
# ---------------------------------------------------------
write(f"{ROOT}/src/git/GitClient.hpp", r"""#pragma once
#include <string>
#include <vector>

struct GitStatusEntry {
    std::string path;
    std::string status;
};

class GitClient {
public:
    explicit GitClient(const std::string& repoPath);

    std::vector<GitStatusEntry> status();
    void commit(const std::string& message);
    void add(const std::string& path);
    void push();

private:
    std::string repoPath;
};
""")

write(f"{ROOT}/src/git/GitClient.cpp", r"""#include "GitClient.hpp"
#include <iostream>

GitClient::GitClient(const std::string& path)
    : repoPath(path)
{
}

std::vector<GitStatusEntry> GitClient::status() {
    std::cout << "[Git] status in " << repoPath << std::endl;
    return {};
}

void GitClient::add(const std::string& path) {
    std::cout << "[Git] add " << path << std::endl;
}

void GitClient::commit(const std::string& message) {
    std::cout << "[Git] commit: " << message << std::endl;
}

void GitClient::push() {
    std::cout << "[Git] push from " << repoPath << std::endl;
}
""")

# ---------------------------------------------------------
# 5. Wire file browser → editor in EditorWindow
# ---------------------------------------------------------
write(f"{ROOT}/src/ui/ClipboardListener.hpp", r"""#pragma once
#include <QObject>
#include <QClipboard>
#include <QMimeData>

class ClipboardListener : public QObject {
    Q_OBJECT
public:
    explicit ClipboardListener(QObject* parent = nullptr);

signals:
    void codeCopied(const QString& text);

private slots:
    void onClipboardChanged();
};
""")

write(f"{ROOT}/src/ui/ClipboardListener.cpp", r"""#include "ClipboardListener.hpp"
#include <QApplication>

ClipboardListener::ClipboardListener(QObject* parent) : QObject(parent) {
    connect(QApplication::clipboard(), &QClipboard::dataChanged, this, &ClipboardListener::onClipboardChanged);
}

void ClipboardListener::onClipboardChanged() {
    const QMimeData* mimeData = QApplication::clipboard()->mimeData();
    if (mimeData->hasText()) {
        QString text = mimeData->text();
        if (text.length() > 5) { // Basic heuristic to ignore tiny snippets
            emit codeCopied(text);
        }
    }
}
""")

write(f"{ROOT}/src/ui/EditorWindow.hpp", r"""#pragma once

#include <QMainWindow>
#include <QTabWidget>
#include <QStringListModel>

class CustomEditor;
class FileBrowser;
class SearchWidget;
class GitWidget;
class WelcomeWidget;
class AIPatchController;
class CommandPalette;
class ClipboardListener;
class FindReplaceDialog;
class QShowEvent;
class QSplitter;
class QListView;
class QPlainTextEdit;
class QProcess;
class TerminalWidget;
class ProblemsWidget;
class DebugWidget;
class QLineEdit;
class QComboBox;
class QLabel;
class QTableWidget;

class EditorWindow : public QMainWindow {
    Q_OBJECT
public:
    explicit EditorWindow(QWidget *parent = nullptr);
    CustomEditor* currentEditor() const;

private:
    void createMenus();
    void createDocks();
    void createCentralEditor();
    void showEvent(QShowEvent* event) override;
    void openFileInTab(const QString& path);
    void runBuild();
    void readBuildOutput();
    void buildFinished(int exitCode, int exitStatus);
    void parseBuildLine(const QString& line);
    void gotoLine(const QString& file, int line);
    void openWelcomeTab();
    void openSearchTab();
    void showCommandPalette();
    bool eventFilter(QObject* obj, QEvent* event) override;
    void updateDocumentDiagnostics();
    void showSymbolReferences(const QJsonArray& locations);
    Q_INVOKABLE void fixProblemWithAI(const QString& filePath, int line, const QString& message);

    QTabWidget* tabWidget;
    QTabWidget* bottomTabWidget;
    QSplitter* mainSplitter;
    TerminalWidget* powerShellTab;
    TerminalWidget* bashTab;
    DebugWidget* debugTab;
    ProblemsWidget* problemsTab;
    QPlainTextEdit* outputTab;
    QListView* historyView;

    QProcess* buildProcess;

    CustomEditor* editor;
    FileBrowser* fileBrowser;
    SearchWidget* searchWidget;
    GitWidget* gitWidget;
    AIPatchController* aiPatchController;
    CommandPalette* commandPalette;
    QLineEdit* pathLineEdit;
    QLineEdit* cmdLineEdit;
    ClipboardListener* clipboardListener;
    QStringListModel* historyModel;
    QString buildBuffer;
    FindReplaceDialog* findReplaceDialog;

    QComboBox* cmakeTargetCombo;
    QComboBox* cmakeBuildTypeCombo;
    QTableWidget* referencesTable;

    struct EditorDiagnostic {
        QString file;
        int line;
        QString message;
        bool isError;
    };
    std::vector<EditorDiagnostic> activeDiagnostics;
};
""")

write(f"{ROOT}/src/ui/EditorWindow.cpp", r"""#include "EditorWindow.hpp"
#include <iostream>
#include "FileBrowser.hpp"
#include "AIChatPanel.hpp"
#include "CustomEditor.hpp"
#include "DiffView.hpp"
#include "AIPatchController.hpp"
#include "AdminDialog.hpp"
#include "ClipboardListener.hpp"
#include "FindReplaceDialog.hpp"
#include "TerminalWidget.hpp"
#include "ProblemsWidget.hpp"
#include "DebugWidget.hpp"
#include "WelcomeWidget.hpp"
#include "CommandPalette.hpp"
#include "SearchWidget.hpp"
#include "GitWidget.hpp"
#include "LspClient.hpp"
#include <QComboBox>
#include <QLabel>
#include <QTableWidget>
#include <QHeaderView>
#include <QUrl>
#include <QIcon>
#include <QPixmap>

#include <QMenuBar>
#include <QDockWidget>
#include <QListView>
#include <QSplitter>
#include <QPlainTextEdit>
#include <QProcess>
#include <QAction>
#include <QInputDialog>
#include <QFile>
#include <QFileDialog>
#include <QDir>
#include <QShowEvent>
#include <QTimer>
#include <QMessageBox>
#include <QKeyEvent>
#include <QLineEdit>
#include <QHBoxLayout>
#include <QVBoxLayout>
#include <QStatusBar>
#include <QStringListModel>
#include <QTextBlock>
#include <QTextCursor>
#include <QTextDocument>
#include <QMessageBox>

EditorWindow::EditorWindow(QWidget *parent)
    : QMainWindow(parent),
      tabWidget(nullptr),
      bottomTabWidget(nullptr),
      mainSplitter(nullptr),
      powerShellTab(nullptr),
      bashTab(nullptr),
      debugTab(nullptr),
      problemsTab(nullptr),
      outputTab(nullptr),
      historyView(nullptr),
      buildProcess(nullptr),
      fileBrowser(nullptr),
      searchWidget(nullptr),
      gitWidget(nullptr),
      aiPatchController(nullptr),
      commandPalette(nullptr),
      pathLineEdit(nullptr),
      cmdLineEdit(nullptr),
      cmakeTargetCombo(nullptr),
      cmakeBuildTypeCombo(nullptr),
      clipboardListener(nullptr),
      historyModel(new QStringListModel(this)),
      findReplaceDialog(nullptr)
{
    setWindowTitle("AI-IDE");
    setWindowIcon(QIcon(":/idelogo.png"));

    // Application-wide styling (Sleek dark theme)
    setStyleSheet(
        "QMainWindow { background-color: #21252b; color: #abb2bf; }"
        "QWidget { background-color: #21252b; color: #abb2bf; font-family: 'Segoe UI', Arial; }"
        "QScrollBar:vertical { background-color: #21252b; width: 12px; margin: 0px; }"
        "QScrollBar::handle:vertical { background-color: #3e4452; min-height: 20px; border-radius: 6px; border: 2px solid #21252b; }"
        "QScrollBar::handle:vertical:hover { background-color: #5c6370; }"
        "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }"
        "QScrollBar:horizontal { background-color: #21252b; height: 12px; margin: 0px; }"
        "QScrollBar::handle:horizontal { background-color: #3e4452; min-width: 20px; border-radius: 6px; border: 2px solid #21252b; }"
        "QScrollBar::handle:horizontal:hover { background-color: #5c6370; }"
        "QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }"
        "QTabWidget::pane { border: 1px solid #181a1f; background-color: #1e1e1e; }"
        "QTabBar::tab { background-color: #21252b; color: #abb2bf; padding: 8px 12px; border-top-left-radius: 4px; border-top-right-radius: 4px; border: 1px solid #181a1f; border-bottom: none; margin-right: 2px; }"
        "QTabBar::tab:selected { background-color: #1e1e1e; color: #ffffff; border-bottom: 2px solid #61afef; }"
        "QTabBar::tab:hover { background-color: #2c313c; color: #ffffff; }"
        "QTableWidget { background-color: #1e1e1e; color: #abb2bf; border: none; gridline-color: #282c34; selection-background-color: #3e4452; selection-color: #ffffff; }"
        "QTableWidget::item { padding: 4px; }"
        "QHeaderView::section { background-color: #21252b; color: #abb2bf; padding: 4px; border: 1px solid #181a1f; }"
        "QMenuBar { background-color: #21252b; color: #abb2bf; border-bottom: 1px solid #181a1f; }"
        "QMenuBar::item { background-color: transparent; padding: 4px 10px; }"
        "QMenuBar::item:selected { background-color: #3e4452; color: #ffffff; border-radius: 4px; }"
        "QMenu { background-color: #21252b; color: #abb2bf; border: 1px solid #181a1f; border-radius: 4px; padding: 4px 0px; }"
        "QMenu::item { padding: 6px 20px; }"
        "QMenu::item:selected { background-color: #3e4452; color: #ffffff; }"
        "QStatusBar { background-color: #21252b; color: #abb2bf; border-top: 1px solid #181a1f; }"
    );

    createCentralEditor();
    createDocks();
    createMenus();
    openWelcomeTab();
    
    // Defer ClipboardListener initialization until after the window is shown
    // to ensure the native window handle is fully initialized for AddClipboardFormatListener.
    // This is handled in showEvent.
}

void EditorWindow::showEvent(QShowEvent* event) {
    QMainWindow::showEvent(event); // Call base class implementation
    
    if (!clipboardListener && isVisible()) {
        // Ensure handle is created
        (void)winId();
        
        QTimer::singleShot(1000, this, [this]() {
            if (clipboardListener) return;
            clipboardListener = new ClipboardListener(this);
            connect(clipboardListener, &ClipboardListener::codeCopied, this, [this](const QString& text) {
                if (statusBar()) statusBar()->showMessage("Code detected in clipboard", 3000);
            });
        });
    }
}
void EditorWindow::createCentralEditor() {
    // Top Control Bar
    auto* topControlBar = new QWidget(this);
    topControlBar->setStyleSheet("QWidget { background-color: #21252b; border-bottom: 1px solid #181a1f; }");
    auto* topLayout = new QHBoxLayout(topControlBar);
    topLayout->setContentsMargins(10, 4, 10, 4);
    topLayout->setSpacing(20);

    // Left half: Path/Folder Browser
    auto* leftLayout = new QHBoxLayout();
    leftLayout->setSpacing(5);
    
    auto* browseBtn = new QPushButton("Browse...", this);
    browseBtn->setStyleSheet("QPushButton { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 4px 8px; font-family: 'Segoe UI', Arial; }"
                             "QPushButton:hover { background-color: #3e4452; color: #ffffff; }");
    
    pathLineEdit = new QLineEdit(this);
    pathLineEdit->setPlaceholderText("Enter folder or file path to browse...");
    pathLineEdit->setStyleSheet("QLineEdit { background-color: #1e1e1e; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 4px 8px; font-family: 'Segoe UI', Arial; }");
    
    leftLayout->addWidget(pathLineEdit, 1);
    leftLayout->addWidget(browseBtn);
    topLayout->addLayout(leftLayout, 1);

    // Right half: Command line edit
    cmdLineEdit = new QLineEdit(this);
    cmdLineEdit->setPlaceholderText("Type command (Ctrl+Shift+P)...");
    cmdLineEdit->setStyleSheet("QLineEdit { background-color: #1e1e1e; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 4px 8px; font-family: 'Segoe UI', Arial; }");
    topLayout->addWidget(cmdLineEdit, 1);

    // Path line edit triggers
    connect(pathLineEdit, &QLineEdit::returnPressed, this, [this]() {
        QString path = pathLineEdit->text().trimmed();
        if (!path.isEmpty()) {
            QFileInfo info(path);
            if (info.isDir()) {
                if (fileBrowser) fileBrowser->setRootDirectory(path);
            } else {
                openFileInTab(path);
            }
        }
    });

    connect(browseBtn, &QPushButton::clicked, this, [this]() {
        QString dir = QFileDialog::getExistingDirectory(this, "Open Project Folder", pathLineEdit->text());
        if (!dir.isEmpty()) {
            pathLineEdit->setText(dir);
            if (fileBrowser) fileBrowser->setRootDirectory(dir);
        }
    });

    // Command line edit event filtering and connections
    cmdLineEdit->installEventFilter(this);
    connect(cmdLineEdit, &QLineEdit::textChanged, this, [this](const QString& text) {
        if (commandPalette) {
            if (!commandPalette->isVisible()) showCommandPalette();
            commandPalette->filterCommands(text);
        }
    });

    tabWidget = new QTabWidget(this);
    tabWidget->setTabsClosable(true);
    connect(tabWidget, &QTabWidget::tabCloseRequested, this, [this](int index) {
        QWidget* w = tabWidget->widget(index);
        tabWidget->removeTab(index);
        if (w) w->deleteLater();
    });

    // Synchronize pathLineEdit with active tab changes
    connect(tabWidget, &QTabWidget::currentChanged, this, [this](int index) {
        if (index != -1) {
            auto* ed = qobject_cast<CustomEditor*>(tabWidget->widget(index));
            if (ed) {
                pathLineEdit->setText(ed->currentFilePath());
            } else if (qobject_cast<SearchWidget*>(tabWidget->widget(index))) {
                pathLineEdit->setText("Workspace Search");
            } else {
                pathLineEdit->setText("Welcome Page");
            }
        }
    });

    bottomTabWidget = new QTabWidget(this);

    // Create PowerShell terminal tab
    powerShellTab = new TerminalWidget("powershell.exe", this);

    // Create Bash terminal tab - detect Git Bash or fall back to wsl.exe
    QString bashExe;
    QStringList bashCandidates = {
        "C:/Program Files/Git/bin/bash.exe",
        "C:/Program Files (x86)/Git/bin/bash.exe",
        "C:/msys64/usr/bin/bash.exe",
    };
    for (const QString& candidate : bashCandidates) {
        if (QFile::exists(candidate)) { bashExe = candidate; break; }
    }
    if (bashExe.isEmpty()) {
        if (QFile::exists("C:/Windows/System32/wsl.exe")) {
            bashExe = "C:/Windows/System32/wsl.exe";
        } else {
            bashExe = "powershell.exe";
        }
    }
    bashTab = new TerminalWidget(bashExe, this);

    debugTab = new DebugWidget(this);
    problemsTab = new ProblemsWidget(this);
    connect(problemsTab, &ProblemsWidget::problemActivated, this, &EditorWindow::gotoLine);
    
    // Create read-only output terminal text edit
    outputTab = new QPlainTextEdit(this);
    outputTab->setReadOnly(true);
    QFont monoFont("Consolas", 10);
    if (monoFont.fixedPitch()) {
        outputTab->setFont(monoFont);
    }

    bottomTabWidget->addTab(powerShellTab, "PowerShell");
    bottomTabWidget->addTab(bashTab, "Bash");
    bottomTabWidget->addTab(debugTab, "Debug");
    bottomTabWidget->addTab(problemsTab, "Problems");
    bottomTabWidget->addTab(outputTab, "Output");

    // Add AI History view tab
    historyView = new QListView(this);
    historyView->setModel(historyModel);
    bottomTabWidget->addTab(historyView, "AI History");

    mainSplitter = new QSplitter(Qt::Vertical, this);
    mainSplitter->addWidget(tabWidget);
    mainSplitter->addWidget(bottomTabWidget);

    mainSplitter->setStretchFactor(0, 3);
    mainSplitter->setStretchFactor(1, 1);

    auto* container = new QWidget(this);
    auto* containerLayout = new QVBoxLayout(container);
    containerLayout->setContentsMargins(0, 0, 0, 0);
    containerLayout->setSpacing(0);
    containerLayout->addWidget(topControlBar);
    containerLayout->addWidget(mainSplitter);

    // Bottom Status Bar selectors
    cmakeBuildTypeCombo = new QComboBox(this);
    cmakeBuildTypeCombo->addItems(QStringList() << "Debug" << "Release" << "RelWithDebInfo" << "MinSizeRel");
    cmakeBuildTypeCombo->setStyleSheet("QComboBox { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 2px 6px; font-family: 'Segoe UI', Arial; font-size: 11px; }"
                                       "QComboBox::drop-down { border: none; }"
                                       "QComboBox QAbstractItemView { background-color: #2c313c; color: #abb2bf; selection-background-color: #3e4452; }");

    cmakeTargetCombo = new QComboBox(this);
    cmakeTargetCombo->addItems(QStringList() << "ai-ide" << "clean" << "rebuild");
    cmakeTargetCombo->setStyleSheet("QComboBox { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 2px 6px; font-family: 'Segoe UI', Arial; font-size: 11px; }"
                                    "QComboBox::drop-down { border: none; }"
                                    "QComboBox QAbstractItemView { background-color: #2c313c; color: #abb2bf; selection-background-color: #3e4452; }");

    if (statusBar()) {
        auto* buildLabel = new QLabel("  Config: ", this);
        buildLabel->setStyleSheet("QLabel { color: #abb2bf; font-family: 'Segoe UI', Arial; font-size: 11px; }");
        auto* targetLabel = new QLabel("  Target: ", this);
        targetLabel->setStyleSheet("QLabel { color: #abb2bf; font-family: 'Segoe UI', Arial; font-size: 11px; }");
        
        statusBar()->addPermanentWidget(buildLabel);
        statusBar()->addPermanentWidget(cmakeBuildTypeCombo);
        statusBar()->addPermanentWidget(targetLabel);
        statusBar()->addPermanentWidget(cmakeTargetCombo);
    }

    referencesTable = new QTableWidget(this);
    referencesTable->setColumnCount(3);
    referencesTable->setHorizontalHeaderLabels(QStringList() << "File" << "Line" << "Match");
    referencesTable->setStyleSheet("QTableWidget { background-color: #1e1e1e; color: #abb2bf; border: none; font-family: 'Segoe UI', Arial; font-size: 12px; }"
                                   "QTableWidget::item:hover { background-color: #2c313c; }"
                                   "QTableWidget::item:selected { background-color: #3e4452; color: #ffffff; }");
    referencesTable->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    
    connect(referencesTable, &QTableWidget::itemDoubleClicked, this, [this](QTableWidgetItem* item) {
        int row = item->row();
        auto* fileItem = referencesTable->item(row, 0);
        auto* lineItem = referencesTable->item(row, 1);
        if (fileItem && lineItem) {
            gotoLine(fileItem->toolTip(), lineItem->text().toInt());
        }
    });

    bottomTabWidget->addTab(referencesTable, "References");

    setCentralWidget(container);
}

void EditorWindow::openFileInTab(const QString& path) {
    auto* newEditor = new CustomEditor(this);
    if (!path.isEmpty()) newEditor->openFile(path);
    
    connect(newEditor, &CustomEditor::closeRequested, this, [this, newEditor]() {
        int idx = tabWidget->indexOf(newEditor);
        if (idx != -1) {
            tabWidget->removeTab(idx);
            newEditor->deleteLater();
        }
    });

    if (pathLineEdit) pathLineEdit->setText(path);

    QString title = path.isEmpty() ? "Untitled" : QFileInfo(path).fileName();
    int idx = tabWidget->addTab(newEditor, title);
    tabWidget->setCurrentIndex(idx);

    updateDocumentDiagnostics();
}

void EditorWindow::openWelcomeTab() {
    auto* welcome = new WelcomeWidget(this);
    connect(welcome, &WelcomeWidget::newFileRequested, this, [this]() { openFileInTab(""); });
    connect(welcome, &WelcomeWidget::openFileRequested, this, [this]() {
        QString path = QFileDialog::getOpenFileName(this, "Open File");
        if (!path.isEmpty()) openFileInTab(path);
    });
    connect(welcome, &WelcomeWidget::openFolderRequested, this, [this]() {
        QString dir = QFileDialog::getExistingDirectory(this, "Open Project Folder");
        if (!dir.isEmpty() && fileBrowser) {
            fileBrowser->setRootDirectory(dir);
        }
    });
    connect(welcome, &WelcomeWidget::buildRequested, this, &EditorWindow::runBuild);
    connect(welcome, &WelcomeWidget::settingsRequested, this, [this]() {
        AdminDialog dlg(this);
        dlg.exec();
    });

    int idx = tabWidget->addTab(welcome, "Welcome");
    tabWidget->setCurrentIndex(idx);
}

void EditorWindow::openSearchTab() {
    int searchIdx = -1;
    for (int i = 0; i < tabWidget->count(); ++i) {
        if (qobject_cast<SearchWidget*>(tabWidget->widget(i))) {
            searchIdx = i;
            break;
        }
    }
    
    if (searchIdx != -1) {
        tabWidget->setCurrentIndex(searchIdx);
    } else {
        auto* sWidget = new SearchWidget(this);
        if (fileBrowser) {
            sWidget->setRootPath(fileBrowser->rootPath());
        }
        connect(sWidget, &SearchWidget::matchActivated, this, &EditorWindow::gotoLine);
        
        int idx = tabWidget->addTab(sWidget, "Workspace Search");
        tabWidget->setCurrentIndex(idx);
    }
}

void EditorWindow::showCommandPalette() {
    if (!commandPalette) {
        commandPalette = new CommandPalette(this);
        commandPalette->addCommand("File: New File", "Ctrl+N", [this]() { openFileInTab(""); });
        commandPalette->addCommand("File: Open File", "Ctrl+O", [this]() {
            QString path = QFileDialog::getOpenFileName(this, "Open File");
            if (!path.isEmpty()) openFileInTab(path);
        });
        commandPalette->addCommand("File: Search in Workspace", "Ctrl+Shift+F", [this]() { openSearchTab(); });
        commandPalette->addCommand("File: Open Folder", "", [this]() {
            QString dir = QFileDialog::getExistingDirectory(this, "Open Project Folder");
            if (!dir.isEmpty() && fileBrowser) {
                fileBrowser->setRootDirectory(dir);
            }
        });
        commandPalette->addCommand("Build: Build Project", "Ctrl+B", [this]() { runBuild(); });
        commandPalette->addCommand("AI: Refactor with AI", "", [this]() {
            bool ok = false;
            QString instr = QInputDialog::getText(this, "AI Refactor",
                                                  "Describe the refactor:",
                                                  QLineEdit::Normal,
                                                  "", &ok);
            if (ok && !instr.trimmed().isEmpty()) {
                aiPatchController->setEditor(currentEditor());
                aiPatchController->requestRefactor(instr.trimmed());
            }
        });
        commandPalette->addCommand("AI: Provider Settings", "", [this]() {
            AdminDialog dlg(this);
            dlg.exec();
        });
        commandPalette->addCommand("Debugger: Start/Stop", "", [this]() {
            if (bottomTabWidget && debugTab) {
                bottomTabWidget->setCurrentWidget(debugTab);
                auto* startBtn = debugTab->findChild<QPushButton*>();
                if (startBtn) startBtn->click();
            }
        });
        commandPalette->addCommand("Help: About", "", [this]() {
            QMessageBox::about(this, "About AI-IDE", "AI-IDE\nNext-generation C++ development powered by LLVM and Local AI.");
        });
    }
    
    if (cmdLineEdit) {
        commandPalette->filterCommands(cmdLineEdit->text());
        QPoint pos = cmdLineEdit->mapToGlobal(QPoint(0, cmdLineEdit->height()));
        commandPalette->setGeometry(pos.x(), pos.y(), cmdLineEdit->width(), 200);
        commandPalette->show();
        cmdLineEdit->setFocus();
    }
}

bool EditorWindow::eventFilter(QObject* obj, QEvent* event) {
    if (obj == cmdLineEdit) {
        if (event->type() == QEvent::KeyPress) {
            auto* keyEvent = static_cast<QKeyEvent*>(event);
            if (commandPalette && commandPalette->isVisible()) {
                if (keyEvent->key() == Qt::Key_Down) {
                    commandPalette->selectNext();
                    return true;
                } else if (keyEvent->key() == Qt::Key_Up) {
                    commandPalette->selectPrev();
                    return true;
                } else if (keyEvent->key() == Qt::Key_Enter || keyEvent->key() == Qt::Key_Return) {
                    commandPalette->executeCurrent();
                    cmdLineEdit->clear();
                    return true;
                } else if (keyEvent->key() == Qt::Key_Escape) {
                    commandPalette->hide();
                    return true;
                }
            } else if (keyEvent->key() == Qt::Key_Down || keyEvent->key() == Qt::Key_Up) {
                showCommandPalette();
                return true;
            }
        } else if (event->type() == QEvent::FocusIn) {
            showCommandPalette();
        } else if (event->type() == QEvent::FocusOut) {
            QTimer::singleShot(200, this, [this]() {
                if (commandPalette && !cmdLineEdit->hasFocus()) {
                    commandPalette->hide();
                }
            });
        }
    }
    return QMainWindow::eventFilter(obj, event);
}

void EditorWindow::createDocks() {
    std::cout << "[Diagnostics] createDocks: starting..." << std::endl;
    // File Browser / Explorer Dock (Left)
    auto* fileDock = new QDockWidget("Explorer", this);
    fileDock->setMinimumWidth(280);
    
    auto* leftTabs = new QTabWidget(fileDock);
    leftTabs->setStyleSheet("QTabWidget::pane { border: none; }"
                            "QTabBar::tab { background-color: #21252b; color: #abb2bf; padding: 8px 12px; font-family: 'Segoe UI', Arial; }"
                            "QTabBar::tab:selected { background-color: #1e1e1e; color: #ffffff; border-bottom: 2px solid #61afef; }");

    std::cout << "[Diagnostics] createDocks: instantiating FileBrowser and GitWidget..." << std::endl;
    fileBrowser = new FileBrowser(leftTabs);
    gitWidget = new GitWidget(leftTabs);

    leftTabs->addTab(fileBrowser, "Files");
    leftTabs->addTab(gitWidget, "Git");
 
    fileDock->setWidget(leftTabs);
    addDockWidget(Qt::LeftDockWidgetArea, fileDock);
 
    std::cout << "[Diagnostics] createDocks: connecting signals..." << std::endl;
    connect(fileBrowser, &FileBrowser::fileOpened, this, [this](const QString& path) {
        openFileInTab(path);
    });
 
    connect(fileBrowser, &FileBrowser::rootChanged, this, [this](const QString& path) {
        if (pathLineEdit) pathLineEdit->setText(path);
        if (gitWidget) gitWidget->setRootPath(path);
        if (!path.isEmpty()) {
            VectorIndexManager::instance().startIndexing(path);
        }
        for (int i = 0; i < tabWidget->count(); ++i) {
            auto* sWidget = qobject_cast<SearchWidget*>(tabWidget->widget(i));
            if (sWidget) sWidget->setRootPath(path);
        }
    });
 
    std::cout << "[Diagnostics] createDocks: initializing initialPath..." << std::endl;
    QString initialPath = QDir::currentPath();
    std::cout << "[Diagnostics] createDocks: initialPath is " << initialPath.toStdString() << std::endl;
    if (pathLineEdit) pathLineEdit->setText(initialPath);
    
    std::cout << "[Diagnostics] createDocks: setting gitWidget root path..." << std::endl;
    if (gitWidget) gitWidget->setRootPath(initialPath);
    
    std::cout << "[Diagnostics] createDocks: starting background vector indexing..." << std::endl;
    if (!initialPath.isEmpty()) {
        VectorIndexManager::instance().startIndexing(initialPath);
    }

    std::cout << "[Diagnostics] createDocks: starting LSP server..." << std::endl;
    LspClient::instance().startServer(initialPath);
    std::cout << "[Diagnostics] createDocks: setup complete!" << std::endl;

    connect(&LspClient::instance(), &LspClient::definitionReady, this, [this](int id, const QString& path, int line) {
        if (!path.isEmpty()) {
            gotoLine(path, line);
        }
    });

    connect(&LspClient::instance(), &LspClient::referencesReady, this, [this](int id, const QJsonArray& locations) {
        showSymbolReferences(locations);
    });

    // AI Chat (Right)
    auto* aiDock = new QDockWidget("AI Chat", this);
    auto* aiPanel = new AIChatPanel(aiDock);
    aiDock->setWidget(aiPanel);
    addDockWidget(Qt::RightDockWidgetArea, aiDock);

    // Connect AI Chat signals to the Central Editor
    connect(aiPanel, &AIChatPanel::applyToEditor, this, [this](const QString& code) {
        if (auto* ed = currentEditor()) {
            auto* textEdit = ed->findChild<QPlainTextEdit*>();
            if (textEdit) textEdit->setPlainText(code);
        }
    });

    connect(aiPanel, &AIChatPanel::createNewFile, this, [this](const QString& code) {
        openFileInTab("");
        if (auto* ed = currentEditor()) {
            auto* textEdit = ed->findChild<QPlainTextEdit*>();
            if (textEdit) textEdit->setPlainText(code);
        }
    });

    connect(aiPanel, &AIChatPanel::promptArchived, this, [this](const QString& summary) {
        QStringList list = historyModel->stringList();
        list.prepend(summary);
        historyModel->setStringList(list);
    });

    aiPatchController = new AIPatchController(nullptr, this);
}

CustomEditor* EditorWindow::currentEditor() const {
    return qobject_cast<CustomEditor*>(tabWidget->currentWidget());
}

void EditorWindow::createMenus() {
    auto *fileMenu = menuBar()->addMenu("&File");
    
    fileMenu->addAction("New File", [this]() {
        openFileInTab("");
    });
    
    fileMenu->addSeparator();

    fileMenu->addAction("Open File", [this]() {
        QString path = QFileDialog::getOpenFileName(this, "Open File");
        if (!path.isEmpty()) openFileInTab(path);
    });

    fileMenu->addAction("Open Folder", [this]() {
        QString dir = QFileDialog::getExistingDirectory(this, "Open Project Folder");
        if (!dir.isEmpty() && fileBrowser) {
            fileBrowser->setRootDirectory(dir);
        }
    });

    fileMenu->addAction("Close", [this]() {
        tabWidget->removeTab(tabWidget->currentIndex());
    });

    fileMenu->addAction("Save", [this]() {
        if (auto* ed = currentEditor()) ed->saveFile();
    });

    fileMenu->addAction("Save As", [this]() {
        if (auto* ed = currentEditor()) ed->saveAsFile();
    });

    fileMenu->addSeparator();
    fileMenu->addAction("Exit", this, SLOT(close()));

    auto *aiMenu = menuBar()->addMenu("&AI");
    auto *refactorAction = aiMenu->addAction("Refactor with AI");
    connect(refactorAction, &QAction::triggered, this, [this]() {
        bool ok = false;
        QString instr = QInputDialog::getText(this, "AI Refactor",
                                              "Describe the refactor:",
                                              QLineEdit::Normal,
                                              "", &ok);
        if (ok && !instr.trimmed().isEmpty()) {
            aiPatchController->setEditor(currentEditor());
            aiPatchController->requestRefactor(instr.trimmed());
        }
    });

    aiMenu->addAction("AI Settings (Admin)", [this]() {
        AdminDialog dlg(this);
        dlg.exec();
    });

    auto *editMenu = menuBar()->addMenu("&Edit");
    auto *findAction = editMenu->addAction("Find & Replace...", [this]() {
        if (!findReplaceDialog) {
            findReplaceDialog = new FindReplaceDialog(this);
        }
        findReplaceDialog->showReplace();
    });
    findAction->setShortcut(QKeySequence(Qt::CTRL | Qt::Key_F));

    auto *folderSearchAction = editMenu->addAction("Search in Folder...", [this]() {
        if (!findReplaceDialog) {
            findReplaceDialog = new FindReplaceDialog(this);
        }
        findReplaceDialog->showFolderSearch(QDir::currentPath());
    });
    folderSearchAction->setShortcut(QKeySequence(Qt::CTRL | Qt::SHIFT | Qt::Key_F));

    auto *buildMenu = menuBar()->addMenu("&Build");
    buildMenu->addAction("Build Project", QKeySequence(Qt::CTRL | Qt::Key_B), this, &EditorWindow::runBuild);

    auto *searchAction = menuBar()->addAction("Search Workspace", this, &EditorWindow::openSearchTab);
    searchAction->setShortcut(QKeySequence(Qt::CTRL | Qt::SHIFT | Qt::Key_F));

    auto *helpMenu = menuBar()->addMenu("&Help");
    helpMenu->addAction("About", [this]() {
        QMessageBox msgBox(this);
        msgBox.setWindowTitle("About AI-IDE");
        msgBox.setText("<h3>AI-IDE v1.0</h3><p>Next-generation C++ development powered by LLVM and Local AI.</p>");
        QPixmap logo(":/idelogo.png");
        if (!logo.isNull()) {
            msgBox.setIconPixmap(logo.scaled(64, 64, Qt::KeepAspectRatio, Qt::SmoothTransformation));
        }
        msgBox.exec();
    });

    auto *paletteAction = new QAction("Command Palette", this);
    paletteAction->setShortcut(QKeySequence(Qt::CTRL | Qt::SHIFT | Qt::Key_P));
    connect(paletteAction, &QAction::triggered, this, &EditorWindow::showCommandPalette);
    addAction(paletteAction);
}

void EditorWindow::runBuild() {
    if (buildProcess && buildProcess->state() != QProcess::NotRunning) {
        if (statusBar()) statusBar()->showMessage("Build is already running!", 3000);
        return;
    }

    if (!outputTab) return;
    outputTab->clear();
    
    if (problemsTab) {
        problemsTab->clearProblems();
    }
    
    buildBuffer.clear();
    activeDiagnostics.clear();

    // Clear diagnostics on all open editors
    for (int i = 0; i < tabWidget->count(); ++i) {
        if (auto* ed = qobject_cast<CustomEditor*>(tabWidget->widget(i))) {
            auto* codeEd = ed->findChild<CodeEditor*>();
            if (codeEd) codeEd->clearDiagnostics();
        }
    }

    // Switch to Output Tab
    if (bottomTabWidget) {
        int outputIndex = bottomTabWidget->indexOf(outputTab);
        if (outputIndex != -1) {
            bottomTabWidget->setCurrentIndex(outputIndex);
        }
    }

    if (statusBar()) statusBar()->showMessage("Building project...");

    if (!buildProcess) {
        buildProcess = new QProcess(this);
        buildProcess->setProcessChannelMode(QProcess::MergedChannels);
        connect(buildProcess, &QProcess::readyReadStandardOutput, this, &EditorWindow::readBuildOutput);
        connect(buildProcess, &QProcess::finished, this, [this](int exitCode, QProcess::ExitStatus status) {
            this->buildFinished(exitCode, static_cast<int>(status));
        });
    }
    
    buildProcess->setWorkingDirectory(QDir::currentPath());

    QStringList args;
    args << "build.py";
    if (cmakeBuildTypeCombo) {
        args << "--build-type" << cmakeBuildTypeCombo->currentText();
    }
    if (cmakeTargetCombo) {
        QString tgt = cmakeTargetCombo->currentText();
        if (tgt != "ai-ide") {
            args << "--target" << tgt;
        }
    }
    buildProcess->start("python", args);
}

void EditorWindow::readBuildOutput() {
    if (!buildProcess || !outputTab) return;
    
    QByteArray data = buildProcess->readAllStandardOutput();
    if (data.isEmpty()) return;
    
    QString text = QString::fromLocal8Bit(data);
    outputTab->insertPlainText(text);
    outputTab->moveCursor(QTextCursor::End);
    
    buildBuffer.append(text);
    
    int newlineIdx;
    while ((newlineIdx = buildBuffer.indexOf('\n')) != -1) {
        QString line = buildBuffer.left(newlineIdx).trimmed();
        buildBuffer.remove(0, newlineIdx + 1);
        if (!line.isEmpty()) {
            parseBuildLine(line);
        }
    }
}

void EditorWindow::buildFinished(int exitCode, int exitStatus) {
    // Process any leftover text in the buffer
    if (!buildBuffer.isEmpty()) {
        QString line = buildBuffer.trimmed();
        if (!line.isEmpty()) {
            parseBuildLine(line);
        }
        buildBuffer.clear();
    }

    if (statusBar()) {
        if (exitCode == 0 && exitStatus == 0) {
            statusBar()->showMessage("Build Successful!", 5000);
        } else {
            statusBar()->showMessage("Build Failed (Exit Code: " + QString::number(exitCode) + ")", 5000);
        }
    }
}

void EditorWindow::parseBuildLine(const QString& line) {
    static QRegularExpression regex(R"(^(.+?):(\d+):(\d+):\s*(error|warning|note|fatal error):\s*(.*)$)", QRegularExpression::CaseInsensitiveOption);
    QRegularExpressionMatch match = regex.match(line);
    if (match.hasMatch()) {
        QString file = match.captured(1).trimmed();
        int lineNum = match.captured(2).toInt();
        int colNum = match.captured(3).toInt();
        QString severity = match.captured(4).trimmed();
        QString message = match.captured(5).trimmed();
        
        if (problemsTab) {
            problemsTab->addProblem(severity, file, lineNum, colNum, message);
        }

        // Cache diagnostics
        bool isError = severity.contains("error", Qt::CaseInsensitive);
        activeDiagnostics.push_back({file, lineNum, message, isError});
        updateDocumentDiagnostics();
    }
}

void EditorWindow::gotoLine(const QString& file, int line) {
    openFileInTab(file);
    if (auto* ed = currentEditor()) {
        auto* textEdit = ed->findChild<QPlainTextEdit*>();
        if (textEdit) {
            QTextDocument* doc = textEdit->document();
            QTextBlock block = doc->findBlockByLineNumber(line - 1);
            if (block.isValid()) {
                QTextCursor cursor(block);
                cursor.movePosition(QTextCursor::StartOfLine);
                cursor.movePosition(QTextCursor::EndOfLine, QTextCursor::KeepAnchor);
                textEdit->setTextCursor(cursor);
                textEdit->setFocus();
            }
        }
    }
}

void EditorWindow::updateDocumentDiagnostics() {
    for (int i = 0; i < tabWidget->count(); ++i) {
        if (auto* ed = qobject_cast<CustomEditor*>(tabWidget->widget(i))) {
            QString edPath = ed->currentFilePath();
            if (edPath.isEmpty()) continue;
            
            auto* codeEd = ed->findChild<CodeEditor*>();
            if (!codeEd) continue;
            
            std::vector<CodeEditor::Diagnostic> fileDiags;
            for (const auto& diag : activeDiagnostics) {
                if (QFileInfo(diag.file).absoluteFilePath() == QFileInfo(edPath).absoluteFilePath()) {
                    fileDiags.push_back({diag.line, diag.message, diag.isError});
                }
            }
            codeEd->setDiagnostics(fileDiags);
        }
    }
}

void EditorWindow::showSymbolReferences(const QJsonArray& locations) {
    if (!referencesTable) return;

    referencesTable->setRowCount(0);
    for (const auto& val : locations) {
        QJsonObject loc = val.toObject();
        QString uri = loc["uri"].toString();
        QString path = QUrl(uri).toLocalFile();
        int line = loc["range"].toObject()["start"].toObject()["line"].toInt() + 1;

        int row = referencesTable->rowCount();
        referencesTable->insertRow(row);

        auto* fileItem = new QTableWidgetItem(QFileInfo(path).fileName());
        fileItem->setToolTip(path);
        fileItem->setFlags(fileItem->flags() & ~Qt::ItemIsEditable);

        auto* lineItem = new QTableWidgetItem(QString::number(line));
        lineItem->setFlags(lineItem->flags() & ~Qt::ItemIsEditable);

        QString lineContent = "Code reference";
        QFile file(path);
        if (file.open(QIODevice::ReadOnly | QIODevice::Text)) {
            QTextStream in(&file);
            int currentLine = 0;
            while (!in.atEnd()) {
                currentLine++;
                QString content = in.readLine();
                if (currentLine == line) {
                    lineContent = content.trimmed();
                    break;
                }
            }
        }

        auto* codeItem = new QTableWidgetItem(lineContent);
        codeItem->setFlags(codeItem->flags() & ~Qt::ItemIsEditable);

        referencesTable->setItem(row, 0, fileItem);
        referencesTable->setItem(row, 1, lineItem);
        referencesTable->setItem(row, 2, codeItem);
    }

    if (bottomTabWidget) {
        int refIdx = bottomTabWidget->indexOf(referencesTable);
        if (refIdx != -1) {
            bottomTabWidget->setCurrentIndex(refIdx);
        }
    }
}

void EditorWindow::fixProblemWithAI(const QString& filePath, int line, const QString& message) {
    if (filePath.isEmpty() || !aiPatchController) return;

    QString codeContent;
    QFile file(filePath);
    if (file.open(QIODevice::ReadOnly | QIODevice::Text)) {
        codeContent = QTextStream(&file).readAll();
    }
    
    if (codeContent.isEmpty()) return;

    QString prompt = QString("Here is a compiler diagnostic on line %1: \"%2\"\n\n"
                             "Please review this code from the file \"%3\" and rewrite it to fix the compiler warning or error:\n\n"
                             "```cpp\n%4\n```")
                             .arg(line)
                             .arg(message)
                             .arg(QFileInfo(filePath).fileName())
                             .arg(codeContent);

    aiPatchController->setEditor(currentEditor());
    aiPatchController->requestRefactor(prompt);
}
""")

# ---------------------------------------------------------
# 6. Ensure CMake uses Qt and new files
# ---------------------------------------------------------
write(f"{ROOT}/src/main.cpp", r"""#include <QApplication>
#include "ui/EditorWindow.hpp"

int main(int argc, char *argv[]) {
    QApplication::addLibraryPath("C:/Qt/6.11.1/llvm-mingw_64/plugins");
    QApplication app(argc, argv);
    EditorWindow w;
    w.show();
    return app.exec();
}
""")

write(f"{ROOT}/CMakeLists.txt", r"""cmake_minimum_required(VERSION 3.16)
project(AIIDE VERSION 1.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

add_subdirectory(src)
""")

write(f"{ROOT}/src/CMakeLists.txt", r"""cmake_minimum_required(VERSION 3.16)

file(GLOB_RECURSE SOURCES CONFIGURE_DEPENDS *.cpp *.hpp *.qrc)

find_package(Qt6 REQUIRED COMPONENTS Widgets Network Sql)

add_executable(ai-ide ${SOURCES})
target_link_libraries(ai-ide PRIVATE Qt6::Widgets Qt6::Network Qt6::Sql)

# Helps IntelliSense find headers in subdirectories like ui/ or ai/
target_include_directories(ai-ide PRIVATE 
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_compile_definitions(ai-ide PRIVATE
    QT_DEPRECATED_WARNINGS
)
""")

print("Custom editor, file browser wiring, diff view, AI patch workflow, and Git skeleton added successfully!")
