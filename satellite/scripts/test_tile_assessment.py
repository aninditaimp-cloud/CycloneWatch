
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from satellite_analysis import assess_location

print("CYCLONEWATCH TILE ASSESSMENT TEST")
print("---------------------------------")

# Known point inside an actual satellite flood polygon
latitude = 20.302503058291336
longitude = 86.47896922976199

print("Testing known flood location...")
result = assess_location(latitude, longitude)

for key, value in result.items():
    print(f"{key}: {value}")

print("\nTEST RESULT")
print("-----------")

if result["assessment_status"] == "impact_detected":
    print("SUCCESS: Real satellite flood impact detected!")
else:
    print("FAILED: Expected impact_detected for this known point.")
