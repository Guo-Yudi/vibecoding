/**
 * Saves the current travel plan to Supabase.
 * @param {string} planName - The name for the plan.
 * @param {string} city - The city of the plan.
 * @param {number} days - The duration of the plan in days.
 * @param {string} budget - The budget for the plan.
 * @param {string} planContent - The HTML content of the plan.
 * @returns {Promise<Object|null>} - The saved data or null on error.
 */
async function saveTravelPlan(planName, city, days, budget, planContent) {
    const { data: { user } } = await _supabase.auth.getUser();
    if (!user) {
        alert('请先登录再保存计划。');
        return null;
    }

    // 1. Fetch existing plan names to ensure uniqueness
    const { data: existingPlans, error: fetchError } = await _supabase
        .from('travel_plans')
        .select('plan_name')
        .eq('user_id', user.id);

    if (fetchError) {
        console.error('Error fetching existing plans:', fetchError);
        alert('无法验证计划名称，保存失败。');
        return null;
    }

    // 2. Check for name duplicates and add a suffix if needed
    const existingNames = existingPlans.map(p => p.plan_name);
    let finalPlanName = planName;
    let counter = 1;
    const baseName = planName.replace(/\(\d+\)$/, '').trim();

    while (existingNames.includes(finalPlanName)) {
        finalPlanName = `${baseName}(${counter})`;
        counter++;
    }

    const parsedDays = days ? parseInt(days, 10) : null;

    // 3. Insert the new plan with the unique name
    const { data, error } = await _supabase
        .from('travel_plans')
        .insert([
            {
                user_id: user.id,
                plan_name: finalPlanName,
                city: city,
                days: parsedDays,
                budget: budget,
                plan_content: planContent
            }
        ])
        .select();

    if (error) {
        console.error('Error saving plan:', error);
        alert('保存计划失败！');
        return null;
    }

    alert('计划已成功保存！');
    console.log('Plan saved:', data);
    return data;
}

/**
 * Fetches a single travel plan by its ID.
 * @param {number} planId - The ID of the plan to fetch.
 * @returns {Promise<Object|null>} - The plan data or null on error.
 */
async function getPlanById(planId) {
    const { data, error } = await _supabase
        .from('travel_plans')
        .select('*')
        .eq('id', planId)
        .single();

    if (error) {
        console.error('获取计划详情时出错:', error);
        alert('加载计划失败！');
        return null;
    }
    return data;
}

/**
 * Updates an existing travel plan.
 * @param {number} planId - The ID of the plan to update.
 * @param {object} updatedData - An object containing the data to update.
 * @returns {Promise<Object|null>} - The updated data or null on error.
 */
async function updateTravelPlan(planId, updatedData) {
    const { data, error } = await _supabase
        .from('travel_plans')
        .update(updatedData)
        .eq('id', planId)
        .select();

    if (error) {
        console.error('更新旅行计划时出错:', error);
        alert(`更新失败: ${error.message}`);
        return null;
    } else {
        alert('计划已成功更新！');
        console.log('更新后的数据:', data);
        return data;
    }
}

/**
 * Fetches all travel plans for the current user.
 * @returns {Promise<Array|null>} - An array of plans or null on error.
 */
async function fetchUserPlans() {
    const { data: { user } } = await _supabase.auth.getUser();
    if (!user) {
        // This case should ideally not be hit if UI is correct
        console.log('No user logged in to fetch plans.');
        return null;
    }

    const { data, error } = await _supabase
        .from('travel_plans')
        .select('id, plan_name, city, create_at, days')
        .eq('user_id', user.id)
        .order('create_at', { ascending: false });

    if (error) {
        console.error('Error fetching plans:', error);
        alert('获取计划列表失败！');
        return null;
    }

    return data;
}

/**
 * Fetches a single travel plan by its ID.
 * @param {number} planId - The ID of the plan to fetch.
 * @returns {Promise<Object|null>} - The plan object or null on error.
 */
async function fetchPlanDetails(planId) {
    const { data, error } = await _supabase
        .from('travel_plans')
        .select('plan_content')
        .eq('id', planId)
        .single(); // .single() expects only one row

    if (error) {
        console.error('Error fetching plan details:', error);
        alert('加载计划详情失败！');
        return null;
    }
    return data;
}