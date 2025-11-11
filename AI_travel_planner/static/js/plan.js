/**
 * Saves the current travel plan to Supabase.
 * @param {string} planTitle - The title for the plan.
 * @param {string} planContent - The HTML content of the plan.
 * @returns {Promise<Object|null>} - The saved data or null on error.
 */
async function saveTravelPlan(planTitle, planContent) {
    const { data: { user } } = await _supabase.auth.getUser();
    if (!user) {
        alert('请先登录再保存计划。');
        return null;
    }

    const { data, error } = await _supabase
        .from('travel_plans')
        .insert([
            { 
                user_id: user.id, 
                title: planTitle,
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
        .select('id, title, created_at')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });

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