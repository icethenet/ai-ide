#pragma once
#include <QWidget>
#include <QListWidget>
#include <QLineEdit>
#include <QProcess>

class GitWidget : public QWidget {
    Q_OBJECT
public:
    explicit GitWidget(QWidget* parent = nullptr);
    void setRootPath(const QString& path);

private slots:
    void refreshStatus();
    void commitChanges();
    void syncChanges();
    void onProcessFinished(int exitCode);

private:
    QString rootPath;
    QListWidget* statusList;
    QLineEdit* commitMessageEdit;
    QProcess* gitProcess;
    QString currentMode;
    QStringList filesToStage;
};
