#include "SearchWidget.hpp"
#include <QVBoxLayout>
#include <QHBoxLayout>
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
        
        QString cleanPath = QDir::cleanPath(path);
        if (cleanPath.contains("/.git/") || cleanPath.contains("/build/") || cleanPath.contains("/.agents/") || cleanPath.contains("/.antigravity/")) {
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
            int lineNumber = 1;
            while (!in.atEnd()) {
                if (isInterruptionRequested()) break;
                QString line = in.readLine();
                if (line.contains(q, Qt::CaseInsensitive)) {
                    emit matchFound(path, lineNumber, line.trimmed());
                }
                lineNumber++;
            }
            file.close();
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
    
    searchBtn = new QPushButton("Find", this);
    searchBtn->setStyleSheet("QPushButton { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 4px; padding: 4px 8px; font-family: 'Segoe UI', Arial; }"
                             "QPushButton:hover { background-color: #3e4452; color: #ffffff; }");
    
    searchBar->addWidget(searchEdit);
    searchBar->addWidget(searchBtn);
    layout->addLayout(searchBar);

    auto* semanticBar = new QHBoxLayout();
    semanticSearchCheckbox = new QCheckBox("Semantic (AI RAG)", this);
    semanticSearchCheckbox->setStyleSheet("QCheckBox { color: #abb2bf; font-size: 11px; }");
    
    indexBtn = new QPushButton("Rebuild Index", this);
    indexBtn->setStyleSheet("QPushButton { background-color: #2c313c; color: #abb2bf; border: 1px solid #3e4452; border-radius: 3px; padding: 2px 6px; font-size: 11px; }"
                            "QPushButton:hover { background-color: #3e4452; color: #ffffff; }");
    
    semanticBar->addWidget(semanticSearchCheckbox);
    semanticBar->addWidget(indexBtn);
    layout->addLayout(semanticBar);

    progressLabel = new QLabel(this);
    progressLabel->setStyleSheet("QLabel { color: #5c6370; font-size: 11px; padding: 2px; }");
    layout->addWidget(progressLabel);

    resultsTree = new QTreeWidget(this);
    resultsTree->setHeaderLabel("Search Results");
    resultsTree->setStyleSheet("QTreeWidget { background-color: #1e1e1e; color: #abb2bf; border: none; font-family: 'Segoe UI', Arial; }"
                               "QTreeWidget::item:hover { background-color: #2c313c; }"
                               "QTreeWidget::item:selected { background-color: #3e4452; color: #ffffff; }");
    layout->addWidget(resultsTree);

    connect(searchEdit, &QLineEdit::returnPressed, this, &SearchWidget::startSearch);
    connect(searchBtn, &QPushButton::clicked, this, &SearchWidget::startSearch);
    connect(indexBtn, &QPushButton::clicked, this, &SearchWidget::startIndexing);
    connect(resultsTree, &QTreeWidget::itemDoubleClicked, this, &SearchWidget::onDoubleClicked);

    connect(&VectorIndexManager::instance(), &VectorIndexManager::indexingProgress, this, &SearchWidget::updateProgress);
    connect(&VectorIndexManager::instance(), &VectorIndexManager::indexingFinished, this, &SearchWidget::indexingFinished);
    updateIndexStats();
}

void SearchWidget::setRootPath(const QString& path) {
    rootPath = path;
    updateIndexStats();
}

void SearchWidget::startIndexing() {
    if (rootPath.isEmpty()) return;
    indexBtn->setEnabled(false);
    progressLabel->setText("Building semantic index...");
    VectorIndexManager::instance().startIndexing(rootPath);
}

void SearchWidget::updateProgress(int current, int total) {
    QString lastErr = VectorIndexManager::instance().getLastError();
    if (!lastErr.isEmpty()) {
        progressLabel->setText(QString("Indexing codebase: %1 of %2 files... (Error: %3)")
                               .arg(current).arg(total).arg(lastErr.left(120)));
    } else {
        progressLabel->setText(QString("Indexing codebase: %1 of %2 files...").arg(current).arg(total));
    }
}

void SearchWidget::indexingFinished() {
    indexBtn->setEnabled(true);
    QString lastErr = VectorIndexManager::instance().getLastError();
    if (!lastErr.isEmpty()) {
        progressLabel->setText(QString("Indexing finished with errors. Last Error: %1").arg(lastErr.left(120)));
    } else {
        updateIndexStats();
    }
}

void SearchWidget::updateIndexStats() {
    auto stats = VectorIndexManager::instance().getIndexStats();
    progressLabel->setText(QString("Local Index: %1 chunks across %2 files indexed.")
                           .arg(stats.chunks)
                           .arg(stats.files));
}

void SearchWidget::startSearch() {
    if (semanticSearchCheckbox->isChecked()) {
        runSemanticSearch();
        return;
    }

    if (activeThread) {
        activeThread->requestInterruption();
        activeThread->wait();
        delete activeThread;
        activeThread = nullptr;
    }

    resultsTree->clear();
    progressLabel->clear();
    QString query = searchEdit->text().trimmed();
    if (query.isEmpty() || rootPath.isEmpty()) return;

    activeThread = new SearchThread(rootPath, query, this);
    connect(activeThread, &SearchThread::matchFound, this, &SearchWidget::addMatch);
    activeThread->start();
}

void SearchWidget::runSemanticSearch() {
    if (activeSemanticThread) {
        activeSemanticThread->requestInterruption();
        activeSemanticThread->wait();
        delete activeSemanticThread;
        activeSemanticThread = nullptr;
    }

    resultsTree->clear();
    QString query = searchEdit->text().trimmed();
    if (query.isEmpty() || rootPath.isEmpty()) return;

    progressLabel->setText("Querying vector model...");
    searchBtn->setEnabled(false);
    searchEdit->setEnabled(false);

    activeSemanticThread = new SemanticSearchThread(query, this);
    connect(activeSemanticThread, &SemanticSearchThread::searchCompleted, this, &SearchWidget::renderSemanticResults);
    connect(activeSemanticThread, &QThread::finished, this, [this]() {
        searchBtn->setEnabled(true);
        searchEdit->setEnabled(true);
    });
    activeSemanticThread->start();
}

void SearchWidget::renderSemanticResults(const QVector<SearchResult>& results) {
    progressLabel->setText(QString("Found %1 semantic matches.").arg(results.size()));
    for (const auto& r : results) {
        QList<QTreeWidgetItem*> items = resultsTree->findItems(r.filePath, Qt::MatchExactly, 0);
        QTreeWidgetItem* parentItem = nullptr;
        
        if (items.isEmpty()) {
            parentItem = new QTreeWidgetItem(resultsTree);
            parentItem->setText(0, r.filePath);
            parentItem->setToolTip(0, r.filePath);
        } else {
            parentItem = items.first();
        }

        auto* childItem = new QTreeWidgetItem(parentItem);
        childItem->setText(0, QString("[%1% Match] Line %2: %3").arg(qRound(r.score * 100)).arg(r.lineNumber).arg(r.lineContent));
        childItem->setData(0, Qt::UserRole, r.filePath);
        childItem->setData(0, Qt::UserRole + 1, r.lineNumber);
        
        parentItem->setExpanded(true);
    }
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
