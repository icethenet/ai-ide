#include "DebugWidget.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QSplitter>
#include <QTreeWidget>
#include <QTreeWidgetItem>
#include <QHeaderView>
#include <QPushButton>
#include <QLineEdit>
#include <QLabel>
#include <QPlainTextEdit>
#include <QDir>
#include <QFile>
#include <QRegularExpression>
#include <QDateTime>

DebugWidget::DebugWidget(QWidget* parent)
    : QWidget(parent),
      gdbProcess(nullptr),
      isSimulated(false),
      simStepCount(0)
{
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(0, 0, 0, 0);

    // 1. Toolbar at the top
    auto* toolbar = new QHBoxLayout();
    startBtn = new QPushButton("Start Debugging", this);
    stopBtn = new QPushButton("Stop", this);
    stepOverBtn = new QPushButton("Step Over", this);
    stepIntoBtn = new QPushButton("Step Into", this);
    continueBtn = new QPushButton("Continue", this);
    statusLabel = new QLabel("Status: Idle", this);
    statusLabel->setStyleSheet("font-weight: bold; margin-left: 10px;");

    stopBtn->setEnabled(false);
    stepOverBtn->setEnabled(false);
    stepIntoBtn->setEnabled(false);
    continueBtn->setEnabled(false);

    toolbar->addWidget(startBtn);
    toolbar->addWidget(stopBtn);
    toolbar->addWidget(stepOverBtn);
    toolbar->addWidget(stepIntoBtn);
    toolbar->addWidget(continueBtn);
    toolbar->addWidget(statusLabel);
    toolbar->addStretch();
    mainLayout->addLayout(toolbar);

    // 2. Splitter for console output and variables inspector
    auto* splitter = new QSplitter(Qt::Horizontal, this);

    // Left container: Console output and manual command input
    auto* consoleContainer = new QWidget(this);
    auto* consoleLayout = new QVBoxLayout(consoleContainer);
    consoleLayout->setContentsMargins(0, 0, 0, 0);

    consoleLog = new QPlainTextEdit(this);
    consoleLog->setReadOnly(true);
    consoleLog->setStyleSheet("QPlainTextEdit { background-color: #1e1e1e; color: #d4d4d4; font-family: 'Consolas', monospace; }");
    consoleLayout->addWidget(consoleLog);

    auto* cmdLayout = new QHBoxLayout();
    cmdInput = new QLineEdit(this);
    cmdInput->setPlaceholderText("Enter GDB/debugger command...");
    cmdInput->setStyleSheet("QLineEdit { background-color: #2d2d2d; color: #ffffff; font-family: 'Consolas', monospace; }");
    cmdInput->setEnabled(false);
    cmdLayout->addWidget(cmdInput);
    consoleLayout->addLayout(cmdLayout);

    splitter->addWidget(consoleContainer);

    // Right container: Variables tree widget
    variablesTree = new QTreeWidget(this);
    variablesTree->setColumnCount(3);
    variablesTree->setHeaderLabels({"Name", "Type", "Value"});
    variablesTree->header()->setSectionResizeMode(QHeaderView::Stretch);
    variablesTree->setStyleSheet("QTreeWidget { background-color: #1e1e1e; color: #d4d4d4; } QHeaderView::section { background-color: #2d2d2d; color: #ffffff; }");
    splitter->addWidget(variablesTree);

    mainLayout->addWidget(splitter);

    // Connections
    connect(startBtn, &QPushButton::clicked, this, &DebugWidget::startDebugging);
    connect(stopBtn, &QPushButton::clicked, this, &DebugWidget::stopDebugging);
    connect(stepOverBtn, &QPushButton::clicked, this, &DebugWidget::stepOver);
    connect(stepIntoBtn, &QPushButton::clicked, this, &DebugWidget::stepInto);
    connect(continueBtn, &QPushButton::clicked, this, &DebugWidget::continueDebug);
    connect(cmdInput, &QLineEdit::returnPressed, this, &DebugWidget::sendManualCommand);
}

DebugWidget::~DebugWidget() {
    stopDebugging();
}

void DebugWidget::startDebugging() {
    consoleLog->clear();
    variablesTree->clear();
    simStepCount = 0;
    
    // Check if lldb-mi.exe exists in the toolchain directory
    QString lldbMiPath = "C:/Qt/Tools/llvm-mingw_64/bin/lldb-mi.exe";
    QString targetExe = QDir::currentPath() + "/ai-ide/build/src/ai-ide.exe";

    if (!QFile::exists(lldbMiPath)) {
        // Fallback: search system PATH for lldb-mi or gdb
        lldbMiPath = "lldb-mi.exe";
    }

    consoleLog->appendPlainText("--- Launching Debug Session ---");
    consoleLog->appendPlainText("Target Executable: " + targetExe);

    gdbProcess = new QProcess(this);
    gdbProcess->setProcessChannelMode(QProcess::MergedChannels);
    connect(gdbProcess, &QProcess::readyReadStandardOutput, this, &DebugWidget::readGdbOutput);
    connect(gdbProcess, static_cast<void(QProcess::*)(int, QProcess::ExitStatus)>(&QProcess::finished), this, [this](int exitCode) {
        this->gdbFinished(exitCode);
    });

    // Try to run lldb-mi or gdb
    QStringList args;
    args << targetExe;

    gdbProcess->start(lldbMiPath, args);
    if (!gdbProcess->waitForStarted(1500)) {
        // Debugger process failed to start, enter simulation fallback
        enterSimulationMode();
    } else {
        isSimulated = false;
        consoleLog->appendPlainText("Debugger process started successfully via: " + lldbMiPath);
        statusLabel->setText("Status: Running");
        startBtn->setEnabled(false);
        stopBtn->setEnabled(true);
        stepOverBtn->setEnabled(true);
        stepIntoBtn->setEnabled(true);
        continueBtn->setEnabled(true);
        cmdInput->setEnabled(true);
        
        // Initial setup commands
        sendGdbCommand("break main");
        sendGdbCommand("run");
    }
}

void DebugWidget::enterSimulationMode() {
    isSimulated = true;
    consoleLog->appendPlainText("\n[WARNING] lldb-mi.exe or gdb.exe not found in toolchain or system PATH.");
    consoleLog->appendPlainText("[INFO] Starting Panel in Debug Simulation Mode instead...\n");
    consoleLog->appendPlainText("[Sim] Process launched. Breakpoint hit at main() in src/main.cpp:5");
    
    statusLabel->setText("Status: Paused");
    startBtn->setEnabled(false);
    stopBtn->setEnabled(true);
    stepOverBtn->setEnabled(true);
    stepIntoBtn->setEnabled(true);
    continueBtn->setEnabled(true);
    cmdInput->setEnabled(true);

    updateVariables();
}

void DebugWidget::stopDebugging() {
    if (gdbProcess) {
        if (gdbProcess->state() != QProcess::NotRunning) {
            gdbProcess->write("quit\n");
            gdbProcess->waitForFinished(1000);
            if (gdbProcess->state() != QProcess::NotRunning) {
                gdbProcess->kill();
            }
        }
        gdbProcess->deleteLater();
        gdbProcess = nullptr;
    }

    isSimulated = false;
    statusLabel->setText("Status: Idle");
    startBtn->setEnabled(true);
    stopBtn->setEnabled(false);
    stepOverBtn->setEnabled(false);
    stepIntoBtn->setEnabled(false);
    continueBtn->setEnabled(false);
    cmdInput->setEnabled(false);
    consoleLog->appendPlainText("--- Debug Session Stopped ---");
}

void DebugWidget::stepOver() {
    if (isSimulated) {
        consoleLog->appendPlainText("[Sim] step over");
        runSimulationStep();
    } else {
        sendGdbCommand("next");
    }
}

void DebugWidget::stepInto() {
    if (isSimulated) {
        consoleLog->appendPlainText("[Sim] step into");
        runSimulationStep();
    } else {
        sendGdbCommand("step");
    }
}

void DebugWidget::continueDebug() {
    if (isSimulated) {
        consoleLog->appendPlainText("[Sim] continue");
        consoleLog->appendPlainText("[Sim] Program exited normally.");
        stopDebugging();
    } else {
        sendGdbCommand("continue");
    }
}

void DebugWidget::sendManualCommand() {
    QString cmd = cmdInput->text().trimmed();
    if (cmd.isEmpty()) return;

    consoleLog->appendPlainText("> " + cmd);
    cmdInput->clear();

    if (isSimulated) {
        if (cmd == "next" || cmd == "n") {
            stepOver();
        } else if (cmd == "step" || cmd == "s") {
            stepInto();
        } else if (cmd == "continue" || cmd == "c") {
            continueDebug();
        } else if (cmd == "info locals" || cmd == "info l") {
            updateVariables();
        } else {
            consoleLog->appendPlainText("[Sim Mode] Unsupported simulation command. Try 'next', 'step', 'continue', or 'info locals'.");
        }
    } else {
        sendGdbCommand(cmd);
    }
}

void DebugWidget::sendGdbCommand(const QString& cmd) {
    if (gdbProcess && gdbProcess->state() == QProcess::Running) {
        gdbProcess->write((cmd + "\n").toLocal8Bit());
    }
}

void DebugWidget::readGdbOutput() {
    if (!gdbProcess) return;
    QByteArray output = gdbProcess->readAllStandardOutput();
    if (!output.isEmpty()) {
        QString text = QString::fromLocal8Bit(output);
        consoleLog->appendPlainText(text);
        
        // Auto-refresh variables if we hit a stopping point
        if (text.contains("stopped") || text.contains("Breakpoint") || text.contains("step")) {
            sendGdbCommand("info locals");
        }
        
        // Parse simple locals from GDB output
        QStringList lines = text.split('\n');
        bool foundLocals = false;
        for (const QString& line : lines) {
            static QRegularExpression varRegex(R"(^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*)$)");
            auto match = varRegex.match(line.trimmed());
            if (match.hasMatch()) {
                if (!foundLocals) {
                    variablesTree->clear();
                    foundLocals = true;
                }
                QString name = match.captured(1);
                QString val = match.captured(2);
                addVariable(name, "auto", val);
            }
        }
    }
}

void DebugWidget::gdbFinished(int exitCode) {
    consoleLog->appendPlainText("Debugger process finished with exit code: " + QString::number(exitCode));
    stopDebugging();
}

void DebugWidget::addVariable(const QString& name, const QString& type, const QString& val) {
    auto* item = new QTreeWidgetItem(variablesTree);
    item->setText(0, name);
    item->setText(1, type);
    item->setText(2, val);
}

void DebugWidget::updateVariables() {
    variablesTree->clear();
    if (isSimulated) {
        if (simStepCount == 0) {
            addVariable("argc", "int", "1");
            addVariable("argv", "char**", "0x0000021a8d052a60");
            addVariable("app", "QApplication", "{...}");
            addVariable("isInitialized", "bool", "false");
        } else if (simStepCount == 1) {
            addVariable("argc", "int", "1");
            addVariable("argv", "char**", "0x0000021a8d052a60");
            addVariable("app", "QApplication", "{...}");
            addVariable("isInitialized", "bool", "true");
            addVariable("w", "EditorWindow", "{...}");
        } else if (simStepCount == 2) {
            addVariable("argc", "int", "1");
            addVariable("argv", "char**", "0x0000021a8d052a60");
            addVariable("app", "QApplication", "{...}");
            addVariable("isInitialized", "bool", "true");
            addVariable("w", "EditorWindow", "{...}");
            addVariable("loopCount", "int", "0");
        } else {
            addVariable("argc", "int", "1");
            addVariable("argv", "char**", "0x0000021a8d052a60");
            addVariable("app", "QApplication", "{...}");
            addVariable("isInitialized", "bool", "true");
            addVariable("w", "EditorWindow", "{...}");
            addVariable("loopCount", "int", QString::number(simStepCount - 2));
            addVariable("status", "QString", "\"Processing window event loop...\"");
        }
    }
}

void DebugWidget::runSimulationStep() {
    simStepCount++;
    statusLabel->setText("Status: Paused (Step " + QString::number(simStepCount) + ")");
    
    if (simStepCount == 1) {
        consoleLog->appendPlainText("[Sim] Stopped at main.cpp:6 - QApplication app(argc, argv);");
    } else if (simStepCount == 2) {
        consoleLog->appendPlainText("[Sim] Stopped at main.cpp:7 - EditorWindow w;");
    } else if (simStepCount == 3) {
        consoleLog->appendPlainText("[Sim] Stopped at main.cpp:8 - w.show();");
    } else {
        consoleLog->appendPlainText("[Sim] Stopped at main.cpp:9 - return app.exec(); (Iteration: " + QString::number(simStepCount - 3) + ")");
    }
    
    updateVariables();
}
