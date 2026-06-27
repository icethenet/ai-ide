#pragma once
#include <QDialog>
#include <QLineEdit>
#include <QCheckBox>
#include <QPushButton>
#include <QRadioButton>
#include <QLabel>
#include <QString>

class EditorWindow;

class FindReplaceDialog : public QDialog {
    Q_OBJECT
public:
    explicit FindReplaceDialog(EditorWindow* parent = nullptr);
    void showFind();
    void showReplace();
    void showFolderSearch(const QString& defaultFolder);

private slots:
    void onFindNext();
    void onFindPrev();
    void onReplace();
    void onReplaceAll();
    void onBrowseFolder();
    void onScopeChanged();

private:
    void setupUI();
    bool doFind(bool forward);
    void performFolderReplace();

    EditorWindow* mainWin;

    QLineEdit* findEdit;
    QLineEdit* replaceEdit;
    QLineEdit* folderEdit;
    QLineEdit* filterEdit;
    QPushButton* browseBtn;

    QCheckBox* caseCheck;
    QCheckBox* wordCheck;
    QCheckBox* regexCheck;

    QRadioButton* currentFileRadio;
    QRadioButton* folderRadio;

    QPushButton* findNextBtn;
    QPushButton* findPrevBtn;
    QPushButton* replaceBtn;
    QPushButton* replaceAllBtn;

    QLabel* statusLabel;
};
