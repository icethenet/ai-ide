#pragma once
#include <QWidget>
#include <QString>

class QPlainTextEdit;

class DiffView : public QWidget {
    Q_OBJECT
public:
    explicit DiffView(QWidget* parent = nullptr);

    void setTexts(const QString& original, const QString& modified);

private:
    QPlainTextEdit* leftView;
    QPlainTextEdit* rightView;
};
