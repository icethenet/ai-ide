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
    QLineEdit* endpointEdit;
    QComboBox* providerCombo;
    QComboBox* modelCombo;
};
