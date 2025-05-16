# Map Component Integration

- Utilize Leaflet.js to display processed poles on an interactive map within the results page.
- In the `result.html` template:
  - Include Leaflet CSS and JS libraries.
  - Add a `<div>` element with an ID (e.g., `poleMap`) to serve as the map container.
- During backend processing:
  - Collect geographic data for each processed pole, including:
    - Normalized Pole ID
    - Latitude and Longitude
    - Status summary (e.g., "Make-Ready Required", "No Change", "Issue Detected")
  - Pass this data as a JSON object to the `result.html` template.
- In the frontend JavaScript:
  - Initialize the Leaflet map centered to encompass all pole locations.
  - Iterate through the pole data to:
    - Place markers at each pole's location.
    - Bind popups to each marker displaying the Pole ID and status.
    - Optionally, use different marker icons or colors based on the pole's status.
