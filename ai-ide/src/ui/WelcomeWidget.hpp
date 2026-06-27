#pragma once
#include <QWidget>

class WelcomeWidget : public QWidget {
    Q_OBJECT
public:
    explicit WelcomeWidget(QWidget* parent = nullptr);

signals:
    void newFileRequested();
    void openFileRequested();
    void openFolderRequested();
    void buildRequested();
    void settingsRequested();
};
