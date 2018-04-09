/*
 * The list of visible pizzerias is refreshed when the map moves.
 */

const server = "http://localhost:8888/v1";
const bucket = "restaurants";
const collection = "pizzerias";


// A map with OpenStreetMap background.
const map = L.map('map');
L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

map.on('load moveend', (e) => {
  const bbox = e.target.getBounds();
  // Query ElasticSearch with the current map bounds as search extent.
  searchExtent(bbox)
    .then(hits => {
      // Render the results as a list of bullet points.
      const listing = document.getElementById("listing");
      listing.innerHTML = "";
      hits.map((pizzeria) => {
        const node = document.createElement("li");
        const textnode = document.createTextNode(pizzeria.name || "(No name)");
        node.appendChild(textnode);
        listing.appendChild(node);
      });
    });
});
// Center map on Roma.
map.setView([41.8, 12.5], 9);

// Add a sidebar panel to show results.
L.control.sidebar('sidebar').addTo(map).show();


// Fetch all records from Kinto to populate the map layer.
// (Note: this also could have been done using ES.)
const kinto = new KintoClient(server);

kinto.bucket(bucket).collection(collection).listRecords()
  .then(({data: pizzerias}) => {
    // Add a circle on the map for each record.
    pizzerias.map((pizzeria) => {
      // Leaflet maps use [lat, lng] and [lng, lat].
      const latlng = [pizzeria._geoloc['lat'], pizzeria._geoloc['lng']];
      L.circleMarker(latlng, {
        color: 'purple',
        fillOpacity: 0.7
      }).setRadius(4).addTo(map);
    });
  });



function searchExtent(bbox) {
  const boundingBox = [
    // P1 lat, lng
    bbox.getNorthWest().lat, bbox.getNorthWest().lng,
    // P2 lat, lng
    bbox.getSouthEast().lat, bbox.getSouthEast().lng
  ];
  const query = {
    insideBoundingBox: boundingBox.join()
  };

  return fetch(`${server}/buckets/${bucket}/collections/${collection}/search`, {
    body: JSON.stringify(query), method: "POST", headers: {"Content-Type": "application/json"}
  })
    .then(response => response.json())
    .then(({hits}) => hits);
}
