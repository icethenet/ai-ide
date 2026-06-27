#pragma once
#include <QWidget>
#include <QListWidget>
#include <vector>
#include <functional>

class CommandPalette : public QWidget {
    Q_OBJECT
public:
    explicit CommandPalette(QWidget* parent = nullptr);

    void addCommand(const QString& name, const QString& shortcut, const std::function<void()>& action);
    void filterCommands(const QString& text);
    void selectNext();
    void selectPrev();
    void executeCurrent();

private:
    struct PaletteCommand {
        QString name;
        QString shortcut;
        std::function<void()> action;
    };
    std::vector<PaletteCommand> commands;
    QListWidget* listWidget;
};
