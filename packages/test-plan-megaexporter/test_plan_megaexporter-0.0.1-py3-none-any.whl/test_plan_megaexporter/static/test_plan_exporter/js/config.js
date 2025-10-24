// config.js
const AppConfig = {
    // API конфигурация
    api: {
        projects: '/api/v2/projects/?page_size=10000&is_archive=false',
        testplans: '/api/v2/testplans/',

    },

    // Типы документов
    documentTypes: {
        testplan: {
            id: 'testplan',
            title: 'Тестовый план',
            description: 'Создание PDF документа с тестовым планом',
            icon: '📋',
            features: [
                'Выбор плана тестирования',
                'Настройка содержания',
                'Экспорт в PDF'
            ],
            steps: ['project', 'documentType', 'testplanSelection', 'testSelection', 'final']
        },
        testreport: {
            id: 'testreport',
            title: 'Отчёт о тестировании',
            description: 'Создание отчёта по результатам тестирования',
            icon: '📊',
            features: [
                'Выбор плана тестирования',
                'Добавление заключения',
                'Экспорт в PDF'
            ],
            steps: ['project', 'documentType', 'testplanSelection', 'conclusion', 'final']
        }
    },

    // Настройки шагов
    steps: {
        project: {
            title: 'Выбор проекта',
            required: true
        },
        documentType: {
            title: 'Тип документа',
            required: true
        },
        // Шаг-пустышка для отображения до выбора типа документа
        placeholder3: {
            title: 'Выбор плана тестирования',
            required: true,
            condition: (state) => !state.documentType
        },
        placeholder4: {
            title: 'Выбор тестов или заключение',
            required: false,
            condition: (state) => !state.documentType
        },

        testplanSelection: {
            title: 'Выбор плана',
            required: true,
            condition: (state) => !!state.documentType
        },
        testSelection: {
            title: 'Выбор тестов',
            required: false,
            condition: (state) => state.documentType === 'testplan'
        },
        conclusion: {
            title: 'Заключение',
            required: false,
            condition: (state) => state.documentType === 'testreport'
        },
        final: {
            title: 'Последний шаг',
            required: true
        }
    }
};