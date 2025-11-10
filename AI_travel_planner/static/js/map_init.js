window.onload = function() {
    // 创建地图实例
    var map = new BMapGL.Map("container");
    // 设置中心点坐标和缩放级别
    var point = new BMapGL.Point(116.404, 39.915);
    map.centerAndZoom(point, 15);
    map.enableScrollWheelZoom(true);

    // 添加地图控件
    map.addControl(new BMapGL.ScaleControl());
    map.addControl(new BMapGL.ZoomControl());
    map.addControl(new BMapGL.CityListControl());

    // --- 功能 1: 地点搜索 ---
    var local = new BMapGL.LocalSearch(map, {
        renderOptions: { map: map, autoViewport: true }
    });

    document.getElementById("search-input").addEventListener("keydown", function(e) {
        if (e.key === "Enter") {
            local.search(this.value);
        }
    });

    // --- 功能 2: 用户定位 ---
    document.getElementById("locate-btn").addEventListener("click", function() {
        var geolocation = new BMapGL.Geolocation();
        geolocation.getCurrentPosition(function(r) {
            if (this.getStatus() == BMAP_STATUS_SUCCESS) {
                map.addOverlay(new BMapGL.Marker(r.point));
                map.panTo(r.point);
                alert('定位成功！');
            } else {
                alert('定位失败：' + this.getStatus());
            }
        });
    });
};