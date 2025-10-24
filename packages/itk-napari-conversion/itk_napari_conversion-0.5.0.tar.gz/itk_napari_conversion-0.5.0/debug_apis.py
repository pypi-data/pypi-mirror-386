#!/usr/bin/env python
"""Debug script to understand ITK PointSet APIs."""
import numpy as np
import itk

print("=== Testing ITK PointSet Metadata ===")
PointSetType = itk.PointSet[itk.F, 3]
point_set = PointSetType.New()

# Add points
points_data = np.array([[1.0, 2.0, 3.0]], dtype=np.float32)
points = itk.vector_container_from_array(points_data.flatten())
point_set.SetPoints(points)

# Test 1: Try setting metadata
print("\n1. Setting metadata with bracket notation:")
try:
    point_set["test_key"] = "test_value"
    print("   ✓ Set metadata")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 2: Try reading metadata
print("\n2. Reading metadata with bracket notation:")
try:
    value = point_set["test_key"]
    print(f"   ✓ Read metadata: {value}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 3: Check metadata dictionary
print("\n3. Checking metadata dictionary:")
try:
    md = point_set.GetMetaDataDictionary()
    print(f"   Dictionary type: {type(md)}")
    keys = md.GetKeys()
    print(f"   Keys: {keys}")
    print(f"   Number of keys: {len(keys)}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 4: Point data
print("\n=== Testing Point Data ===")
feature_data = np.array([10.0], dtype=np.float32)
print(f"Feature data: {feature_data}")
print(f"Feature data shape: {feature_data.shape}")
print(f"Feature data dtype: {feature_data.dtype}")

try:
    point_data = itk.vector_container_from_array(feature_data)
    print(f"   ✓ Created vector container")
    print(f"   Container size: {point_data.Size()}")
    point_set.SetPointData(point_data)
    print(f"   ✓ Set point data")
    
    # Try to read back
    retrieved = point_set.GetPointData()
    print(f"   Retrieved size: {retrieved.Size()}")
    
    if retrieved.Size() > 0:
        arr = itk.array_from_vector_container(retrieved)
        print(f"   ✓ Read back: {arr}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 5: Try dict_from_pointset
print("\n=== Testing dict_from_pointset ===")
try:
    state = itk.dict_from_pointset(point_set)
    print(f"   State keys: {list(state.keys())}")
    if 'test_key' in state:
        print(f"   ✓ Metadata in state: {state['test_key']}")
    else:
        print(f"   ✗ Metadata not in state")
except Exception as e:
    print(f"   ✗ Error: {e}")
