document.addEventListener('DOMContentLoaded', function () {
    const planForm = document.getElementById('plan-form');
    const resultModal = document.getElementById('result-modal');
    const resultText = document.getElementById('result-text');
    const savePlanBtn = document.getElementById('save-plan-btn');
    // Make the selector more specific to the result modal
    const closeBtn = resultModal ? resultModal.querySelector('.close-btn') : null;
    
    if (planForm) {
        planForm.addEventListener('submit', function (event) {
            event.preventDefault();

            // Show modal immediately with "Generating..." text and disable save button
            if (resultModal && resultText) {
                resultText.innerHTML = '生成中...';
                resultModal.style.display = 'flex';
                if (savePlanBtn) {
                    savePlanBtn.disabled = true;
                }
            }

            const formData = new FormData(planForm);

            fetch('/generate', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (!resultText) return;

                if (data.error) {
                    resultText.innerHTML = `<p style="color: red;">生成计划失败: ${data.error}</p>`;
                    if (savePlanBtn) savePlanBtn.disabled = true; // Keep disabled on error
                } else {
                    const converter = new showdown.Converter();
                    const html = converter.makeHtml(data.plan);
                    resultText.innerHTML = html;
                    // Always enable the save button on success, as the click handler will check for auth
                    if (savePlanBtn) savePlanBtn.disabled = false; 
                }
            })
            .catch(error => {
                if (resultText) {
                    resultText.innerHTML = '<p style="color: red;">发生未知错误，请稍后重试。</p>';
                }
                if (savePlanBtn) savePlanBtn.disabled = true; // Keep disabled on error
                console.error('Error:', error);
            });
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', function () {
            if (resultModal) {
                resultModal.style.display = 'none';
            }
        });
    }

    window.addEventListener('click', function (event) {
        if (event.target == resultModal) {
            resultModal.style.display = 'none';
        }
    });
});