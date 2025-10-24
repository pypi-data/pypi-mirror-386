#!/usr/bin/env python
"""Comprehensive test of point set conversion."""
import numpy as np
import itk
import napari
import itk_napari_conversion

print("=" * 60)
print("Test 1: Basic ITK to napari conversion")
print("=" * 60)
PointSetType = itk.PointSet[itk.F, 3]
point_set = PointSetType.New()
points_data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float32)
points = itk.vector_container_from_array(points_data.flatten())
point_set.SetPoints(points)

points_layer = itk_napari_conversion.points_layer_from_point_set(point_set)
print(f"✓ Converted to napari")
print(f"  Points match: {np.allclose(points_data, points_layer.data)}")

print("\n" + "=" * 60)
print("Test 2: ITK with metadata to napari")
print("=" * 60)
point_set2 = PointSetType.New()
point_set2.SetPoints(points)
point_set2["annotation"] = "test points"
point_set2["count"] = 42

print(f"Set metadata on ITK point set:")
print(f"  point_set2['annotation'] = 'test points'")
print(f"  point_set2['count'] = 42")

points_layer2 = itk_napari_conversion.points_layer_from_point_set(point_set2)
print(f"\nConverted to napari:")
print(f"  Metadata: {points_layer2.metadata}")
print(f"  Has 'annotation': {'annotation' in points_layer2.metadata}")
print(f"  Has 'count': {'count' in points_layer2.metadata}")
if 'annotation' in points_layer2.metadata:
    print(f"  annotation value: {points_layer2.metadata['annotation']}")
if 'count' in points_layer2.metadata:
    print(f"  count value: {points_layer2.metadata['count']}")

print("\n" + "=" * 60)
print("Test 3: napari with features to ITK")
print("=" * 60)
data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])
features = {'feature': np.array([10.0, 20.0, 30.0])}
points_layer3 = napari.layers.Points(data, features=features)

print(f"Napari features type: {type(points_layer3.features)}")
print(f"Napari features: {points_layer3.features}")

point_set3 = itk_napari_conversion.point_set_from_points_layer(points_layer3)
point_data3 = point_set3.GetPointData()
print(f"\nITK point data size: {point_data3.Size()}")
if point_data3.Size() > 0:
    arr = itk.array_from_vector_container(point_data3)
    print(f"✓ Point data retrieved: {arr}")
    print(f"  Matches features: {np.allclose(features['feature'], arr)}")
else:
    print(f"✗ Point data is empty!")

print("\n" + "=" * 60)
print("Test 4: napari with metadata to ITK")
print("=" * 60)
metadata = {"annotation": "test points", "count": 42}
points_layer4 = napari.layers.Points(data, metadata=metadata)

point_set4 = itk_napari_conversion.point_set_from_points_layer(points_layer4)
metadata_dict = point_set4.GetMetaDataDictionary()
keys = metadata_dict.GetKeys()

print(f"Metadata dictionary keys: {keys}")
print(f"Has 'annotation': {'annotation' in keys}")
print(f"Has 'count': {'count' in keys}")

if 'annotation' in keys:
    print(f"  annotation = {point_set4['annotation']}")
if 'count' in keys:
    print(f"  count = {point_set4['count']}")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
