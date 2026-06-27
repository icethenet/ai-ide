#pragma once
#include <QWidget>
#include <QPlainTextEdit>
#include <QProcess>

class TerminalWidget : public QWidget {
    Q_OBJECT
public:
    explicit TerminalWidget(const QString& shellPath, QWidget* parent = nullptr);
    ~TerminalWidget() override;

protected:
    bool eventFilter(QObject* obj, QEvent* event) override;

private slots:
    void readOutput();

private:
    QPlainTextEdit* terminalEdit;
    QProcess* process;
};
