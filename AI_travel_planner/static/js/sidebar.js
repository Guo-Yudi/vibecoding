// 侧边栏交互功能：拖动地图时自动隐藏，停止拖动时自动显示

document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    const mapContainer = document.getElementById('container');
    
    if (!sidebar || !mapContainer) {
        console.warn('未找到侧边栏或地图容器');
        return;
    }
    
    // 隐藏侧边栏
    function hideSidebar() {
        sidebar.style.opacity = '0';
        sidebar.style.transform = 'translateX(-20px)';
        sidebar.style.pointerEvents = 'none';
    }
    
    // 显示侧边栏
    function showSidebar() {
        sidebar.style.opacity = '1';
        sidebar.style.transform = 'translateX(0)';
        sidebar.style.pointerEvents = 'auto';
    }
    
    // 监听地图拖动事件
    let mapInstance = null;
    
    // 在地图初始化完成后绑定事件
    window.addEventListener('mapInitialized', function(e) {
        mapInstance = e.detail.map;
        
        if (mapInstance) {
            // 监听地图开始拖动事件
            mapInstance.addEventListener('dragstart', function() {
                hideSidebar();
            });
            
            // 监听地图停止拖动事件
            mapInstance.addEventListener('dragend', function() {
                showSidebar();
            });
            
            // 监听触摸开始事件（移动端）
            mapInstance.addEventListener('touchstart', function() {
                hideSidebar();
            });
            
            // 监听触摸结束事件（移动端）
            mapInstance.addEventListener('touchend', function() {
                setTimeout(showSidebar, 300); // 稍微延迟显示，避免干扰用户操作
            });
            
            // 监听鼠标滚轮事件
            mapInstance.addEventListener('zoomstart', function() {
                hideSidebar();
            });
            
            mapInstance.addEventListener('zoomend', function() {
                setTimeout(showSidebar, 300);
            });
        }
    });
    
    // 默认情况下显示侧边栏
    showSidebar();
});