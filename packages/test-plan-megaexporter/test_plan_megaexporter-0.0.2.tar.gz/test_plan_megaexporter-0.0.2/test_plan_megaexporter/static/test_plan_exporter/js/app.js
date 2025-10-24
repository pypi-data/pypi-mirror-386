// app.js
const App = {
    // Инициализация приложения
    init: () => {
        document.addEventListener('DOMContentLoaded', () => {
            App.start();
        });
    },

    // Запуск приложения
    start: async () => {
        // Инициализируем состояние
        AppState.reset();

        // Определяем начальный шаг на основе URL
        await App.initializeFromURL();

        // Инициализируем навигацию
        Navigation.init();

        // Показываем соответствующий шаг
        const currentStep = Steps.getCurrentStep();
        if (currentStep) {
            Steps.renderStep(currentStep);
        }

        console.log('test plan megaexporter App started');
    },

    // Инициализация состояния из URL параметров
    initializeFromURL: async () => {
        const params = URLManager.getParams();
        let lastValidStepIndex = 0;

        try {
            // 1. Проект - всегда первый приоритет
            if (params.project_id) {
                const projects = await API.getProjects();
                const project = projects.find(p => p.id == params.project_id);
                if (project) {
                    AppState.set('selectedProject', project);
                    lastValidStepIndex = Math.max(lastValidStepIndex, 0); // project step
                }
            }

            // 2. Тип документа
            if (params.document_type) {
                const docTypes = Object.keys(AppConfig.documentTypes);
                if (docTypes.includes(params.document_type)) {
                    AppState.set('documentType', params.document_type);
                    lastValidStepIndex = Math.max(lastValidStepIndex, 1); // documentType step
                }
            }

            // 3. План тестирования (теперь всегда на 3 шаге для обоих типов документов)
            if (params.plan_id && params.project_id) {
                try {
                    const testplans = await API.getTestPlans(params.project_id);
                    const testplan = testplans.find(p => p.id == params.plan_id);
                    if (testplan) {
                        AppState.set('selectedTestplan', testplan);
                        lastValidStepIndex = Math.max(lastValidStepIndex, 2); // testplanSelection step
                    }
                } catch (error) {
                    console.warn('Не удалось загрузить план тестирования:', error);
                }
            }

            // Устанавливаем начальный шаг
            AppState.set('currentStep', lastValidStepIndex);

        } catch (error) {
            console.error('Ошибка при инициализации из URL:', error);
            // В случае ошибки остаемся на первом шаге
            AppState.set('currentStep', 0);
        }
    }
};

// Запускаем приложение
App.init();