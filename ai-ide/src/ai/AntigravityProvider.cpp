#include "AntigravityProvider.hpp"
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
