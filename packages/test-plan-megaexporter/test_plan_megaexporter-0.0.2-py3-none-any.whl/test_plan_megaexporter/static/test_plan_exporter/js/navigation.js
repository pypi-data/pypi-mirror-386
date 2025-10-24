
const Navigation = {
    init: () => {
        Navigation.render();
    },

    render: () => {
        const container = document.querySelector('.container');

        const navHTML = `
            <div class="row">
                <div class="col-12">
                    <div id="ready_documents" class="d-flex justify-content-end mb-3">
                        <a href="/plugins/test-plan-megaexporter/documents-list/" class="btn btn-outline-primary">Готовые документы</a>
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-12">
                    <div class="progress-wrapper mb-4">
                        <div id="progress-indicator" class="progress-indicator"></div>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-12">
                    <div id="step-container" class="step-container"></div>
                </div>
            </div>
            <div class="row">
                <div class="col-12">
                    <div id="navigation-buttons" class="navigation-buttons mt-4"></div>
                </div>
            </div>
        `;

        container.innerHTML = navHTML;
        Navigation.updateProgressIndicator();
        Navigation.updateButtons();
    },

    updateProgressIndicator: () => {
        const indicator = document.getElementById('progress-indicator');
        const currentIndex = AppState.get('currentStep');
        const availableSteps = Steps.getAvailableSteps();

        let html = '';
        availableSteps.forEach((step, index) => {
            const isActive = index === currentIndex;
            const isCompleted = index < currentIndex;
            const className = isActive ? 'active' : (isCompleted ? 'completed' : '');

            // Делаем завершенные шаги кликабельными
            const clickable = isCompleted ? 'clickable' : '';
            const clickHandler = isCompleted ? `onclick="Navigation.goToStep(${index})"` : '';

            html += `
            <div class="progress-step ${className} ${clickable}" ${clickHandler}>
                <div class="step-number">${index + 1}</div>
                <div class="step-title">${step.title}</div>
            </div>
        `;
        });

        indicator.innerHTML = html;
    },

    updateButtons: () => {
        const buttonsContainer = document.getElementById('navigation-buttons');
        const currentIndex = AppState.get('currentStep');
        const availableSteps = Steps.getAvailableSteps();
        const isLastStep = currentIndex === availableSteps.length - 1;

        let html = '<div class="d-flex justify-content-between">';

        if (currentIndex > 0) {
            html += `
                <button type="button" class="btn btn-secondary" onclick="Navigation.goBack()">
                    <i class="fas fa-arrow-left"></i> Назад
                </button>
            `;
        } else {
            html += '<div></div>';
        }

        const nextButtonText = isLastStep ? 'Получить документ' : 'Далее';
        const nextButtonClass = isLastStep ? 'btn-success' : 'btn-primary';
        const nextButtonIcon = isLastStep ? 'fas ' : 'fas fa-arrow-right';

        html += `
            <button type="button" class="btn ${nextButtonClass}" 
                    onclick="Navigation.goNext()" 
                    id="next-button">
                ${nextButtonText} <i class="${nextButtonIcon}"></i>
            </button>
        `;

        html += '</div>';
        buttonsContainer.innerHTML = html;

        Navigation.updateNextButtonState();
    },

    updateNextButtonState: () => {
        const nextButton = document.getElementById('next-button');
        if (nextButton) {
            nextButton.disabled = !AppState.isCurrentStepValid();
        }
    },

    goBack: () => {
        const currentIndex = AppState.get('currentStep');
        if (currentIndex > 0) {
            Navigation.clearURLParamsFromStep(currentIndex);
            Navigation.clearStateFromStep(currentIndex);
            AppState.set('currentStep', currentIndex - 1);
            Navigation.navigateToStep();
        }
    },

    clearURLParamsFromStep: (stepIndex) => {
        const availableSteps = Steps.getAvailableSteps();
        const paramsToRemove = [];

        for (let i = stepIndex; i < availableSteps.length; i++) {
            const step = availableSteps[i];

            switch (step.id) {
                case 'documentType':
                    paramsToRemove.push('document_type');
                    break;
                case 'testplanSelection':
                    paramsToRemove.push('plan_id');
                    break;
            }
        }

        paramsToRemove.forEach(param => {
            URLManager.clearParam(param);
        });
    },

    clearStateFromStep: (stepIndex) => {
        const availableSteps = Steps.getAvailableSteps();

        for (let i = stepIndex; i < availableSteps.length; i++) {
            const step = availableSteps[i];

            switch (step.id) {
                case 'project':
                    AppState.set('selectedProject', null);
                    break;
                case 'documentType':
                    AppState.set('documentType', null);
                    break;
                case 'testSelection':
                    AppState.set('selectedTests', []);
                    break;
                case 'testplanSelection':
                    AppState.set('selectedTestplan', null);
                    break;
                case 'conclusion':
                    AppState.set('conclusion', '');
                    break;
                case 'final':
                    break;
            }
        }
    },

    goNext: () => {
        const currentIndex = AppState.get('currentStep');
        const availableSteps = Steps.getAvailableSteps();

        if (!AppState.isCurrentStepValid()) {
            alert('Пожалуйста, заполните все обязательные поля');
            return;
        }

        if (currentIndex < availableSteps.length - 1) {
            AppState.set('currentStep', currentIndex + 1);
            Navigation.navigateToStep();
        } else {
            Navigation.generateDocument();
        }
    },

    navigateToStep: () => {
        const currentStep = Steps.getCurrentStep();
        if (currentStep) {
            Steps.renderStep(currentStep);
            Navigation.updateProgressIndicator();
            Navigation.updateButtons();
        }
    },

    generateDocument: async () => {
        try {
            const originalText = document.querySelector('.btn-success').textContent;
            document.querySelector('.btn-success').innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Генерация...';
            document.querySelector('.btn-success').disabled = true;

            const selectedTests = AppState.get('selectedTests') || [];

            const selectedTestIds = selectedTests
                .filter(item => item.type === 'test')
                .map(item => item.id);

            const selectedPlanIds = selectedTests
                .filter(item => item.type === 'plan')
                .map(item => item.id);

            const documentData = {
                project_id: AppState.get('selectedProject')?.id,
                document_type: AppState.get('documentType'),
                testplan_id: AppState.get('selectedTestplan')?.id,
                selected_test_ids: selectedTestIds,
                conclusion: AppState.get('conclusion') || ''
            };

            console.log('Отправляем данные для генерации:', documentData);
            console.log(`Выбранные тесты (ID): [${selectedTestIds.join(', ')}]`);
            console.log(`Выбранные планы (ID): [${selectedPlanIds.join(', ')}]`);

            const result = await API.generateDocument(documentData);

            console.log('Результат генерации:', result);

            Navigation.showResultMessage('success', `Документ принят в обработку. Смотрите результат на <a href="/plugins/test-plan-megaexporter/documents-list/">странице</a> скачиваний.`);


        } catch (error) {
            console.error('Ошибка при генерации документа:', error);
            Navigation.showResultMessage('error', 'Что-то пошло не так. Попробуйте еще раз.');
        } finally {
            const successButton = document.querySelector('.btn-success');
            if (successButton) {
                successButton.textContent = 'Получить документ';
                successButton.disabled = false;
            }
        }
    },

    showResultMessage: (type, message) => {
        const stepContainer = document.getElementById('step-container');

        const isSuccess = type === 'success';
        const backgroundColor = isSuccess ? '#d4edda' : '#f8d7da';
        const borderColor = isSuccess ? '#c3e6cb' : '#f5c6cb';
        const textColor = isSuccess ? '#155724' : '#721c24';
        const icon = isSuccess ? 'fas fa-check-circle' : 'fas fa-exclamation-triangle';

        const resultHTML = `
            <div style="
                background-color: ${backgroundColor};
                border: 1px solid ${borderColor};
                color: ${textColor};
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                margin: 20px 0;
            ">
                <i class="${icon}" style="font-size: 2rem; margin-bottom: 15px;"></i>
                <h4 style="margin-bottom: 10px; color: ${textColor};">
                    ${isSuccess ? 'Успешно!' : 'Ошибка'}
                </h4>
                <p style="margin: 0; font-size: 1.1rem;">
                    ${message}
                </p>
            </div>
        `;

        stepContainer.innerHTML = resultHTML;

        if (isSuccess) {
            const generateButton = document.querySelector('button[onclick*="generateDocument"], .btn-success, button[type="submit"]');
            if (generateButton) {
                generateButton.style.display = 'none';
            }

        }
    },

    goToStep: (targetIndex) => {
        const currentIndex = AppState.get('currentStep');

        // Можно переходить только к предыдущим шагам
        if (targetIndex >= currentIndex) {
            return;
        }

        // Имитируем нажатия кнопки "Назад" нужное количество раз
        const stepsBack = currentIndex - targetIndex;

        for (let i = 0; i < stepsBack; i++) {
            // Очищаем URL параметры и состояние для каждого шага
            const stepToClear = currentIndex - i;
            Navigation.clearURLParamsFromStep(stepToClear);
            Navigation.clearStateFromStep(stepToClear);
        }

        // Устанавливаем целевой шаг
        AppState.set('currentStep', targetIndex);
        Navigation.navigateToStep();
    },


};