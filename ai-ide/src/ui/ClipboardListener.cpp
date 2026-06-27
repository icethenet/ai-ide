#include "ClipboardListener.hpp"
#include <QApplication>

ClipboardListener::ClipboardListener(QObject* parent) : QObject(parent) {
    connect(QApplication::clipboard(), &QClipboard::dataChanged, this, &ClipboardListener::onClipboardChanged);
}

void ClipboardListener::onClipboardChanged() {
    const QMimeData* mimeData = QApplication::clipboard()->mimeData();
    if (mimeData->hasText()) {
        QString text = mimeData->text();
        if (text.length() > 5) { // Basic heuristic to ignore tiny snippets
            emit codeCopied(text);
        }
    }
}
