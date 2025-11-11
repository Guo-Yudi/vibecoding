// 侧边栏交互功能：简化实现，避免影响地图拖动

document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    const mapContainer = document.getElementById('container');
    
    if (!sidebar || !mapContainer) {
        console.warn('未找到侧边栏或地图容器');
        return;
    }
    
    // 默认情况下显示侧边栏
    sidebar.style.opacity = '1';
    sidebar.style.transform = 'translateX(0)';
    sidebar.style.pointerEvents = 'auto';
});