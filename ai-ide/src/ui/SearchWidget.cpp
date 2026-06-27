#include "SearchWidget.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QPushButton>
#include <QDirIterator>
#include <QFile>
#include <QTextStream>
#include <QFileInfo>

SearchThread::SearchThread(const QString& rootPath, const QString& query, QObject* parent)
    : QThread(parent), root(rootPath), q(query) {}

void SearchThread::run() {
    if (root.isEmpty() || q.isEmpty()) return;
    
    QDirIterator it(root, QDir::Files, QDirIterator::Subdirectories);
    while (it.hasNext()) {
        if (isInterruptionRequested()) break;
        QString path = it.next();
        
        if (path.contains("/.git/") || path.contains("/build/") || path.contains("/.agents/") || path.contains("/.antigravity/")) {
            continue;
        }
        
        QFileInfo info(path);
        QString ext = info.suffix().toLower();
        if (ext != "cpp" && ext != "hpp" && ext != "h" && ext != "txt" && ext != "md" && ext != "py" && ext != "json" && ext != "cmake") {
            continue;
        }

        QFile file(path);
        if (file.open(QIODevice::ReadOnly | QIODevice::Text)) {
            QTextStream in(&file);
            int lineNum = 0;
            while (!in.atEnd()) {
                if (isInterruptionRequested()) break;
                lineNum++;
                QString line = in.readLine();
                if (line.contains(q, Qt::CaseInsensitive)) {
                    emit matchFound(path, lineNum, line.trimmed());
                }
            }
        }
    }
}

SearchWidget::SearchWidget(QWidget* parent)
    : QWidget(parent), activeThread(nullptr)
{
    auto* layout = new QVBoxLayout(this);
    layout->setContentsMargins(5, 5, 5, 5);

    auto* searchBar = new QHBoxLayout();
    searchEdit = new QLineEdit(this);
    searchEdit->setPlaceholderText("Search in workspace...");
    searchEdit->setStyleSheet("QLineEdit { background-color: #1e1e1e; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 4px; font-family: 'Segoe UI', Arial; }");
    
    auto* searchBtn = new QPushButton("Find", this);
    searchBtn->setStyleSheet("QPushButton { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 4px 8px; font-family: 'Segoe UI', Arial; }"
                             "QPushButton:hover { background-color: #3e4452; color: #ffffff; }");
    
    searchBar->addWidget(searchEdit);
    searchBar->addWidget(searchBtn);
    layout->addLayout(searchBar);

    resultsTree = new QTreeWidget(this);
    resultsTree->setHeaderLabel("Search Results");
    resultsTree->setStyleSheet("QTreeWidget { background-color: #1e1e1e; color: #abb2bf; border: none; font-family: 'Segoe UI', Arial; }"
                               "QTreeWidget::item:hover { background-color: #2c313c; }"
                               "QTreeWidget::item:selected { background-color: #3e4452; color: #ffffff; }");
    layout->addWidget(resultsTree);

    connect(searchEdit, &QLineEdit::returnPressed, this, &SearchWidget::startSearch);
    connect(searchBtn, &QPushButton::clicked, this, &SearchWidget::startSearch);
    connect(resultsTree, &QTreeWidget::itemDoubleClicked, this, &SearchWidget::onDoubleClicked);
}

void SearchWidget::setRootPath(const QString& path) {
    rootPath = path;
}

void SearchWidget::startSearch() {
    if (activeThread) {
        activeThread->requestInterruption();
        activeThread->wait();
        delete activeThread;
        activeThread = nullptr;
    }

    resultsTree->clear();
    QString query = searchEdit->text().trimmed();
    if (query.isEmpty() || rootPath.isEmpty()) return;

    activeThread = new SearchThread(rootPath, query, this);
    connect(activeThread, &SearchThread::matchFound, this, &SearchWidget::addMatch);
    activeThread->start();
}

void SearchWidget::addMatch(const QString& filePath, int lineNumber, const QString& lineContent) {
    QList<QTreeWidgetItem*> items = resultsTree->findItems(filePath, Qt::MatchExactly, 0);
    QTreeWidgetItem* parentItem = nullptr;
    
    if (items.isEmpty()) {
        parentItem = new QTreeWidgetItem(resultsTree);
        parentItem->setText(0, filePath);
        parentItem->setToolTip(0, filePath);
    } else {
        parentItem = items.first();
    }

    auto* childItem = new QTreeWidgetItem(parentItem);
    childItem->setText(0, QString::number(lineNumber) + ": " + lineContent);
    childItem->setData(0, Qt::UserRole, filePath);
    childItem->setData(0, Qt::UserRole + 1, lineNumber);
    
    parentItem->setExpanded(true);
}

void SearchWidget::onDoubleClicked(QTreeWidgetItem* item, int /* column */) {
    QVariant fileVal = item->data(0, Qt::UserRole);
    QVariant lineVal = item->data(0, Qt::UserRole + 1);
    if (fileVal.isValid() && lineVal.isValid()) {
        emit matchActivated(fileVal.toString(), lineVal.toInt());
    }
}
