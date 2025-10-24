const API = {
    getCSRFToken: () => {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];

        if (cookieValue) {
            return cookieValue;
        }

        const metaToken = document.querySelector('meta[name=csrf-token]');
        if (metaToken) {
            return metaToken.getAttribute('content');
        }

        const hiddenInput = document.querySelector('input[name=csrfmiddlewaretoken]');
        if (hiddenInput) {
            return hiddenInput.value;
        }

        console.warn('CSRF token не найден');
        return null;
    },

    request: async (url, options = {}) => {
        try {
            const csrfToken = API.getCSRFToken();

            const headers = {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                ...options.headers
            };

            if (options.method && !['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(options.method.toUpperCase())) {
                if (csrfToken) {
                    headers['X-CSRFToken'] = csrfToken;
                }
            }

            const response = await fetch(url, {
                headers,
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    },

    getProjects: async () => {
        const data = await API.request(AppConfig.api.projects);
        const projects = data.results || data;
        return projects.filter(project => project.is_visible === true);
    },

    getTestPlans: async (projectId) => {
        const url = `${AppConfig.api.testplans}?project=${projectId}&page_size=10000&is_archive=false`;
        const data = await API.request(url);
        return data.results || data;
    },

    getTestsHierarchy: async (planId) => {
        const url = `/plugins/test-plan-megaexporter/api/plan/${planId}/tests/hierarchy/`;
        const data = await API.request(url);
        return data.data || data;
    },

    generateDocument: async (documentData) => {
        const documentType = documentData.document_type;
        if (!documentType) {
            throw new Error('document_type is required');
        }

        const url = `/plugins/test-plan-megaexporter/api/documents/${documentType}/`;
        return await API.request(url, {
            method: 'POST',
            body: JSON.stringify(documentData)
        });
    }

};