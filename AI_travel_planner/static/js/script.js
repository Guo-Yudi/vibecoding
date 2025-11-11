document.addEventListener('DOMContentLoaded', function () {
    const planForm = document.getElementById('plan-form');
    const loaderModal = document.getElementById('loader-modal');
    const resultModal = document.getElementById('result-modal');
    const resultText = document.getElementById('result-text');
    const closeBtn = document.querySelector('.close-btn');

    if (planForm) {
        planForm.addEventListener('submit', function (event) {
            event.preventDefault();
            loaderModal.style.display = 'flex';

            const formData = new FormData(planForm);

            fetch('/generate', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                loaderModal.style.display = 'none';
                if (data.error) {
                    alert('Error: ' + data.error);
                } else {
                    const converter = new showdown.Converter();
                    const html = converter.makeHtml(data.plan);
                    resultText.innerHTML = html;
                    resultModal.style.display = 'flex';
                }
            })
            .catch(error => {
                loaderModal.style.display = 'none';
                alert('An error occurred. Please try again.');
                console.error('Error:', error);
            });
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', function () {
            resultModal.style.display = 'none';
        });
    }

    window.addEventListener('click', function (event) {
        if (event.target == resultModal) {
            resultModal.style.display = 'none';
        }
    });
});