#!/usr/bin/env python
"""Simple test to debug point set conversion."""
import numpy as np
import itk
import napari
import itk_napari_conversion

# Test 1: Basic conversion
print("Test 1: Basic point set to napari")
PointSetType = itk.PointSet[itk.F, 3]
point_set = PointSetType.New()
points_data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]], dtype=np.float32)
points = itk.vector_container_from_array(points_data.flatten())
point_set.SetPoints(points)

points_layer = itk_napari_conversion.points_layer_from_point_set(point_set)
print(f"  Points data shape: {points_layer.data.shape}")
print(f"  Points match: {np.allclose(points_data, points_layer.data)}")

# Test 2: With features
print("\nTest 2: Point set with features")
point_set2 = PointSetType.New()
point_set2.SetPoints(points)
feature_data = np.array([10.0, 20.0, 30.0], dtype=np.float32)
point_data = itk.vector_container_from_array(feature_data)
point_set2.SetPointData(point_data)

points_layer2 = itk_napari_conversion.points_layer_from_point_set(point_set2)
print(f"  Has features: {points_layer2.features is not None}")
if points_layer2.features:
    print(f"  Feature keys: {list(points_layer2.features.keys())}")
    print(f"  Feature values match: {np.allclose(feature_data, points_layer2.features['feature'])}")

# Test 3: Napari to ITK
print("\nTest 3: Napari points to ITK point set")
data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])
points_layer3 = napari.layers.Points(data)
print(f"  Points layer affine: {points_layer3.affine}")
print(f"  Points layer features: {points_layer3.features}")

point_set3 = itk_napari_conversion.point_set_from_points_layer(points_layer3)
points_array = itk.array_from_vector_container(point_set3.GetPoints())
print(f"  Points array shape: {points_array.shape}")
print(f"  Points match: {np.allclose(data, points_array)}")

# Test 4: With metadata
print("\nTest 4: Metadata handling")
point_set4 = PointSetType.New()
point_set4.SetPoints(points)
point_set4["annotation"] = "test points"
point_set4["count"] = 42

points_layer4 = itk_napari_conversion.points_layer_from_point_set(point_set4)
print(f"  Metadata: {points_layer4.metadata}")

print("\nAll tests completed!")
