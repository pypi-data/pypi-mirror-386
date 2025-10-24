// utils.js - обновленная версия без символов в отладке

const Utils = {
    // Создание HTML элемента
    createElement: (tag, className = '', innerHTML = '') => {
        const element = document.createElement(tag);
        if (className) element.className = className;
        if (innerHTML) element.innerHTML = innerHTML;
        return element;
    },

    // Показать/скрыть загрузку
    showLoading: (container, message = 'Загрузка...') => {
        container.innerHTML = `
            <div class="d-flex justify-content-center align-items-center" style="min-height: 200px;">
                <div class="text-center">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="sr-only">Загрузка...</span>
                    </div>
                    <div>${message}</div>
                </div>
            </div>
        `;
    },

    // Показать ошибку
    showError: (container, message) => {
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i>
                ${message}
            </div>
        `;
    },

    // Улучшенное построение дерева из плоского массива
    buildTree: (items, parentField = 'parent') => {
        const map = new Map();
        const roots = [];

        // Создаем мапу всех элементов
        items.forEach(item => {
            map.set(item.id, { ...item, children: [] });
        });

        // Строим дерево с учетом разных форматов parent поля
        items.forEach(item => {
            const node = map.get(item.id);
            let parentId = null;

            // Определяем ID родителя в зависимости от формата
            if (item[parentField]) {
                if (typeof item[parentField] === 'object' && item[parentField].id) {
                    // Случай: parent: {id: 123, name: "..."}
                    parentId = item[parentField].id;
                } else if (typeof item[parentField] === 'number' || typeof item[parentField] === 'string') {
                    // Случай: parent: 123 или parent: "123"
                    parentId = item[parentField];
                }
            }

            if (parentId) {
                const parent = map.get(parentId);
                if (parent) {
                    parent.children.push(node);
                } else {
                    // Родитель не найден в текущем наборе данных - добавляем в корень
                    roots.push(node);
                }
            } else {
                // Нет родителя - корневой элемент
                roots.push(node);
            }
        });

        return roots;
    },

    // Построение плоского массива из дерева (для отладки)
    flattenTree: (tree) => {
        const result = [];

        const flatten = (nodes, level = 0) => {
            nodes.forEach(node => {
                result.push({
                    ...node,
                    level: level,
                    hasChildren: node.children && node.children.length > 0
                });

                if (node.children && node.children.length > 0) {
                    flatten(node.children, level + 1);
                }
            });
        };

        flatten(tree);
        return result;
    },

    // Поиск узла в дереве по ID
    findNodeInTree: (tree, nodeId) => {
        for (const node of tree) {
            if (node.id === nodeId) {
                return node;
            }
            if (node.children && node.children.length > 0) {
                const found = Utils.findNodeInTree(node.children, nodeId);
                if (found) return found;
            }
        }
        return null;
    },

    // Получить путь к узлу (хлебные крошки)
    getNodePath: (tree, nodeId) => {
        const path = [];

        const findPath = (nodes, targetId, currentPath) => {
            for (const node of nodes) {
                const newPath = [...currentPath, node];

                if (node.id === targetId) {
                    return newPath;
                }

                if (node.children && node.children.length > 0) {
                    const result = findPath(node.children, targetId, newPath);
                    if (result) return result;
                }
            }
            return null;
        };

        return findPath(tree, nodeId, []);
    },

    // Поиск по массиву объектов
    filterItems: (items, query, fields = ['name', 'title']) => {
        if (!query.trim()) return items;

        const searchQuery = query.toLowerCase();
        return items.filter(item =>
            fields.some(field =>
                item[field] && item[field].toLowerCase().includes(searchQuery)
            )
        );
    },

    // Поиск в дереве с учетом иерархии
    filterTreeNodes: (tree, query, fields = ['name', 'title']) => {
        if (!query.trim()) return tree;

        const searchQuery = query.toLowerCase();

        const filterNode = (node) => {
            // Проверяем совпадение в текущем узле
            const matches = fields.some(field =>
                node[field] && node[field].toLowerCase().includes(searchQuery)
            );

            // Рекурсивно фильтруем детей
            const filteredChildren = node.children ?
                node.children.map(filterNode).filter(child => child !== null) : [];

            // Возвращаем узел если он сам подходит или у него есть подходящие дети
            if (matches || filteredChildren.length > 0) {
                return {
                    ...node,
                    children: filteredChildren,
                    _matched: matches // Помечаем напрямую найденные узлы
                };
            }

            return null;
        };

        return tree.map(filterNode).filter(node => node !== null);
    },

    // Получить все ID узлов в поддереве
    getSubtreeIds: (node) => {
        const ids = [node.id];

        if (node.children) {
            node.children.forEach(child => {
                ids.push(...Utils.getSubtreeIds(child));
            });
        }

        return ids;
    },

    // Отладочная информация о дереве (убрал символы)
    debugTree: (tree, label = 'Tree Structure') => {
        console.group(label);

        const logNode = (node, level = 0) => {
            const indent = '  '.repeat(level);
            const childrenInfo = node.children ? `(${node.children.length} children)` : '(leaf)';
            const parentInfo = node.parent ?
                (typeof node.parent === 'object' ? `parent: ${node.parent.id}` : `parent: ${node.parent}`) :
                'root';

            console.log(`${indent}${node.name || node.title} [ID: ${node.id}] ${childrenInfo} ${parentInfo}`);

            if (node.children) {
                node.children.forEach(child => logNode(child, level + 1));
            }
        };

        tree.forEach(node => logNode(node));
        console.groupEnd();

        return tree;
    }
};

// Добавить в utils.js
const URLManager = {
    // Получить параметры из URL
    getParams: () => {
        const urlParams = new URLSearchParams(window.location.search);
        const params = {};

        for (const [key, value] of urlParams.entries()) {
            params[key] = value;
        }

        return params;
    },

    // Обновить параметры URL
    updateParams: (newParams) => {
        const url = new URL(window.location);

        Object.keys(newParams).forEach(key => {
            if (newParams[key] !== null && newParams[key] !== undefined) {
                url.searchParams.set(key, newParams[key]);
            }
        });

        window.history.replaceState({}, '', url);
    },

    // Удалить параметр из URL
    clearParam: (paramName) => {
        const url = new URL(window.location);
        url.searchParams.delete(paramName);
        window.history.replaceState({}, '', url);
    },

    // Очистить все параметры URL
    clearAllParams: () => {
        const url = new URL(window.location);
        url.search = '';
        window.history.replaceState({}, '', url);
    }
};