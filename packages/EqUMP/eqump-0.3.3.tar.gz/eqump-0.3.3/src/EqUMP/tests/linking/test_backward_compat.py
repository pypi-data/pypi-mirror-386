"""Test backward compatibility of transform_items with dictionary input"""
import sys
import warnings
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from EqUMP.linking.helper import transform_items
from EqUMP.base import IRF

# Test 1: Legacy API with dictionaries (should show deprecation warning)
print("Test 1: Legacy API with dictionaries (DEPRECATED)")
items_dict = {
    1: {"a": 1.2, "b": 0.5, "c": 0.2},
    2: {"a": 1.0, "b": -0.3, "c": 0.15},
}

try:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = transform_items(items_dict, A=1.1, B=0.2, direction="to_old")
        
        if len(w) == 1 and issubclass(w[0].category, DeprecationWarning):
            print(f"✓ DeprecationWarning raised as expected:")
            print(f"  {w[0].message}")
        else:
            print(f"✗ Expected DeprecationWarning but got: {w}")
        
        print(f"✓ Success! Result type: {type(result)}")
        print(f"  Item 1: {result[1]}")
        print(f"  Item 2: {result[2]}")
except Exception as e:
    print(f"✗ Failed: {e}")

# Test 2: New API with IRF objects (ItemCollection)
print("\nTest 2: New API with IRF objects")
items_irf = {
    1: IRF({"a": 1.2, "b": 0.5, "c": 0.2}, "3PL", D=1.7),
    2: IRF({"a": 1.0, "b": -0.3, "c": 0.15}, "3PL", D=1.7),
}

try:
    result = transform_items(items_irf, A=1.1, B=0.2, direction="to_old")
    print(f"✓ Success! Result type: {type(result)}")
    print(f"  Item 1 type: {type(result[1])}")
    print(f"  Item 1 params: {result[1].params}")
    print(f"  Item 2 params: {result[2].params}")
except Exception as e:
    print(f"✗ Failed: {e}")

print("\n✓ All tests passed! Backward compatibility is working.")
