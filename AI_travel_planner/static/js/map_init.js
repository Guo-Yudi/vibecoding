// 地图初始化函数
function initMap() {
    console.log('开始初始化地图...');

    // 检查百度地图API是否加载成功
    if (typeof BMapGL === 'undefined') {
        console.error('百度地图API加载失败');
        showMapError('地图API加载失败，请检查网络连接或API密钥');
        return;
    }

    try {
        // 获取地图容器
        var container = document.getElementById('container');
        if (!container) {
            console.error('未找到地图容器 #container');
            showMapError('未找到地图容器');
            return;
        }

        // 创建地图实例
        var map = new BMapGL.Map("container", {
            enableDragging: true,  // 启用拖动
            enableScrollWheelZoom: true,  // 启用鼠标滚轮缩放
            enablePinchToZoom: true  // 启用手势缩放
        });

        // 设置中心点坐标和缩放级别 (北京天安门)
        var point = new BMapGL.Point(116.404, 39.915);
        map.centerAndZoom(point, 15); // 调整缩放级别为12，显示更大范围
        
        // 启用地图拖动功能
        map.enableDragging(true);
        map.enableScrollWheelZoom(true);
        map.enablePinchToZoom(true);

        // 添加地图控件到右上角
        // 设置控件位置为右上角
        var topRight = {
            anchor: BMAP_ANCHOR_TOP_RIGHT,
            offset: new BMapGL.Size(10, 10)
        };

        // 添加导航控件（放大缩小按钮）
        var navigationControl = new BMapGL.NavigationControl({
            anchor: BMAP_ANCHOR_TOP_RIGHT,
            offset: new BMapGL.Size(10, 10),
            type: BMAP_NAVIGATION_CONTROL_ZOOM, // 显示缩放按钮
            showZoomInfo: true
        });
        map.addControl(navigationControl);

        // 添加比例尺控件
        var scaleControl = new BMapGL.ScaleControl({
            anchor: BMAP_ANCHOR_TOP_RIGHT,
            offset: new BMapGL.Size(10, 60) // 在导航控件下方
        });
        map.addControl(scaleControl);

        // 添加缩略图控件
        var overviewMapControl = new BMapGL.OverviewMapControl({
            anchor: BMAP_ANCHOR_TOP_RIGHT,
            offset: new BMapGL.Size(10, 100), // 在比例尺控件下方
            isOpen: true // 默认展开缩略图
        });
        map.addControl(overviewMapControl);

        // 添加地图类型控件
        var mapTypeControl = new BMapGL.MapTypeControl({
            anchor: BMAP_ANCHOR_TOP_RIGHT,
            offset: new BMapGL.Size(10, 160) // 在缩略图控件下方
        });
        map.addControl(mapTypeControl);
        map.setCurrentCity("北京"); // 设置默认城市以启用地图类型切换功能

        window.mapInstance = map;

        // 发送地图初始化完成事件
        const event = new CustomEvent('mapInitialized', { detail: { map: map } });
        window.dispatchEvent(event);

        console.log('地图初始化完成');
    } catch (error) {
        console.error('地图初始化过程中发生错误:', error);
        showMapError('地图初始化失败: ' + error.message);
    }
}

// 显示地图错误信息
function showMapError(message) {
    var container = document.getElementById('container');
    if (container) {
        container.innerHTML = '<div style="color: white; text-align: center; padding-top: 50px;">' + message + '</div>';
    }
}

// 页面加载完成后初始化地图
window.onload = function() {
    // 延迟执行以确保DOM完全加载
    setTimeout(function() {
        initMap();
    }, 100);
};