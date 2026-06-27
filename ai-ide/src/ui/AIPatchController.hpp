#pragma once
#include <QObject>
#include <QString>
#include <memory>
#include "SettingsManager.hpp"
#include "CustomEditor.hpp"

class AIProvider;

class AIPatchController : public QObject {
    Q_OBJECT
public:
    explicit AIPatchController(CustomEditor* editor, QObject* parent = nullptr);
    void setEditor(CustomEditor* ed);

public slots:
    void requestRefactor(const QString& instruction);

private:
    CustomEditor* editor;
    std::unique_ptr<AIProvider> provider;
};
