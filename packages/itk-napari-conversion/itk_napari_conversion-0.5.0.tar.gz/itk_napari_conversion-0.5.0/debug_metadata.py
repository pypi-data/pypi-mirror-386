#!/usr/bin/env python
"""Debug script to test metadata API."""
import numpy as np
import itk
import napari

# Test metadata API
print("Testing ITK metadata API...")
PointSetType = itk.PointSet[itk.F, 3]
point_set = PointSetType.New()

# Add points
points_data = np.array([[1.0, 2.0, 3.0]], dtype=np.float32)
points = itk.vector_container_from_array(points_data.flatten())
point_set.SetPoints(points)

# Try different ways to set metadata
print("\n1. Using point_set[key] = value:")
try:
    point_set["test1"] = "hello"
    print(f"   Set 'test1' = 'hello'")
    print(f"   Read back: {point_set['test1']}")
except Exception as e:
    print(f"   Error: {e}")

print("\n2. Using EncapsulateMetaData:")
try:
    metadata_dict = point_set.GetMetaDataDictionary()
    itk.EncapsulateMetaData(metadata_dict, "test2", "world")
    print(f"   Set 'test2' = 'world'")
    print(f"   Read back: {point_set['test2']}")
except Exception as e:
    print(f"   Error: {e}")

print("\n3. Check napari affine:")
data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
scale = np.array([2.0, 3.0, 4.0])
points_layer = napari.layers.Points(data, scale=scale)

print(f"   Affine matrix:\n{np.asarray(points_layer.affine)}")
print(f"   Scale: {points_layer.scale}")
print(f"   Translate: {points_layer.translate}")

identity = np.eye(4)
print(f"   Is identity: {np.allclose(np.asarray(points_layer.affine), identity)}")
