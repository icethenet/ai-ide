#pragma once
#include <QWidget>
#include <QPlainTextEdit>
#include <QProcess>
#include <QSplitter>
#include <QVBoxLayout>

class TerminalPane : public QWidget {
    Q_OBJECT
public:
    explicit TerminalPane(const QString& shellPath, QPlainTextEdit* existingEdit = nullptr, QProcess* existingProc = nullptr, QWidget* parent = nullptr);
    ~TerminalPane() override;

signals:
    void closed();

protected:
    bool eventFilter(QObject* obj, QEvent* event) override;

private slots:
    void readOutput();
    void splitHorizontal();
    void splitVertical();
    void closePane();
    void onChildClosed();

private:
    void split(Qt::Orientation orientation);
    QString ansiToHtml(const QString& ansiText);

    QString shell;
    QPlainTextEdit* terminalEdit;
    QProcess* process;
    QWidget* toolbar;
    QWidget* contentArea;
    QVBoxLayout* contentLayout;
    
    bool isSplit;
    QSplitter* splitter;
    TerminalPane* child1;
    TerminalPane* child2;
};

class TerminalWidget : public QWidget {
    Q_OBJECT
public:
    explicit TerminalWidget(const QString& shellPath, QWidget* parent = nullptr);
private:
    TerminalPane* rootPane;
};
