
// steps.js
const Steps = {
    // Инициализация
    init: () => {
        Steps.renderStep(Steps.getCurrentStep());
    },

    // Получить доступные шаги
    getAvailableSteps: () => {
        const documentType = AppState.get('documentType');
        const allSteps = AppConfig.steps;

        return Object.keys(allSteps)
            .filter(stepId => {
                const step = allSteps[stepId];
                if (!step.condition) return true;

                const currentState = {
                    documentType: documentType,
                    selectedProject: AppState.get('selectedProject'),
                    selectedTestplan: AppState.get('selectedTestplan'),
                    conclusion: AppState.get('conclusion')
                };

                return step.condition(currentState);
            })
            .map(stepId => ({
                id: stepId,
                ...allSteps[stepId]
            }));
    },

    // Получить текущий шаг
    getCurrentStep: () => {
        const currentIndex = AppState.get('currentStep');
        const availableSteps = Steps.getAvailableSteps();
        return availableSteps[currentIndex] || availableSteps[0];
    },

    // Рендер текущего шага
    renderStep: (step) => {
        const container = document.getElementById('step-container');

        if (!step) {
            container.innerHTML = '<div class="alert alert-danger">Шаг не найден</div>';
            return;
        }

        switch (step.id) {
            case 'project':
                Steps.renderProjectSelection(container);
                break;
            case 'documentType':
                Steps.renderDocumentTypeSelection(container);
                break;
            case 'testSelection':
                Steps.renderTestSelection(container);
                break;
            case 'testplanSelection':
                Steps.renderTestplanSelection(container);
                break;
            case 'conclusion':
                Steps.renderConclusionStep(container);
                break;
            case 'final':
                Steps.renderFinalSelection(container);
                break;
            default:
                container.innerHTML = '<div class="alert alert-warning">Неизвестный шаг</div>';
        }
    },

// Шаг 1: Выбор проекта
    renderProjectSelection: async (container) => {
        const selectedProject = AppState.get('selectedProject');

        container.innerHTML = `
        <div class="step-content">
            <h3>Выбор проекта</h3>
            <div class="mb-3">
                <div class="search-wrapper">
                    <input type="text" 
                           class="form-control" 
                           id="project-search" 
                           placeholder="Поиск проектов..."
                           oninput="Steps.searchProjects(this.value)"
                           style="margin-bottom: 15px;">
                </div>
            </div>
            <div id="projects-list">
                ${Steps.renderLoading('Загружаем список проектов...')}
            </div>
        </div>
    `;

        try {
            const projects = await API.getProjects();
            AppState.set('allProjects', projects); // Сохраняем все проекты для поиска
            const projectsList = document.getElementById('projects-list');

            if (projects.length === 0) {
                projectsList.innerHTML = '<div class="alert alert-info">Проекты не найдены</div>';
                return;
            }

            Steps.renderProjectsList(projects, selectedProject);

            // Выбираем проект из URL если есть
            const params = URLManager.getParams();
            if (params.project_id && !selectedProject) {
                const project = projects.find(p => p.id == params.project_id);
                if (project) {
                    Steps.selectProject(project);
                }
            }

            if (selectedProject) {
                setTimeout(() => {
                    const activeItem = document.querySelector('#projects-list .active');
                    activeItem?.scrollIntoView({ behavior: 'smooth' });
                }, 100);
            }

        } catch (error) {
            const projectsList = document.getElementById('projects-list');
            projectsList.innerHTML = `
            <div class="alert alert-danger">
                Ошибка загрузки проектов: ${error.message}
            </div>
        `;
        }
    },

// Новый метод для отображения списка проектов
    renderProjectsList: (projects, selectedProject) => {
        const projectsList = document.getElementById('projects-list');

        if (projects.length === 0) {
            projectsList.innerHTML = '<div class="alert alert-info">По запросу ничего не найдено</div>';
            return;
        }

        let html = '<div class="list-group">';
        projects.forEach(project => {
            const isSelected = selectedProject && selectedProject.id === project.id;
            html += `
            <div class="list-group-item list-group-item-action ${isSelected ? 'active' : ''}" 
                 style="cursor: pointer;"
                 onclick="Steps.selectProject(${JSON.stringify(project).replace(/"/g, '&quot;')})">
                <div class="d-flex w-100 justify-content-between">
                    <h5 class="mb-1">${project.name}</h5>
                    <small>ID: ${project.id}</small>
                </div>
                ${project.description ? `<p class="mb-1">${project.description}</p>` : ''}
            </div>
        `;
        });
        html += '</div>';

        projectsList.innerHTML = html;
    },

// Новый метод для поиска проектов
    searchProjects: (searchTerm) => {
        const allProjects = AppState.get('allProjects') || [];
        const selectedProject = AppState.get('selectedProject');

        if (!searchTerm.trim()) {
            // Если поиск пустой, показываем все проекты
            Steps.renderProjectsList(allProjects, selectedProject);
            return;
        }

        // Фильтруем проекты по названию и описанию
        const searchLower = searchTerm.toLowerCase();
        const filteredProjects = allProjects.filter(project => {
            const nameMatch = project.name.toLowerCase().includes(searchLower);
            const descMatch = project.description ?
                project.description.toLowerCase().includes(searchLower) : false;
            const idMatch = project.id.toString().includes(searchTerm);

            return nameMatch || descMatch || idMatch;
        });

        Steps.renderProjectsList(filteredProjects, selectedProject);
    },

    // Выбор проекта
    selectProject: (project) => {
        AppState.set('selectedProject', project);
        URLManager.updateParams({ project_id: project.id });

        // Обновляем активный элемент
        const items = document.querySelectorAll('#projects-list .list-group-item');
        items.forEach(item => {
            item.classList.remove('active');
        });

        // Ищем и выделяем выбранный проект
        const selectedItem = Array.from(items).find(item => {
            const smallElement = item.querySelector('small');
            if (smallElement) {
                return smallElement.textContent.trim() === `ID: ${project.id}`;
            }
            return false;
        });

        if (selectedItem) {
            selectedItem.classList.add('active');
        }

        Navigation.updateNextButtonState();
    },

    // Шаг 2: Выбор типа документа
    renderDocumentTypeSelection: (container) => {
        const selectedType = AppState.get('documentType');
        const documentTypes = AppConfig.documentTypes;

        let html = `
            <div class="step-content">
                <h3>Выбор типа документа</h3>
                <div class="row">
        `;

        Object.values(documentTypes).forEach(docType => {
            const isSelected = selectedType === docType.id;
            html += `
                <div class="col-md-6 mb-4">
                    <div class="card ${isSelected ? 'border-primary' : ''}" style="cursor: pointer;"
                         onclick="Steps.selectDocumentType('${docType.id}')">
                        <div class="card-body text-center">
                            <div style="font-size: 3rem;">${docType.icon}</div>
                            <h5 class="card-title mt-3">${docType.title}</h5>
                            <p class="card-text">${docType.description}</p>
                            <ul class="list-unstyled">
                                ${docType.features.map(feature => `<li>✓ ${feature}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
            `;
        });

        html += `
                </div>
            </div>
        `;

        container.innerHTML = html;

        // Выбираем тип документа из URL если есть
        const params = URLManager.getParams();
        if (params.document_type && !selectedType) {
            Steps.selectDocumentType(params.document_type);
        }
    },

    // Выбор типа документа
    selectDocumentType: (typeId) => {
        AppState.set('documentType', typeId);
        URLManager.updateParams({ document_type: typeId });

        // Обновляем выделение карточек
        const cards = document.querySelectorAll('#step-container .card');
        cards.forEach(card => {
            card.classList.remove('border-primary');
        });

        const selectedCard = Array.from(cards).find(card =>
            card.getAttribute('onclick').includes(typeId)
        );
        if (selectedCard) {
            selectedCard.classList.add('border-primary');
        }

        Navigation.updateNextButtonState();
    },

    // Шаг 3: Выбор плана тестирования
    renderTestplanSelection: async (container) => {
        const selectedProject = AppState.get('selectedProject');
        const selectedTestplan = AppState.get('selectedTestplan');

        if (!selectedProject) {
            container.innerHTML = '<div class="alert alert-danger">Сначала выберите проект</div>';
            return;
        }

        container.innerHTML = `
            <div class="step-content">
                <h3>Выбор плана тестирования</h3>
                <div id="testplans-tree" class="tree-container">
                    ${Steps.renderLoading('Загружаем планы тестирования...')}
                </div>
            </div>
        `;

        try {
            const testplans = await API.getTestPlans(selectedProject.id);
            Steps.renderTestPlansTree(testplans);

            // Выбираем план из URL если есть
            const params = URLManager.getParams();
            if (params.plan_id && !selectedTestplan) {
                Steps.selectTestplanById(params.plan_id, testplans);
            }
        } catch (error) {
            const container = document.getElementById('testplans-tree');
            Utils.showError(container, `Ошибка загрузки планов: ${error.message}`);
        }
    },

    // Рендер дерева планов с автоматическим разворачиванием
    renderTestPlansTree: (testplans) => {
        const container = document.getElementById('testplans-tree');
        AppState.set('testplansData', testplans);

        if (testplans.length === 0) {
            container.innerHTML = Steps.renderEmptyTree('планов тестирования');
            return;
        }

        // Проверяем, есть ли выбранный план из URL
        const params = URLManager.getParams();
        const selectedPlanId = params.plan_id;

        // Определяем какие узлы должны быть развернуты (только если есть выбранный план)
        const expandedNodes = selectedPlanId ?
            Steps.getExpandedNodesForTarget(selectedPlanId, testplans) : new Set();

        const tree = Utils.buildTree(testplans, 'parent');

        const html = `
            <div class="tree-root" id="testplan-tree-root">
                ${Steps.renderTreeNodes(tree, 'testplan', 0, expandedNodes, selectedPlanId)}
            </div>
        `;
        container.innerHTML = html;

        // Если есть выбранный план, прокручиваем к нему
        if (selectedPlanId) {
            setTimeout(() => {
                const selectedElement = document.querySelector(`[data-node-id="${selectedPlanId}"]`);
                if (selectedElement) {
                    Steps.scrollToElement(selectedElement);
                }
            }, 100);
        }
    },

    // Получить список узлов, которые должны быть развернуты для показа целевого узла
    getExpandedNodesForTarget: (targetNodeId, allNodes) => {
        const expandedNodes = new Set();

        // Находим целевой узел
        const targetNode = allNodes.find(node => node.id == targetNodeId);
        if (!targetNode) return expandedNodes;

        // Строим цепочку родителей
        const parentChain = Steps.buildParentChain(targetNode, allNodes);

        // Все родители должны быть развернуты
        parentChain.forEach(parentId => {
            expandedNodes.add(parentId);
        });

        return expandedNodes;
    },

    // Построение цепочки родителей
    buildParentChain: (targetNode, allNodes) => {
        const parentChain = [];
        const visited = new Set();
        let currentNode = targetNode;

        while (currentNode && currentNode.parent && !visited.has(currentNode.id)) {
            visited.add(currentNode.id);

            // Извлекаем ID родителя
            let parentId = null;
            if (typeof currentNode.parent === 'object' && currentNode.parent.id) {
                parentId = currentNode.parent.id;
            } else {
                parentId = currentNode.parent;
            }

            const parent = allNodes.find(node => node.id == parentId);
            if (parent) {
                parentChain.unshift(parent.id);
                currentNode = parent;
            } else {
                break;
            }
        }

        return parentChain;
    },

    // Рендеринг узлов дерева
    renderTreeNodes: (nodes, type, level = 0, expandedNodes = new Set(), selectedNodeId = null) => {
        return nodes.map((node) => {
            const hasChildren = node.children && node.children.length > 0;
            const isSelected = selectedNodeId && selectedNodeId == node.id;
            const isExpanded = expandedNodes.has(node.id);

            let nodeClasses = ['tree-node'];
            if (isSelected) nodeClasses.push('selected');
            if (hasChildren) nodeClasses.push('has-children');
            else nodeClasses.push('leaf-node');
            if (isExpanded) nodeClasses.push('expanded');

            let html = `<div class="${nodeClasses.join(' ')}" data-node-id="${node.id}" data-level="${level}">`;

            html += `
                <div class="node-content" 
                     style="padding-left: ${level * 15}px;" 
                     onclick="Steps.selectTreeNode(${JSON.stringify(node).replace(/"/g, '&quot;')}, '${type}')">
                    ${hasChildren ?
                `<button class="node-toggle" onclick="event.stopPropagation(); Steps.toggleTreeNode(this)">${isExpanded ? '▼' : '▶'}</button>` :
                '<span class="node-spacer"></span>'
            }
                    <span class="node-name">${node.name}</span>
                    ${hasChildren ? `<span class="node-count">(${node.children.length})</span>` : ''}
                </div>
            `;

            // Дочерние узлы
            if (hasChildren) {
                html += `
                    <div class="node-children" style="display: ${isExpanded ? 'block' : 'none'};">
                        ${Steps.renderTreeNodes(node.children, type, level + 1, expandedNodes, selectedNodeId)}
                    </div>
                `;
            }

            html += '</div>';
            return html;
        }).join('');
    },

    // Выбор узла дерева
    selectTreeNode: (node, type) => {
        // Убираем выделение с других узлов
        const treeSelector = '#testplans-tree';
        const allNodes = document.querySelectorAll(`${treeSelector} .tree-node`);
        allNodes.forEach(n => n.classList.remove('selected'));

        // Выделяем выбранный узел
        const selectedElement = document.querySelector(`${treeSelector} [data-node-id="${node.id}"]`);
        if (selectedElement) {
            selectedElement.classList.add('selected');
        }

        // Сохраняем выбор в состоянии
        if (type === 'testplan') {
            AppState.set('selectedTestplan', node);
            URLManager.updateParams({ plan_id: node.id });
        }

        Navigation.updateNextButtonState();
    },

    // Переключение состояния узла
    toggleTreeNode: (button) => {
        const nodeElement = button.closest('.tree-node');
        const nodeChildren = nodeElement.querySelector('.node-children');

        if (!nodeChildren) return;

        const isExpanded = nodeElement.classList.contains('expanded');

        if (isExpanded) {
            nodeElement.classList.remove('expanded');
            nodeChildren.style.display = 'none';
            button.textContent = '▶';
        } else {
            nodeElement.classList.add('expanded');
            nodeChildren.style.display = 'block';
            button.textContent = '▼';
        }
    },

    selectTestplanById: async (planId, testplans) => {
        const testplan = Steps.findNodeInFlat(testplans, planId);
        if (testplan) {
            AppState.set('selectedTestplan', testplan);
            Navigation.updateNextButtonState();

            setTimeout(() => {
                const selectedElement = document.querySelector(`[data-node-id="${planId}"]`);
                if (selectedElement) {
                    Steps.scrollToElement(selectedElement);
                }
            }, 100);
        }
    },

    // Поиск узла в плоском массиве
    findNodeInFlat: (nodes, nodeId) => {
        return nodes.find(node => node.id == nodeId);
    },

    renderTestPlansTree: (testplans) => {
        const container = document.getElementById('testplans-tree');
        AppState.set('testplansData', testplans);

        if (testplans.length === 0) {
            container.innerHTML = Steps.renderEmptyTree('планов тестирования');
            return;
        }

        const params = URLManager.getParams();
        const selectedPlanId = params.plan_id;

        const expandedNodes = selectedPlanId ?
            Steps.getExpandedNodesForTarget(selectedPlanId, testplans) : new Set();

        const tree = Utils.buildTree(testplans, 'parent');

        const html = `
        <div class="tree-root" id="testplan-tree-root">
            ${Steps.renderTreeNodes(tree, 'testplan', 0, expandedNodes, selectedPlanId)}
        </div>
    `;
        container.innerHTML = html;

        setTimeout(() => {
            new TreeSearchManager(container, {
                placeholder: 'Поиск планов тестирования...'
            });
        }, 100);

        if (selectedPlanId) {
            setTimeout(() => {
                const selectedElement = document.querySelector(`[data-node-id="${selectedPlanId}"]`);
                if (selectedElement) {
                    Steps.scrollToElement(selectedElement);
                }
            }, 100);
        }
    },

    renderTestSelection: async (container) => {
        const selectedTestplan = AppState.get('selectedTestplan');
        const selectedTests = AppState.get('selectedTests') || [];

        if (!selectedTestplan) {
            container.innerHTML = '<div class="alert alert-danger">План тестирования не выбран</div>';
            return;
        }

        container.innerHTML = `
        <div class="step-content">
            <h3>Выбор тестов</h3>
            <div class="selected-testplan mb-3">
                <strong>План:</strong> ${selectedTestplan.name}
            </div>
            
            <div class="test-selection-controls mb-3">
                <div class="btn-group" role="group">
                    <button type="button" class="btn btn-outline-primary btn-sm" 
                            onclick="Steps.selectAllTests()">Выбрать все</button>
                    <button type="button" class="btn btn-outline-secondary btn-sm" 
                            onclick="Steps.deselectAllTests()">Снять все</button>
                </div>
            </div>
            
            <div id="tests-tree" class="tree-container">
                ${Steps.renderLoading('Загружаем структуру тестов...')}
            </div>
        </div>
    `;

        try {
            const testsData = await API.getTestsHierarchy(selectedTestplan.id);
            AppState.set('testsHierarchyData', testsData);

            const testsTree = document.getElementById('tests-tree');
            const treeData = Utils.buildTree(testsData, 'parent');

            testsTree.innerHTML = Steps.renderTestsTree(treeData);

            setTimeout(() => {
                new TreeSearchManager(testsTree, {
                    placeholder: 'Поиск тестов...'
                });
            }, 100);

            const params = URLManager.getParams();
            if (params.selected_tests) {
                const testIds = params.selected_tests.split(',').map(id => parseInt(id));
                AppState.set('selectedTests', testIds);

                testIds.forEach(testId => {
                    const checkbox = testsTree.querySelector(`input[data-node-id="${testId}"]`);
                    if (checkbox) {
                        checkbox.checked = true;
                    }
                });

                Steps.updateAllParentStates();
            } else {
                setTimeout(() => {
                    Steps.selectAllTests();
                }, 100);
            }

        } catch (error) {
            const testsTree = document.getElementById('tests-tree');
            testsTree.innerHTML = `
            <div class="alert alert-danger">
                Ошибка загрузки тестов: ${error.message}
            </div>
        `;
        }
    },

    // Переключение узла в дереве тестов
    toggleTestTreeNode: (button) => {
        const nodeElement = button.closest('.tree-node');
        const nodeChildren = nodeElement.querySelector('.node-children');

        if (!nodeChildren) return;

        const isExpanded = nodeElement.classList.contains('expanded');

        if (isExpanded) {
            nodeElement.classList.remove('expanded');
            nodeChildren.style.display = 'none';
            button.textContent = '▶';
        } else {
            nodeElement.classList.add('expanded');
            nodeChildren.style.display = 'block';
            button.textContent = '▼';
        }
    },

    // Обработчик выбора тестов
    handleTestSelection: (checkbox) => {
        const nodeId = parseInt(checkbox.getAttribute('data-node-id'));
        const nodeType = checkbox.getAttribute('data-node-type');
        const isChecked = checkbox.checked;

        // Обновляем состояние потомков
        if (nodeType === 'folder') {
            Steps.updateChildrenStates(nodeId, isChecked);
        }

        // Обновляем состояние всех родителей рекурсивно
        Steps.updateParentStatesRecursively(nodeId);

        // Обновляем состояние приложения
        Steps.updateSelectedTestsFromDOM();
        Navigation.updateNextButtonState();
    },

    // Обновить состояние всех потомков
    updateChildrenStates: (parentId, checked) => {
        const testsTree = document.getElementById('tests-tree');
        const parentNode = testsTree.querySelector(`[data-node-id="${parentId}"]`);
        if (!parentNode) return;

        const childrenContainer = parentNode.querySelector('.node-children');
        if (!childrenContainer) return;

        const childCheckboxes = childrenContainer.querySelectorAll('input[type="checkbox"]');
        childCheckboxes.forEach(childCheckbox => {
            if (childCheckbox.checked !== checked) {
                childCheckbox.checked = checked;
                // Рекурсивно обновляем потомков этого элемента
                const childNodeId = parseInt(childCheckbox.getAttribute('data-node-id'));
                const childNodeType = childCheckbox.getAttribute('data-node-type');
                if (childNodeType === 'folder') {
                    Steps.updateChildrenStates(childNodeId, checked);
                }
            }
        });
    },

    // Рекурсивное обновление состояния всех родителей
    updateParentStatesRecursively: (nodeId) => {
        const testsTree = document.getElementById('tests-tree');
        const nodeElement = testsTree.querySelector(`[data-node-id="${nodeId}"]`);
        if (!nodeElement) return;

        // Находим родительский элемент
        const parentElement = Steps.findParentTreeNode(nodeElement);
        if (!parentElement) return;

        const parentId = parseInt(parentElement.getAttribute('data-node-id'));

        // Обновляем состояние родителя
        Steps.updateParentState(parentId);

        // Рекурсивно обновляем состояние дедушки
        Steps.updateParentStatesRecursively(parentId);
    },

    // Найти родительский элемент дерева
    findParentTreeNode: (nodeElement) => {
        // Поднимаемся вверх по DOM, ищем родительский .tree-node
        let current = nodeElement.parentElement;

        while (current) {
            // Если мы нашли .node-children, значит следующий .tree-node будет родительским
            if (current.classList.contains('node-children')) {
                const parentTreeNode = current.parentElement;
                if (parentTreeNode && parentTreeNode.classList.contains('tree-node')) {
                    return parentTreeNode;
                }
            }
            current = current.parentElement;
        }

        return null;
    },

    // Обновить состояние всех родителей (старый метод для совместимости)
    updateAllParentStates: () => {
        const testsTree = document.getElementById('tests-tree');
        const folderCheckboxes = testsTree.querySelectorAll('input[data-node-type="folder"]');

        folderCheckboxes.forEach(folderCheckbox => {
            const nodeId = parseInt(folderCheckbox.getAttribute('data-node-id'));
            Steps.updateParentState(nodeId);
        });
    },

    // Обновить состояние конкретного родителя
    updateParentState: (parentId) => {
        const testsTree = document.getElementById('tests-tree');
        const parentNode = testsTree.querySelector(`[data-node-id="${parentId}"]`);
        if (!parentNode) return;

        const parentCheckbox = parentNode.querySelector('input[type="checkbox"]');
        const childrenContainer = parentNode.querySelector('.node-children');

        if (!parentCheckbox || !childrenContainer) return;

        const childCheckboxes = childrenContainer.querySelectorAll('input[type="checkbox"]');
        if (childCheckboxes.length === 0) return;

        let checkedCount = 0;
        let totalCount = 0;

        childCheckboxes.forEach(childCheckbox => {
            totalCount++;
            if (childCheckbox.checked) {
                checkedCount++;
            }
        });

        // Обновляем состояние родительского чекбокса
        if (checkedCount === 0) {
            parentCheckbox.checked = false;
            parentCheckbox.indeterminate = false;
        } else if (checkedCount === totalCount) {
            parentCheckbox.checked = true;
            parentCheckbox.indeterminate = false;
        } else {
            parentCheckbox.checked = false;
            parentCheckbox.indeterminate = true;
        }
    },

    // Обновить состояние selectedTests на основе DOM
    updateSelectedTestsFromDOM: () => {
        const testsTree = document.getElementById('tests-tree');
        const checkedCheckboxes = testsTree.querySelectorAll('input[type="checkbox"]:checked');
        const selectedTests = [];

        checkedCheckboxes.forEach(checkbox => {
            const nodeId = parseInt(checkbox.getAttribute('data-node-id'));
            const nodeType = checkbox.getAttribute('data-node-type');

            selectedTests.push({
                id: nodeId,
                type: nodeType === 'folder' ? 'plan' : 'test'
            });
        });

        AppState.set('selectedTests', selectedTests);
    },

    // Выбор всех тестов
    selectAllTests: () => {
        const testsTree = document.getElementById('tests-tree');
        const checkboxes = testsTree.querySelectorAll('input[type="checkbox"]');

        checkboxes.forEach(checkbox => {
            checkbox.checked = true;
            checkbox.indeterminate = false;
        });

        Steps.updateSelectedTestsFromDOM();
        Navigation.updateNextButtonState();

        const selectedTests = AppState.get('selectedTests') || [];
        const testIds = selectedTests.map(item => item.id);
    },

    // Снятие выбора со всех тестов
    deselectAllTests: () => {
        const testsTree = document.getElementById('tests-tree');
        const checkboxes = testsTree.querySelectorAll('input[type="checkbox"]');

        checkboxes.forEach(checkbox => {
            checkbox.checked = false;
            checkbox.indeterminate = false;
        });

        AppState.set('selectedTests', []);
        Navigation.updateNextButtonState();
        URLManager.clearParam('selected_tests');
    },

    // Шаг 5: Заключение (только для testplan)
    renderConclusionStep: (container) => {
        const selectedTestplan = AppState.get('selectedTestplan');
        const selectedTests = AppState.get('selectedTests') || [];
        const conclusion = AppState.get('conclusion') || '';

        container.innerHTML = `
            <div class="step-content">
                <h3>Заключение</h3>
                
                <div class="mb-4">
                    <div class="alert alert-info">
                        <strong>План тестирования:</strong> ${selectedTestplan ? selectedTestplan.name : 'Не выбран'}<br>
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="conclusion-text">Заключение (необязательно):</label>
                    <textarea class="form-control" id="conclusion-text" rows="6"
                              placeholder="Введите заключение к документу..."
                              oninput="Steps.updateConclusion(this.value)">${conclusion}</textarea>
                    <small class="form-text text-muted">
                        Заключение будет добавлено в конец документа
                    </small>
                </div>
            </div>
        `;
    },


    updateConclusion: (value) => {
        AppState.set('conclusion', value);
    },


    renderFinalSelection: async (container) => {
        const selectedProject = AppState.get('selectedProject');
        const selectedTestplan = AppState.get('selectedTestplan');
        const documentType = AppState.get('documentType');
        const selectedTests = AppState.get('selectedTests') || [];
        const conclusion = AppState.get('conclusion') || '';

        const documentTypeName = AppConfig.documentTypes[documentType]?.title || 'Неизвестный тип';
        const testCount = selectedTests.filter(item => item.type === 'test').length;

        container.innerHTML = `
        <div class="step-content">
            <h3>Подтверждение выбора</h3>
            <div id="final-info">
                <div class="alert alert-info">
                    <strong>Проект:</strong> ${selectedProject?.name || 'Не выбран'}<br>
                    <strong>Тип документа:</strong> ${documentTypeName}<br>
                    ${selectedTestplan ? `<strong>План тестирования:</strong> ${selectedTestplan.name}<br>` : ''}
                    ${documentType === 'testplan' ? `<strong>Выбрано тестов:</strong> ${testCount}<br>` : ''}
                    <strong>Заключение:</strong> ${conclusion.trim() ? 'Заполнено' : 'Не заполнено'}
                </div>
            </div>
        </div>
    `;
    },



    // Вспомогательные методы
    renderLoading: (message = 'Загрузка...') => {
        return `
            <div class="d-flex justify-content-center align-items-center" style="min-height: 200px;">
                <div class="text-center">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="sr-only">Loading...</span>
                    </div>
                    <div>${message}</div>
                </div>
            </div>
        `;
    },

    renderEmptyTree: (itemType) => {
        return `<div class="alert alert-info">Не найдено ${itemType}</div>`;
    },

    scrollToElement: (element) => {
        if (element) {
            element.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        }
    },
    renderTestsTree: (nodes) => {
        if (!nodes || nodes.length === 0) {
            return '<div class="alert alert-info">Тесты не найдены</div>';
        }

        let html = '<div class="tree-root">';

        const renderNode = (node, level = 0) => {
            const hasChildren = node.children && node.children.length > 0;
            const hasTests = node.tests && node.tests.length > 0;
            const isFolder = hasChildren || hasTests;
            const nodeType = isFolder ? 'folder' : 'test';

            let nodeClasses = ['tree-node'];
            if (isFolder) {
                nodeClasses.push('has-children');
                nodeClasses.push('expanded');
            } else {
                nodeClasses.push('leaf-node');
            }

            let nodeHtml = `<div class="${nodeClasses.join(' ')}" data-node-id="${node.id}" data-level="${level}">`;

            nodeHtml += `
                <div class="node-content" style="padding-left: ${level * 10}px;">
                    ${(hasChildren || hasTests) ?
                `<button class="node-toggle" onclick="Steps.toggleTestTreeNode(this)">▼</button>` :
                '<span class="node-spacer"></span>'
            }
                    <div class="checkbox-wrapper">
                        <input type="checkbox" 
                               data-node-id="${node.id}" 
                               data-node-type="${nodeType}"
                               checked
                               onchange="Steps.handleTestSelection(this)" />
                        <span class="node-name">${node.name}</span>
                        ${hasTests ? `<span class="node-count">(${node.tests.length})</span>` : ''}
                    </div>
                </div>
            `;

            if (hasChildren || hasTests) {
                nodeHtml += '<div class="node-children" style="display: block;">';

                if (hasChildren) {
                    node.children.forEach(child => {
                        nodeHtml += renderNode(child, level + 1);
                    });
                }

                if (hasTests) {
                    node.tests.forEach(test => {
                        nodeHtml += `
                            <div class="tree-node test-node leaf-node" data-node-id="${test.id}" data-level="${level + 1}">
                                <div class="node-content" style="padding-left: ${(level + 1) * 10}px;">
                                    <span class="node-spacer"></span>
                                    <div class="checkbox-wrapper">
                                        <input type="checkbox" 
                                               data-node-id="${test.id}" 
                                               data-node-type="test"
                                               checked
                                               onchange="Steps.handleTestSelection(this)" />
                                        <span class="node-name">${test.name}</span>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                }

                nodeHtml += '</div>';
            }

            nodeHtml += '</div>';
            return nodeHtml;
        };

        nodes.forEach(node => {
            html += renderNode(node);
        });

        html += '</div>';
        return html;
    },
};