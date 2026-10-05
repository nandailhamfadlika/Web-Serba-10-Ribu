/**
 * Serba 10 Ribu Group - Hyperlocal Store Locator & Geolocation Engine
 * Handles Leaflet.js map visualization, user GPS distance calculations,
 * and automatic branch selection between Ciomas and Dramaga.
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Ambil data cabang yang di-inject dari Django template
    const branchesDataElement = document.getElementById('branches-data-json');
    if (!branchesDataElement) return;

    const branches = JSON.parse(branchesDataElement.textContent);
    const mapElement = document.getElementById('store-map');
    if (!mapElement) return;

    // Koordinat pusat peta antara Ciomas & Dramaga Bogor
    const centerBogor = [-6.5887, 106.7550];
    const map = L.map('store-map', {
        zoomControl: true,
        scrollWheelZoom: false // Mencegah scrolling halaman macet di mobile
    }).setView(centerBogor, 13);

    // Tile Layer: OpenStreetMap Humanitarian (HOT) - 100% Gratis, Tanpa API Key, Bebas Blokir
    const osmHot = L.tileLayer('https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Tiles style by <a href="https://www.hotosm.org/" target="_blank">HOT</a>'
    }).addTo(map);

    // Tile Layer Cadangan: Esri World Street Map - 100% Gratis, Tanpa API Key
    const esriStreets = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19,
        attribution: 'Tiles &copy; Esri'
    });

    // Kontrol Layer Pilihan di Pojok Kanan Atas
    L.control.layers({
        "Peta Standar (OSM HOT)": osmHot,
        "Peta ArcGIS (Esri)": esriStreets
    }, null, { position: 'topright' }).addTo(map);

    // Kustom Pin Icon Generator
    function createBranchIcon(isActive) {
        const bgColor = isActive ? '#e52329' : '#64748b'; // brand red #e52329 vs slate-500
        const svgHtml = `
            <div style="position: relative; width: 36px; height: 46px;">
                <svg viewBox="0 0 24 24" width="36" height="46" fill="${bgColor}" style="filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));">
                    <path d="M12 0C7.58 0 4 3.58 4 8c0 5.25 7 13 8 13s8-7.75 8-13c0-4.42-3.58-8-8-8zm0 11c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z"/>
                </svg>
                <div style="position: absolute; top: 6px; left: 10px; color: #ffffff; font-weight: 900; font-size: 11px;">10k</div>
            </div>
        `;
        return L.divIcon({
            html: svgHtml,
            className: 'custom-leaflet-marker',
            iconSize: [36, 46],
            iconAnchor: [18, 46],
            popupAnchor: [0, -42]
        });
    }

    const storefrontEl = document.getElementById('home-storefront');
    const currentBranchSlug = document.body.dataset.selectedBranch || (storefrontEl ? storefrontEl.dataset.selectedBranch : null) || 'ciomas';
    const markers = {};

    // 2. Tambahkan Marker untuk Cabang Ciomas dan Cabang Dramaga
    branches.forEach(branch => {
        const isCurrent = (branch.slug === currentBranchSlug);
        const marker = L.marker([branch.lat, branch.lng], {
            icon: createBranchIcon(isCurrent)
        }).addTo(map);

        const logoHtml = branch.logo_url ? `
            <div style="text-align: center; margin-bottom: 8px;">
                <img src="${branch.logo_url}" alt="${branch.name}" style="height: 48px; width: auto; object-fit: contain; border-radius: 8px; border: 1px solid #fecaca; padding: 2px; background: #ffffff; margin: 0 auto; display: inline-block;">
            </div>
        ` : '';

        const popupContent = `
            <div style="font-family: inherit; padding: 6px; max-width: 240px; text-align: center;">
                ${logoHtml}
                <div style="font-weight: 800; font-size: 14px; color: #0f172a; margin-bottom: 2px;">
                    ${branch.name}
                </div>
                <div style="font-size: 11px; color: #475569; margin-bottom: 6px; line-height: 1.4;">
                    ${branch.address}
                </div>
                <div style="display: inline-block; font-size: 11px; font-weight: 700; color: #059669; background: #ecfdf5; border: 1px solid #a7f3d0; padding: 2px 8px; border-radius: 9999px; margin-bottom: 8px;">
                    ⏰ ${branch.opening_hours}
                </div>
                <div style="margin-top: 4px;">
                    <a href="${branch.gmaps_url}" target="_blank" rel="noopener noreferrer" 
                       style="display: block; text-align: center; font-size: 12px; font-weight: 800; color: #ffffff; background: #e52329; padding: 7px 10px; border-radius: 8px; text-decoration: none; box-shadow: 0 1px 3px rgba(229,35,41,0.3);">
                        🧭 Buka Petunjuk Rute Maps
                    </a>
                </div>
            </div>
        `;
        marker.bindPopup(popupContent);
        markers[branch.slug] = marker;

        if (isCurrent) {
            marker.openPopup();
        }
    });

    // 3. Formula Haversine Client-Side untuk Kalkulasi Instan
    function calculateHaversineDistanceKm(lat1, lon1, lat2, lon2) {
        const toRad = x => (x * Math.PI) / 180;
        const R = 6371; // Radius bumi km
        const dLat = toRad(lat2 - lat1);
        const dLon = toRad(lon2 - lon1);
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                  Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
                  Math.sin(dLon / 2) * Math.sin(dLon / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return parseFloat((R * c).toFixed(2));
    }

    let userMarker = null;

    // 4. Tombol "Cari Cabang Terdekat" (Geolocation)
    const geolocateBtn = document.getElementById('btn-find-nearest');
    const geolocateStatus = document.getElementById('geo-status-banner');

    if (geolocateBtn) {
        geolocateBtn.addEventListener('click', function () {
            if (!navigator.geolocation) {
                alert('Browser Anda tidak mendukung deteksi lokasi (Geolocation). Silakan pilih cabang secara manual.');
                return;
            }

            // Indikator Loading
            geolocateBtn.disabled = true;
            geolocateBtn.innerHTML = `
                <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Mendeteksi Lokasi GPS...
            `;

            navigator.geolocation.getCurrentPosition(
                function (position) {
                    const uLat = position.coords.latitude;
                    const uLng = position.coords.longitude;

                    // Buat / Update marker posisi pengguna di peta
                    if (userMarker) {
                        userMarker.setLatLng([uLat, uLng]);
                    } else {
                        const pulseIcon = L.divIcon({
                            className: 'leaflet-custom-pulse',
                            iconSize: [18, 18],
                            iconAnchor: [9, 9]
                        });
                        userMarker = L.marker([uLat, uLng], { icon: pulseIcon }).addTo(map);
                        userMarker.bindPopup('<b style="color: #2563eb;">Lokasi Anda Saat Ini</b>');
                    }

                    // Hitung jarak ke setiap cabang
                    let nearestBranch = null;
                    let shortestDistance = Infinity;

                    branches.forEach(b => {
                        const dist = calculateHaversineDistanceKm(uLat, uLng, b.lat, b.lng);
                        b.distance = dist;

                        // Perbarui badge jarak di tombol tab cabang
                        const badgeEl = document.getElementById(`distance-badge-${b.slug}`);
                        if (badgeEl) {
                            badgeEl.textContent = `${dist} km`;
                            badgeEl.classList.remove('hidden');
                        }

                        if (dist < shortestDistance) {
                            shortestDistance = dist;
                            nearestBranch = b;
                        }
                    });

                    // Tampilkan banner notifikasi cabang terdekat
                    if (geolocateStatus && nearestBranch) {
                        geolocateStatus.innerHTML = `
                            <div class="p-3 bg-red-50/80 border border-brand-200 rounded-xl flex items-center justify-between shadow-xs animate-fade-in">
                                <div class="flex items-center gap-2.5">
                                    <span class="flex h-3 w-3 relative">
                                        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-400 opacity-75"></span>
                                        <span class="relative inline-flex rounded-full h-3 w-3 bg-brand-600"></span>
                                    </span>
                                    <span class="text-xs sm:text-sm font-bold text-slate-800">
                                        Cabang Terdekat Anda: <span class="text-brand-700 font-extrabold underline">${nearestBranch.name}</span> (${shortestDistance} km)
                                    </span>
                                </div>
                                ${nearestBranch.slug !== currentBranchSlug ? `
                                    <a href="?branch=${nearestBranch.slug}" class="text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white px-3 py-1.5 rounded-lg transition-colors shadow">
                                        Pindah ke ${nearestBranch.slug.toUpperCase()}
                                    </a>
                                ` : `
                                    <span class="text-xs font-bold text-emerald-700 bg-emerald-100 px-2.5 py-1 rounded-md">
                                        Sedang Aktif
                                    </span>
                                `}
                            </div>
                        `;
                        geolocateStatus.classList.remove('hidden');
                    }

                    // Zoom peta agar menampilkan posisi user dan cabang terdekat
                    const group = new L.featureGroup([
                        userMarker,
                        markers[nearestBranch.slug]
                    ]);
                    map.fitBounds(group.getBounds().pad(0.2));

                    // Reset tombol
                    geolocateBtn.disabled = false;
                    geolocateBtn.innerHTML = `
                        <svg class="w-4 h-4 mr-1.5 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
                        </svg>
                        Lokasi Terdeteksi (${shortestDistance} km)
                    `;
                },
                function (error) {
                    geolocateBtn.disabled = false;
                    geolocateBtn.innerHTML = `
                        <svg class="w-4 h-4 mr-1.5 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
                        </svg>
                        Cari Cabang Terdekat
                    `;
                    let errMsg = 'Tidak dapat mendeteksi lokasi.';
                    if (error.code === error.PERMISSION_DENIED) {
                        errMsg = 'Izin akses lokasi ditolak oleh browser. Anda tetap dapat memilih cabang secara manual di tab atas.';
                    }
                    alert(errMsg);
                },
                { timeout: 10000, enableHighAccuracy: true }
            );
        });
    }

    // 5. Filter Kategori Menu di Live Inventory
    const filterButtons = document.querySelectorAll('.category-filter-btn');
    const menuItems = document.querySelectorAll('.menu-item-card');

    filterButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            filterButtons.forEach(b => {
                b.classList.remove('bg-brand-600', 'text-white', 'shadow');
                b.classList.add('bg-white', 'text-slate-700', 'border-slate-200');
            });
            this.classList.remove('bg-white', 'text-slate-700', 'border-slate-200');
            this.classList.add('bg-brand-600', 'text-white', 'shadow');

            const selectedCat = this.dataset.category;
            menuItems.forEach(item => {
                if (selectedCat === 'all' || item.dataset.category === selectedCat) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    });
});
