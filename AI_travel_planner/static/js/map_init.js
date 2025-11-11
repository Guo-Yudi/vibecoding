document.addEventListener('DOMContentLoaded', function () {
    /**
     * Encapsulates all map-related functionality.
     */
    const mapApp = {
        map: null,
        container: document.getElementById('container'),

        /**
         * Displays an error message in the map container.
         * @param {string} message - The error message to display.
         */
        showError(message) {
            if (this.container) {
                this.container.innerHTML = `<div style="color: white; text-align: center; padding-top: 50px;">${message}</div>`;
            }
            console.error(message);
        },

        /**
         * Adds all necessary controls to the map.
         * @private
         */
        _addControls() {
            if (!this.map) return;

            // Navigation control (zoom)
            const navControl = new BMapGL.NavigationControl({
                anchor: BMAP_ANCHOR_BOTTOM_RIGHT,
                offset: new BMapGL.Size(10, 10)
            });
            this.map.addControl(navControl);

            // Scale control
            const scaleControl = new BMapGL.ScaleControl({
                anchor: BMAP_ANCHOR_BOTTOM_RIGHT,
                offset: new BMapGL.Size(50, 20)
            });
            this.map.addControl(scaleControl);

            // Overview map control
            const overviewControl = new BMapGL.OverviewMap({
                anchor: BMAP_ANCHOR_TOP_RIGHT,
                offset: new BMapGL.Size(10, 100),
                isOpen: true
            });
            this.map.addControl(overviewControl);

            // Map type control
            const mapTypeControl = new BMapGL.MapTypeControl({
                anchor: BMAP_ANCHOR_BOTTOM_RIGHT,
                offset: new BMapGL.Size(10, 160)
            });
            this.map.addControl(mapTypeControl);
        },

        /**
         * Initializes the map.
         */
        init() {
            console.log('Initializing map...');
            if (typeof BMapGL === 'undefined') {
                this.showError('Baidu Maps API failed to load. Please check your network or API key.');
                return;
            }
            if (!this.container) {
                this.showError('Map container #container not found.');
                return;
            }

            try {
                this.map = new BMapGL.Map(this.container);
                const point = new BMapGL.Point(118.785186, 32.064004);
                this.map.centerAndZoom(point, 17);

                const marker = new BMapGL.Marker(point);
                this.map.addOverlay(marker);

                this.map.enableDragging(true);
                this.map.enableScrollWheelZoom(true);

                this._addControls();
                this.map.setCurrentCity("北京"); // Required for map type switching

                this._attachEventListeners();
                
                // Make the app object globally accessible if needed by other scripts
                window.mapApp = this;

                console.log('Map initialization complete.');
            } catch (error) {
                this.showError(`Map initialization failed: ${error.message}`);
            }
        },

        /**
         * Attaches event listeners to UI elements.
         * @private
         */
        _attachEventListeners() {
            const locateBtn = document.getElementById('locate-btn');
            if (locateBtn) {
                locateBtn.addEventListener('click', () => {
                    this.locate();
                });
            }
        },

        /**
         * Finds the user's current location and displays it on the map.
         */
        locate() {
            if (!this.map) {
                this.showError('Map is not initialized.');
                return;
            }
            console.log('Attempting to locate user...');
            const geolocation = new BMapGL.Geolocation();
            geolocation.getCurrentPosition((r) => {
                if (geolocation.getStatus() === BMAP_STATUS_SUCCESS) {
                    const marker = new BMapGL.Marker(r.point);
                    this.map.addOverlay(marker);
                    this.map.panTo(r.point);
                    console.log('User located at:', r.point);
                    alert('定位成功！您的位置：' + r.point.lng + ',' + r.point.lat);
                } else {
                    this.showError('Geolocation failed. Status: ' + geolocation.getStatus());
                    alert('定位失败，请检查浏览器权限或网络设置。');
                }
            });
        },

        /**
         * Calculates and displays a driving route on the map.
         * @param {string | BMapGL.Point} start - The starting point.
         * @param {string | BMapGL.Point} end - The ending point.
         */
        driveRoute(start, end) {
            if (!this.map) {
                this.showError('Map is not initialized.');
                return;
            }
            if (!start || !end) {
                this.showError('Please provide both a start and end point for directions.');
                return;
            }
            this.map.clearOverlays();
            const driving = new BMapGL.DrivingRoute(this.map, {
                renderOptions: { map: this.map, autoViewport: true }
            });
            driving.search(start, end);
        }
    };

    // Initialize the map application
    mapApp.init();
});