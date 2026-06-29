#include "GitHistoryWidget.hpp"
#include <QVBoxLayout>
#include <QHeaderView>
#include <QPainter>
#include <QBrush>
#include <QPen>
#include <QMessageBox>

GitHistoryDelegate::GitHistoryDelegate(const QList<CommitNode>& nodes, QObject* parent)
    : QStyledItemDelegate(parent), commitNodes(nodes) {}

void GitHistoryDelegate::paint(QPainter* painter, const QStyleOptionViewItem& option, const QModelIndex& index) const {
    if (index.column() != 0) {
        QStyledItemDelegate::paint(painter, option, index);
        return;
    }

    if (option.state & QStyle::State_Selected) {
        painter->fillRect(option.rect, QColor("#2c313c"));
    } else {
        painter->fillRect(option.rect, QColor("#1e1e1e"));
    }

    int row = index.row();
    if (row < 0 || row >= commitNodes.size()) return;

    painter->save();
    painter->setRenderHint(QPainter::Antialiasing);

    const auto& node = commitNodes[row];
    int xCenter = option.rect.left() + 15 + node.column * 12;
    int yCenter = option.rect.center().y();

    QList<QColor> colors = { QColor("#61afef"), QColor("#98c379"), QColor("#d19a66"), QColor("#e5c07b"), QColor("#c678dd"), QColor("#56b6c2") };
    QColor colColor = colors[node.column % colors.size()];

    // Draw track line down
    painter->setPen(QPen(colColor, 2));
    painter->drawLine(xCenter, yCenter, xCenter, option.rect.bottom());

    // Draw track line up
    painter->drawLine(xCenter, option.rect.top(), xCenter, yCenter);

    // Draw node circle
    painter->setBrush(colColor);
    painter->setPen(QPen(QColor("#ffffff"), 1));
    painter->drawEllipse(QPoint(xCenter, yCenter), 4, 4);

    painter->restore();
}

GitHistoryWidget::GitHistoryWidget(QWidget* parent)
    : QWidget(parent), gitProcess(new QProcess(this))
{
    auto* layout = new QVBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);

    tableWidget = new QTableWidget(this);
    tableWidget->setColumnCount(4);
    tableWidget->setHorizontalHeaderLabels({"Graph", "Message", "Author", "Commit"});
    tableWidget->horizontalHeader()->setSectionResizeMode(0, QHeaderView::ResizeToContents);
    tableWidget->horizontalHeader()->setSectionResizeMode(1, QHeaderView::Stretch);
    tableWidget->horizontalHeader()->setSectionResizeMode(2, QHeaderView::Interactive);
    tableWidget->horizontalHeader()->setSectionResizeMode(3, QHeaderView::ResizeToContents);
    
    tableWidget->setStyleSheet("QTableWidget { background-color: #1e1e1e; color: #abb2bf; border: none; font-family: 'Segoe UI', Arial; font-size: 11px; }"
                               "QHeaderView::section { background-color: #2c313c; color: #abb2bf; border: 1px solid #181a1f; padding: 4px; }");
    tableWidget->setSelectionBehavior(QAbstractItemView::SelectRows);
    tableWidget->setSelectionMode(QAbstractItemView::SingleSelection);
    tableWidget->verticalHeader()->setVisible(false);

    layout->addWidget(tableWidget);

    connect(gitProcess, &QProcess::finished, this, &GitHistoryWidget::onProcessFinished);
}

void GitHistoryWidget::setRootPath(const QString& path) {
    rootPath = path;
    refreshHistory();
}

void GitHistoryWidget::refreshHistory() {
    if (rootPath.isEmpty() || gitProcess->state() != QProcess::NotRunning) return;

    gitProcess->setWorkingDirectory(rootPath);
    gitProcess->start("git", QStringList() << "log" << "--pretty=format:%h|%p|%an|%s|%d" << "-n" << "50");
}

void GitHistoryWidget::onProcessFinished(int exitCode) {
    if (exitCode != 0) {
        tableWidget->setRowCount(0);
        return;
    }

    QString out = gitProcess->readAllStandardOutput();
    commitNodes.clear();

    QStringList lines = out.split('\n', Qt::SkipEmptyParts);
    for (const QString& line : lines) {
        QStringList parts = line.split('|');
        if (parts.size() < 4) continue;
        CommitNode node;
        node.hash = parts[0].trimmed();
        node.parents = parts[1].split(' ', Qt::SkipEmptyParts);
        node.author = parts[2].trimmed();
        node.message = parts[3].trimmed();
        if (parts.size() > 4) {
            node.refDecorations = parts[4].trimmed();
        }
        node.column = 0;
        commitNodes.append(node);
    }

    // Assign tracks columns
    QList<QString> activeTracks;
    for (int i = 0; i < commitNodes.size(); ++i) {
        QString h = commitNodes[i].hash;
        int col = activeTracks.indexOf(h);
        if (col == -1) {
            col = activeTracks.size();
            activeTracks.append(h);
        }
        commitNodes[i].column = col;

        activeTracks.removeAt(col);
        for (const QString& p : commitNodes[i].parents) {
            if (activeTracks.indexOf(p) == -1) {
                activeTracks.insert(col, p);
            }
        }
    }

    tableWidget->setRowCount(commitNodes.size());
    tableWidget->setItemDelegate(new GitHistoryDelegate(commitNodes, this));

    for (int i = 0; i < commitNodes.size(); ++i) {
        const auto& node = commitNodes[i];
        
        auto* graphItem = new QTableWidgetItem();
        tableWidget->setItem(i, 0, graphItem);

        QString msg = node.message;
        if (!node.refDecorations.isEmpty()) {
            msg = node.refDecorations + " " + msg;
        }
        auto* msgItem = new QTableWidgetItem(msg);
        tableWidget->setItem(i, 1, msgItem);

        auto* authorItem = new QTableWidgetItem(node.author);
        tableWidget->setItem(i, 2, authorItem);

        auto* hashItem = new QTableWidgetItem(node.hash);
        tableWidget->setItem(i, 3, hashItem);
    }
}
