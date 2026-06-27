#pragma once
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
