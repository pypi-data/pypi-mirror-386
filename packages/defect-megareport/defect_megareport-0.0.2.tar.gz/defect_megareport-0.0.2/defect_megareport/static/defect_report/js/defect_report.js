(function() {
    const Config = {
        apiUrls: {
            plans: '/api/v2/testplans/',
            defectReport: '/plugins/defect-megareport/api/defect-megareport/',
            customAttributes: '/api/v2/custom-attributes/',
            jiraPrefix: 'https://jira-example.com/browse/'
        },

        pagination: {
            defaultPageSize: 20,
            availablePageSizes: [20, 50, 100]
        },

        excludedColumns: [
            'plan_id',
            'plan_breadcrumbs',
            'defect_status',
            'result_id',
            'test_id',
            'result_status_color',
            'latest_result_status',
            'latest_result_color',
            'result_rank',
        ]
    };

    const URLManager = {
        updateURL: function() {
            const params = new URLSearchParams();

            const projectId = UI.elements.projectSelect?.value;
            if (projectId) {
                params.set('project', projectId);
            }

            if (AppState.selectedPlanId !== null && AppState.selectedPlanId !== undefined) {
                params.set('plan', AppState.selectedPlanId);
            }

            if (AppState.selectedAttributeNames && AppState.selectedAttributeNames.length > 0) {
                AppState.selectedAttributeNames.forEach(attr => {
                    params.append('attributes', attr);
                });
            }

            if (AppState.currentPageSize !== Config.pagination.defaultPageSize) {
                params.set('pageSize', AppState.currentPageSize);
            }

            if (AppState.searchText) {
                params.set('search', AppState.searchText);
            }

            if (AppState.resultFilter && AppState.resultFilter !== 'all') {
                params.set('filter', AppState.resultFilter);
            }

            const newURL = params.toString() ? `${window.location.pathname}?${params.toString()}` : window.location.pathname;
            window.history.replaceState(null, '', newURL);
        },

        parseURLParams: function() {
            const params = new URLSearchParams(window.location.search);
            const state = {};

            state.projectId = params.get('project');
            state.planId = params.get('plan');
            state.attributeNames = params.getAll('attributes');
            state.pageSize = params.get('pageSize');
            state.searchText = params.get('search') || '';
            state.resultFilter = params.get('filter') || 'all';

            return state;
        },

        restoreStateFromURL: async function() {
            const urlState = this.parseURLParams();

            if (!urlState.projectId) {
                return;
            }

            if (UI.elements.projectSelect) {
                UI.elements.projectSelect.value = urlState.projectId;

                if (urlState.pageSize) {
                    const pageSize = parseInt(urlState.pageSize);
                    if (Config.pagination.availablePageSizes.includes(pageSize)) {
                        AppState.currentPageSize = pageSize;
                        UI.elements.pageSizeButtons.forEach(button => {
                            button.classList.remove('active');
                            if (parseInt(button.dataset.pageSize) === pageSize) {
                                button.classList.add('active');
                            }
                        });
                    }
                }

                if (urlState.searchText && UI.elements.searchInput) {
                    AppState.searchText = urlState.searchText;
                    UI.elements.searchInput.value = urlState.searchText;
                }

                if (urlState.resultFilter) {
                    AppState.resultFilter = urlState.resultFilter;
                    UI.elements.resultFilterRadios.forEach(radio => {
                        if (radio.value === urlState.resultFilter) {
                            radio.checked = true;
                        }
                    });
                }

                UI.elements.attributeFilterContainer.style.display = 'block';
                UI.elements.planFilterContainer.style.display = 'block';
                UI.elements.searchContainer.style.display = 'block';
                UI.elements.resultFilterContainer.style.display = 'block';

                try {
                    const attributesData = await DataFetcher.loadCustomAttributes(urlState.projectId);
                    const attributes = DataProcessor.processCustomAttributes(attributesData);
                    DataProcessor.fillAttributeSelect(UI.elements.attributeSelect, attributes);
                    UI.elements.attributeSelect.disabled = false;

                    if (urlState.attributeNames && urlState.attributeNames.length > 0) {
                        AppState.selectedAttributeNames = urlState.attributeNames;
                        Array.from(UI.elements.attributeSelect.options).forEach(option => {
                            option.selected = urlState.attributeNames.includes(option.value);
                        });
                    } else {
                        const defaultAttribute = DataProcessor.getDefaultAttribute(attributes);
                        if (defaultAttribute) {
                            AppState.selectedAttributeNames = [defaultAttribute];
                            Array.from(UI.elements.attributeSelect.options).forEach(option => {
                                option.selected = option.value === defaultAttribute;
                            });
                        }
                    }

                    UI.elements.loadingPlans.style.display = 'block';
                    const plansData = await DataFetcher.loadPlans(urlState.projectId);
                    UI.elements.loadingPlans.style.display = 'none';

                    if (plansData.results && Array.isArray(plansData.results)) {
                        const plansTree = DataProcessor.buildPlansTree(plansData.results);
                        Renderer.renderPlansTree(plansTree, UI.elements.plansTreeContainer, planId => {
                            AppState.selectedPlanId = planId;
                            URLManager.updateURL();
                            DataFetcher.loadDefectReport();
                        });

                        if (urlState.planId) {
                            AppState.selectedPlanId = parseInt(urlState.planId);

                            const planElement = document.querySelector(`[data-plan-id="${AppState.selectedPlanId}"]`);
                            if (planElement) {
                                const selectedNodes = document.querySelectorAll('.tree-node-content.selected');
                                selectedNodes.forEach(node => node.classList.remove('selected'));
                                planElement.classList.add('selected');

                                let parent = planElement.closest('.tree-children');
                                while (parent) {
                                    parent.classList.add('expanded');
                                    const toggle = parent.parentElement.querySelector('.tree-toggle');
                                    if (toggle) {
                                        toggle.textContent = '-';
                                    }
                                    parent = parent.parentElement.closest('.tree-children');
                                }
                            }

                            DataFetcher.loadDefectReport();
                        }
                    }

                } catch (error) {
                    console.error('Ошибка при восстановлении состояния из URL:', error);
                }
            }
        }
    };

    const AppState = {
        defaultAttribute: 'Defect',
        selectedPlanId: null,
        selectedAttributeNames: [],
        currentPageSize: Config.pagination.defaultPageSize,
        searchText: '',
        resultFilter: 'all',

        reset: function() {
            this.selectedPlanId = null;
            this.selectedAttributeNames = [];
            this.searchText = '';
            this.resultFilter = 'all';
            this.defaultAttribute = 'Defect';
            URLManager.updateURL();
        }
    };

    const UI = {
        elements: {
            projectSelect: null,
            attributeFilterContainer: null,
            attributeSelect: null,
            planFilterContainer: null,
            plansTreeContainer: null,
            loadingPlans: null,
            contentContainer: null,
            paginationContainer: null,
            paginationList: null,
            paginationInfo: null,
            pageSizeButtons: null,
            contentElement: null,
            resultFilterContainer: null,
            resultFilterRadios: null
        },

        init: function() {
            this.cacheElements();
            this.setupEventListeners();
            this.setupPageSizeButtons();

            setTimeout(() => {
                URLManager.restoreStateFromURL();
            }, 0);
        },

        cacheElements: function() {
            this.elements.projectSelect = document.getElementById('project-select');
            this.elements.attributeFilterContainer = document.getElementById('attribute-filter-container');
            this.elements.attributeSelect = document.getElementById('attribute-select');
            this.elements.planFilterContainer = document.getElementById('plan-filter-container');
            this.elements.plansTreeContainer = document.querySelector('.plans-tree-container');
            this.elements.loadingPlans = document.querySelector('.loading-plans');
            this.elements.contentContainer = document.getElementById('content-container');
            this.elements.paginationContainer = document.getElementById('pagination-container');
            this.elements.paginationList = document.getElementById('pagination-list');
            this.elements.paginationInfo = document.getElementById('pagination-info');
            this.elements.pageSizeButtons = document.querySelectorAll('.page-size-selector button');
            this.elements.contentElement = document.getElementById('defect-megareport-content');
            this.elements.searchContainer = document.getElementById('search-container');
            this.elements.searchInput = document.getElementById('search-input');
            this.elements.searchButton = document.getElementById('search-button');
            this.elements.resultFilterContainer = document.getElementById('result-filter-container');
            this.elements.resultFilterRadios = document.querySelectorAll('input[name="result-filter"]');
        },

        setupEventListeners: function() {
            this.elements.projectSelect.addEventListener('change', EventHandlers.onProjectChange);
            this.elements.attributeSelect.addEventListener('change', EventHandlers.onAttributeChange);

            this.elements.searchButton.addEventListener('click', EventHandlers.onSearchButtonClick);
            this.elements.searchInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    EventHandlers.onSearchButtonClick();
                }
            });

            this.elements.resultFilterRadios.forEach(radio => {
                radio.addEventListener('change', EventHandlers.onResultFilterChange);
            });
        },

        setupPageSizeButtons: function() {
            this.elements.pageSizeButtons.forEach(button => {
                const pageSize = parseInt(button.dataset.pageSize);
                if (pageSize === AppState.currentPageSize) {
                    button.classList.add('active');
                }

                button.addEventListener('click', function() {
                    UI.elements.pageSizeButtons.forEach(btn => btn.classList.remove('active'));
                    this.classList.add('active');

                    const newPageSize = parseInt(this.dataset.pageSize);

                    if (newPageSize !== AppState.currentPageSize) {
                        AppState.currentPageSize = newPageSize;
                        URLManager.updateURL();
                        DataFetcher.loadDefectReport();
                    }
                });
            });
        },

        showLoading: function(element) {
            if (element) {
                element.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="sr-only">Загрузка...</span></div></div>';
            }
        },

        showError: function(element, message) {
            if (element) {
                element.innerHTML = `<p class="text-danger">Ошибка: ${message || 'При загрузке данных произошла ошибка. Пожалуйста, попробуйте еще раз.'}</p>`;
            }
        },

        showEmptyMessage: function(element, message) {
            if (element) {
                element.innerHTML = `<p>${message || 'Нет данных для отображения'}</p>`;
            }
        }
    };

    const EventHandlers = {
        onProjectChange: function() {
            const projectId = UI.elements.projectSelect.value;

            if (projectId) {
                UI.elements.attributeFilterContainer.style.display = 'block';
                UI.elements.attributeSelect.innerHTML = '<option value="">Загрузка...</option>';
                UI.elements.attributeSelect.disabled = true;

                UI.elements.planFilterContainer.style.display = 'block';
                UI.elements.searchContainer.style.display = 'block';
                UI.elements.resultFilterContainer.style.display = 'block';

                UI.elements.loadingPlans.style.display = 'block';
                UI.elements.plansTreeContainer.innerHTML = '';

                const attributesPromise = DataFetcher.loadCustomAttributes(projectId)
                    .then(data => {
                        const attributes = DataProcessor.processCustomAttributes(data);
                        DataProcessor.fillAttributeSelect(UI.elements.attributeSelect, attributes);

                        UI.elements.attributeSelect.disabled = false;

                        const selectedAttribute = DataProcessor.getDefaultAttribute(attributes);
                        if (selectedAttribute) {
                            AppState.selectedAttributeNames = [selectedAttribute];
                            Array.from(UI.elements.attributeSelect.options).forEach(option => {
                                option.selected = option.value === selectedAttribute;
                            });
                        } else {
                            AppState.selectedAttributeNames = [];
                        }
                    })
                    .catch(error => {
                        console.error('Ошибка загрузки атрибутов:', error);
                        UI.elements.attributeSelect.innerHTML = '<option value="">Ошибка загрузки</option>';
                        UI.elements.attributeSelect.disabled = true;
                        AppState.selectedAttributeNames = [];
                    });

                const plansPromise = DataFetcher.loadPlans(projectId)
                    .then(data => {
                        UI.elements.loadingPlans.style.display = 'none';

                        if (data.results && Array.isArray(data.results)) {
                            const plansTree = DataProcessor.buildPlansTree(data.results);
                            Renderer.renderPlansTree(plansTree, UI.elements.plansTreeContainer, planId => {
                                AppState.selectedPlanId = planId;
                                URLManager.updateURL();
                                DataFetcher.loadDefectReport();
                            });
                        } else {
                            UI.elements.plansTreeContainer.innerHTML = '<div class="no-plans">Планы не найдены</div>';
                        }
                    })
                    .catch(error => {
                        console.error('Ошибка загрузки планов:', error);
                        UI.elements.loadingPlans.style.display = 'none';
                        UI.elements.plansTreeContainer.innerHTML = '<div class="error">Ошибка при загрузке планов</div>';
                    });

                UI.elements.contentContainer.style.display = 'none';
                AppState.selectedPlanId = null;
                AppState.searchText = '';
                AppState.resultFilter = 'all';
                AppState.selectedAttributeNames = [];
                UI.elements.searchInput.value = '';

                UI.elements.resultFilterRadios.forEach(radio => {
                    if (radio.value === 'all') {
                        radio.checked = true;
                    } else {
                        radio.checked = false;
                    }
                });

                URLManager.updateURL();

            } else {
                UI.elements.attributeFilterContainer.style.display = 'none';
                UI.elements.planFilterContainer.style.display = 'none';
                UI.elements.contentContainer.style.display = 'none';
                UI.elements.searchContainer.style.display = 'none';
                UI.elements.resultFilterContainer.style.display = 'none';

                AppState.reset();
            }
        },

        onAttributeChange: function() {
            const selectedOptions = Array.from(UI.elements.attributeSelect.selectedOptions);
            AppState.selectedAttributeNames = selectedOptions.map(option => option.value).filter(value => value);

            URLManager.updateURL();
            DataFetcher.loadDefectReport();
        },

        onPageChange: function(pageOrUrl) {
            if (typeof pageOrUrl === 'string') {
                DataFetcher.loadDefectReport(pageOrUrl);
            } else {
                DataFetcher.loadDefectReport(null, pageOrUrl);
            }
        },

        onSearchButtonClick: function() {
            const searchText = UI.elements.searchInput.value.trim();
            AppState.searchText = searchText;
            URLManager.updateURL();
            DataFetcher.loadDefectReport();
        },

        onResultFilterChange: function() {
            const selectedFilter = document.querySelector('input[name="result-filter"]:checked')?.value || 'all';
            AppState.resultFilter = selectedFilter;
            URLManager.updateURL();
            DataFetcher.loadDefectReport();
        }
    };

    const DataFetcher = {
        loadCustomAttributes: function(projectId) {
            return fetch(`${Config.apiUrls.customAttributes}?project=${projectId}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                });
        },

        loadPlans: function(projectId) {
            return fetch(`${Config.apiUrls.plans}?project=${projectId}&page_size=10000`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                });
        },

        loadDefectReport: function(url = null, page = null) {
            if (!url && (AppState.selectedPlanId === null || AppState.selectedPlanId === undefined)) {
                return;
            }

            UI.elements.contentContainer.style.display = 'block';
            UI.showLoading(UI.elements.contentElement);

            UI.elements.paginationContainer.style.display = 'none';
            UI.elements.paginationInfo.style.display = 'none';

            if (!url) {
                url = `${Config.apiUrls.defectReport}?project_id=${UI.elements.projectSelect.value}`;

                if (AppState.selectedPlanId !== 0) {
                    url += `&plan_id=${AppState.selectedPlanId}`;
                }

                url += `&page_size=${AppState.currentPageSize}`;

                if (AppState.selectedAttributeNames && AppState.selectedAttributeNames.length > 0) {
                    AppState.selectedAttributeNames.forEach(attributeName => {
                        url += `&attributes=${encodeURIComponent(attributeName)}`;
                    });
                } else {
                    url += `&attributes=${AppState.defaultAttribute}`;
                }

                if (AppState.searchText) {
                    url += `&search=${encodeURIComponent(AppState.searchText)}`;
                }

                if (AppState.resultFilter === 'last-defects' || AppState.resultFilter === 'last-test-results') {
                    url += `&just_last_result=true`;
                }

                if (page) {
                    url += `&page=${page}`;
                }
            }

            fetch(url)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    return response.json();
                })
                .then(data => {
                    this.handleDefectReportResponse(data);
                })
                .catch(error => {
                    console.error('Ошибка загрузки данных:', error);
                    UI.showError(UI.elements.contentElement);
                    UI.elements.paginationContainer.style.display = 'none';
                    UI.elements.paginationInfo.style.display = 'none';
                });
        },

        handleDefectReportResponse: function(data) {
            const resultsData = data.results || [];

            if (resultsData.length > 0) {
                const topPaginationBlock = Renderer.createPaginationBlock(data, EventHandlers.onPageChange);

                const tableContainer = document.createElement('div');
                Renderer.renderDataTable(resultsData, tableContainer);

                const bottomPaginationBlock = Renderer.createPaginationBlock(data, EventHandlers.onPageChange);

                UI.elements.contentElement.innerHTML = '';
                UI.elements.contentElement.appendChild(topPaginationBlock);
                UI.elements.contentElement.appendChild(tableContainer);
                UI.elements.contentElement.appendChild(bottomPaginationBlock);

                UI.elements.paginationContainer.style.display = 'none';
                UI.elements.paginationInfo.style.display = 'none';
            } else {
                UI.showEmptyMessage(UI.elements.contentElement);
                UI.elements.paginationContainer.style.display = 'none';
                UI.elements.paginationInfo.style.display = 'none';
            }
        }
    };

    const DataProcessor = {
        processCustomAttributes: function(data) {
            if (!Array.isArray(data)) {
                return [];
            }

            const activeAttributes = data

            return activeAttributes.sort((a, b) => a.name.localeCompare(b.name));
        },

        fillAttributeSelect: function(select, attributes) {
            select.innerHTML = '';
            select.multiple = true;
            select.size = Math.min(attributes.length + 1, 8);

            attributes.forEach(attribute => {
                const option = document.createElement('option');
                option.value = attribute.name;
                option.textContent = attribute.name;
                select.appendChild(option);
            });

            return null;
        },

        getDefaultAttribute: function(attributes) {
            const defectsAttribute = attributes.find(attr => attr.name === "Defects");
            return defectsAttribute ? defectsAttribute.name : null;
        },

        buildPlansTree: function(plans) {
            const plansMap = {};

            plans.forEach(plan => {
                plansMap[plan.id] = {
                    ...plan,
                    children: []
                };
            });

            const rootNodes = [];
            plans.forEach(plan => {
                if (plan.parent) {
                    const parentId = plan.parent.id;
                    if (plansMap[parentId]) {
                        plansMap[parentId].children.push(plansMap[plan.id]);
                    } else {
                        rootNodes.push(plansMap[plan.id]);
                    }
                } else {
                    rootNodes.push(plansMap[plan.id]);
                }
            });

            const allNode = {
                id: 0,
                name: 'All',
                children: rootNodes
            };

            return [allNode];
        },

        formatHeader: function(header) {
            return header.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        },

        formatCellValue: function(header, value, row) {
            if (value === null) {
                return '-';
            }

            switch (header) {
                case 'result_date':
                    if (value) {
                        const date = new Date(value);
                        return date.toLocaleString('sv-SE', {
                            year: 'numeric',
                            month: '2-digit',
                            day: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit'
                        });
                    }
                    return value;


                case 'defect':
                    if (value) {
                        return `<a href="${Config.apiUrls.jiraPrefix}${value}" target="_blank">${value}</a>`;
                    }
                    return value;

                case 'test_name':
                    if (value && row.test_id) {
                        const projectId = UI.elements.projectSelect.value;
                        const testId = row.test_id;
                        const resultId = row.result_id;
                        return `<a href="/projects/${projectId}/plans/${row.plan_id}?test=${testId}#result-${resultId}" target="_blank">${value}</a>`;
                    }
                    return value;

                case 'result_status':
                    let statusValue = value;
                    let colorValue = row.result_status_color;

                    if (AppState.resultFilter === 'last-test-results') {
                        statusValue = row.latest_result_status;
                        colorValue = row.latest_result_color;
                    }

                    return `<span class="status_button" style="background-color:${colorValue}">${statusValue}</span>`

                case 'plan_name':
                    return `<div><div>${value}</div><div class="plan_breadcrumbs">${row.plan_breadcrumbs}</div></div>`

                default:
                    return value;
            }
        },

        getVisibleHeaders: function(headers) {
            return headers.filter(header => !Config.excludedColumns.includes(header));
        }
    };

    const Renderer = {
        renderPlansTree: function(nodes, container, onPlanSelect, level = 0) {
            nodes.forEach(node => {
                const hasChildren = node.children && node.children.length > 0;

                const nodeElement = document.createElement('div');
                nodeElement.className = 'tree-node';

                const nodeContent = document.createElement('div');
                nodeContent.className = 'tree-node-content';
                nodeContent.dataset.planId = node.id;

                if (hasChildren) {
                    const toggle = document.createElement('span');
                    toggle.className = 'tree-toggle';
                    toggle.textContent = '+';
                    toggle.onclick = function(e) {
                        e.stopPropagation();
                        const childrenContainer = nodeElement.querySelector('.tree-children');
                        if (childrenContainer.classList.contains('expanded')) {
                            childrenContainer.classList.remove('expanded');
                            toggle.textContent = '+';
                        } else {
                            childrenContainer.classList.add('expanded');
                            toggle.textContent = '-';
                        }
                    };
                    nodeContent.appendChild(toggle);
                } else {
                    const leaf = document.createElement('span');
                    leaf.className = 'tree-leaf';
                    leaf.innerHTML = '&nbsp;&nbsp;';
                    nodeContent.appendChild(leaf);
                }

                const nameSpan = document.createElement('span');
                nameSpan.textContent = node.name;
                nodeContent.appendChild(nameSpan);

                nodeContent.onclick = function() {
                    const selectedNodes = document.querySelectorAll('.tree-node-content.selected');
                    selectedNodes.forEach(node => node.classList.remove('selected'));

                    nodeContent.classList.add('selected');

                    if (onPlanSelect) {
                        onPlanSelect(node.id);
                    }
                };

                nodeElement.appendChild(nodeContent);

                if (hasChildren) {
                    const childrenContainer = document.createElement('div');
                    childrenContainer.className = 'tree-children';
                    this.renderPlansTree(node.children, childrenContainer, onPlanSelect, level + 1);
                    nodeElement.appendChild(childrenContainer);
                }

                container.appendChild(nodeElement);
            });
        },

        renderDataTable: function(resultsData, container) {
            let html = '<div class="table-responsive"><table class="table table-striped"><thead><tr>';

            const allHeaders = Object.keys(resultsData[0]);
            const visibleHeaders = DataProcessor.getVisibleHeaders(allHeaders);

            visibleHeaders.forEach(header => {
                const formattedHeader = DataProcessor.formatHeader(header);
                html += `<th>${formattedHeader}</th>`;
            });

            html += '</tr></thead><tbody>';

            resultsData.forEach(row => {
                html += '<tr>';
                visibleHeaders.forEach(header => {
                    let value = DataProcessor.formatCellValue(header, row[header], row);
                    html += `<td>${value}</td>`;
                });
                html += '</tr>';
            });

            html += '</tbody></table></div>';
            container.innerHTML = html;
        },

        createPaginationBlock: function(data, onPageChange) {
            const paginationBlock = document.createElement('div');
            paginationBlock.className = 'pagination-block d-flex justify-content-between align-items-center mb-3';

            const infoDiv = document.createElement('div');
            infoDiv.className = 'pagination-info';

            if (data.count && data.pages && data.pages.current) {
                const currentPage = data.pages.current;
                const totalPages = data.pages.total;
                const totalCount = data.count;

                infoDiv.textContent = `Страница ${currentPage} из ${totalPages} (всего ${totalCount} элементов)`;

                const paginationNav = document.createElement('nav');
                paginationNav.setAttribute('aria-label', 'Навигация по страницам');

                const paginationList = document.createElement('ul');
                paginationList.className = 'pagination pagination-sm justify-content-center mb-0';

                if (data.previous) {
                    const prevItem = document.createElement('li');
                    prevItem.className = 'page-item';
                    const prevLink = document.createElement('a');
                    prevLink.className = 'page-link';
                    prevLink.href = '#';
                    prevLink.textContent = 'Предыдущая';
                    prevLink.onclick = function(e) {
                        e.preventDefault();
                        onPageChange(data.previous);
                    };
                    prevItem.appendChild(prevLink);
                    paginationList.appendChild(prevItem);
                }

                const maxVisiblePages = 5;
                let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
                let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

                if (endPage - startPage < maxVisiblePages - 1) {
                    startPage = Math.max(1, endPage - maxVisiblePages + 1);
                }

                for (let i = startPage; i <= endPage; i++) {
                    const pageItem = document.createElement('li');
                    pageItem.className = 'page-item' + (i === currentPage ? ' active' : '');
                    const pageLink = document.createElement('a');
                    pageLink.className = 'page-link';
                    pageLink.href = '#';
                    pageLink.textContent = i;
                    pageLink.onclick = function(e) {
                        e.preventDefault();
                        onPageChange(i);
                    };
                    pageItem.appendChild(pageLink);
                    paginationList.appendChild(pageItem);
                }

                if (data.next) {
                    const nextItem = document.createElement('li');
                    nextItem.className = 'page-item';
                    const nextLink = document.createElement('a');
                    nextLink.className = 'page-link';
                    nextLink.href = '#';
                    nextLink.textContent = 'Следующая';
                    nextLink.onclick = function(e) {
                        e.preventDefault();
                        onPageChange(data.next);
                    };
                    nextItem.appendChild(nextLink);
                    paginationList.appendChild(nextItem);
                }

                paginationNav.appendChild(paginationList);
                paginationBlock.appendChild(infoDiv);
                paginationBlock.appendChild(paginationNav);
            }

            return paginationBlock;
        }
    };

    document.addEventListener('DOMContentLoaded', function() {
        UI.init();
    });

})();