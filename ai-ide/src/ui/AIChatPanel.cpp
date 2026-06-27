#include "AIChatPanel.hpp"
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
