#pragma once

#include <QMainWindow>
#include <QTabWidget>
#include <QStringListModel>
#include "../ai/AIAction.hpp"

class CustomEditor;
class FileBrowser;
class SearchWidget;
class GitWidget;
class WelcomeWidget;
class AIPatchController;
class CommandPalette;
class ClipboardListener;
class FindReplaceDialog;
class OutlineWidget;
class GitConflictResolver;
class RemoteServerWidget;
class QShowEvent;
class QSplitter;
class QListView;
class QPlainTextEdit;
class QProcess;
class TerminalWidget;
class ProblemsWidget;
class DebugWidget;
class QLineEdit;
class QComboBox;
class QLabel;
class QTableWidget;

class EditorWindow : public QMainWindow {
    Q_OBJECT
public:
    explicit EditorWindow(QWidget *parent = nullptr);
    CustomEditor* currentEditor() const;
    void openFileInTab(const QString& path);
    void executeAIAction(const AIAction& action);
    QString getActiveProgrammingDirectory() const;

signals:
    void buildCompleted(int exitCode, const QString& buildErrors);

private:
    void createMenus();
    void createDocks();
    void createCentralEditor();
    void showEvent(QShowEvent* event) override;
    void runBuild();
    void readBuildOutput();
    void buildFinished(int exitCode, int exitStatus);
    void parseBuildLine(const QString& line);
    void gotoLine(const QString& file, int line);
    void openWelcomeTab();
    void openSearchTab();
    void openConflictResolver(const QString& filePath);
    void openSshTerminal(const QString& host, const QString& port, const QString& user);
    void showCommandPalette();
    bool eventFilter(QObject* obj, QEvent* event) override;
    void updateDocumentDiagnostics();
    void showSymbolReferences(const QJsonArray& locations);
    Q_INVOKABLE void fixProblemWithAI(const QString& filePath, int line, const QString& message);

    QTabWidget* tabWidget;
    QTabWidget* bottomTabWidget;
    QSplitter* mainSplitter;
    TerminalWidget* powerShellTab;
    TerminalWidget* bashTab;
    DebugWidget* debugTab;
    ProblemsWidget* problemsTab;
    QPlainTextEdit* outputTab;
    QListView* historyView;

    QProcess* buildProcess;

    CustomEditor* editor;
    FileBrowser* fileBrowser;
    SearchWidget* searchWidget;
    GitWidget* gitWidget;
    AIPatchController* aiPatchController;
    CommandPalette* commandPalette;
    QLineEdit* pathLineEdit;
    QLineEdit* cmdLineEdit;
    ClipboardListener* clipboardListener;
    QStringListModel* historyModel;
    QString buildBuffer;
    FindReplaceDialog* findReplaceDialog;
    OutlineWidget* outlineWidget;
    RemoteServerWidget* serverWidget;
    int lastOutlineRequestId;

    QComboBox* cmakeTargetCombo;
    QComboBox* cmakeBuildTypeCombo;
    QComboBox* targetEnvCombo;
    QString dockerImageName;
    QTableWidget* referencesTable;

    struct EditorDiagnostic {
        QString file;
        int line;
        QString message;
        bool isError;
    };
    std::vector<EditorDiagnostic> activeDiagnostics;
};
