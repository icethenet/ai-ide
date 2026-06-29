#pragma once
#include <QWidget>
#include <QTextEdit>
#include <QPushButton>
#include <QCheckBox>
#include <QLabel>
#include <QScrollArea>
#include <QVBoxLayout>
#include <QVector>
#include <memory>
#include "SettingsManager.hpp"
#include "../ai/AIProvider.hpp"
#include "../ai/AIAction.hpp"

class ActionItemWidget : public QWidget {
    Q_OBJECT
public:
    explicit ActionItemWidget(const AIAction& action, QWidget* parent = nullptr);
    bool isChecked() const { return checkBox->isChecked(); }
    AIAction getAction() const { return action; }

signals:
    void previewRequested(const AIAction& action);

private:
    QCheckBox* checkBox;
    QLabel* typeBadge;
    QLabel* infoLabel;
    QPushButton* previewBtn;
    AIAction action;
};

class ProposedActionsWidget : public QWidget {
    Q_OBJECT
public:
    explicit ProposedActionsWidget(QWidget* parent = nullptr);
    void setActions(const QVector<AIAction>& actions);
    QVector<AIAction> getCheckedActions() const;
    void clearActions();

signals:
    void executeRequested();
    void previewAction(const AIAction& action);

private:
    QLabel* titleLabel;
    QWidget* listContainer;
    QVBoxLayout* listLayout;
    QScrollArea* scrollArea;
    QPushButton* applyBtn;
    QPushButton* discardBtn;
    QVector<ActionItemWidget*> items;
};

class AIChatPanel : public QWidget {
    Q_OBJECT
public:
    explicit AIChatPanel(QWidget* parent = nullptr);
    static QString applySearchReplace(const QString& originalText, const QString& patchContent, bool& success, QString& errorMsg);

signals:
    void executeAction(const AIAction& action);
    void requestActiveFileContext(QString& filePath, QString& fileContent, QString& baseDir);
    void promptArchived(const QString& summary);
    void requestBuildRun();

public slots:
    void handleBuildFinished(int exitCode, const QString& buildErrors);

private slots:
    void sendPrompt();
    void handlePreview(const AIAction& action);
    void executeActions();

private:
    void queryAI(const QString& prompt, bool isAutoFix = false);
    void stopAgenticLoop();

    QTextEdit* chatHistory;
    QTextEdit* inputBox;
    QPushButton* sendButton;
    ProposedActionsWidget* actionsPanel;
    QCheckBox* agenticModeCheck;
    std::unique_ptr<AIProvider> provider;

    bool isAgenticRunning;
    int agenticIteration;
    const int maxAgenticIterations = 5;
};
