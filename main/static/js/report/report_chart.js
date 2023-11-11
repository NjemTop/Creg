const chartDataTag = document.getElementById('report-data-tag');
const chartData = JSON.parse(chartDataTag.textContent);

let causeCount = {};
chartData.forEach(entry => {
    const cause = entry.cause;
    causeCount[cause] = (causeCount[cause] || 0) + 1;
});

const ctx = document.getElementById('chart').getContext('2d');
const chart = new Chart(ctx, {
    type: 'pie',
    data: {
        labels: Object.keys(causeCount),
        datasets: [{
            data: Object.values(causeCount),
            backgroundColor: [
                '#FF6384',
                '#36A2EB',
                '#FFCE56',
                '#4BC0C0',
                '#9966FF',
                '#FF9F40',
                '#808080',
            ],
            borderColor: [
                '#FF6384',
                '#36A2EB',
                '#FFCE56',
                '#4BC0C0',
                '#9966FF',
                '#FF9F40',
                '#808080',
            ],
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const total = context.dataset.data.reduce((a, b) => a + b);
                        const value = context.raw;
                        const percentage = ((value / total) * 100).toFixed(2);
                        return `${value} (${percentage}%)`;
                    }
                }
            },
            legend: {
                position: 'right', // положение легенды: 'top', 'right', 'bottom' или 'left'
                labels: {
                    boxWidth: 20, // ширина блока метки
                    padding: 10, // отступ между метками
                }
            }
        },
        layout: {
            padding: {
                left: 0,
                right: 0,
                top: 0,
                bottom: 0
            }
        },
    }
});


const moduleData = {}; // Подготовка объекта для подсчета модулей

chartData.forEach(entry => {
    const module = entry.module_boardmaps;
    moduleData[module] = (moduleData[module] || 0) + 1;
});

const ctxModules = document.getElementById('chart-modules').getContext('2d');
const chartModules = new Chart(ctxModules, {
    type: 'pie',
    data: {
        labels: Object.keys(moduleData),
        datasets: [{
            data: Object.values(moduleData),
            backgroundColor: [
                '#FF6384',
                '#36A2EB',
                '#FFCE56',
                '#4BC0C0',
                '#9966FF',
                '#FF9F40',
                '#808080',
            ],
            borderColor: [
                '#FF6384',
                '#36A2EB',
                '#FFCE56',
                '#4BC0C0',
                '#9966FF',
                '#FF9F40',
                '#808080',
            ],
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const total = context.dataset.data.reduce((a, b) => a + b);
                        const value = context.raw;
                        const percentage = ((value / total) * 100).toFixed(2);
                        return `${value} (${percentage}%)`;
                    }
                }
            },
            legend: {
                position: 'right', // положение легенды: 'top', 'right', 'bottom' или 'left'
                labels: {
                    boxWidth: 20, // ширина блока метки
                    padding: 10, // отступ между метками
                }
            }
        },
        layout: {
            padding: {
                left: 0,
                right: 0,
                top: 0,
                bottom: 0
            }
        },
    }
});


// Функция для сортировки легенды графика "Причины возникновения"
function sortLegend() {
    const dataset = chart.data.datasets[0];
    const labels = chart.data.labels;
    const data = dataset.data;

    const dataArray = labels.map((label, index) => ({
        label: label,
        data: data[index],
        backgroundColor: dataset.backgroundColor[index],
        borderColor: dataset.borderColor[index]
    }));

    dataArray.sort((a, b) => b.data - a.data);

    labels.length = 0;
    data.length = 0;
    dataset.backgroundColor.length = 0;
    dataset.borderColor.length = 0;

    dataArray.forEach(item => {
        labels.push(item.label);
        data.push(item.data);
        dataset.backgroundColor.push(item.backgroundColor);
        dataset.borderColor.push(item.borderColor);
    });

    chart.update();
}

// Вызовите функцию сортировки легенды после создания графика "Причины возникновения"
sortLegend();

// Функция для сортировки легенды графика "Модули"
function sortModuleLegend() {
    const datasetModules = chartModules.data.datasets[0];
    const labelsModules = chartModules.data.labels;
    const dataModules = datasetModules.data;

    const dataArrayModules = labelsModules.map((label, index) => ({
        label: label,
        data: dataModules[index],
        backgroundColor: datasetModules.backgroundColor[index],
        borderColor: datasetModules.borderColor[index]
    }));

    dataArrayModules.sort((a, b) => b.data - a.data);

    labelsModules.length = 0;
    dataModules.length = 0;
    datasetModules.backgroundColor.length = 0;
    datasetModules.borderColor.length = 0;

    dataArrayModules.forEach(item => {
        labelsModules.push(item.label);
        dataModules.push(item.data);
        datasetModules.backgroundColor.push(item.backgroundColor);
        datasetModules.borderColor.push(item.borderColor);
    });

    chartModules.update();
}

// Вызовите функцию сортировки легенды после создания графика "Модули"
sortModuleLegend();
