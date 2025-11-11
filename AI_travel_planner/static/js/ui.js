document.addEventListener('DOMContentLoaded', () => {
    // Auth Modal Logic
    const authModal = document.getElementById('auth-modal');
    const loginBtn = document.getElementById('login-btn');
    const signupBtn = document.getElementById('signup-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const closeModalBtn = document.querySelector('.auth-close');
    const authForm = document.getElementById('auth-form');
    const authTitle = document.getElementById('auth-title');
    const authSubmitBtn = document.getElementById('auth-submit-btn');
    let isLoginMode = true;

    const openModal = (loginMode) => {
        isLoginMode = loginMode;
        authTitle.textContent = isLoginMode ? '登录' : '注册';
        authSubmitBtn.textContent = isLoginMode ? '登录' : '注册';
        authModal.style.display = 'flex';
    };

    const closeModal = () => {
        authModal.style.display = 'none';
    };

    if(loginBtn) loginBtn.addEventListener('click', () => openModal(true));
    if(signupBtn) signupBtn.addEventListener('click', () => openModal(false));
    if(closeModalBtn) closeModalBtn.addEventListener('click', closeModal);
    if(logoutBtn) logoutBtn.addEventListener('click', () => signOutUser());

    if(authForm) authForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('auth-email').value;
        const password = document.getElementById('auth-password').value;
        if (isLoginMode) {
            await signInUser(email, password);
        } else {
            await signUpUser(email, password);
        }
        closeModal();
    });

    // Plan Management Logic
    const savePlanBtn = document.getElementById('save-plan-btn');
    const myPlansBtn = document.getElementById('my-plans-btn');
    const plansModal = document.getElementById('plans-modal');
    const closePlansModalBtn = document.querySelector('.plans-close');
    const plansList = document.getElementById('plans-list');
    const aiResponseDiv = document.getElementById('ai-response');

    if(savePlanBtn) savePlanBtn.addEventListener('click', () => {
        const planContent = aiResponseDiv.innerHTML;
        if (!planContent.trim()) {
            alert('当前没有可以保存的旅行计划。');
            return;
        }
        const planTitle = prompt('请输入计划标题：', '我的新旅行计划');
        if (planTitle) {
            saveTravelPlan(planTitle, planContent);
        }
    });

    if(myPlansBtn) myPlansBtn.addEventListener('click', async () => {
        const plans = await fetchUserPlans();
        plansList.innerHTML = '';
        if (plans && plans.length > 0) {
            plans.forEach(plan => {
                const planElement = document.createElement('div');
                planElement.classList.add('plan-item');
                planElement.dataset.planId = plan.id;
                planElement.innerHTML = `
                    <h4>${plan.title}</h4>
                    <p>创建于: ${new Date(plan.created_at).toLocaleString()}</p>
                `;
                plansList.appendChild(planElement);
            });
        } else {
            plansList.innerHTML = '<p>您还没有保存任何计划。</p>';
        }
        plansModal.style.display = 'flex';
    });

    if(closePlansModalBtn) closePlansModalBtn.addEventListener('click', () => {
        plansModal.style.display = 'none';
    });

    if(plansList) plansList.addEventListener('click', async (e) => {
        const planItem = e.target.closest('.plan-item');
        if (planItem) {
            const planId = planItem.dataset.planId;
            const planDetails = await fetchPlanDetails(planId);
            if (planDetails) {
                aiResponseDiv.innerHTML = planDetails.plan_content;
                plansModal.style.display = 'none';
            }
        }
    });

    // Close modals on outside click
    window.addEventListener('click', (event) => {
        if (event.target == authModal) {
            authModal.style.display = 'none';
        }
        if (event.target == plansModal) {
            plansModal.style.display = 'none';
        }
    });
});