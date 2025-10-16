import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Importing module...")
import services.trend_aggregator as ta

print(f"Module: {ta}")
print(f"Module file: {ta.__file__}")
print(f"Module contents: {[x for x in dir(ta) if not x.startswith('_')]}")

# Try to see if there's an error
print("\nTrying to access TrendAggregator...")
try:
    print(ta.TrendAggregator)
except AttributeError as e:
    print(f"AttributeError: {e}")
    
# Check if TrendSummary exists
print("\nTrying to access TrendSummary...")
try:
    print(ta.TrendSummary)
except AttributeError as e:
    print(f"AttributeError: {e}")
