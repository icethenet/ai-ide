#include "AdminDialog.hpp"
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
