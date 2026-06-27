#pragma once
#include <QWidget>
#include <QTextEdit>
#include <QPushButton>
#include <memory>
#include "SettingsManager.hpp"
#include "../ai/AIProvider.hpp"

class AIChatPanel : public QWidget {
    Q_OBJECT
public:
    explicit AIChatPanel(QWidget* parent = nullptr);
signals:
    void applyToEditor(const QString& code);
    void createNewFile(const QString& code);
    void promptArchived(const QString& summary);

private slots:
    void sendPrompt();
private:
    QTextEdit* chatHistory;
    QTextEdit* inputBox;
    QPushButton* sendButton;
    std::unique_ptr<AIProvider> provider;
    QString lastExtractedCode;
};
