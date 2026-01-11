#!/usr/bin/env python3
"""
Zolo Usage Examples

Demonstrates how to use the zolo library (parser for .zolo files).
"""

import sys
from pathlib import Path

# Add src directory to path (for local testing)
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import zolo

print("="*80)
print("Zolo Parser Usage Examples")
print("="*80)

# Example 1: Load from string (string-first)
print("\n1. Load from string (string-first):")
print("-" * 80)

data = zolo.loads('''
port: 8080
country: NO
enabled: yes
version: 1.0
''')

print(f"port: {data['port']!r} (type: {type(data['port']).__name__})")
print(f"country: {data['country']!r} (type: {type(data['country']).__name__})")
print(f"enabled: {data['enabled']!r} (type: {type(data['enabled']).__name__})")
print(f"version: {data['version']!r} (type: {type(data['version']).__name__})")

# Example 2: Load with type hints
print("\n2. Load with type hints:")
print("-" * 80)

data = zolo.loads('''
port(int): 8080
price(float): 19.99
enabled(bool): true
label: Welcome
''')

print(f"port: {data['port']!r} (type: {type(data['port']).__name__})")
print(f"price: {data['price']!r} (type: {type(data['price']).__name__})")
print(f"enabled: {data['enabled']!r} (type: {type(data['enabled']).__name__})")
print(f"label: {data['label']!r} (type: {type(data['label']).__name__})")

# Example 3: Load from file
print("\n3. Load from file:")
print("-" * 80)

example_file = Path(__file__).parent / "basic.zolo"
data = zolo.load(example_file)

print(f"app_name: {data['app_name']!r}")
print(f"server.port: {data['server']['port']!r} (type: {type(data['server']['port']).__name__})")
print(f"server.ssl: {data['server']['ssl']!r} (type: {type(data['server']['ssl']).__name__})")
print(f"features.analytics: {data['features']['analytics']!r} (type: {type(data['features']['analytics']).__name__})")

# Example 4: Dump to string
print("\n4. Dump to string:")
print("-" * 80)

data = {
    'app': 'My App',
    'port': 8080,
    'enabled': True
}

output = zolo.dumps(data)
print(output)

# Example 5: Dump to file
print("\n5. Dump to file:")
print("-" * 80)

output_file = Path(__file__).parent / "output_example.zolo"
zolo.dump(data, output_file)
print(f"✅ Dumped to: {output_file}")

# Clean up
output_file.unlink()
print(f"🗑️  Cleaned up: {output_file}")

print("\n" + "="*80)
print("✅ All examples completed successfully!")
print("="*80)
