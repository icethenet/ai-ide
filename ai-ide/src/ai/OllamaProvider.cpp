#include "OllamaProvider.hpp"
#include <iostream>
#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QEventLoop>
#include <QJsonObject>
#include <QJsonDocument>
#include <QUrl>
#include "../ui/SettingsManager.hpp"

OllamaProvider::OllamaProvider(const std::string& ep) : endpoint(ep) {
    (void)ep; 
}

AIResponse OllamaProvider::send(const AIRequest& req) {
    auto& settings = SettingsManager::instance();
    QString currentEndpoint = QString::fromStdString(settings.getEndpoint());
    QString currentModel = QString::fromStdString(settings.getModel());

    if (currentEndpoint.isEmpty()) currentEndpoint = "http://localhost:11434";

    std::cout << "[AI] Sending request to " << currentEndpoint.toStdString() 
              << " using model: " << currentModel.toStdString() << std::endl;

    QNetworkAccessManager manager;
    QNetworkRequest request(QUrl(currentEndpoint + "/api/generate"));
    request.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");

    QJsonObject json;
    json["model"] = currentModel.isEmpty() ? "llama3" : currentModel;
    json["prompt"] = QString::fromStdString(req.prompt);
    json["system"] = "You are a world-class software engineer and IDE coding assistant. "
                     "Your task is to provide complete, functional source code. "
                     "When asked for a 'blank' page or file, provide a standard boilerplate/template for that language. "
                     "ALWAYS wrap code in markdown blocks with language identifiers (e.g., ```html). "
                     "Do not provide empty code blocks. "
                     "Minimize conversational filler and prioritize clean code output.";
    json["stream"] = false;

    QNetworkReply* reply = manager.post(request, QJsonDocument(json).toJson());

    // Create a local event loop to wait for the response (synchronous call)
    QEventLoop loop;
    QObject::connect(reply, &QNetworkReply::finished, &loop, &QEventLoop::quit);
    loop.exec();

    AIResponse res;
    if (reply->error() == QNetworkReply::NoError) {
        QJsonDocument resDoc = QJsonDocument::fromJson(reply->readAll());
        res.text = resDoc.object()["response"].toString().toStdString();
    } else {
        res.text = "Error: " + reply->errorString().toStdString();
    }

    reply->deleteLater();
    return res;
}
