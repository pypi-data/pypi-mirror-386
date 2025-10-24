class TreeSearchManager {
    constructor(treeContainer, options = {}) {
        this.treeContainer = treeContainer;
        this.options = {
            placeholder: options.placeholder || 'Поиск...',
            ...options
        };

        this.init();
    }

    init() {
        this.createSearchInput();
        this.bindEvents();
    }

    createSearchInput() {
        const searchContainer = document.createElement('div');
        searchContainer.className = 'tree-search-container mb-3';
        searchContainer.innerHTML = `
            <input type="text" 
                   class="form-control tree-search-input" 
                   placeholder="${this.options.placeholder}">
        `;

        this.treeContainer.parentNode.insertBefore(searchContainer, this.treeContainer);
        this.searchInput = searchContainer.querySelector('.tree-search-input');
    }

    bindEvents() {
        this.searchInput.addEventListener('input', (e) => {
            this.performSearch(e.target.value.trim());
        });
    }

    performSearch(searchTerm) {
        const allNodes = this.treeContainer.querySelectorAll('.tree-node');

        if (!searchTerm) {
            // Показываем все узлы
            allNodes.forEach(node => {
                node.style.display = '';
            });
            return;
        }

        const searchLower = searchTerm.toLowerCase();
        const matchingNodes = new Set();

        // Находим все узлы, которые соответствуют поиску
        allNodes.forEach(node => {
            const nodeNameElement = node.querySelector('.node-name');
            if (nodeNameElement) {
                const nodeName = nodeNameElement.textContent.toLowerCase();
                if (nodeName.includes(searchLower)) {
                    matchingNodes.add(node);
                    // Добавляем всех родителей
                    this.addParentNodes(node, matchingNodes);
                    // Добавляем всех детей
                    this.addChildNodes(node, matchingNodes);
                }
            }
        });

        // Скрываем все узлы, затем показываем только найденные
        allNodes.forEach(node => {
            if (matchingNodes.has(node)) {
                node.style.display = '';
                // Разворачиваем родительские узлы для видимости найденных
                this.expandParentNodes(node);
            } else {
                node.style.display = 'none';
            }
        });
    }

    addParentNodes(node, matchingNodes) {
        let current = node;
        while (current) {
            // Поднимаемся вверх по DOM дереву
            const parentContainer = current.parentElement;
            if (!parentContainer) break;

            // Если это контейнер детей (.node-children), то родитель - это следующий .tree-node
            if (parentContainer.classList.contains('node-children')) {
                const parentNode = parentContainer.parentElement;
                if (parentNode && parentNode.classList.contains('tree-node')) {
                    matchingNodes.add(parentNode);
                    current = parentNode;
                } else {
                    break;
                }
            } else {
                break;
            }
        }
    }

    addChildNodes(node, matchingNodes) {
        const childrenContainer = node.querySelector('.node-children');
        if (childrenContainer) {
            const childNodes = childrenContainer.querySelectorAll('.tree-node');
            childNodes.forEach(child => matchingNodes.add(child));
        }
    }

    expandParentNodes(node) {
        let current = node;
        while (current) {
            const parentContainer = current.parentElement;
            if (!parentContainer) break;

            if (parentContainer.classList.contains('node-children')) {
                const parentNode = parentContainer.parentElement;
                if (parentNode && parentNode.classList.contains('tree-node')) {
                    // Разворачиваем родительский узел
                    parentNode.classList.add('expanded');
                    parentContainer.style.display = 'block';

                    // Обновляем кнопку toggle
                    const toggleButton = parentNode.querySelector('.node-toggle');
                    if (toggleButton) {
                        toggleButton.textContent = '▼';
                    }

                    current = parentNode;
                } else {
                    break;
                }
            } else {
                break;
            }
        }
    }
}