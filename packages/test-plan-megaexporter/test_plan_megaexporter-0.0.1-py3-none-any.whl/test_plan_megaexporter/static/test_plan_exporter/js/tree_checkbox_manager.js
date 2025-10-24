// tree-checkbox-manager.js
class TreeCheckboxManager {
    constructor(treeContainer) {
        this.treeContainer = treeContainer;
        this.init();
    }

    init() {
        // Добавляем обработчики событий для всех чекбоксов
        this.treeContainer.addEventListener('change', (e) => {
            if (e.target.type === 'checkbox') {
                this.handleCheckboxChange(e.target);
            }
        });

        // Инициализируем начальные состояния
        setTimeout(() => {
            this.updateAllParentStates();
        }, 100);
    }

    handleCheckboxChange(checkbox) {
        const nodeId = checkbox.getAttribute('data-node-id');
        const isChecked = checkbox.checked;

        // Обновляем состояние всех дочерних элементов
        this.updateChildrenState(nodeId, isChecked);
        
        // Обновляем состояние всех родительских элементов
        this.updateParentStates(nodeId);
        
        // Уведомляем основное приложение об изменении
        if (typeof Steps.handleTestSelection === 'function') {
            Steps.handleTestSelection(checkbox);
        }
    }

    updateChildrenState(nodeId, state) {
        const nodeElement = this.findNodeElement(nodeId);
        if (!nodeElement) return;

        // Находим все дочерние чекбоксы
        const childCheckboxes = nodeElement.querySelectorAll('.tree-children input[type="checkbox"]');
        
        childCheckboxes.forEach(childCheckbox => {
            childCheckbox.checked = state;
            childCheckbox.indeterminate = false;
            this.updateCheckboxVisualState(childCheckbox);
        });
    }

    updateParentStates(nodeId) {
        const parentId = this.getParentNodeId(nodeId);
        if (!parentId) return;

        this.updateParentState(parentId);
        // Рекурсивно обновляем состояния родителей выше по иерархии
        this.updateParentStates(parentId);
    }

    updateParentState(parentId) {
        const parentElement = this.findNodeElement(parentId);
        if (!parentElement) return;

        const parentCheckbox = parentElement.querySelector(`:scope > .tree-node-content input[data-node-id="${parentId}"]`);
        if (!parentCheckbox) return;

        const childrenIds = this.getChildrenNodeIds(parentId);
        if (childrenIds.length === 0) return;

        let checkedCount = 0;
        let indeterminateCount = 0;

        childrenIds.forEach(childId => {
            const childCheckbox = this.findCheckbox(childId);
            if (childCheckbox) {
                if (childCheckbox.checked && !childCheckbox.indeterminate) {
                    checkedCount++;
                } else if (childCheckbox.indeterminate) {
                    indeterminateCount++;
                }
            }
        });

        // Определяем состояние родительского чекбокса
        if (checkedCount === childrenIds.length && indeterminateCount === 0) {
            // Все дети отмечены
            parentCheckbox.checked = true;
            parentCheckbox.indeterminate = false;
        } else if (checkedCount === 0 && indeterminateCount === 0) {
            // Все дети не отмечены
            parentCheckbox.checked = false;
            parentCheckbox.indeterminate = false;
        } else {
            // Частично отмечены
            parentCheckbox.checked = false;
            parentCheckbox.indeterminate = true;
        }

        this.updateCheckboxVisualState(parentCheckbox);
    }

    updateAllParentStates() {
        // Получаем все узлы
        const allNodes = this.treeContainer.querySelectorAll('.tree-node');
        const processedNodes = new Set();
        
        // Сначала обрабатываем листовые узлы (без детей), затем идем вверх
        const processNode = (nodeElement) => {
            const nodeId = nodeElement.getAttribute('data-node-id');
            if (processedNodes.has(nodeId)) return;
            
            const children = this.getChildrenNodeIds(nodeId);
            
            // Если у узла есть дети, сначала обрабатываем их
            if (children.length > 0) {
                let allChildrenProcessed = true;
                children.forEach(childId => {
                    if (!processedNodes.has(childId)) {
                        const childElement = this.findNodeElement(childId);
                        if (childElement) {
                            processNode(childElement);
                        }
                    }
                });
                
                // Теперь обновляем состояние родителя
                this.updateParentState(nodeId);
            }
            
            processedNodes.add(nodeId);
        };
        
        // Обрабатываем все узлы
        Array.from(allNodes).forEach(processNode);
    }

    updateCheckboxVisualState(checkbox) {
        const wrapper = checkbox.closest('.checkbox-wrapper');
        if (!wrapper) return;

        // Удаляем все классы состояний
        wrapper.classList.remove('checked', 'unchecked', 'indeterminate');

        // Добавляем соответствующий класс
        if (checkbox.indeterminate) {
            wrapper.classList.add('indeterminate');
        } else if (checkbox.checked) {
            wrapper.classList.add('checked');
        } else {
            wrapper.classList.add('unchecked');
        }
    }

    // Вспомогательные методы
    findNodeElement(nodeId) {
        return this.treeContainer.querySelector(`.tree-node[data-node-id="${nodeId}"]`);
    }

    findCheckbox(nodeId) {
        return this.treeContainer.querySelector(`input[data-node-id="${nodeId}"]`);
    }

    getParentNodeId(nodeId) {
        const nodeElement = this.findNodeElement(nodeId);
        if (!nodeElement) return null;

        const parentNode = nodeElement.parentElement.closest('.tree-node');
        if (!parentNode) return null;

        return parentNode.getAttribute('data-node-id');
    }

    getChildrenNodeIds(parentId) {
        const parentElement = this.findNodeElement(parentId);
        if (!parentElement) return [];

        const childNodes = parentElement.querySelectorAll(':scope > .tree-children > .tree-node');
        return Array.from(childNodes).map(node => node.getAttribute('data-node-id')).filter(Boolean);
    }

    // Публичные методы для управления состояниями
    getSelectedNodeIds() {
        const checkboxes = this.treeContainer.querySelectorAll('input[type="checkbox"]:checked:not([indeterminate])');
        return Array.from(checkboxes).map(cb => cb.getAttribute('data-node-id'));
    }

    getPartiallySelectedNodeIds() {
        const checkboxes = this.treeContainer.querySelectorAll('input[type="checkbox"]');
        return Array.from(checkboxes)
            .filter(cb => cb.indeterminate)
            .map(cb => cb.getAttribute('data-node-id'));
    }
}
