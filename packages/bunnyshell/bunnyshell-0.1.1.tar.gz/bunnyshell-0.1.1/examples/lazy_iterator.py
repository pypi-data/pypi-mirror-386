#!/usr/bin/env python3
"""
Sync lazy iterator example.

Shows the difference between .list() and .iter()
"""

from bunnyshell import Sandbox

API_KEY = "hopx_f0dfeb804627ca3c1ccdd3d43d2913c9"

print("📊 Iterator vs List Comparison\n")

# Method 1: .list() - loads ALL into memory
print("1. Using .list() (loads all into memory):")
sandboxes = Sandbox.list(api_key=API_KEY)
print(f"   Loaded {len(sandboxes)} sandboxes into memory")
for sb in sandboxes[:3]:
    info = sb.get_info()
    print(f"   • {sb.sandbox_id}: {info.status}")

# Method 2: .iter() - lazy loading (better for large lists)
print("\n2. Using .iter() (lazy loading):")
count = 0
for sandbox in Sandbox.iter(api_key=API_KEY):
    info = sandbox.get_info()
    print(f"   • {sandbox.sandbox_id}: {info.status}")
    count += 1
    
    if count >= 3:  # Stop early
        print("   (stopping early - remaining pages not fetched!)")
        break

print("\n✅ With .iter(), you can break early and save API calls!")

