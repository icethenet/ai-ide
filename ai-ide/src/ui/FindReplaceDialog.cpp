#include "FindReplaceDialog.hpp"
#include "EditorWindow.hpp"
#include "CustomEditor.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QFormLayout>
#include <QFileDialog>
#include <QMessageBox>
#include <QTextDocument>
#include <QTextCursor>
#include <QDirIterator>
#include <QFile>
#include <QTextStream>
#include <QFileInfo>
#include <QRegularExpression>
#include <QDir>
#if QT_VERSION < QT_VERSION_CHECK(6, 0, 0)
#include <QRegExp>
#endif

FindReplaceDialog::FindReplaceDialog(EditorWindow* parent)
    : QDialog(parent), mainWin(parent)
{
    setWindowFlags(Qt::Tool | Qt::WindowTitleHint | Qt::WindowCloseButtonHint);
    setWindowTitle("Find & Replace");
    resize(480, 280);

    setupUI();
    onScopeChanged();
}

void FindReplaceDialog::setupUI() {
    // Dark modern styling matching EditorWindow
    setStyleSheet(
        "QDialog { background-color: #21252b; color: #abb2bf; font-family: 'Segoe UI', Arial; }"
        "QLabel { color: #abb2bf; font-size: 12px; }"
        "QLineEdit { background-color: #1e1e1e; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 6px; font-size: 12px; }"
        "QLineEdit:focus { border: 1px solid #61afef; }"
        "QCheckBox { color: #abb2bf; font-size: 12px; }"
        "QCheckBox::indicator { width: 14px; height: 14px; }"
        "QRadioButton { color: #abb2bf; font-size: 12px; }"
        "QPushButton { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 6px 12px; font-size: 12px; min-width: 80px; }"
        "QPushButton:hover { background-color: #3e4452; color: #ffffff; border-color: #61afef; }"
        "QPushButton:pressed { background-color: #4b5263; }"
    );

    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->setContentsMargins(15, 15, 15, 15);
    mainLayout->setSpacing(12);

    auto* formLayout = new QFormLayout();
    formLayout->setSpacing(8);

    findEdit = new QLineEdit(this);
    findEdit->setPlaceholderText("Text to search...");
    formLayout->addRow("Find:", findEdit);

    replaceEdit = new QLineEdit(this);
    replaceEdit->setPlaceholderText("Replacement text...");
    formLayout->addRow("Replace with:", replaceEdit);

    // Options layout (Case sensitive, Whole word, Regex)
    auto* optionsLayout = new QHBoxLayout();
    caseCheck = new QCheckBox("Match Case", this);
    wordCheck = new QCheckBox("Whole Word", this);
    regexCheck = new QCheckBox("Regex", this);
    optionsLayout->addWidget(caseCheck);
    optionsLayout->addWidget(wordCheck);
    optionsLayout->addWidget(regexCheck);
    optionsLayout->addStretch();
    formLayout->addRow("", optionsLayout);

    // Scope layout
    auto* scopeLayout = new QHBoxLayout();
    currentFileRadio = new QRadioButton("Current File", this);
    currentFileRadio->setChecked(true);
    folderRadio = new QRadioButton("Folder/Workspace", this);
    scopeLayout->addWidget(currentFileRadio);
    scopeLayout->addWidget(folderRadio);
    scopeLayout->addStretch();
    formLayout->addRow("Scope:", scopeLayout);

    // Folder and Filter layout
    auto* folderLayout = new QHBoxLayout();
    folderEdit = new QLineEdit(this);
    folderEdit->setText(QDir::currentPath());
    folderEdit->setPlaceholderText("Directory path...");
    browseBtn = new QPushButton("Browse...", this);
    browseBtn->setMaximumWidth(80);
    folderLayout->addWidget(folderEdit);
    folderLayout->addWidget(browseBtn);
    formLayout->addRow("Directory:", folderLayout);

    filterEdit = new QLineEdit(this);
    filterEdit->setPlaceholderText("e.g. *.cpp, *.hpp, *.txt");
    formLayout->addRow("File Filters:", filterEdit);

    mainLayout->addLayout(formLayout);

    // Buttons layout
    auto* btnLayout = new QHBoxLayout();
    findPrevBtn = new QPushButton("Find Prev", this);
    findNextBtn = new QPushButton("Find Next", this);
    replaceBtn = new QPushButton("Replace", this);
    replaceAllBtn = new QPushButton("Replace All", this);

    btnLayout->addWidget(findPrevBtn);
    btnLayout->addWidget(findNextBtn);
    btnLayout->addWidget(replaceBtn);
    btnLayout->addWidget(replaceAllBtn);
    mainLayout->addLayout(btnLayout);

    statusLabel = new QLabel(this);
    statusLabel->setStyleSheet("color: #98c379; font-style: italic;");
    mainLayout->addWidget(statusLabel);

    // Connect signals/slots
    connect(browseBtn, &QPushButton::clicked, this, &FindReplaceDialog::onBrowseFolder);
    connect(currentFileRadio, &QRadioButton::toggled, this, &FindReplaceDialog::onScopeChanged);
    connect(folderRadio, &QRadioButton::toggled, this, &FindReplaceDialog::onScopeChanged);
    
    connect(findNextBtn, &QPushButton::clicked, this, &FindReplaceDialog::onFindNext);
    connect(findPrevBtn, &QPushButton::clicked, this, &FindReplaceDialog::onFindPrev);
    connect(replaceBtn, &QPushButton::clicked, this, &FindReplaceDialog::onReplace);
    connect(replaceAllBtn, &QPushButton::clicked, this, &FindReplaceDialog::onReplaceAll);

    // Focus on find edit initially
    findEdit->setFocus();
}

void FindReplaceDialog::showFind() {
    replaceEdit->setVisible(false);
    replaceBtn->setVisible(false);
    replaceAllBtn->setText("Find All");
    findEdit->setFocus();
    findEdit->selectAll();
    show();
    raise();
    activateWindow();
}

void FindReplaceDialog::showReplace() {
    replaceEdit->setVisible(true);
    replaceBtn->setVisible(true);
    replaceAllBtn->setText("Replace All");
    findEdit->setFocus();
    findEdit->selectAll();
    show();
    raise();
    activateWindow();
}

void FindReplaceDialog::showFolderSearch(const QString& defaultFolder) {
    folderRadio->setChecked(true);
    if (!defaultFolder.isEmpty()) {
        folderEdit->setText(defaultFolder);
    }
    onScopeChanged();
    findEdit->setFocus();
    findEdit->selectAll();
    show();
    raise();
    activateWindow();
}

void FindReplaceDialog::onBrowseFolder() {
    QString dir = QFileDialog::getExistingDirectory(this, "Select Directory to Search", folderEdit->text());
    if (!dir.isEmpty()) {
        folderEdit->setText(dir);
    }
}

void FindReplaceDialog::onScopeChanged() {
    bool isFolder = folderRadio->isChecked();
    folderEdit->setEnabled(isFolder);
    browseBtn->setEnabled(isFolder);
    filterEdit->setEnabled(isFolder);

    findPrevBtn->setEnabled(!isFolder);
    replaceBtn->setEnabled(!isFolder);
}

bool FindReplaceDialog::doFind(bool forward) {
    if (!mainWin) return false;
    CustomEditor* activeEd = mainWin->currentEditor();
    if (!activeEd) {
        statusLabel->setText("No active file editor.");
        return false;
    }

    CodeEditor* codeEd = activeEd->getCodeEditor();
    if (!codeEd) return false;

    QString query = findEdit->text();
    if (query.isEmpty()) return false;

    QTextDocument::FindFlags flags;
    if (!forward) flags |= QTextDocument::FindBackward;
    if (caseCheck->isChecked()) flags |= QTextDocument::FindCaseSensitively;
    if (wordCheck->isChecked()) flags |= QTextDocument::FindWholeWords;

    bool found = false;
    if (regexCheck->isChecked()) {
#if QT_VERSION >= QT_VERSION_CHECK(6, 0, 0)
        QRegularExpression::PatternOptions options = QRegularExpression::NoPatternOption;
        if (!caseCheck->isChecked()) {
            options |= QRegularExpression::CaseInsensitiveOption;
        }
        QRegularExpression regex(query, options);
        if (regex.isValid()) {
            QTextCursor foundCursor = codeEd->document()->find(regex, codeEd->textCursor(), flags);
            if (!foundCursor.isNull()) {
                codeEd->setTextCursor(foundCursor);
                found = true;
            }
        } else {
            statusLabel->setText("Invalid regular expression.");
            return false;
        }
#else
        QRegExp regex(query, caseCheck->isChecked() ? Qt::CaseSensitive : Qt::CaseInsensitive);
        QTextCursor foundCursor = codeEd->document()->find(regex, codeEd->textCursor(), flags);
        if (!foundCursor.isNull()) {
            codeEd->setTextCursor(foundCursor);
            found = true;
        }
#endif
    } else {
        found = codeEd->find(query, flags);
    }

    if (found) {
        statusLabel->setText("Match found.");
    } else {
        // Wrap around search
        QTextCursor startCursor = codeEd->textCursor();
        if (forward) {
            startCursor.movePosition(QTextCursor::Start);
        } else {
            startCursor.movePosition(QTextCursor::End);
        }
        
        bool wrapFound = false;
        if (regexCheck->isChecked()) {
#if QT_VERSION >= QT_VERSION_CHECK(6, 0, 0)
            QRegularExpression regex(query, caseCheck->isChecked() ? QRegularExpression::NoPatternOption : QRegularExpression::CaseInsensitiveOption);
            QTextCursor foundCursor = codeEd->document()->find(regex, startCursor, flags);
            if (!foundCursor.isNull()) {
                codeEd->setTextCursor(foundCursor);
                wrapFound = true;
            }
#else
            QRegExp regex(query, caseCheck->isChecked() ? Qt::CaseSensitive : Qt::CaseInsensitive);
            QTextCursor foundCursor = codeEd->document()->find(regex, startCursor, flags);
            if (!foundCursor.isNull()) {
                codeEd->setTextCursor(foundCursor);
                wrapFound = true;
            }
#endif
        } else {
            QTextCursor wrapCursor = codeEd->document()->find(query, startCursor, flags);
            if (!wrapCursor.isNull()) {
                codeEd->setTextCursor(wrapCursor);
                wrapFound = true;
            }
        }

        if (wrapFound) {
            statusLabel->setText("Search wrapped around.");
            found = true;
        } else {
            statusLabel->setText("No match found.");
        }
    }
    return found;
}

void FindReplaceDialog::onFindNext() {
    if (folderRadio->isChecked()) {
        statusLabel->setText("Use 'Replace All' for folder scope.");
        return;
    }
    doFind(true);
}

void FindReplaceDialog::onFindPrev() {
    doFind(false);
}

void FindReplaceDialog::onReplace() {
    if (folderRadio->isChecked()) return;

    if (!mainWin) return;
    CustomEditor* activeEd = mainWin->currentEditor();
    if (!activeEd) return;

    CodeEditor* codeEd = activeEd->getCodeEditor();
    if (!codeEd) return;

    QTextCursor cursor = codeEd->textCursor();
    if (cursor.hasSelection()) {
        cursor.insertText(replaceEdit->text());
        codeEd->setTextCursor(cursor);
        statusLabel->setText("Replaced match.");
    }
    doFind(true);
}

void FindReplaceDialog::onReplaceAll() {
    QString query = findEdit->text();
    if (query.isEmpty()) return;

    if (currentFileRadio->isChecked()) {
        if (!mainWin) return;
        CustomEditor* activeEd = mainWin->currentEditor();
        if (!activeEd) return;

        CodeEditor* codeEd = activeEd->getCodeEditor();
        if (!codeEd) return;

        int count = 0;
        QTextCursor startCursor = codeEd->textCursor();
        startCursor.movePosition(QTextCursor::Start);
        codeEd->setTextCursor(startCursor);

        codeEd->setUpdatesEnabled(false);

        QTextDocument::FindFlags flags;
        if (caseCheck->isChecked()) flags |= QTextDocument::FindCaseSensitively;
        if (wordCheck->isChecked()) flags |= QTextDocument::FindWholeWords;

        while (true) {
            QTextCursor foundCursor;
            if (regexCheck->isChecked()) {
#if QT_VERSION >= QT_VERSION_CHECK(6, 0, 0)
                QRegularExpression regex(query, caseCheck->isChecked() ? QRegularExpression::NoPatternOption : QRegularExpression::CaseInsensitiveOption);
                foundCursor = codeEd->document()->find(regex, codeEd->textCursor(), flags);
#else
                QRegExp regex(query, caseCheck->isChecked() ? Qt::CaseSensitive : Qt::CaseInsensitive);
                foundCursor = codeEd->document()->find(regex, codeEd->textCursor(), flags);
#endif
            } else {
                foundCursor = codeEd->document()->find(query, codeEd->textCursor(), flags);
            }

            if (!foundCursor.isNull()) {
                foundCursor.insertText(replaceEdit->text());
                codeEd->setTextCursor(foundCursor);
                count++;
            } else {
                break;
            }
        }

        codeEd->setUpdatesEnabled(true);
        statusLabel->setText(QString("Replaced %1 occurrences in file.").arg(count));
    } else {
        performFolderReplace();
    }
}

void FindReplaceDialog::performFolderReplace() {
    QString query = findEdit->text();
    QString replacement = replaceEdit->text();
    QString root = folderEdit->text();
    if (query.isEmpty() || root.isEmpty()) {
        statusLabel->setText("Find query and directory path cannot be empty.");
        return;
    }

    QString filterStr = filterEdit->text().trimmed();
    QStringList filters;
    if (!filterStr.isEmpty()) {
        filters = filterStr.split(QRegularExpression("[,;\\s]+"), Qt::SkipEmptyParts);
    } else {
        filters << "*.cpp" << "*.hpp" << "*.h" << "*.txt" << "*.md" << "*.py" << "*.json" << "*.cmake";
    }

    QMessageBox::StandardButton reply = QMessageBox::question(
        this, "Confirm Replace All",
        QString("Are you sure you want to replace all occurrences of '%1' with '%2' in folder '%3'?")
            .arg(query).arg(replacement).arg(root),
        QMessageBox::Yes | QMessageBox::No
    );

    if (reply != QMessageBox::Yes) {
        statusLabel->setText("Folder replacement cancelled.");
        return;
    }

    int filesChanged = 0;
    int occurrencesReplaced = 0;

    QDirIterator it(root, QDir::Files, QDirIterator::Subdirectories);
    while (it.hasNext()) {
        QString path = it.next();
        QString cleanPath = QDir::cleanPath(path);
        if (cleanPath.contains("/.git/") || cleanPath.contains("/build/") || cleanPath.contains("/.agents/") || cleanPath.contains("/.antigravity/")) {
            continue;
        }

        QFileInfo info(path);
        bool matchesFilter = false;
        for (const QString& filter : filters) {
            QRegularExpression filterRegex(QRegularExpression::wildcardToRegularExpression(filter));
            if (filterRegex.match(info.fileName()).hasMatch()) {
                matchesFilter = true;
                break;
            }
        }
        if (!matchesFilter) continue;

        QFile file(path);
        if (file.open(QIODevice::ReadOnly | QIODevice::Text)) {
            QTextStream in(&file);
            QString content = in.readAll();
            file.close();

            bool contentChanged = false;
            int countInFile = 0;

            if (regexCheck->isChecked()) {
#if QT_VERSION >= QT_VERSION_CHECK(6, 0, 0)
                QRegularExpression::PatternOptions options = QRegularExpression::NoPatternOption;
                if (!caseCheck->isChecked()) {
                    options |= QRegularExpression::CaseInsensitiveOption;
                }
                QRegularExpression regex(query, options);
                
                auto matchIterator = regex.globalMatch(content);
                while (matchIterator.hasNext()) {
                    matchIterator.next();
                    countInFile++;
                }

                if (countInFile > 0) {
                    content.replace(regex, replacement);
                    contentChanged = true;
                }
#else
                QRegExp regex(query, caseCheck->isChecked() ? Qt::CaseSensitive : Qt::CaseInsensitive);
                int pos = 0;
                while ((pos = regex.indexIn(content, pos)) != -1) {
                    countInFile++;
                    pos += regex.matchedLength();
                }
                if (countInFile > 0) {
                    content.replace(regex, replacement);
                    contentChanged = true;
                }
#endif
            } else {
                Qt::CaseSensitivity cs = caseCheck->isChecked() ? Qt::CaseSensitive : Qt::CaseInsensitive;
                
                int pos = 0;
                while ((pos = content.indexOf(query, pos, cs)) != -1) {
                    countInFile++;
                    pos += query.length();
                }

                if (countInFile > 0) {
                    content.replace(query, replacement, cs);
                    contentChanged = true;
                }
            }

            if (contentChanged) {
                if (file.open(QIODevice::WriteOnly | QIODevice::Truncate | QIODevice::Text)) {
                    QTextStream out(&file);
                    out << content;
                    file.close();
                    filesChanged++;
                    occurrencesReplaced += countInFile;
                }
            }
        }
    }

    statusLabel->setText(QString("Replaced %1 occurrences in %2 files.").arg(occurrencesReplaced).arg(filesChanged));
    QMessageBox::information(this, "Replace All Complete", 
                             QString("Successfully replaced %1 occurrences in %2 files.").arg(occurrencesReplaced).arg(filesChanged));
}
