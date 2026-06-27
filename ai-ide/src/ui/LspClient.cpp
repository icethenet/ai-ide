#include "LspClient.hpp"
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
