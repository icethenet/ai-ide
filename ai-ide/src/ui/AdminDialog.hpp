#pragma once
#include <QDialog>
#include <QLineEdit>
#include <QComboBox>

class AdminDialog : public QDialog {
    Q_OBJECT
public:
    explicit AdminDialog(QWidget* parent = nullptr);
private slots:
    void refreshModels();
    void saveSettings();
private:
    QComboBox* providerCombo;
    QComboBox* modelCombo;

    QLineEdit* ollamaEndpointEdit;

    QLineEdit* geminiApiKeyEdit;
    QLineEdit* geminiEndpointEdit;

    QLineEdit* claudeApiKeyEdit;
    QLineEdit* claudeEndpointEdit;

    QLineEdit* antigravityApiKeyEdit;
    QLineEdit* antigravityEndpointEdit;
};
