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
                position: place.geometry.location,
                map: map,
                title: place.name,
                animation: google.maps.Animation.DROP
            });
        }
        document.getElementById("location-name").value = place.name;
        document.getElementById("location-address").value = place.formatted_address;
        document.getElementById("location-lat").value = place.geometry.location.lat();
        document.getElementById("location-lng").value = place.geometry.location.lng();
        document.getElementById("location-place-id").value = place.place_id;
    });
    map.addListener("click", (mapsMouseEvent) => {
        const clickLocation = mapsMouseEvent.latLng;
        const geocoder = new google.maps.Geocoder();
        geocoder.geocode({ location: clickLocation }, (results, status) => {
            if (status === "OK") {
                if (results[0]) {
                    placeDetails(results[0].place_id);
                }
            }
        });
    });
    const savedLat = document.getElementById("location-lat").value;
    const savedLng = document.getElementById("location-lng").value;
    if (savedLat && savedLng) {
        const savedLocation = { lat: parseFloat(savedLat), lng: parseFloat(savedLng) };
        map.setCenter(savedLocation);
        map.setZoom(17);
        marker = new google.maps.Marker({
            position: savedLocation,
            map: map,
            title: document.getElementById("location-name").value
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
                        position: place.geometry.location,
                        map: map,
                        title: place.name
                    });
                }
                document.getElementById("location-name").value = place.name;
                document.getElementById("location-address").value = place.formatted_address;
                document.getElementById("location-lat").value = place.geometry.location.lat();
                document.getElementById("location-lng").value = place.geometry.location.lng();
                document.getElementById("location-place-id").value = place.place_id;
                document.getElementById("location-search").value = place.name;
            }
        }
    );
}