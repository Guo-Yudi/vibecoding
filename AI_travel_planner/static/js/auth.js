
// Supabase credentials are now passed from the backend via index.html
const SUPABASE_URL = window.SUPABASE_URL;
const SUPABASE_ANON_KEY = window.SUPABASE_ANON_KEY;

const { createClient } = supabase;
const _supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
    console.error("Supabase URL or Anon Key is missing. Make sure they are passed correctly from the backend.");
    alert("Supabase configuration is missing. App functionality will be limited.");
} else {
    console.log('Supabase client initialized.');
}

// --- Authentication Functions ---

/**
 * Signs up a new user and creates a profile.
 * @param {string} email
 * @param {string} password
 * @param {string} username
 * @returns {Promise<object|null>} The user object or null on error.
 */
async function signUpUser(email, password, username) {
    const { data, error } = await _supabase.auth.signUp({
        email: email,
        password: password,
        options: {
            data: {
                username: username
            }
        }
    });
    if (error) {
        console.error('Error signing up:', error.message);
        alert('注册失败: ' + error.message);
        return null;
    }
    if (data.user) {
        console.log('Sign up successful, user:', data.user);
        // The profile is now created by a trigger in Supabase.
        
        alert('注册成功！请检查您的邮箱以验证您的账户。');
        return data.user;
    }
    return null;
}

/**
 * Signs in an existing user.
 * @param {string} email
 * @param {string} password
 * @returns {Promise<object|null>} The user object or null on error.
 */
async function signInUser(email, password) {
    const { data, error } = await _supabase.auth.signInWithPassword({
        email: email,
        password: password,
    });
    if (error) {
        console.error('Error signing in:', error.message);
        alert('登录失败: ' + error.message);
        return null;
    }
    console.log('Sign in successful, user:', data.user);
    return data.user;
}

/**
 * Signs out the current user.
 */
async function signOutUser() {
    const { error } = await _supabase.auth.signOut();
    if (error) {
        console.error('Error signing out:', error.message);
        alert('登出失败: ' + error.message);
    } else {
        console.log('Signed out successfully.');
        alert('您已成功登出。');
    }
}

// --- Auth State Change Listener ---

document.addEventListener('DOMContentLoaded', function() {
    _supabase.auth.onAuthStateChange((event, session) => {
        console.log('Auth state changed:', event);
        const authSection = document.getElementById('auth-section');
        const userSection = document.getElementById('user-section');
        const userEmailDisplay = document.getElementById('user-email-display');
        const savePlanBtn = document.getElementById('save-plan-btn');

        if (event === 'SIGNED_IN' && session) {
            // User is signed in
            if (authSection) authSection.style.display = 'none';
            if (userSection) userSection.style.display = 'flex';
            if (userEmailDisplay) userEmailDisplay.textContent = session.user.email;
            if (savePlanBtn) savePlanBtn.style.display = 'block'; // Show save button
            
        } else if (event === 'SIGNED_OUT') {
            // User is signed out
            if (authSection) authSection.style.display = 'flex';
            if (userSection) userSection.style.display = 'none';
            if (userEmailDisplay) userEmailDisplay.textContent = '';
        // Keep save plan button visible, but its click handler will check for auth
        if (savePlanBtn) savePlanBtn.style.display = 'block'; 
    }
    });
});