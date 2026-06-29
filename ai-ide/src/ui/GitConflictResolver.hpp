#pragma once
#include <QWidget>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QLabel>

class GitConflictResolver : public QWidget {
    Q_OBJECT
public:
    explicit GitConflictResolver(const QString& filePath, QWidget* parent = nullptr);
    QString getFilePath() const { return filePath; }

signals:
    void resolved(const QString& path);

private slots:
    void acceptLocal();
    void acceptRemote();
    void acceptBoth();
    void saveAndResolve();

private:
    bool parseConflictData();

    QString filePath;
    QString localContent;
    QString remoteContent;
    QString rawConflictContent;

    QPlainTextEdit* leftEdit;
    QPlainTextEdit* rightEdit;
    QPlainTextEdit* centerEdit;
    QLabel* titleLabel;
};
