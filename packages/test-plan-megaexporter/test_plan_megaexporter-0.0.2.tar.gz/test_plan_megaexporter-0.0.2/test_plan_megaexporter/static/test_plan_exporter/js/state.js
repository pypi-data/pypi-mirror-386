// state.js
const AppState = {
    // Внутреннее хранилище состояния
    _state: {
        currentStep: 0,
        selectedProject: null,
        documentType: null,
        selectedTestplan: null,
        selectedTests: [],
        conclusion: '',
        testplansData: [],
        testsHierarchyData: []
    },

    // Получить значение из состояния
    get: (key) => {
        return AppState._state[key];
    },

    // Установить значение в состоянии
    set: (key, value) => {
        AppState._state[key] = value;
        console.log(`AppState: ${key} установлен в`, value);
    },

    // Сброс состояния к начальным значениям
    reset: () => {
        AppState._state = {
            currentStep: 0,
            selectedProject: null,
            documentType: null,
            selectedTestplan: null,
            selectedTests: [],
            conclusion: '',
            testplansData: [],
            testsHierarchyData: []
        };
        console.log('AppState: состояние сброшено');
    },

    // Проверка валидности текущего шага
    isCurrentStepValid: () => {
        const currentIndex = AppState.get('currentStep');
        const documentType = AppState.get('documentType');

        // Определяем доступные шаги на основе типа документа
        const availableSteps = Steps.getAvailableSteps();
        const currentStep = availableSteps[currentIndex];

        if (!currentStep) return false;

        switch (currentStep.id) {
            case 'project':
                return AppState.get('selectedProject') !== null;

            case 'documentType':
                return AppState.get('documentType') !== null;

            case 'testplanSelection':
                return AppState.get('selectedTestplan') !== null;

            case 'testSelection':
                // Для testplan - обязательно выбрать хотя бы один тест
                const selectedTests = AppState.get('selectedTests') || [];
                return selectedTests.length > 0;

            case 'conclusion':
                return true;

            case 'Final':
                return true

            default:
                return true;
        }
    },

    // Получить полное состояние для отладки
    getFullState: () => {
        return { ...AppState._state };
    },

    // Установить несколько значений одновременно
    setMultiple: (updates) => {
        Object.keys(updates).forEach(key => {
            AppState._state[key] = updates[key];
        });
        console.log('AppState: установлены множественные значения', updates);
    }
};

