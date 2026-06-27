#include "CommandPalette.hpp"
#include <QVBoxLayout>
#include <QVariant>

CommandPalette::CommandPalette(QWidget* parent)
    : QWidget(parent, Qt::FramelessWindowHint | Qt::Popup)
{
    setAttribute(Qt::WA_ShowWithoutActivating);
    setFocusPolicy(Qt::NoFocus);
    
    setMinimumWidth(550);
    setMaximumHeight(250);
    setStyleSheet("QWidget { background-color: #21252b; border: 1px solid #3e4452; border-radius: 8px; }"
                  "QListWidget { background-color: #21252b; color: #abb2bf; border: none; font-size: 13px; font-family: 'Segoe UI', Arial; }"
                  "QListWidget::item { padding: 10px; border-bottom: 1px solid #2c313c; border-radius: 4px; }"
                  "QListWidget::item:selected { background-color: #3e4452; color: #ffffff; }");

    auto* layout = new QVBoxLayout(this);
    layout->setContentsMargins(2, 2, 2, 2);
    listWidget = new QListWidget(this);
    listWidget->setFocusPolicy(Qt::NoFocus);
    layout->addWidget(listWidget);
}

void CommandPalette::addCommand(const QString& name, const QString& shortcut, const std::function<void()>& action) {
    commands.push_back({name, shortcut, action});
}

void CommandPalette::filterCommands(const QString& text) {
    listWidget->clear();
    for (size_t i = 0; i < commands.size(); ++i) {
        if (text.isEmpty() || commands[i].name.contains(text, Qt::CaseInsensitive)) {
            auto* item = new QListWidgetItem(listWidget);
            QString label = commands[i].name;
            if (!commands[i].shortcut.isEmpty()) {
                label += "   (" + commands[i].shortcut + ")";
            }
            item->setText(label);
            item->setData(Qt::UserRole, QVariant::fromValue(static_cast<int>(i)));
        }
    }
    if (listWidget->count() > 0) {
        listWidget->setCurrentRow(0);
    }
}

void CommandPalette::selectNext() {
    int row = listWidget->currentRow();
    if (row < listWidget->count() - 1) {
        listWidget->setCurrentRow(row + 1);
    }
}

void CommandPalette::selectPrev() {
    int row = listWidget->currentRow();
    if (row > 0) {
        listWidget->setCurrentRow(row - 1);
    }
}

void CommandPalette::executeCurrent() {
    auto* item = listWidget->currentItem();
    if (item) {
        int idx = item->data(Qt::UserRole).toInt();
        if (idx >= 0 && idx < static_cast<int>(commands.size())) {
            commands[idx].action();
        }
    }
    hide();
}
