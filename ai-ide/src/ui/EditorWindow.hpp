#pragma once

#include <QMainWindow>
#include <QTabWidget>
#include <QStringListModel>

class CustomEditor;
class FileBrowser;
class SearchWidget;
class GitWidget;
class WelcomeWidget;
class AIPatchController;
class CommandPalette;
class ClipboardListener;
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

private:
    void createMenus();
    void createDocks();
    void createCentralEditor();
    void showEvent(QShowEvent* event) override;
    void openFileInTab(const QString& path);
    CustomEditor* currentEditor() const;
    void runBuild();
    void readBuildOutput();
    void buildFinished(int exitCode, int exitStatus);
    void parseBuildLine(const QString& line);
    void gotoLine(const QString& file, int line);
    void openWelcomeTab();
    void showCommandPalette();
    bool eventFilter(QObject* obj, QEvent* event) override;
    void updateDocumentDiagnostics();
    void showSymbolReferences(const QJsonArray& locations);

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

    QComboBox* cmakeTargetCombo;
    QComboBox* cmakeBuildTypeCombo;
    QTableWidget* referencesTable;

    struct EditorDiagnostic {
        QString file;
        int line;
        QString message;
        bool isError;
    };
    std::vector<EditorDiagnostic> activeDiagnostics;
};
