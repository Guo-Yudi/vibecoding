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
    const usernameGroup = document.getElementById('username-group');
    let isLoginMode = true;

    const openModal = (loginMode) => {
        isLoginMode = loginMode;
        authTitle.textContent = isLoginMode ? '登录' : '注册';
        authSubmitBtn.textContent = isLoginMode ? '登录' : '注册';
        usernameGroup.style.display = isLoginMode ? 'none' : 'block';
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
            const username = document.getElementById('auth-username').value;
            if (!username) {
                alert('请输入用户名！');
                return;
            }
            await signUpUser(email, password, username);
        }
        closeModal();
    });

    // Plan Management Logic
    const savePlanBtn = document.getElementById('save-plan-btn');
    const myPlansBtn = document.getElementById('my-plans-btn');
    const plansModal = document.getElementById('plans-modal');
    const closePlansModalBtn = document.querySelector('.plans-close');
    const plansList = document.getElementById('plans-list');
    const aiResponseDiv = document.getElementById('result-text');
    const generatePlanBtn = document.getElementById('generate-plan-btn');
    const planActionsContainer = document.getElementById('plan-actions');
    // Assuming a new result modal exists for editing, as per instructions.
    const resultModal = document.getElementById('result-modal');

    let currentEditingPlanId = null; // To track the plan being edited

    /**
     * Enters plan editing mode.
     * @param {object} plan - The plan object to edit.
     */
    function enterEditMode(plan) {
        currentEditingPlanId = plan.id;

        // Populate form fields on the main page
        document.getElementById('city').value = plan.city || '';
        document.getElementById('days').value = plan.days || '';
        document.getElementById('budget').value = plan.budget || '';
        
        // Populate content in the result modal and make it editable
        aiResponseDiv.innerHTML = plan.plan_content || '';
        aiResponseDiv.setAttribute('contenteditable', 'true');
        aiResponseDiv.classList.add('editable');

        // Show the result modal for editing
        if (resultModal) resultModal.style.display = 'flex';

        // Toggle main page button visibility
        if (savePlanBtn) savePlanBtn.style.display = 'none';
        if (generatePlanBtn) generatePlanBtn.style.display = 'none';

        // Create and show 'Update' and 'Cancel' buttons if they don't exist
        if (!document.getElementById('update-plan-btn')) {
            const updateBtn = document.createElement('button');
            updateBtn.id = 'update-plan-btn';
            updateBtn.textContent = '更新计划';
            updateBtn.className = 'action-btn';
            if (planActionsContainer) planActionsContainer.appendChild(updateBtn);

            const cancelBtn = document.createElement('button');
            cancelBtn.id = 'cancel-edit-btn';
            cancelBtn.textContent = '取消';
            cancelBtn.className = 'action-btn secondary-btn';
            if (planActionsContainer) planActionsContainer.appendChild(cancelBtn);

            updateBtn.addEventListener('click', handleUpdatePlan);
            cancelBtn.addEventListener('click', exitEditMode);
        }

        // Close the 'My Plans' list modal
        if (plansModal) plansModal.style.display = 'none';
    }

    /**
     * Exits plan editing mode and restores the UI.
     */
    function exitEditMode() {
        currentEditingPlanId = null;

        // Hide the result modal
        if (resultModal) resultModal.style.display = 'none';

        // Clear form and content area
        document.getElementById('city').value = '';
        document.getElementById('days').value = '';
        document.getElementById('budget').value = '';
        aiResponseDiv.innerHTML = '生成中...'; // Reset to a default state
        aiResponseDiv.setAttribute('contenteditable', 'false');
        aiResponseDiv.classList.remove('editable');

        // Restore original buttons
        if (savePlanBtn) savePlanBtn.style.display = 'inline-block';
        if (generatePlanBtn) generatePlanBtn.style.display = 'inline-block';

        // Remove 'Update' and 'Cancel' buttons
        const updateBtn = document.getElementById('update-plan-btn');
        const cancelBtn = document.getElementById('cancel-edit-btn');
        if (updateBtn) updateBtn.remove();
        if (cancelBtn) cancelBtn.remove();
    }

    /**
     * Handles the logic for updating a plan.
     */
    async function handleUpdatePlan() {
        if (!currentEditingPlanId) return;

        const originalPlan = await getPlanById(currentEditingPlanId);
        if (!originalPlan) {
            alert('无法获取原始计划详情。');
            return;
        }

        const newPlanName = prompt('请确认或修改计划名称：', originalPlan.plan_name);

        if (newPlanName === null || newPlanName.trim() === '') {
            console.log('用户取消了更新。');
            return;
        }

        const updatedData = {
            plan_name: newPlanName.trim(),
            city: document.getElementById('city').value,
            days: document.getElementById('days').value,
            budget: document.getElementById('budget').value,
            plan_content: aiResponseDiv.innerHTML
        };

        const result = await updateTravelPlan(currentEditingPlanId, updatedData);
        if (result) {
            alert('计划更新成功！');
            exitEditMode();
        }
    }

    if(savePlanBtn) savePlanBtn.addEventListener('click', () => {
        const user = _supabase.auth.getUser();

        user.then(response => {
            if (!response.data.user) {
                openModal(true);
                return;
            }

            const planContent = aiResponseDiv.innerHTML;
            if (!planContent.trim() || planContent === '生成中...') {
                alert('当前没有可以保存的有效旅行计划。');
                return;
            }

            const city = document.getElementById('city').value;
            const days = document.getElementById('days').value;
            const budget = document.getElementById('budget').value;

            const defaultPlanName = `${city || '我的'}${days ? days + '日' : ''}旅行计划`;
            const planName = prompt('请输入计划名称：', defaultPlanName);

            if (planName === null || planName.trim() === '') {
                console.log('用户取消了保存或未输入名称。');
                return;
            }

            saveTravelPlan(planName.trim(), city, days, budget, planContent);
        });
    });

    if(myPlansBtn) myPlansBtn.addEventListener('click', async () => {
        const plans = await fetchUserPlans();
        plansList.innerHTML = '';
        if (plans && plans.length > 0) {
            plans.forEach(plan => {
                const planElement = document.createElement('div');
                planElement.classList.add('plan-item');
                planElement.dataset.planId = plan.id;
                const planName = plan.plan_name || `${plan.city || '未知地点'}${plan.days ? plan.days + '日游' : '计划'}`;
                planElement.innerHTML = `
                    <div class="plan-item-header">
                        <h4 class="plan-title">${planName}</h4>
                        <span class="plan-date">${new Date(plan.create_at).toLocaleDateString()}</span>
                    </div>
                    <p class="plan-city">城市：${plan.city || '未指定'}</p>
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
            if (planId) {
                const plan = await getPlanById(planId);
                if (plan) {
                    enterEditMode(plan);
                }
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