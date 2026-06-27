#include "CompletionPopup.hpp"
#include <QJsonObject>

CompletionPopup::CompletionPopup(QWidget* parent)
    : QListWidget(parent)
{
    setWindowFlags(Qt::ToolTip | Qt::FramelessWindowHint);
    setAttribute(Qt::WA_ShowWithoutActivating);
    setFocusPolicy(Qt::NoFocus);
    
    setStyleSheet("QListWidget { background-color: #21252b; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; font-family: 'Segoe UI', Arial; font-size: 12px; }"
                  "QListWidget::item { padding: 4px 8px; }"
                  "QListWidget::item:selected { background-color: #3e4452; color: #ffffff; }");
    
    setMinimumWidth(250);
    setMaximumHeight(150);
}

void CompletionPopup::setCompletions(const QJsonArray& items) {
    clear();
    for (const auto& val : items) {
        QJsonObject item = val.toObject();
        QString label = item["label"].toString();
        QString detail = item["detail"].toString();
        QString insertText = item["insertText"].toString();
        if (insertText.isEmpty()) insertText = label;

        auto* listItem = new QListWidgetItem(this);
        listItem->setText(label);
        if (!detail.isEmpty()) {
            listItem->setToolTip(detail);
        }
        listItem->setData(Qt::UserRole, insertText);
    }
    if (count() > 0) {
        setCurrentRow(0);
    }
}

void CompletionPopup::showAt(const QPoint& pos) {
    move(pos);
    show();
}
