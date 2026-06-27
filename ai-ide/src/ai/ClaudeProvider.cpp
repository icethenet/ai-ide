#include "ClaudeProvider.hpp"
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
