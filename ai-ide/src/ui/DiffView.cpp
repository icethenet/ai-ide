#include "DiffView.hpp"
#include <QHBoxLayout>
#include <QPlainTextEdit>
#include <QStringList>

DiffView::DiffView(QWidget* parent)
    : QWidget(parent)
{
    auto* layout = new QHBoxLayout(this);
    leftView = new QPlainTextEdit(this);
    rightView = new QPlainTextEdit(this);

    leftView->setReadOnly(true);
    rightView->setReadOnly(true);
    
    // Set a monospace font for code clarity
    QFont monoFont("Consolas", 10);
    if (monoFont.fixedPitch()) {
        leftView->setFont(monoFont);
        rightView->setFont(monoFont);
    }

    layout->addWidget(leftView);
    layout->addWidget(rightView);
}

void DiffView::setTexts(const QString& original, const QString& modified) {
    leftView->clear();
    rightView->clear();

    QStringList leftLines = original.split('\n');
    QStringList rightLines = modified.split('\n');

    const int contextLines = 3;
    for (int i = 0; i < std::max(leftLines.size(), rightLines.size()); ++i) {
        bool isChanged = (i >= leftLines.size() || i >= rightLines.size() || leftLines[i] != rightLines[i]);
        bool nearChange = false;

        for (int j = i - contextLines; j <= i + contextLines; ++j) {
            if (j >= 0 && j < leftLines.size() && j < rightLines.size() && leftLines[j] != rightLines[j]) {
                nearChange = true; break;
            }
        }

        if (isChanged) {
            if (i < leftLines.size()) 
                leftView->appendHtml("<div style='background-color: #ffdce0;'>" + QString::number(i+1).rightJustified(4) + " | " + leftLines[i].toHtmlEscaped() + "</div>");
            if (i < rightLines.size())
                rightView->appendHtml("<div style='background-color: #e6ffed;'>" + QString::number(i+1).rightJustified(4) + " | " + rightLines[i].toHtmlEscaped() + "</div>");
        } else if (nearChange) {
            leftView->appendPlainText(QString::number(i+1).rightJustified(4) + " | " + leftLines[i]);
            rightView->appendPlainText(QString::number(i+1).rightJustified(4) + " | " + rightLines[i]);
        } else if (i > 0 && (i-1 < leftLines.size() && leftLines[i-1] != rightLines[i-1])) {
            leftView->appendPlainText(" --- [Hunk Boundary] --- ");
            rightView->appendPlainText(" --- [Hunk Boundary] --- ");
        }
    }
}
