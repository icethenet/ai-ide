#pragma once
#include <QListWidget>
#include <QJsonArray>

class CompletionPopup : public QListWidget {
    Q_OBJECT
public:
    explicit CompletionPopup(QWidget* parent = nullptr);
    void setCompletions(const QJsonArray& items);
    void showAt(const QPoint& pos);
};
