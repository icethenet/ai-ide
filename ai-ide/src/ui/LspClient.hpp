#pragma once
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
