#pragma once
#include <QObject>
#include <QClipboard>
#include <QMimeData>

class ClipboardListener : public QObject {
    Q_OBJECT
public:
    explicit ClipboardListener(QObject* parent = nullptr);

signals:
    void codeCopied(const QString& text);

private slots:
    void onClipboardChanged();
};
