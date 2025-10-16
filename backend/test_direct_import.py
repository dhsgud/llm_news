import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Testing direct execution of trend_aggregator.py...")

try:
    with open('services/trend_aggregator.py', 'r', encoding='utf-8') as f:
        code = f.read()
    
    # Create a namespace
    namespace = {}
    
    # Execute the code
    exec(code, namespace)
    
    print(f"Execution successful!")
    print(f"Defined names: {[x for x in namespace.keys() if not x.startswith('_')]}")
    
    if 'TrendAggregator' in namespace:
        print(f"??TrendAggregator found: {namespace['TrendAggregator']}")
    else:
        print("??TrendAggregator not found")
        
except Exception as e:
    print(f"??Execution failed: {e}")
    import traceback
    traceback.print_exc()
