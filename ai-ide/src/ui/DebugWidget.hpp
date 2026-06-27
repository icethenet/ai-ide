#pragma once
#include <QWidget>
#include <QProcess>
#include <QString>

class QPushButton;
class QPlainTextEdit;
class QTreeWidget;
class QLineEdit;
class QLabel;

class DebugWidget : public QWidget {
    Q_OBJECT
public:
    explicit DebugWidget(QWidget* parent = nullptr);
    ~DebugWidget() override;

private slots:
    void startDebugging();
    void stopDebugging();
    void stepOver();
    void stepInto();
    void continueDebug();
    void sendManualCommand();
    void readGdbOutput();
    void gdbFinished(int exitCode);

private:
    void sendGdbCommand(const QString& cmd);
    void updateVariables();
    void addVariable(const QString& name, const QString& type, const QString& val);
    
    // Simulation mode helpers
    void enterSimulationMode();
    void runSimulationStep();

    QProcess* gdbProcess;
    bool isSimulated;
    int simStepCount;

    QPushButton* startBtn;
    QPushButton* stopBtn;
    QPushButton* stepOverBtn;
    QPushButton* stepIntoBtn;
    QPushButton* continueBtn;
    QLabel* statusLabel;
    
    QPlainTextEdit* consoleLog;
    QLineEdit* cmdInput;
    QTreeWidget* variablesTree;
};
