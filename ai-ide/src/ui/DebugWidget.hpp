#pragma once
#include <QWidget>
#include <QProcess>
#include <QString>
#include <vector>
#include <utility>

class QPushButton;
class QPlainTextEdit;
class QTreeWidget;
class QLineEdit;
class QLabel;

enum VisType { VisNone, VisArray, VisMatrix, VisGraph };

class VisualInspectorWidget : public QWidget {
    Q_OBJECT
public:
    explicit VisualInspectorWidget(QWidget* parent = nullptr);
    void inspectVariable(const QString& name, const QString& type, const QString& val);

protected:
    void paintEvent(QPaintEvent* event) override;

private:
    QString varName;
    QString varType;
    QString varVal;

    VisType visType;
    std::vector<double> arrayData;
    std::vector<std::vector<double>> matrixData;
    std::vector<int> graphNodes;
    std::vector<std::pair<int, int>> graphEdges;
};

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
    VisualInspectorWidget* visualInspector;
};
