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
#include <QPainter>
#include <QLinearGradient>
#include <QRadialGradient>
#include <QtMath>
#include <cmath>

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

    // Right container: Variables tree widget and Visual Inspector
    auto* rightContainer = new QWidget(this);
    auto* rightLayout = new QVBoxLayout(rightContainer);
    rightLayout->setContentsMargins(0, 0, 0, 0);
    rightLayout->setSpacing(0);

    auto* rightSplitter = new QSplitter(Qt::Vertical, rightContainer);

    variablesTree = new QTreeWidget(rightContainer);
    variablesTree->setColumnCount(3);
    variablesTree->setHeaderLabels({"Name", "Type", "Value"});
    variablesTree->header()->setSectionResizeMode(QHeaderView::Stretch);
    variablesTree->setStyleSheet("QTreeWidget { background-color: #21252b; color: #abb2bf; border: none; font-family: 'Segoe UI', Arial; font-size: 11px; }"
                                  "QHeaderView::section { background-color: #2c313c; color: #abb2bf; border: 1px solid #181a1f; padding: 4px; }");

    visualInspector = new VisualInspectorWidget(rightContainer);

    rightSplitter->addWidget(variablesTree);
    rightSplitter->addWidget(visualInspector);
    rightSplitter->setStretchFactor(0, 1);
    rightSplitter->setStretchFactor(1, 1);

    rightLayout->addWidget(rightSplitter);
    splitter->addWidget(rightContainer);

    mainLayout->addWidget(splitter);

    // Connections
    connect(startBtn, &QPushButton::clicked, this, &DebugWidget::startDebugging);
    connect(stopBtn, &QPushButton::clicked, this, &DebugWidget::stopDebugging);
    connect(stepOverBtn, &QPushButton::clicked, this, &DebugWidget::stepOver);
    connect(stepIntoBtn, &QPushButton::clicked, this, &DebugWidget::stepInto);
    connect(continueBtn, &QPushButton::clicked, this, &DebugWidget::continueDebug);
    connect(cmdInput, &QLineEdit::returnPressed, this, &DebugWidget::sendManualCommand);
    
    connect(variablesTree, &QTreeWidget::itemClicked, this, [this](QTreeWidgetItem* item, int column) {
        if (item && visualInspector) {
            visualInspector->inspectVariable(item->text(0), item->text(1), item->text(2));
        }
    });
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
            addVariable("my_array", "std::vector<int>", "[12, 45, 78, 34, 89, 56]");
            addVariable("my_matrix", "int[3][3]", "[[10, 20, 30], [40, 50, 60], [70, 80, 90]]");
        } else if (simStepCount == 2) {
            addVariable("argc", "int", "1");
            addVariable("argv", "char**", "0x0000021a8d052a60");
            addVariable("app", "QApplication", "{...}");
            addVariable("isInitialized", "bool", "true");
            addVariable("my_array", "std::vector<int>", "[18, 55, 78, 22, 99, 44]");
            addVariable("my_matrix", "int[3][3]", "[[15, 25, 35], [45, 55, 65], [75, 85, 95]]");
            addVariable("my_graph", "Graph", "{\"nodes\": [1, 2, 3, 4], \"edges\": [[1, 2], [2, 3], [3, 4], [4, 1]]}");
        } else {
            addVariable("argc", "int", "1");
            addVariable("argv", "char**", "0x0000021a8d052a60");
            addVariable("app", "QApplication", "{...}");
            addVariable("isInitialized", "bool", "true");
            addVariable("my_array", "std::vector<int>", QString("[%1, 40, 60, 80, 100, 20]").arg(simStepCount * 10));
            addVariable("my_matrix", "int[3][3]", QString("[[%1, 20, 30], [40, %1, 60], [70, 80, %1]]").arg(simStepCount * 5));
            addVariable("my_graph", "Graph", QString("{\"nodes\": [1, 2, 3, 4, 5], \"edges\": [[1, 2], [2, 3], [3, 4], [4, 5], [5, %1]]}").arg((simStepCount % 2 == 0) ? "1" : "3"));
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

VisualInspectorWidget::VisualInspectorWidget(QWidget* parent)
    : QWidget(parent), visType(VisNone)
{
    setMinimumHeight(180);
}

void VisualInspectorWidget::inspectVariable(const QString& name, const QString& type, const QString& val) {
    varName = name;
    varType = type;
    varVal = val;
    
    arrayData.clear();
    matrixData.clear();
    graphNodes.clear();
    graphEdges.clear();
    visType = VisNone;

    QString cleanVal = val.trimmed();
    
    // Parse Graph
    if (cleanVal.contains("nodes") && cleanVal.contains("edges")) {
        visType = VisGraph;
        QRegularExpression nodeRegex(R"("nodes"\s*:\s*\[([0-9,\s]*)\])");
        auto nodeMatch = nodeRegex.match(cleanVal);
        if (nodeMatch.hasMatch()) {
            QStringList ns = nodeMatch.captured(1).split(',');
            for (const QString& n : ns) {
                QString trimmed = n.trimmed();
                if (!trimmed.isEmpty()) graphNodes.push_back(trimmed.toInt());
            }
        }
        QRegularExpression edgeRegex(R"("edges"\s*:\s*\[\s*(\[[0-9,\s,]*\]\s*,?\s*)*\s*\])");
        QRegularExpression pairRegex(R"(\[\s*(\d+)\s*,\s*(\d+)\s*\])");
        auto pairIt = pairRegex.globalMatch(cleanVal);
        while (pairIt.hasNext()) {
            auto pairMatch = pairIt.next();
            int u = pairMatch.captured(1).toInt();
            int v = pairMatch.captured(2).toInt();
            graphEdges.push_back({u, v});
        }
    }
    // Parse Matrix
    else if (cleanVal.startsWith("[[") || cleanVal.startsWith("{{")) {
        visType = VisMatrix;
        QRegularExpression rowRegex(R"(\[([0-9,\s.-]+)\])");
        if (cleanVal.startsWith("{")) {
            rowRegex = QRegularExpression(R"(\{([0-9,\s.-]+)\})");
        }
        auto rowIt = rowRegex.globalMatch(cleanVal);
        while (rowIt.hasNext()) {
            auto rowMatch = rowIt.next();
            QStringList cols = rowMatch.captured(1).split(',');
            std::vector<double> rowData;
            for (const QString& c : cols) {
                QString trimmed = c.trimmed();
                if (!trimmed.isEmpty()) rowData.push_back(trimmed.toDouble());
            }
            if (!rowData.empty()) {
                matrixData.push_back(rowData);
            }
        }
    }
    // Parse Array
    else if (cleanVal.startsWith("[") || cleanVal.startsWith("{")) {
        visType = VisArray;
        QString inner = cleanVal;
        if (inner.startsWith("[")) {
            inner = inner.mid(1, inner.length() - 2);
        } else {
            inner = inner.mid(1, inner.length() - 2);
        }
        QStringList items = inner.split(',');
        for (const QString& item : items) {
            QString trimmed = item.trimmed();
            if (!trimmed.isEmpty()) {
                arrayData.push_back(trimmed.toDouble());
            }
        }
    }
    
    update();
}

void VisualInspectorWidget::paintEvent(QPaintEvent* event) {
    QPainter painter(this);
    painter.setRenderHint(QPainter::Antialiasing);

    painter.fillRect(rect(), QColor("#1e1e1e"));

    if (visType == VisNone || (arrayData.empty() && matrixData.empty() && graphNodes.empty())) {
        painter.setPen(QColor("#5c6370"));
        painter.setFont(QFont("Segoe UI", 10));
        painter.drawText(rect(), Qt::AlignCenter, "Select a collection variable (array, matrix, or graph)\nin the variables pane to view graphical visualization.");
        return;
    }

    painter.setPen(QColor("#abb2bf"));
    painter.setFont(QFont("Segoe UI", 9, QFont::Bold));
    painter.drawText(QRect(10, 10, width() - 20, 20), Qt::AlignLeft | Qt::AlignVCenter, QString("Visualizing: %1 (%2)").arg(varName).arg(varType));

    int contentY = 35;
    int contentHeight = height() - contentY - 15;
    int contentWidth = width() - 30;
    int contentX = 15;

    if (visType == VisArray) {
        int numElements = arrayData.size();
        double maxVal = 1e-5;
        for (double val : arrayData) {
            if (qAbs(val) > maxVal) maxVal = qAbs(val);
        }

        int barSpacing = 6;
        int totalSpacing = barSpacing * (numElements - 1);
        int barWidth = (contentWidth - totalSpacing) / numElements;
        if (barWidth < 4) barWidth = 4;

        for (int i = 0; i < numElements; ++i) {
            double val = arrayData[i];
            int barHeight = static_cast<int>((qAbs(val) / maxVal) * (contentHeight - 20));
            int x = contentX + i * (barWidth + barSpacing);
            int y = contentY + contentHeight - barHeight;

            QLinearGradient gradient(x, y, x, y + barHeight);
            gradient.setColorAt(0.0, QColor("#61afef"));
            gradient.setColorAt(1.0, QColor("#4db5ff"));
            
            painter.setBrush(gradient);
            painter.setPen(QColor("#3e4452"));
            painter.drawRect(x, y, barWidth, barHeight);

            painter.setPen(QColor("#abb2bf"));
            painter.setFont(QFont("Segoe UI", 8));
            QString valStr = QString::number(val);
            painter.drawText(QRect(x - 10, y - 18, barWidth + 20, 15), Qt::AlignCenter, valStr);
        }
    }
    else if (visType == VisMatrix) {
        int rows = matrixData.size();
        int cols = 0;
        double maxVal = 1e-5;
        for (const auto& r : matrixData) {
            if (static_cast<int>(r.size()) > cols) cols = r.size();
            for (double val : r) {
                if (qAbs(val) > maxVal) maxVal = qAbs(val);
            }
        }

        if (rows > 0 && cols > 0) {
            int cellSizeX = contentWidth / cols;
            int cellSizeY = contentHeight / rows;
            int cellSize = qMin(cellSizeX, cellSizeY);
            if (cellSize < 10) cellSize = 10;

            int startX = contentX + (contentWidth - cellSize * cols) / 2;
            int startY = contentY + (contentHeight - cellSize * rows) / 2;

            for (int r = 0; r < rows; ++r) {
                for (int c = 0; c < static_cast<int>(matrixData[r].size()); ++c) {
                    double val = matrixData[r][c];
                    double ratio = qAbs(val) / maxVal;

                    int red = static_cast<int>(33 + ratio * (152 - 33));
                    int green = static_cast<int>(37 + ratio * (195 - 37));
                    int blue = static_cast<int>(43 + ratio * (121 - 43));
                    QColor cellColor(red, green, blue);

                    int x = startX + c * cellSize;
                    int y = startY + r * cellSize;

                    painter.setBrush(cellColor);
                    painter.setPen(QColor("#181a1f"));
                    painter.drawRect(x, y, cellSize, cellSize);

                    painter.setPen(ratio > 0.5 ? QColor("#1e1e1e") : QColor("#abb2bf"));
                    painter.setFont(QFont("Segoe UI", 8, QFont::Bold));
                    painter.drawText(QRect(x, y, cellSize, cellSize), Qt::AlignCenter, QString::number(val));
                }
            }
        }
    }
    else if (visType == VisGraph) {
        int numNodes = graphNodes.size();
        if (numNodes > 0) {
            int centerX = contentX + contentWidth / 2;
            int centerY = contentY + contentHeight / 2;
            int radius = qMin(contentWidth, contentHeight) / 2 - 25;
            if (radius < 20) radius = 20;

            QHash<int, QPoint> nodePos;
            for (int i = 0; i < numNodes; ++i) {
                double angle = (2.0 * M_PI * i) / numNodes;
                int x = centerX + static_cast<int>(radius * qCos(angle));
                int y = centerY + static_cast<int>(radius * qSin(angle));
                nodePos[graphNodes[i]] = QPoint(x, y);
            }

            painter.setPen(QPen(QColor("#5c6370"), 2));
            for (const auto& edge : graphEdges) {
                if (nodePos.contains(edge.first) && nodePos.contains(edge.second)) {
                    QPoint p1 = nodePos[edge.first];
                    QPoint p2 = nodePos[edge.second];
                    painter.drawLine(p1, p2);
                }
            }

            int nodeRadius = 15;
            for (int i = 0; i < numNodes; ++i) {
                int nodeId = graphNodes[i];
                QPoint pos = nodePos[nodeId];

                QRadialGradient grad(pos.x(), pos.y(), nodeRadius);
                grad.setColorAt(0.0, QColor("#61afef"));
                grad.setColorAt(1.0, QColor("#4db5ff"));

                painter.setBrush(grad);
                painter.setPen(QPen(QColor("#ffffff"), 1.5));
                painter.drawEllipse(pos, nodeRadius, nodeRadius);

                painter.setPen(QColor("#1e1e1e"));
                painter.setFont(QFont("Segoe UI", 9, QFont::Bold));
                painter.drawText(QRect(pos.x() - nodeRadius, pos.y() - nodeRadius, nodeRadius * 2, nodeRadius * 2), Qt::AlignCenter, QString::number(nodeId));
            }
        }
    }
}
