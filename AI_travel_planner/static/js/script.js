document.getElementById('planner-form').addEventListener('submit', function(event) {
    event.preventDefault();

    const form = event.target;
    const data = {
        destination: form.destination.value,
        duration: form.duration.value,
        budget: form.budget.value,
        preferences: form.preferences.value
    };

    const loading = document.getElementById('loading');
    const result = document.getElementById('result');
    const planOutput = document.getElementById('plan-output');

    loading.style.display = 'block';
    result.style.display = 'none';

    fetch('/plan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        loading.style.display = 'none';
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            planOutput.textContent = data.plan;
            result.style.display = 'block';
        }
    })
    .catch(error => {
        loading.style.display = 'none';
        alert('An error occurred. Please try again.');
        console.error('Error:', error);
    });
});

function route() {
    const start = document.getElementById('start').value;
    const end = document.getElementById('end').value;

    if (!start || !end) {
        alert('请输入起点和终点');
        return;
    }

    map.clearOverlays();
    const driving = new BMap.DrivingRoute(map, {
        renderOptions: { map: map, autoViewport: true },
        onSearchComplete: function (results) {
            if (driving.getStatus() == BMAP_STATUS_SUCCESS) {
                const plan = results.getPlan(0);
                let output = "";
                for (let i = 0; i < plan.getNumRoutes(); i++) {
                    const route = plan.getRoute(i);
                    output += `路线${i + 1}: ${route.getDistance(true)} (${route.getDuration(true)})\n`;
                }
                document.getElementById('plan-output').innerText += "\n" + output;
            }
        }
    });
    driving.search(start, end);
}