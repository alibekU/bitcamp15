var marker, map, lat, lng, pos;
function initialize() {
  var mapOptions = {
    zoom: 8
  };
  map = new google.maps.Map(document.getElementById('map-canvas'), mapOptions);
  map.setOptions({disableDoubleClickZoom: true});
  if(navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(function(position) {
      pos = new google.maps.LatLng(position.coords.latitude,
                                       position.coords.longitude);
      document.getElementById("latbox").value = pos.lat();
      document.getElementById("lngbox").value = pos.lng();
      map.setCenter(pos);
      placeMarker(pos,map);
    }, function() {
      handleNoGeolocation(true);
    });
  } else {
    d = {lat: 40.79464329620785, lng: -77.85736083984375};
    map.setCenter(d);
    placeMarker(d,map)
    handleNoGeolocation(false);
  }

  google.maps.event.addListener(map, 'click', function(e) {
    placeMarker(e.latLng, map);
  });
  function placeMarker(position, map) {
    if(marker != null)
      marker.setMap(null);
    marker = new google.maps.Marker({
      position: position,
      map: map
    });
    map.panTo(position);
    document.getElementById("latbox").value = marker.getPosition().lat();
    document.getElementById("lngbox").value = marker.getPosition().lng();
  }
}
google.maps.event.addDomListener(window, 'load', initialize);
