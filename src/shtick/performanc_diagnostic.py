#!/usr/bin/env python3
"""
Diagnostic script to identify performance bottlenecks
"""

import time
import tempfile
import os
import sys
import cProfile
import pstats
from pathlib import Path

# Fix imports
current_file = Path(__file__).resolve()
shtick_dir = current_file.parent
src_dir = shtick_dir.parent
project_root = src_dir.parent

sys.path.insert(0, str(shtick_dir))
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(project_root))

try:
    from shtick import ShtickManager
    from shtick.config import Config

    print("✓ Successfully imported shtick modules")

    # Check version
    if hasattr(ShtickManager, "_get_all_items_by_type"):
        print("✓ OPTIMIZED version detected")
        VERSION = "optimized"
    else:
        print("✓ STANDARD version detected")
        VERSION = "standard"
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


def profile_operation(func, name):
    """Profile a single operation"""
    print(f"\nProfiling: {name}")
    print("-" * 50)

    # Time it
    start = time.perf_counter()
    func()
    elapsed = (time.perf_counter() - start) * 1000
    print(f"Time: {elapsed:.2f}ms")

    # Profile it
    profiler = cProfile.Profile()
    profiler.enable()
    func()
    profiler.disable()

    # Show top time consumers
    stats = pstats.Stats(profiler)
    stats.sort_stats("cumulative")
    print("\nTop 10 time consumers:")
    stats.print_stats(10)

    return elapsed


def main():
    """Run diagnostic tests"""
    print("=" * 60)
    print(f"PERFORMANCE DIAGNOSTICS - {VERSION.upper()} VERSION")
    print("=" * 60)

    # Setup
    temp_dir = tempfile.mkdtemp(prefix="shtick_diag_")
    config_path = os.path.join(temp_dir, "config.toml")

    with open(config_path, "w") as f:
        f.write("[persistent]\n")

    # Disable logging
    import logging

    logging.disable(logging.CRITICAL)

    manager = ShtickManager(config_path=config_path, debug=False)

    # Test 1: Single add operation
    counter = 0

    def add_single():
        nonlocal counter
        manager.add_alias(f"test_{counter}", f"echo {counter}", "test")
        counter += 1

    profile_operation(add_single, "Single alias add")

    # Test 2: Batch operation (if available)
    if hasattr(manager, "add_items_batch"):

        def add_batch():
            items = [
                {
                    "type": "alias",
                    "group": "batch",
                    "key": f"batch_{i}",
                    "value": f"echo {i}",
                }
                for i in range(100)
            ]
            manager.add_items_batch(items)

        profile_operation(add_batch, "Batch add (100 items)")

    # Test 3: Conflict checking
    # First add some items
    for i in range(100):
        manager.add_alias(f"existing_{i}", f"echo {i}", "conflicts")

    def check_conflicts():
        for i in range(50):
            manager.check_conflicts("alias", f"new_{i}", "conflicts")

    profile_operation(check_conflicts, "Conflict checking (50 checks)")

    # Test 4: List operations
    def list_all():
        items = manager.list_items()
        return len(items)

    profile_operation(list_all, "List all items")

    # Test 5: Specific to optimized version
    if VERSION == "optimized":
        print("\n" + "=" * 60)
        print("OPTIMIZED VERSION SPECIFIC CHECKS")
        print("=" * 60)

        # Check if caches are working
        if hasattr(manager, "_get_all_items_by_type") and hasattr(
            manager._get_all_items_by_type, "cache_info"
        ):
            cache_info = manager._get_all_items_by_type.cache_info()
            print(f"\nLRU Cache stats:")
            print(f"  Hits: {cache_info.hits}")
            print(f"  Misses: {cache_info.misses}")
            print(
                f"  Hit rate: {cache_info.hits/(cache_info.hits+cache_info.misses)*100:.1f}%"
                if cache_info.hits + cache_info.misses > 0
                else "  Hit rate: N/A"
            )

        # Check if we're clearing caches too often
        clear_count = 0
        original_clear = None
        if hasattr(manager, "_clear_caches"):
            original_clear = manager._clear_caches

            def counting_clear():
                nonlocal clear_count
                clear_count += 1
                original_clear()

            manager._clear_caches = counting_clear

        # Do some operations
        for i in range(10):
            manager.add_alias(f"cache_test_{i}", f"echo {i}", "cache_test")

        print(f"\nCache clears during 10 adds: {clear_count}")

        if clear_count > 10:
            print("⚠️  WARNING: Caches are being cleared too frequently!")

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir)

    print("\n✓ Diagnostic complete")


if __name__ == "__main__":
    main()
