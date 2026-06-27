#include "AIPatchController.hpp"
#include "DiffView.hpp"
#include "../ai/GeminiProvider.hpp"
#include "../ai/OllamaProvider.hpp"
#include <QDialog>
#include <QVBoxLayout>
#include <QPushButton>
#include <QDialogButtonBox>
#include <QRegularExpression>
#include <QFile>
#include <QTextStream>
#include <QDir>

AIPatchController::AIPatchController(CustomEditor* ed, QObject* parent)
    : QObject(parent),
      editor(ed)
{
    auto& settings = SettingsManager::instance();
    if (settings.getProviderType() == "Gemini")
        provider = std::make_unique<GeminiProvider>(settings.getEndpoint());
    else
        provider = std::make_unique<OllamaProvider>(settings.getEndpoint());
}

void AIPatchController::setEditor(CustomEditor* ed) {
    editor = ed;
}

void AIPatchController::requestRefactor(const QString& instruction) {
    if (!editor) return;
    QString code = editor->currentFilePath().isEmpty()
        ? QString()
        : editor->findChild<QPlainTextEdit*>()->toPlainText();

    AIRequest req;
    req.mode = "refactor";
    req.prompt = instruction.toStdString() + "\n\n" + code.toStdString();

    AIResponse res = provider->send(req);

    QString rawResponse = QString::fromStdString(res.text);
    QString newCode;

    // Extract the code block from the Markdown response
    QRegularExpression codeRegex("```(?:[a-zA-Z0-9+#]+)?\\n([\\s\\S]*?)```");
    QRegularExpressionMatch match = codeRegex.match(rawResponse);
    if (match.hasMatch()) {
        newCode = match.captured(1).trimmed();
    } else {
        newCode = rawResponse.trimmed();
    }

    // Persist the proposed code to a physical file
    QString tempPath = QDir::tempPath() + "/ai_proposed_patch.txt";
    QFile tempFile(tempPath);
    if (tempFile.open(QIODevice::WriteOnly | QIODevice::Text)) {
        QTextStream out(&tempFile);
        out << newCode;
        tempFile.close();
    }

    DiffView diffView;
    diffView.setTexts(code, newCode);

    QDialog dlg;
    dlg.setWindowTitle("AI Patch Preview");
    auto* layout = new QVBoxLayout(&dlg);
    layout->addWidget(&diffView);

    auto* buttons = new QDialogButtonBox(QDialogButtonBox::Cancel | QDialogButtonBox::Ok, &dlg);
    layout->addWidget(buttons);

    QObject::connect(buttons, &QDialogButtonBox::accepted, &dlg, [&]() {
        auto* textEdit = editor->findChild<QPlainTextEdit*>();
        if (textEdit) {
            textEdit->setPlainText(newCode);
        }
        dlg.accept();
    });
    QObject::connect(buttons, &QDialogButtonBox::rejected, &dlg, [&]() {
        dlg.reject();
    });

    dlg.exec();
}
