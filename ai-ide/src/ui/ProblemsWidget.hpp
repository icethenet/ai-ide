#pragma once
#include <QWidget>
#include <QString>

class QTableWidget;

class ProblemsWidget : public QWidget {
    Q_OBJECT
public:
    explicit ProblemsWidget(QWidget* parent = nullptr);
    void addProblem(const QString& severity, const QString& file, int line, int col, const QString& message);
    void clearProblems();

signals:
    void problemActivated(const QString& file, int line);

private:
    QTableWidget* table;
};
