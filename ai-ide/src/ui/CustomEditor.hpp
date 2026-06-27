#pragma once
#include <QWidget>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QString>

class CustomEditor : public QWidget {
    Q_OBJECT
public:
    explicit CustomEditor(QWidget* parent = nullptr);

    void openFile(const QString& path);
    void saveFile();
    void saveAsFile();
    QString currentFilePath() const;

signals:
    void fileChanged(const QString& path);
    void closeRequested();

private:
    QPlainTextEdit* editor;
    QPushButton* closeButton;
    QPushButton* saveAsButton;
    QString filePath;
};
