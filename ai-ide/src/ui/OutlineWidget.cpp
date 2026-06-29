#include "OutlineWidget.hpp"
#include <QVBoxLayout>
#include <QBrush>
#include <QHeaderView>

OutlineWidget::OutlineWidget(QWidget* parent) : QWidget(parent) {
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(4, 4, 4, 4);
    mainLayout->setSpacing(6);

    filterEdit = new QLineEdit(this);
    filterEdit->setPlaceholderText("Filter symbols...");
    filterEdit->setStyleSheet("QLineEdit { background-color: #1e1e1e; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 4px 8px; font-family: 'Segoe UI', Arial; font-size: 11px; }"
                               "QLineEdit:focus { border-color: #61afef; }");

    treeWidget = new QTreeWidget(this);
    treeWidget->setHeaderHidden(true);
    treeWidget->setColumnCount(1);
    treeWidget->setStyleSheet("QTreeWidget { background-color: #21252b; color: #abb2bf; border: none; font-family: 'Segoe UI', Arial; font-size: 11px; }"
                              "QTreeWidget::item { padding: 4px; }"
                              "QTreeWidget::item:hover { background-color: #2c313c; color: #ffffff; }"
                              "QTreeWidget::item:selected { background-color: #3e4452; color: #ffffff; }");

    placeholderLabel = new QLabel("Open a C++ file to see its outline hierarchy.", this);
    placeholderLabel->setWordWrap(true);
    placeholderLabel->setAlignment(Qt::AlignCenter);
    placeholderLabel->setStyleSheet("QLabel { color: #5c6370; font-family: 'Segoe UI', Arial; font-size: 11px; padding: 20px; }");

    mainLayout->addWidget(filterEdit);
    mainLayout->addWidget(treeWidget);
    mainLayout->addWidget(placeholderLabel);

    treeWidget->hide();
    placeholderLabel->show();

    connect(filterEdit, &QLineEdit::textChanged, this, &OutlineWidget::onFilterChanged);
    connect(treeWidget, &QTreeWidget::itemClicked, this, &OutlineWidget::onItemClicked);
}

void OutlineWidget::clearOutline() {
    treeWidget->clear();
    treeWidget->hide();
    placeholderLabel->show();
}

void OutlineWidget::updateSymbols(const QJsonArray& symbols) {
    treeWidget->clear();
    if (symbols.isEmpty()) {
        treeWidget->hide();
        placeholderLabel->show();
        return;
    }

    for (const auto& val : symbols) {
        QJsonObject sym = val.toObject();
        populateOutlineNode(nullptr, sym);
    }

    placeholderLabel->hide();
    treeWidget->show();
    
    for (int i = 0; i < treeWidget->topLevelItemCount(); ++i) {
        treeWidget->topLevelItem(i)->setExpanded(true);
    }
}

void OutlineWidget::populateOutlineNode(QTreeWidgetItem* parentItem, const QJsonObject& symbol) {
    QString name = symbol["name"].toString();
    int kind = symbol["kind"].toInt();
    
    QJsonObject range = symbol["range"].toObject();
    QJsonObject start = range["start"].toObject();
    int line = start["line"].toInt();

    QTreeWidgetItem* item = nullptr;
    if (parentItem) {
        item = new QTreeWidgetItem(parentItem);
    } else {
        item = new QTreeWidgetItem(treeWidget);
    }

    item->setText(0, getSymbolPrefix(kind) + name);
    item->setForeground(0, QBrush(getSymbolColor(kind)));
    item->setData(0, Qt::UserRole, line + 1);

    if (symbol.contains("children") && symbol["children"].isArray()) {
        QJsonArray children = symbol["children"].toArray();
        for (const auto& chVal : children) {
            populateOutlineNode(item, chVal.toObject());
        }
    }
}

QString OutlineWidget::getSymbolPrefix(int kind) const {
    switch (kind) {
        case 5: return "[C] ";
        case 6: return "[M] ";
        case 7: return "[P] ";
        case 8: return "[F] ";
        case 9: return "[Ctor] ";
        case 10: return "[Dtor] ";
        case 12: return "[F] ";
        case 13: return "[V] ";
        case 22: return "[E] ";
        case 23: return "[EM] ";
        case 24: return "[S] ";
        default: return "";
    }
}

QColor OutlineWidget::getSymbolColor(int kind) const {
    switch (kind) {
        case 5: return QColor("#98c379");
        case 24: return QColor("#98c379");
        case 6: return QColor("#61afef");
        case 9: return QColor("#61afef");
        case 10: return QColor("#61afef");
        case 12: return QColor("#61afef");
        case 8: return QColor("#d19a66");
        case 13: return QColor("#d19a66");
        case 22: return QColor("#e5c07b");
        case 23: return QColor("#e5c07b");
        default: return QColor("#abb2bf");
    }
}

void OutlineWidget::onFilterChanged(const QString& text) {
    std::function<bool(QTreeWidgetItem*)> filterNode = [&](QTreeWidgetItem* item) -> bool {
        bool anyChildVisible = false;
        for (int i = 0; i < item->childCount(); ++i) {
            if (filterNode(item->child(i))) {
                anyChildVisible = true;
            }
        }
        bool matches = item->text(0).contains(text, Qt::CaseInsensitive);
        bool visible = matches || anyChildVisible;
        item->setHidden(!visible);
        return visible;
    };

    for (int i = 0; i < treeWidget->topLevelItemCount(); ++i) {
        filterNode(treeWidget->topLevelItem(i));
    }
}

void OutlineWidget::onItemClicked(QTreeWidgetItem* item, int column) {
    QVariant val = item->data(0, Qt::UserRole);
    if (val.isValid()) {
        emit lineNavigationRequested(val.toInt());
    }
}
