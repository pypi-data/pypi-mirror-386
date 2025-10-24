#!/usr/bin/env python
"""Check napari features type."""
import numpy as np
import napari

data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
features = {'feature': np.array([10.0, 20.0])}
points_layer = napari.layers.Points(data, features=features)

print(f"Features type: {type(points_layer.features)}")
print(f"Features: {points_layer.features}")
print(f"Features keys: {list(points_layer.features.keys())}")
print(f"Feature values type: {type(points_layer.features['feature'])}")
print(f"Feature values: {points_layer.features['feature']}")
