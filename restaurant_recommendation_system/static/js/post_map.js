let map;
let marker;
let autocomplete;
let placeId;

function initMap() {
    const defaultCenter = { lat: 23.97565, lng: 120.9738819 };
    map = new google.maps.Map(document.getElementById("map"), {
        center: defaultCenter,
        zoom: 7,
        mapTypeControl: false
    });
    const input = document.getElementById("location-search");
    autocomplete = new google.maps.places.Autocomplete(input, {
        fields: ["place_id", "geometry", "name", "formatted_address"],
        types: ["restaurant", "food"],
        strictBounds: false
    });
    autocomplete.addListener("place_changed", () => {
        const place = autocomplete.getPlace();
        if (!place.geometry || !place.geometry.location) return;
        map.setCenter(place.geometry.location);
        map.setZoom(17);
        if (marker) {
            marker.setPosition(place.geometry.location);
        } else {
            marker = new google.maps.Marker({
                map: map,
                position: place.geometry.location,
                title: place.name,
                animation: google.maps.Animation.DROP
            });
        }
        // 設定表單欄位（請依你的 input id 調整）
        const nameInput = document.getElementById("location-name");
        const addressInput = document.getElementById("location-address");
        const latInput = document.getElementById("location-lat");
        const lngInput = document.getElementById("location-lng");
        const placeIdInput = document.getElementById("id_location_place_id");
        if (nameInput) nameInput.value = place.name || "";
        if (addressInput) addressInput.value = place.formatted_address || "";
        if (latInput) latInput.value = place.geometry.location.lat();
        if (lngInput) lngInput.value = place.geometry.location.lng();
        if (placeIdInput) placeIdInput.value = place.place_id || "";
    });
    map.addListener("click", (mapsMouseEvent) => {
        const clickLocation = mapsMouseEvent.latLng;
        const geocoder = new google.maps.Geocoder();
        geocoder.geocode({ location: clickLocation }, (results, status) => {
            if (status === "OK" && results[0]) {
                placeDetails(results[0].place_id);
            }
        });
    });

    // 如果有已儲存的地點，初始化地圖標記
    const latInput = document.getElementById("location-lat");
    const lngInput = document.getElementById("location-lng");
    const nameInput = document.getElementById("location-name");
    if (latInput && lngInput && latInput.value && lngInput.value) {
        const savedLocation = {
            lat: parseFloat(latInput.value),
            lng: parseFloat(lngInput.value)
        };
        map.setCenter(savedLocation);
        map.setZoom(17);
        marker = new google.maps.Marker({
            map: map,
            position: savedLocation,
            title: nameInput && nameInput.value ? nameInput.value : "",
            animation: google.maps.Animation.DROP
        });
    }
}

function placeDetails(placeId) {
    const service = new google.maps.places.PlacesService(map);
    service.getDetails(
        { placeId: placeId, fields: ["name", "formatted_address", "geometry", "place_id"] },
        (place, status) => {
            if (status === google.maps.places.PlacesServiceStatus.OK) {
                if (marker) {
                    marker.setPosition(place.geometry.location);
                } else {
                    marker = new google.maps.Marker({
                        map: map,
                        position: place.geometry.location,
                        title: place.name,
                        animation: google.maps.Animation.DROP
                    });
                }
                // 設定表單欄位（請依你的 input id 調整）
                const nameInput = document.getElementById("location-name");
                const addressInput = document.getElementById("location-address");
                const latInput = document.getElementById("location_lat");
                const lngInput = document.getElementById("location_lng");
                const placeIdInput = document.getElementById("id_location_place_id");
                const searchInput = document.getElementById("location-search");
                if (nameInput) nameInput.value = place.name || "";
                if (addressInput) addressInput.value = place.formatted_address || "";
                if (latInput) latInput.value = place.geometry.location.lat();
                if (lngInput) lngInput.value = place.geometry.location.lng();
                if (placeIdInput) placeIdInput.value = place.place_id || "";
                if (searchInput) searchInput.value = place.name || "";
            }
        }
    );
}