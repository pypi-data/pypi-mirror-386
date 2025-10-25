# AnyMap

[![image](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/opengeos/anymap/HEAD)
[![image](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/opengeos/anymap/blob/main)
[![image](https://img.shields.io/pypi/v/anymap.svg)](https://pypi.python.org/pypi/anymap)
[![image](https://img.shields.io/conda/vn/conda-forge/anymap.svg)](https://anaconda.org/conda-forge/anymap)
[![Conda Recipe](https://img.shields.io/badge/recipe-anymap-green.svg)](https://github.com/conda-forge/anymap-feedstock)
[![image](https://static.pepy.tech/badge/anymap)](https://pepy.tech/project/anymap)
[![Conda Downloads](https://img.shields.io/conda/dn/conda-forge/anymap.svg)](https://anaconda.org/conda-forge/anymap)
[![image](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<!-- [![Docker Image](https://img.shields.io/badge/docker-opengeos%2Fanymap-blue?logo=docker)](https://hub.docker.com/r/opengeos/anymap/tags)     -->

**A Python package for creating interactive maps with anywidget and JavaScript mapping libraries**

-   GitHub repo: <https://github.com/opengeos/anymap>
-   Documentation: <https://anymap.dev>
-   PyPI: <https://pypi.org/project/anymap>
-   Conda-forge: <https://anaconda.org/conda-forge/anymap>
-   Free software: MIT License

## Features

-   🗺️ **Interactive Maps**: Create beautiful, interactive maps in Jupyter notebooks
-   🔄 **Bidirectional Communication**: Full Python ↔ JavaScript communication
-   📱 **Multi-cell Support**: Render maps in multiple notebook cells without conflicts
-   🎯 **MapLibre Integration**: Built-in support for MapLibre GL JS
-   🛠️ **Extensible**: Easy to add support for other mapping libraries
-   🚀 **Familiar API**: Similar to ipyleaflet for easy migration

## Installation

```bash
pip install anymap
```

```bash
conda install -c conda-forge anymap
```

## Quick Start

```python
from anymap import MapLibreMap

# Create a basic map
m = MapLibreMap(
    center=[-122.4194, 37.7749],  # San Francisco
    zoom=12,
    height="600px"
)
m
```

## Basic Usage

### Creating Maps

```python
from anymap import MapLibreMap

# Create a map with custom settings
m = MapLibreMap(
    center=[-74.0060, 40.7128],  # New York City
    zoom=13,
    height="500px",
    bearing=45,  # Map rotation
    pitch=60     # 3D tilt
)
```

### Adding Markers

```python
# Add a marker with popup
m.add_marker(
    lat=40.7128,
    lng=-74.0060,
    popup="<h3>New York City</h3><p>The Big Apple</p>"
)
```

### Working with GeoJSON

```python
# Add GeoJSON data
geojson_data = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [-74.0060, 40.7128]
            },
            "properties": {"name": "NYC"}
        }
    ]
}

m.add_geojson_layer(
    layer_id="cities",
    geojson_data=geojson_data,
    layer_type="circle",
    paint={
        "circle-radius": 8,
        "circle-color": "#ff0000"
    }
)
```

### Event Handling

```python
def handle_click(event):
    lat, lng = event['lngLat']
    print(f"Clicked at: {lat:.4f}, {lng:.4f}")

m.on_map_event('click', handle_click)
```

### Dynamic Updates

```python
# Change map properties
m.set_center(-0.1278, 51.5074)  # London
m.set_zoom(14)

# Animate to a location
m.fly_to(2.3522, 48.8566, zoom=15)  # Paris
```

## Multi-Cell Rendering

AnyMap is designed to work seamlessly across multiple notebook cells:

```python
# Cell 1
m = MapLibreMap(center=[0, 0], zoom=2)
m

# Cell 2 - Same map instance
m.add_marker(0, 0, popup="Origin")

# Cell 3 - Display again
m
```

## Advanced Features

### Layer Management

```python
# Add and remove layers
m.add_source("my-source", {
    "type": "geojson",
    "data": geojson_data
})

m.add_layer("my-layer", {
    "id": "my-layer",
    "type": "circle",
    "source": "my-source",
    "paint": {"circle-radius": 5}
})

# Remove layers
m.remove_layer("my-layer")
m.remove_source("my-source")
```

### Custom JavaScript Methods

```python
# Call any MapLibre GL JS method
m.call_js_method('easeTo', {
    'center': [lng, lat],
    'zoom': 14,
    'duration': 2000
})
```

## Examples

Check out the example notebooks in the `examples/` directory:

-   `basic_usage.ipynb` - Basic map creation and interaction
-   `advanced_features.ipynb` - Advanced layer management and styling
-   `multi_cell_test.ipynb` - Multi-cell rendering tests

## Development

To set up for development:

```bash
git clone https://github.com/opengeos/anymap.git
cd anymap
pip install -e .
```

Run tests:

```bash
python -m unittest tests.test_anymap -v
```

## Roadmap

-   ✅ MapLibre GL JS backend
-   ✅ Mapbox GL JS backend
-   ✅ Leaflet backend
-   ✅ OpenLayers backend
-   ✅ DeckGL backend
-   ✅ KeplerGL backend
-   🔲 Cesium backend
-   🔲 Potree backend

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
