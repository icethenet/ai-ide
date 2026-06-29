#pragma once
#include <QWidget>
#include <QTableWidget>
#include <QProcess>
#include <QStringList>
#include <QStyledItemDelegate>

struct CommitNode {
    QString hash;
    QStringList parents;
    QString author;
    QString message;
    QString refDecorations;
    int column;
};

class GitHistoryDelegate : public QStyledItemDelegate {
    Q_OBJECT
public:
    explicit GitHistoryDelegate(const QList<CommitNode>& nodes, QObject* parent = nullptr);
    void paint(QPainter* painter, const QStyleOptionViewItem& option, const QModelIndex& index) const override;

private:
    const QList<CommitNode>& commitNodes;
};

class GitHistoryWidget : public QWidget {
    Q_OBJECT
public:
    explicit GitHistoryWidget(QWidget* parent = nullptr);
    void setRootPath(const QString& path);
    void refreshHistory();

private slots:
    void onProcessFinished(int exitCode);

private:
    QString rootPath;
    QTableWidget* tableWidget;
    QProcess* gitProcess;
    QList<CommitNode> commitNodes;
};
