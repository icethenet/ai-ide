#pragma once
#include <QDialog>
#include <QLineEdit>
#include <QListWidget>
#include <vector>
#include <functional>

class CommandPalette : public QDialog {
    Q_OBJECT
public:
    explicit CommandPalette(QWidget* parent = nullptr);

    void addCommand(const QString& name, const QString& shortcut, const std::function<void()>& action);
    void showPalette();

protected:
    bool eventFilter(QObject* obj, QEvent* event) override;

private slots:
    void filterCommands(const QString& text);
    void executeSelected();

private:
    struct PaletteCommand {
        QString name;
        QString shortcut;
        std::function<void()> action;
    };
    std::vector<PaletteCommand> commands;

    QLineEdit* searchEdit;
    QListWidget* listWidget;
};
