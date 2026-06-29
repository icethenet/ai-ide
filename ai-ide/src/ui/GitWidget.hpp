#pragma once
#include <QWidget>
#include <QListWidget>
#include <QLineEdit>
#include <QProcess>

class GitHistoryWidget;

class GitWidget : public QWidget {
    Q_OBJECT
public:
    explicit GitWidget(QWidget* parent = nullptr);
    void setRootPath(const QString& path);

signals:
    void conflictResolutionRequested(const QString& filePath);

public slots:
    void refreshStatus();
    void commitChanges();
    void syncChanges();

private slots:
    void onProcessFinished(int exitCode);

private:
    QString rootPath;
    QListWidget* statusList;
    QLineEdit* commitMessageEdit;
    QProcess* gitProcess;
    QString currentMode;
    QStringList filesToStage;

    GitHistoryWidget* historyWidget;
};
