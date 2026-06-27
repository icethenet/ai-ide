#include "ProblemsWidget.hpp"
#include <QVBoxLayout>
#include <QTableWidget>
#include <QHeaderView>
#include <QTableWidgetItem>

ProblemsWidget::ProblemsWidget(QWidget* parent)
    : QWidget(parent)
{
    auto* layout = new QVBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);

    table = new QTableWidget(0, 4, this);
    table->setHorizontalHeaderLabels({"Severity", "File", "Line", "Message"});
    table->horizontalHeader()->setSectionResizeMode(3, QHeaderView::Stretch);
    table->horizontalHeader()->setSectionResizeMode(1, QHeaderView::ResizeToContents);
    table->setEditTriggers(QAbstractItemView::NoEditTriggers);
    table->setSelectionBehavior(QAbstractItemView::SelectRows);
    table->setAlternatingRowColors(true);
    table->verticalHeader()->setVisible(false);

    layout->addWidget(table);

    connect(table, &QTableWidget::itemDoubleClicked, this, [this](QTableWidgetItem* item) {
        int row = item->row();
        QString file = table->item(row, 1)->text();
        int line = table->item(row, 2)->text().toInt();
        emit problemActivated(file, line);
    });
}

void ProblemsWidget::clearProblems() {
    table->setRowCount(0);
}

void ProblemsWidget::addProblem(const QString& severity, const QString& file, int line, int col, const QString& message) {
    int row = table->rowCount();
    table->insertRow(row);

    auto* sevItem = new QTableWidgetItem(severity);
    if (severity.toLower() == "error") {
        sevItem->setForeground(QColor(220, 60, 60));
    } else if (severity.toLower() == "warning") {
        sevItem->setForeground(QColor(220, 160, 40));
    } else {
        sevItem->setForeground(QColor(100, 160, 240));
    }
    table->setItem(row, 0, sevItem);
    table->setItem(row, 1, new QTableWidgetItem(file));
    table->setItem(row, 2, new QTableWidgetItem(QString::number(line)));
    table->setItem(row, 3, new QTableWidgetItem(message));
    
    (void)col; // stored in item data if needed later
}
