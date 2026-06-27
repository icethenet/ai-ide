#include "GeminiProvider.hpp"
#include <iostream>
#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QEventLoop>
#include <QJsonObject>
#include <QJsonDocument>
#include <QJsonArray>
#include <QUrl>

GeminiProvider::GeminiProvider(const std::string& key) : apiKey(key) {
    (void)key; // Suppress unused warning
}

AIResponse GeminiProvider::send(const AIRequest& req) {
    if (apiKey.empty()) {
        return {"Error: Gemini API key not configured. Please set API_KEY in settings."};
    }

    QNetworkAccessManager manager;
    QString apiUrl = QString::fromStdString(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + apiKey
    );
    
    QNetworkRequest request{QUrl(apiUrl)};
    request.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");

    // Build Gemini API request
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

    // Create a local event loop to wait for the response (synchronous call)
    QEventLoop loop;
    QObject::connect(reply, &QNetworkReply::finished, &loop, &QEventLoop::quit);
    loop.exec();

    AIResponse res;
    if (reply->error() == QNetworkReply::NoError) {
        QJsonDocument resDoc = QJsonDocument::fromJson(reply->readAll());
        QJsonObject obj = resDoc.object();
        
        // Extract text from Gemini response structure
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
        
        // If structured extraction failed, try to get error info
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
