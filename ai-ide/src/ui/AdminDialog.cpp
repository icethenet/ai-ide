#include "AdminDialog.hpp"
#include "SettingsManager.hpp"
#include <QVBoxLayout>
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

AdminDialog::AdminDialog(QWidget* parent) : QDialog(parent) {
    setWindowTitle("AI Settings & Administration");
    setMinimumWidth(450);

    auto* layout = new QVBoxLayout(this);
    auto* form = new QFormLayout();

    providerCombo = new QComboBox(this);
    providerCombo->addItems({"Ollama", "Gemini", "Claude"});
    providerCombo->setCurrentText(QString::fromStdString(SettingsManager::instance().getProviderType()));

    endpointEdit = new QLineEdit(this);
    endpointEdit->setText(QString::fromStdString(SettingsManager::instance().getEndpoint()));

    modelCombo = new QComboBox(this);
    modelCombo->setEditable(true);
    modelCombo->setCurrentText(QString::fromStdString(SettingsManager::instance().getModel()));

    auto* refreshBtn = new QPushButton("Find Installed Models", this);
    connect(refreshBtn, &QPushButton::clicked, this, &AdminDialog::refreshModels);

    form->addRow("Provider:", providerCombo);
    form->addRow("AI IP/Endpoint:", endpointEdit);
    form->addRow("Current Model:", modelCombo);
    
    auto* btnLayout = new QHBoxLayout();
    btnLayout->addWidget(refreshBtn);
    form->addRow("Discovery:", btnLayout);

    layout->addLayout(form);
    
    auto* line = new QFrame();
    line->setFrameShape(QFrame::HLine);
    layout->addWidget(line);

    auto* saveBtn = new QPushButton("Save Changes", this);
    connect(saveBtn, &QPushButton::clicked, this, &AdminDialog::saveSettings);
    layout->addWidget(saveBtn, 0, Qt::AlignRight);
}

void AdminDialog::refreshModels() {
    QString url = endpointEdit->text() + "/api/tags";
    auto* manager = new QNetworkAccessManager(this);
    auto* reply = manager->get(QNetworkRequest(QUrl(url)));
    connect(reply, &QNetworkReply::finished, this, [this, reply]() {
        if (reply->error() == QNetworkReply::NoError) {
            modelCombo->clear();
            auto models = QJsonDocument::fromJson(reply->readAll()).object()["models"].toArray();
            for (const auto& m : models) modelCombo->addItem(m.toObject()["name"].toString());
        }
        reply->deleteLater();
    });
}

void AdminDialog::saveSettings() {
    auto& s = SettingsManager::instance();
    s.setEndpoint(endpointEdit->text().toStdString());
    s.setProviderType(providerCombo->currentText().toStdString());
    s.setModel(modelCombo->currentText().toStdString());
    accept();
}
