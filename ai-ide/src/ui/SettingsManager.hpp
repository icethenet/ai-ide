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

    void setEndpoint(const std::string& ep) { 
        endpoint = ep; 
        QSettings s("Aide", "AI-IDE");
        s.setValue("endpoint", QString::fromStdString(ep));
    }
    std::string getEndpoint() const { return endpoint; }

    void setModel(const std::string& m) { 
        model = m; 
        QSettings s("Aide", "AI-IDE");
        s.setValue("model", QString::fromStdString(m));
    }
    std::string getModel() const { return model; }

    void setProviderType(const std::string& type) { 
        providerType = type; 
        QSettings s("Aide", "AI-IDE");
        s.setValue("providerType", QString::fromStdString(type));
    }
    std::string getProviderType() const { return providerType; }

private:
    SettingsManager() {
        QSettings s("Aide", "AI-IDE");
        endpoint = s.value("endpoint", "http://localhost:11434").toString().toStdString();
        model = s.value("model", "llama3").toString().toStdString();
        providerType = s.value("providerType", "Ollama").toString().toStdString();
    }

    std::string endpoint;
    std::string model;
    std::string providerType;
};
