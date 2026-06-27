#include "CommandPalette.hpp"
#include <QVBoxLayout>
#include <QKeyEvent>
#include <QVariant>

CommandPalette::CommandPalette(QWidget* parent)
    : QDialog(parent, Qt::FramelessWindowHint | Qt::Popup)
{
    setMinimumWidth(550);
    setMaximumHeight(350);
    setStyleSheet("QDialog { background-color: #21252b; border: 1px solid #3e4452; border-radius: 8px; }"
                  "QLineEdit { background-color: #2c313c; color: #ffffff; border: 1px solid #181a1f; border-radius: 4px; padding: 8px; font-size: 14px; font-family: 'Segoe UI', Arial; }"
                  "QListWidget { background-color: #21252b; color: #abb2bf; border: none; font-size: 13px; font-family: 'Segoe UI', Arial; }"
                  "QListWidget::item { padding: 10px; border-bottom: 1px solid #2c313c; border-radius: 4px; }"
                  "QListWidget::item:selected { background-color: #3e4452; color: #ffffff; }");

    auto* layout = new QVBoxLayout(this);
    searchEdit = new QLineEdit(this);
    searchEdit->setPlaceholderText("Type a command to search...");
    layout->addWidget(searchEdit);

    listWidget = new QListWidget(this);
    layout->addWidget(listWidget);

    connect(searchEdit, &QLineEdit::textChanged, this, &CommandPalette::filterCommands);
    connect(listWidget, &QListWidget::itemActivated, this, &CommandPalette::executeSelected);

    searchEdit->installEventFilter(this);
}

void CommandPalette::addCommand(const QString& name, const QString& shortcut, const std::function<void()>& action) {
    commands.push_back({name, shortcut, action});
}

void CommandPalette::showPalette() {
    searchEdit->clear();
    filterCommands("");
    
    if (parentWidget()) {
        QPoint center = parentWidget()->rect().center();
        QPoint pos(center.x() - width() / 2, parentWidget()->rect().top() + 50);
        move(parentWidget()->mapToGlobal(pos));
    }
    
    show();
    searchEdit->setFocus();
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

void CommandPalette::executeSelected() {
    auto* item = listWidget->currentItem();
    if (item) {
        int idx = item->data(Qt::UserRole).toInt();
        if (idx >= 0 && idx < static_cast<int>(commands.size())) {
            commands[idx].action();
        }
    }
    accept();
}

bool CommandPalette::eventFilter(QObject* obj, QEvent* event) {
    if (obj == searchEdit && event->type() == QEvent::KeyPress) {
        auto* keyEvent = static_cast<QKeyEvent*>(event);
        if (keyEvent->key() == Qt::Key_Down) {
            int row = listWidget->currentRow();
            if (row < listWidget->count() - 1) {
                listWidget->setCurrentRow(row + 1);
            }
            return true;
        } else if (keyEvent->key() == Qt::Key_Up) {
            int row = listWidget->currentRow();
            if (row > 0) {
                listWidget->setCurrentRow(row - 1);
            }
            return true;
        } else if (keyEvent->key() == Qt::Key_Enter || keyEvent->key() == Qt::Key_Return) {
            executeSelected();
            return true;
        } else if (keyEvent->key() == Qt::Key_Escape) {
            reject();
            return true;
        }
    }
    return QDialog::eventFilter(obj, event);
}
