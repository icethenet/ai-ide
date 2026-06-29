#pragma once
#include <QWidget>
#include <QTreeWidget>
#include <QLineEdit>
#include <QLabel>
#include <QJsonArray>
#include <QJsonObject>

class OutlineWidget : public QWidget {
    Q_OBJECT
public:
    explicit OutlineWidget(QWidget* parent = nullptr);

signals:
    void lineNavigationRequested(int line);

public slots:
    void updateSymbols(const QJsonArray& symbols);
    void clearOutline();

private slots:
    void onFilterChanged(const QString& text);
    void onItemClicked(QTreeWidgetItem* item, int column);

private:
    void populateOutlineNode(QTreeWidgetItem* parentItem, const QJsonObject& symbol);
    QString getSymbolPrefix(int kind) const;
    QColor getSymbolColor(int kind) const;

    QLineEdit* filterEdit;
    QTreeWidget* treeWidget;
    QLabel* placeholderLabel;
};
