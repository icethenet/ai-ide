#include "AIChatPanel.hpp"
#include "../ai/GeminiProvider.hpp"
#include "../ai/OllamaProvider.hpp"
#include "../ai/ClaudeProvider.hpp"
#include "../ai/AntigravityProvider.hpp"
#include "DiffView.hpp"
#include <QApplication>
#include <QCheckBox>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QRegularExpression>
#include <QFile>
#include <QTextStream>
#include <QDir>
#include <QMessageBox>
#include <QDateTime>
#include <QDialog>
#include <QDialogButtonBox>

QString AIChatPanel::applySearchReplace(const QString& originalText, const QString& patchContent, bool& success, QString& errorMsg) {
    QString modifiedText = originalText;
    success = true;

    QRegularExpression hunkRegex("(?s)<<<<<<< SEARCH\\s*\\n(.*?)\\n?=======\\s*\\n(.*?)\\n?>>>>>>> REPLACE");
    QRegularExpressionMatchIterator it = hunkRegex.globalMatch(patchContent);
    
    int matchCount = 0;
    while (it.hasNext()) {
        QRegularExpressionMatch match = it.next();
        QString searchText = match.captured(1);
        QString replaceText = match.captured(2);
        matchCount++;

        QString cleanSearch = searchText.trimmed();
        
        int index = modifiedText.indexOf(searchText);
        if (index == -1) {
            index = modifiedText.indexOf(cleanSearch);
            if (index == -1) {
                success = false;
                errorMsg = QString("Could not find SEARCH block #%1 in the target file. SEARCH text was:\n%2").arg(matchCount).arg(cleanSearch.left(120));
                return originalText;
            }
            modifiedText.replace(index, cleanSearch.length(), replaceText);
        } else {
            modifiedText.replace(index, searchText.length(), replaceText);
        }
    }

    if (matchCount == 0) {
        modifiedText = patchContent;
    }

    return modifiedText;
}

ActionItemWidget::ActionItemWidget(const AIAction& act, QWidget* parent)
    : QWidget(parent), action(act)
{
    auto* layout = new QHBoxLayout(this);
    layout->setContentsMargins(4, 4, 4, 4);
    layout->setSpacing(6);

    checkBox = new QCheckBox(this);
    checkBox->setChecked(true);

    typeBadge = new QLabel(this);
    typeBadge->setContentsMargins(4, 2, 4, 2);
    
    if (action.type == "create_file") {
        typeBadge->setText(" CREATE ");
        typeBadge->setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; border-radius: 3px; font-size: 9px;");
    } else if (action.type == "modify_file") {
        typeBadge->setText(" MODIFY ");
        typeBadge->setStyleSheet("background-color: #3498db; color: white; font-weight: bold; border-radius: 3px; font-size: 9px;");
    } else if (action.type == "modify_current_editor") {
        typeBadge->setText(" EDIT ACT ");
        typeBadge->setStyleSheet("background-color: #9b59b6; color: white; font-weight: bold; border-radius: 3px; font-size: 9px;");
    } else if (action.type == "insert_at_cursor") {
        typeBadge->setText(" INSERT ");
        typeBadge->setStyleSheet("background-color: #e67e22; color: white; font-weight: bold; border-radius: 3px; font-size: 9px;");
    }

    QString text = action.path.isEmpty() ? action.description : QString("%1 (%2)").arg(action.path).arg(action.description);
    infoLabel = new QLabel(text, this);
    infoLabel->setStyleSheet("font-size: 11px; font-weight: 500; color: #2c3e50;");
    
    previewBtn = new QPushButton("Diff", this);
    previewBtn->setFixedWidth(40);
    previewBtn->setStyleSheet("QPushButton { background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 3px; font-size: 10px; padding: 2px; color: #475569; font-weight: bold; }"
                             "QPushButton:hover { background-color: #e2e8f0; }");

    layout->addWidget(checkBox);
    layout->addWidget(typeBadge);
    layout->addWidget(infoLabel, 1);
    layout->addWidget(previewBtn);

    connect(previewBtn, &QPushButton::clicked, this, [this]() {
        emit previewRequested(action);
    });
}

ProposedActionsWidget::ProposedActionsWidget(QWidget* parent)
    : QWidget(parent)
{
    auto* layout = new QVBoxLayout(this);
    layout->setContentsMargins(6, 6, 6, 6);
    layout->setSpacing(6);

    titleLabel = new QLabel("Proposed Actions:", this);
    titleLabel->setStyleSheet("font-weight: bold; color: #1e293b; font-size: 11px;");

    scrollArea = new QScrollArea(this);
    scrollArea->setWidgetResizable(true);
    scrollArea->setFrameShape(QFrame::NoFrame);
    scrollArea->setMaximumHeight(160);

    listContainer = new QWidget(scrollArea);
    listLayout = new QVBoxLayout(listContainer);
    listLayout->setContentsMargins(0, 0, 0, 0);
    listLayout->setSpacing(4);
    listLayout->addStretch();
    listContainer->setLayout(listLayout);

    scrollArea->setWidget(listContainer);

    auto* btnLayout = new QHBoxLayout();
    applyBtn = new QPushButton("Apply Checked Actions", this);
    applyBtn->setStyleSheet("QPushButton { background-color: #10b981; color: white; font-weight: bold; border-radius: 4px; padding: 5px; font-size: 11px; }"
                            "QPushButton:hover { background-color: #059669; }");

    discardBtn = new QPushButton("Discard", this);
    discardBtn->setStyleSheet("QPushButton { background-color: #ef4444; color: white; font-weight: bold; border-radius: 4px; padding: 5px; font-size: 11px; }"
                             "QPushButton:hover { background-color: #dc2626; }");

    btnLayout->addWidget(applyBtn);
    btnLayout->addWidget(discardBtn);

    layout->addWidget(titleLabel);
    layout->addWidget(scrollArea);
    layout->addLayout(btnLayout);

    setStyleSheet("QWidget { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; }");

    connect(applyBtn, &QPushButton::clicked, this, &ProposedActionsWidget::executeRequested);
    connect(discardBtn, &QPushButton::clicked, this, &ProposedActionsWidget::clearActions);
}

void ProposedActionsWidget::setActions(const QVector<AIAction>& actions) {
    clearActions();
    
    if (listLayout->count() > 0) {
        QLayoutItem* item = listLayout->takeAt(0);
        if (item) delete item;
    }

    for (const auto& action : actions) {
        auto* itemWidget = new ActionItemWidget(action, listContainer);
        listLayout->addWidget(itemWidget);
        items.append(itemWidget);

        connect(itemWidget, &ActionItemWidget::previewRequested, this, &ProposedActionsWidget::previewAction);
    }
    
    listLayout->addStretch();
    titleLabel->setText(QString("Proposed Actions (%1):").arg(actions.size()));
    show();
}

QVector<AIAction> ProposedActionsWidget::getCheckedActions() const {
    QVector<AIAction> checked;
    for (auto* item : items) {
        if (item->isChecked()) {
            checked.append(item->getAction());
        }
    }
    return checked;
}

void ProposedActionsWidget::clearActions() {
    for (auto* item : items) {
        item->deleteLater();
    }
    items.clear();
    hide();
}

AIChatPanel::AIChatPanel(QWidget* parent) 
    : QWidget(parent), isAgenticRunning(false), agenticIteration(0) 
{
    auto* layout = new QVBoxLayout(this);
    chatHistory = new QTextEdit(this);
    chatHistory->setReadOnly(true);
    chatHistory->setPlaceholderText("AI Chat History...");

    actionsPanel = new ProposedActionsWidget(this);
    actionsPanel->hide();

    inputBox = new QTextEdit(this);
    inputBox->setFixedHeight(80);
    inputBox->setPlaceholderText("Type a message or instruction...");

    auto* inputControlLayout = new QHBoxLayout();
    agenticModeCheck = new QCheckBox("Agentic Loop (Auto-Fix Build)", this);
    agenticModeCheck->setStyleSheet("QCheckBox { color: #abb2bf; font-family: 'Segoe UI', Arial; font-size: 11px; }"
                                    "QCheckBox::indicator { width: 14px; height: 14px; border: 1px solid #3e4452; border-radius: 3px; background-color: #1e1e1e; }"
                                    "QCheckBox::indicator:checked { background-color: #98c379; border-color: #7cb057; }");

    sendButton = new QPushButton("Send", this);
    sendButton->setStyleSheet("QPushButton { background-color: #61afef; color: #1e1e1e; font-weight: bold; border-radius: 4px; padding: 6px 12px; font-family: 'Segoe UI', Arial; font-size: 12px; }"
                              "QPushButton:hover { background-color: #4db5ff; }");

    inputControlLayout->addWidget(agenticModeCheck);
    inputControlLayout->addWidget(sendButton);

    layout->addWidget(chatHistory);
    layout->addWidget(actionsPanel);
    layout->addWidget(inputBox);
    layout->addLayout(inputControlLayout);

    connect(sendButton, &QPushButton::clicked, this, &AIChatPanel::sendPrompt);
    connect(actionsPanel, &ProposedActionsWidget::executeRequested, this, &AIChatPanel::executeActions);
    connect(actionsPanel, &ProposedActionsWidget::previewAction, this, &AIChatPanel::handlePreview);
}

void AIChatPanel::sendPrompt() {
    if (isAgenticRunning) {
        chatHistory->append("<br><b style='color:#e5c07b;'>[Agent Stopped]</b> Loop cancelled by user.");
        stopAgenticLoop();
        return;
    }

    QString prompt = inputBox->toPlainText().trimmed();
    if (prompt.isEmpty()) return;

    if (agenticModeCheck->isChecked()) {
        isAgenticRunning = true;
        agenticIteration = 1;
        chatHistory->append("<br><b style='color:#61afef;'>[Agent Mode Enabled]</b> Starting autonomous edit-and-build pipeline...");
    }

    queryAI(prompt, false);
}

void AIChatPanel::stopAgenticLoop() {
    isAgenticRunning = false;
    sendButton->setEnabled(true);
    sendButton->setText("Send");
}

void AIChatPanel::handleBuildFinished(int exitCode, const QString& buildErrors) {
    if (!isAgenticRunning) return;

    if (exitCode == 0) {
        chatHistory->append("<br><b style='color:#98c379;'>[Agent Success]</b> Build succeeded! All changes compiled and linked successfully.");
        stopAgenticLoop();
        return;
    }

    chatHistory->append(QString("<br><b style='color:#e06c75;'>[Agent Build Failed]</b> Build failed (Iteration %1 of %2). Found %3 errors.")
                         .arg(agenticIteration)
                         .arg(maxAgenticIterations)
                         .arg(buildErrors.count('\n')));

    if (agenticIteration >= maxAgenticIterations) {
        chatHistory->append("<br><b style='color:#e06c75;'>[Agent Failed]</b> Reached max iterations (5) without succeeding. Stopping loop.");
        stopAgenticLoop();
        return;
    }

    chatHistory->append("<b>Agent:</b> Asking AI for surgical corrections to resolve the build errors...");
    QApplication::processEvents();

    QString followUpPrompt = QString("The build failed with the following compilation errors:\n\n%1\n\n"
                                     "Please review the errors and provide surgical SEARCH/REPLACE blocks in the affected files to correct them.")
                                     .arg(buildErrors);

    agenticIteration++;
    queryAI(followUpPrompt, true);
}

void AIChatPanel::queryAI(const QString& prompt, bool isAutoFix) {
    if (prompt.isEmpty()) return;

    if (!isAutoFix) {
        chatHistory->append("<b>You:</b> " + prompt);
        actionsPanel->clearActions();
    }

    sendButton->setEnabled(true);
    sendButton->setText(isAgenticRunning ? "Stop Agent" : "Thinking...");
    QApplication::processEvents();

    // Context Gathering
    QString currentFilePath = "";
    QString currentFileContent = "";
    QString baseDir = "";
    emit requestActiveFileContext(currentFilePath, currentFileContent, baseDir);

    QString contextStr = QString("\n\n=== USER ACTIVE EDITOR CONTEXT ===\n"
                                 "Current Workspace Base Directory: %1\n")
                                 .arg(baseDir);

    if (!currentFilePath.isEmpty()) {
        QString relativePath = QDir(baseDir).relativeFilePath(currentFilePath);
        contextStr += QString("Active file path (relative to base): %1\n"
                              "Active file content:\n"
                              "```cpp\n%2\n```\n")
                              .arg(relativePath)
                              .arg(currentFileContent);
    } else {
        contextStr += "No file is currently active/open in the editor.\n";
    }

    QString systemInstructions = 
        "\n\n=== SYSTEM INSTRUCTIONS FOR ACTIONS ===\n"
        "You have the capability to create and edit files directly in the user's workspace. "
        "Analyze the user's prompt. If they want to modify code or create files, choose the appropriate action(s) from the list below and embed the code block inside XML tags in your response. "
        "Any regular commentary should be outside these tags.\n\n"
        "Available Action Tags:\n"
        "1. Create a brand new file:\n"
        "   <create_file path=\"relative/path/to/file\" description=\"what this file does\">\n"
        "   ```cpp\n"
        "   // complete content here\n"
        "   ```\n"
        "   </create_file>\n\n"
        "2. Modify an existing file in the project (use SEARCH/REPLACE block to specify only what lines to change):\n"
        "   <modify_file path=\"relative/path/to/file\" description=\"what was changed\">\n"
        "   <<<<<<< SEARCH\n"
        "   // Exact lines to find in the original file\n"
        "   =======\n"
        "   // Replacement lines\n"
        "   >>>>>>> REPLACE\n"
        "   </modify_file>\n\n"
        "3. Modify the file currently open in the active editor (use SEARCH/REPLACE block):\n"
        "   <modify_current_editor description=\"what was changed\">\n"
        "   <<<<<<< SEARCH\n"
        "   // Exact lines to find in the active editor\n"
        "   =======\n"
        "   // Replacement lines\n"
        "   >>>>>>> REPLACE\n"
        "   </modify_current_editor>\n\n"
        "4. Insert a small snippet of code at the user's current cursor position:\n"
        "   <insert_at_cursor description=\"what is inserted\">\n"
        "   ```cpp\n"
        "   // code snippet here\n"
        "   ```\n"
        "   </insert_at_cursor>\n\n"
        "IMPORTANT RULES:\n"
        "- The path must be a relative path from the project root.\n"
        "- For modify_file and modify_current_editor, always use the SEARCH/REPLACE block schema to modify only the targeted sections. You can write multiple SEARCH/REPLACE hunks within a single action if necessary.\n"
        "- For create_file, provide the COMPLETE file content inside standard markdown code block tags.\n"
        "- Do not put spaces around attribute equal signs (e.g. use path=\"file.cpp\" not path = \"file.cpp\").\n";

    // Re-initialize provider on the fly based on latest settings
    auto& settings = SettingsManager::instance();
    if (settings.getProviderType() == "Gemini") {
        provider = std::make_unique<GeminiProvider>(settings.getGeminiApiKey(), settings.getGeminiEndpoint());
    } else if (settings.getProviderType() == "Claude") {
        provider = std::make_unique<ClaudeProvider>(settings.getClaudeApiKey(), settings.getClaudeEndpoint());
    } else if (settings.getProviderType() == "Antigravity AI") {
        provider = std::make_unique<AntigravityProvider>(settings.getAntigravityApiKey(), settings.getAntigravityEndpoint());
    } else {
        provider = std::make_unique<OllamaProvider>(settings.getOllamaEndpoint());
    }

    AIRequest req;
    req.prompt = prompt.toStdString() + contextStr.toStdString() + systemInstructions.toStdString();
    AIResponse res = provider->send(req);

    QString responseText = QString::fromStdString(res.text);

    // Parse actions out
    QVector<AIAction> actions;
    QRegularExpression actionRegex("(?s)<(create_file|modify_file|modify_current_editor|insert_at_cursor)(?:\\s+path=\"([^\"]*)\")?\\s+description=\"([^\"]*)\"\\s*>\\s*(?:```(?:[a-zA-Z0-9+#]+)?\\s*\\n?)?(.*?)(?:\\s*```)?\\s*</\\1>");
    QRegularExpressionMatchIterator actionIt = actionRegex.globalMatch(responseText);
    while (actionIt.hasNext()) {
        QRegularExpressionMatch match = actionIt.next();
        AIAction action;
        action.type = match.captured(1);
        action.path = match.captured(2);
        action.description = match.captured(3);
        action.content = match.captured(4).trimmed();
        actions.append(action);
    }

    // Fallback: If no action tags but we have standard code blocks
    if (actions.isEmpty()) {
        QRegularExpression fallbackCodeRegex("(?s)```(?:[a-zA-Z0-9+#]+)?\\s*\\n?(.*?)\\n?```");
        QRegularExpressionMatchIterator codeIt = fallbackCodeRegex.globalMatch(responseText);
        int blockIdx = 1;
        while (codeIt.hasNext()) {
            QRegularExpressionMatch match = codeIt.next();
            QString code = match.captured(1).trimmed();
            if (!code.isEmpty()) {
                AIAction action;
                if (!currentFilePath.isEmpty()) {
                    action.type = "modify_current_editor";
                    action.description = QString("Apply code block #%1 to active editor").arg(blockIdx);
                } else {
                    action.type = "create_file";
                    action.path = "untitled_code.cpp";
                    action.description = QString("Create new file with code block #%1").arg(blockIdx);
                }
                action.content = code;
                actions.append(action);
                blockIdx++;
            }
        }
    }

    // Strip actions from text display
    QString cleanText = responseText;
    cleanText.replace(actionRegex, "");
    cleanText = cleanText.trimmed();
    if (cleanText.isEmpty()) {
        cleanText = "I have proposed some changes for you. See the Action Plan below.";
    }

    chatHistory->append("<b>AI:</b> " + cleanText);

    if (!isAutoFix) {
        inputBox->clear();
    }

    QString summary = QString("[%1] %2").arg(QDateTime::currentDateTime().toString("hh:mm")).arg(prompt.left(30) + "...");
    emit promptArchived(summary);

    sendButton->setEnabled(true);
    sendButton->setText(isAgenticRunning ? "Stop Agent" : "Send");

    if (!actions.isEmpty()) {
        actionsPanel->setActions(actions);
        
        if (isAgenticRunning) {
            chatHistory->append("<br><b style='color:#61afef;'>[Agent]</b> Automatically applying proposed fixes...");
            QApplication::processEvents();

            int successCount = 0;
            for (const auto& act : actions) {
                emit executeAction(act);
                successCount++;
            }
            actionsPanel->clearActions();

            chatHistory->append(QString("<b>[Agent]</b> Starting auto-fix build iteration %1...").arg(agenticIteration));
            QApplication::processEvents();
            emit requestBuildRun();
        }
    } else {
        if (isAgenticRunning) {
            chatHistory->append("<br><b style='color:#e06c75;'>[Agent Error]</b> AI returned no code actions. Stopping loop.");
            stopAgenticLoop();
        }
    }
}

void AIChatPanel::executeActions() {
    QVector<AIAction> checked = actionsPanel->getCheckedActions();
    if (checked.isEmpty()) {
        QMessageBox::information(this, "AI Actions", "No actions selected to execute.");
        return;
    }

    int successCount = 0;
    for (const auto& action : checked) {
        emit executeAction(action);
        successCount++;
    }

    actionsPanel->clearActions();

    if (agenticModeCheck->isChecked()) {
        isAgenticRunning = true;
        agenticIteration = 1;
        chatHistory->append("<br><b style='color:#61afef;'>[Agent Mode Activated]</b> Starting auto-fix build iteration 1...");
        QApplication::processEvents();
        emit requestBuildRun();
    } else {
        QMessageBox::information(this, "AI Actions", QString("Successfully applied %1 actions.").arg(successCount));
    }
}

void AIChatPanel::handlePreview(const AIAction& action) {
    QString originalContent = "";
    QString currentFilePath = "";
    QString baseDir = "";
    emit requestActiveFileContext(currentFilePath, originalContent, baseDir);

    if (action.type == "modify_current_editor") {
        // originalContent already contains the current editor content
    } else if (action.type == "modify_file") {
        QString absPath = QFileInfo(action.path).isAbsolute()
            ? action.path
            : QDir(baseDir).absoluteFilePath(action.path);
        QFile file(absPath);
        if (file.open(QIODevice::ReadOnly | QIODevice::Text)) {
            originalContent = QTextStream(&file).readAll();
            file.close();
        }
    }

    bool success = true;
    QString errorMsg = "";
    QString modifiedContent = applySearchReplace(originalContent, action.content, success, errorMsg);

    if (!success) {
        QMessageBox::warning(this, "AI Action Warning", QString("Warning: Some hunks failed to apply.\n%1").arg(errorMsg));
    }

    QDialog dlg(this);
    dlg.setWindowTitle(QString("AI Diff Preview - %1").arg(action.path.isEmpty() ? "Current File" : action.path));
    dlg.resize(900, 600);
    auto* layout = new QVBoxLayout(&dlg);
    auto* diffView = new DiffView(&dlg);
    diffView->setTexts(originalContent, modifiedContent);
    layout->addWidget(diffView);

    auto* buttonBox = new QDialogButtonBox(QDialogButtonBox::Ok, &dlg);
    layout->addWidget(buttonBox);
    connect(buttonBox, &QDialogButtonBox::accepted, &dlg, &QDialog::accept);

    dlg.exec();
}
