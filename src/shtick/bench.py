#!/usr/bin/env python3
"""
Intensive shtick performance benchmark
Tests with larger datasets to show real performance differences
"""

import time
import tempfile
import os
import sys
import shutil
from pathlib import Path
import statistics
from datetime import datetime
import json
import random
import string

# Fix import paths
current_file = Path(__file__).resolve()
shtick_dir = current_file.parent
src_dir = shtick_dir.parent
project_root = src_dir.parent

sys.path.insert(0, str(shtick_dir))
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(project_root))

# Import handling
SHTICK_AVAILABLE = False
OPTIMIZED_VERSION = False

try:
    from shtick import ShtickManager
    from shtick.config import Config
    from shtick.generator import Generator

    SHTICK_AVAILABLE = True
    print("✓ Successfully imported shtick modules")

    if hasattr(ShtickManager, "_get_all_items_by_type"):
        OPTIMIZED_VERSION = True
        print("✓ Detected OPTIMIZED version with caching")
    else:
        print("✓ Detected STANDARD version without optimizations")

except ImportError:
    try:
        import shtick
        from config import Config
        from generator import Generator

        class ShtickManager(shtick.ShtickManager):
            pass

        SHTICK_AVAILABLE = True
        print("✓ Successfully imported shtick modules directly")

    except ImportError as e:
        print(f"✗ Could not import shtick modules: {e}")
        sys.exit(1)


def time_operation(func, iterations=10, warmup=2):
    """Time an operation with proper warmup"""
    # Warmup
    for _ in range(warmup):
        try:
            func()
        except:
            pass

    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # ms

    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "min": min(times),
        "max": max(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        "total": sum(times),
    }


def generate_random_key(prefix="key", length=8):
    """Generate random key for testing"""
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{prefix}_{suffix}"


class IntensiveBenchmark:
    """Intensive benchmark suite with larger datasets"""

    def __init__(self):
        self.temp_dir = None
        self.config_path = None
        self.manager = None
        self.results = {}
        self.version_info = {
            "optimized": OPTIMIZED_VERSION,
            "version": "optimized" if OPTIMIZED_VERSION else "standard",
        }

    def record_result(self, category, operation, stats, notes=None):
        """Record benchmark results"""
        if category not in self.results:
            self.results[category] = {}
        self.results[category][operation] = {
            "mean_ms": stats["mean"],
            "median_ms": stats["median"],
            "min_ms": stats["min"],
            "max_ms": stats["max"],
            "stdev_ms": stats["stdev"],
            "total_ms": stats.get("total", 0),
            "notes": notes,
        }

    def setup(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp(prefix="shtick_bench_")
        self.config_path = os.path.join(self.temp_dir, "config.toml")

        with open(self.config_path, "w") as f:
            f.write("[persistent]\n")

        # Create manager with debug=False to disable logging
        self.manager = ShtickManager(config_path=self.config_path, debug=False)

        # Disable all logging during benchmarks
        import logging

        logging.disable(logging.CRITICAL)

        # Disable auto-generation
        if hasattr(self.manager, "_save_and_regenerate"):
            original_save = self.manager._save_and_regenerate

            def minimal_save(affected_groups=None, changed_items=None):
                config = self.manager._get_config()
                config.save()
                if hasattr(self.manager, "_clear_caches"):
                    self.manager._clear_caches()

            self.manager._original_save_and_regenerate = original_save
            self.manager._save_and_regenerate = minimal_save

        if hasattr(Config, "clear_all_caches"):
            Config.clear_all_caches()

        print(f"✓ Test environment created (logging disabled)")

    def cleanup(self):
        """Cleanup test environment"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

        shtick_dir = os.path.expanduser("~/.config/shtick")
        # Clean up all test groups
        for prefix in ["bench_", "stress_", "large_"]:
            for entry in os.listdir(shtick_dir) if os.path.exists(shtick_dir) else []:
                if entry.startswith(prefix):
                    path = os.path.join(shtick_dir, entry)
                    if os.path.isdir(path):
                        shutil.rmtree(path)

    def benchmark_key_validation_intensive(self):
        """Test key validation with many keys"""
        print("\n=== INTENSIVE Key Validation (10,000 keys) ===")

        # Generate test keys
        valid_keys = [generate_random_key("valid", 12) for _ in range(5000)]

        # Generate various invalid keys
        invalid_keys = []
        for i in range(1000):
            invalid_keys.extend(
                [
                    f"{i}invalid",  # starts with number
                    f"invalid-{i}!",  # invalid character
                    f"inv alid{i}",  # space
                    f"-invalid{i}",  # starts with dash
                    f"inv@lid{i}",  # invalid character
                ]
            )

        all_keys = valid_keys + invalid_keys
        random.shuffle(all_keys)

        # Import validate_key if available
        try:
            from shtick.commands import validate_key
        except:
            try:
                from commands import validate_key
            except:
                print("Could not import validate_key function")
                return

        def validate_all():
            valid_count = 0
            for key in all_keys:
                try:
                    validate_key(key)
                    valid_count += 1
                except ValueError:
                    pass
            return valid_count

        print(f"Validating {len(all_keys)} keys...")
        stats = time_operation(validate_all, iterations=5)
        print(f"Total time for {len(all_keys)} validations: {stats['total']:.1f}ms")
        print(f"Average per 1000 keys: {stats['mean']/10:.2f}ms")
        print(f"Per-key validation: {stats['mean']/len(all_keys)*1000:.3f}μs")

        self.record_result("Key Validation", f"Validate {len(all_keys)} keys", stats)

    def benchmark_conflict_checking_intensive(self):
        """Test conflict checking with large dataset"""
        print("\n=== INTENSIVE Conflict Checking ===")

        # Create a large dataset across multiple groups
        print("Creating large dataset...")
        groups = ["work", "dev", "test", "prod", "staging"]
        items_per_group = 200

        start = time.perf_counter()
        for group in groups:
            for i in range(items_per_group):
                self.manager.add_alias(
                    f"{group}_alias_{i}", f"echo {group}_{i}", f"stress_{group}"
                )
                if i % 3 == 0:
                    self.manager.add_env(
                        f"{group}_var_{i}", f"value_{i}", f"stress_{group}"
                    )
        setup_time = (time.perf_counter() - start) * 1000

        total_items = len(groups) * items_per_group * 4 // 3  # aliases + 1/3 env vars
        print(f"Created {total_items} items in {setup_time:.0f}ms")

        # Test 1: Check for non-existent items (no conflicts)
        print("\nTesting conflict checks for new items...")
        check_counter = 0

        def check_new_items():
            nonlocal check_counter
            for _ in range(100):
                key = generate_random_key("newitem", 10)
                self.manager.check_conflicts("alias", key, "stress_work")
                check_counter += 1

        stats = time_operation(check_new_items, iterations=10)
        print(
            f"Check 100 new items: {stats['mean']:.2f}ms total, {stats['mean']/100:.3f}ms per check"
        )
        self.record_result("Conflict Checking", "Check 100 new items", stats)

        # Test 2: Check for existing items (with conflicts)
        print("\nTesting conflict checks for existing items...")

        def check_existing_items():
            for group in groups:
                for i in range(0, 100, 10):  # Check every 10th item
                    self.manager.check_conflicts(
                        "alias", f"{group}_alias_{i}", "new_group"
                    )

        stats = time_operation(check_existing_items, iterations=10)
        checks = len(groups) * 10
        print(
            f"Check {checks} existing items: {stats['mean']:.2f}ms total, {stats['mean']/checks:.3f}ms per check"
        )
        self.record_result("Conflict Checking", f"Check {checks} existing items", stats)

        # Test 3: Repeated checks (cache effectiveness)
        print("\nTesting repeated conflict checks (cache test)...")
        test_keys = [f"work_alias_{i}" for i in range(20)]

        def check_repeated():
            for _ in range(10):  # Repeat 10 times
                for key in test_keys:
                    self.manager.check_conflicts("alias", key, "test_group")

        # Clear caches if available
        if hasattr(self.manager, "_clear_caches"):
            self.manager._clear_caches()

        stats = time_operation(check_repeated, iterations=5)
        total_checks = 10 * len(test_keys)
        print(f"Repeated checks ({total_checks} total): {stats['mean']:.2f}ms")
        print(f"Per-check (with potential caching): {stats['mean']/total_checks:.3f}ms")

        cache_note = "With LRU cache" if OPTIMIZED_VERSION else "No cache"
        self.record_result(
            "Conflict Checking",
            f"Repeated {total_checks} checks",
            stats,
            notes=cache_note,
        )

    def benchmark_list_operations_intensive(self):
        """Test listing with large datasets"""
        print("\n=== INTENSIVE List Operations ===")

        # Add more items if needed
        print("Ensuring large dataset...")
        groups = ["large_alpha", "large_beta", "large_gamma"]
        for group in groups:
            for i in range(100):
                self.manager.add_alias(f"{group}_alias_{i}", f"echo {i}", group)
                self.manager.add_env(f"{group}_env_{i}", f"{i}", group)
                if i % 2 == 0:
                    self.manager.add_function(
                        f"{group}_func_{i}", f"echo func {i}", group
                    )

        # Activate some groups
        self.manager.activate_group("large_alpha")
        self.manager.activate_group("large_beta")

        # Test listing all items
        def list_all():
            items = self.manager.list_items()
            return len(items)

        print("\nTesting list all items...")
        stats = time_operation(list_all, iterations=20)
        item_count = list_all()
        print(f"List {item_count} items: {stats['mean']:.2f}ms")
        print(f"Processing rate: {item_count/stats['mean']*1000:.0f} items/second")
        self.record_result("List Operations", f"List all ({item_count} items)", stats)

        # Test listing by group
        def list_large_group():
            items = self.manager.list_items("large_alpha")
            return len(items)

        print("\nTesting list single large group...")
        stats = time_operation(list_large_group, iterations=30)
        group_count = list_large_group()
        print(f"List group ({group_count} items): {stats['mean']:.2f}ms")
        self.record_result(
            "List Operations", f"List group ({group_count} items)", stats
        )

    def benchmark_batch_operations(self):
        """Test batch operations if available"""
        print("\n=== Batch Operations Performance ===")

        if not hasattr(self.manager, "add_items_batch"):
            print("Batch operations not available in this version")
            return

        # Test different batch sizes
        batch_sizes = [10, 50, 100, 500]

        for size in batch_sizes:
            print(f"\nTesting batch size: {size}")

            # Create batch
            def add_batch():
                items = [
                    {
                        "type": "alias",
                        "group": "batch_test",
                        "key": generate_random_key(f"batch{size}", 8),
                        "value": f"echo batch_{i}",
                    }
                    for i in range(size)
                ]
                self.manager.add_items_batch(items)

            stats = time_operation(add_batch, iterations=5)
            print(f"Add batch of {size}: {stats['mean']:.2f}ms total")
            print(f"Per-item in batch: {stats['mean']/size:.3f}ms")
            print(f"Items/second: {size/stats['mean']*1000:.0f}")

            self.record_result("Batch Operations", f"Batch add ({size} items)", stats)

            # Compare with individual adds
            def add_individual():
                for i in range(min(size, 20)):  # Limit to 20 for time
                    key = generate_random_key(f"indiv{size}", 8)
                    self.manager.add_alias(key, f"echo {i}", "batch_test")

            stats_indiv = time_operation(add_individual, iterations=3)
            per_item_indiv = stats_indiv["mean"] / min(size, 20)

            print(f"Individual adds: {per_item_indiv:.3f}ms per item")
            print(f"Batch speedup: {per_item_indiv/(stats['mean']/size):.1f}x")

    def benchmark_file_generation_intensive(self):
        """Test file generation with large groups"""
        print("\n=== INTENSIVE File Generation ===")

        # Re-enable generation
        if hasattr(self.manager, "_original_save_and_regenerate"):
            self.manager._save_and_regenerate = (
                self.manager._original_save_and_regenerate
            )

        # Create groups of different sizes
        group_sizes = {"small_gen": 10, "medium_gen": 100, "large_gen": 500}

        generator = Generator()
        config = self.manager._get_config()

        if hasattr(generator, "set_config_for_shells"):
            generator.set_config_for_shells(config)

        for group_name, size in group_sizes.items():
            print(f"\nTesting generation for {group_name} ({size} items)...")

            # Add items
            for i in range(size):
                self.manager.add_alias(f"alias_{i}", f"echo {i}", group_name)
                if i % 3 == 0:
                    self.manager.add_env(f"var_{i}", f"value_{i}", group_name)

            # Test full generation
            group = config.get_group(group_name)
            if group:

                def generate_full():
                    generator.generate_for_group(group)

                stats = time_operation(generate_full, iterations=5)
                print(f"Full generation: {stats['mean']:.2f}ms")
                self.record_result("File Generation", f"Generate {size} items", stats)

                # Test incremental if available
                if hasattr(generator, "update_group_incrementally"):
                    # Single change
                    def incremental_single():
                        changed_items = {
                            "added": [],
                            "modified": [("alias", "alias_0", "echo modified")],
                            "removed": [],
                        }
                        generator.update_group_incrementally(group, changed_items)

                    stats_single = time_operation(incremental_single, iterations=10)
                    print(f"Incremental (1 change): {stats_single['mean']:.2f}ms")
                    print(f"Speedup: {stats['mean']/stats_single['mean']:.1f}x")

                    # Multiple changes
                    def incremental_multi():
                        changed_items = {
                            "added": [
                                ("alias", f"new_{i}", f"echo new_{i}") for i in range(5)
                            ],
                            "modified": [
                                ("alias", f"alias_{i}", f"echo mod_{i}")
                                for i in range(5)
                            ],
                            "removed": [
                                ("alias", f"alias_{i+5}", f"echo {i+5}")
                                for i in range(5)
                            ],
                        }
                        generator.update_group_incrementally(group, changed_items)

                    stats_multi = time_operation(incremental_multi, iterations=10)
                    print(f"Incremental (15 changes): {stats_multi['mean']:.2f}ms")
                    print(f"Speedup: {stats['mean']/stats_multi['mean']:.1f}x")

                    self.record_result(
                        "File Generation",
                        f"Incremental {size} items (1 change)",
                        stats_single,
                    )
                    self.record_result(
                        "File Generation",
                        f"Incremental {size} items (15 changes)",
                        stats_multi,
                    )

    def benchmark_stress_test(self):
        """Ultimate stress test - simulate real heavy usage"""
        print("\n=== STRESS TEST - Simulating Heavy Usage ===")

        print("This simulates a power user with many groups and items...")

        # Setup: Create a realistic large configuration
        departments = ["engineering", "devops", "data", "security", "qa"]
        environments = ["dev", "staging", "prod"]

        total_start = time.perf_counter()

        # Create many items
        print("Creating large configuration...")
        for dept in departments:
            for env in environments:
                group_name = f"{dept}_{env}"

                # Add various items
                for i in range(50):
                    self.manager.add_alias(
                        f"{dept}_cmd_{i}", f"{dept} command {i}", group_name
                    )

                for i in range(30):
                    self.manager.add_env(
                        f"{dept.upper()}_VAR_{i}", f"{env}_{i}", group_name
                    )

                for i in range(10):
                    func_body = f"echo Running {dept} function {i} in {env}"
                    self.manager.add_function(f"{dept}_func_{i}", func_body, group_name)

        creation_time = (time.perf_counter() - total_start) * 1000

        # Now run typical operations
        print("\nRunning typical operations...")

        # 1. List everything
        list_start = time.perf_counter()
        all_items = self.manager.list_items()
        list_time = (time.perf_counter() - list_start) * 1000

        # 2. Check many conflicts
        conflict_start = time.perf_counter()
        for _ in range(100):
            key = generate_random_key("check", 10)
            self.manager.check_conflicts("alias", key, "engineering_dev")
        conflict_time = (time.perf_counter() - conflict_start) * 1000

        # 3. Activate/deactivate groups
        activate_start = time.perf_counter()
        for dept in departments:
            self.manager.activate_group(f"{dept}_dev")
        for dept in departments[:3]:
            self.manager.deactivate_group(f"{dept}_dev")
        activate_time = (time.perf_counter() - activate_start) * 1000

        # 4. Get status
        status_start = time.perf_counter()
        status = self.manager.get_status()
        status_time = (time.perf_counter() - status_start) * 1000

        # Results
        print(f"\nStress Test Results:")
        print(f"Total items created: {len(all_items)}")
        print(
            f"Creation time: {creation_time:.0f}ms ({len(all_items)/creation_time*1000:.0f} items/sec)"
        )
        print(f"List all items: {list_time:.1f}ms")
        print(
            f"100 conflict checks: {conflict_time:.1f}ms ({conflict_time/100:.2f}ms each)"
        )
        print(f"Group operations: {activate_time:.1f}ms")
        print(f"Status check: {status_time:.1f}ms")

        self.record_result(
            "Stress Test",
            f"Create {len(all_items)} items",
            {
                "mean": creation_time,
                "median": creation_time,
                "min": creation_time,
                "max": creation_time,
                "stdev": 0,
            },
        )
        self.record_result(
            "Stress Test",
            f"List {len(all_items)} items",
            {
                "mean": list_time,
                "median": list_time,
                "min": list_time,
                "max": list_time,
                "stdev": 0,
            },
        )
        self.record_result(
            "Stress Test",
            "100 conflict checks",
            {
                "mean": conflict_time,
                "median": conflict_time,
                "min": conflict_time,
                "max": conflict_time,
                "stdev": 0,
            },
        )

    def write_results_to_file(self):
        """Write comprehensive results"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        version_suffix = "opt" if OPTIMIZED_VERSION else "std"
        filename = f"bench-intensive-{version_suffix}-{timestamp}.out"

        with open(filename, "w") as f:
            f.write("SHTICK INTENSIVE PERFORMANCE BENCHMARK RESULTS\n")
            f.write(f"Version: {self.version_info['version'].upper()}\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

            # Summary table
            f.write("PERFORMANCE SUMMARY (all times in milliseconds)\n")
            f.write("-" * 80 + "\n")
            f.write(
                f"{'Category':<25} {'Operation':<40} {'Mean':>10} {'Items/sec':>12}\n"
            )
            f.write("-" * 80 + "\n")

            for category, operations in sorted(self.results.items()):
                for operation, stats in sorted(operations.items()):
                    # Calculate items/sec if applicable
                    items_per_sec = ""
                    if "items)" in operation:
                        # Extract number from operation name
                        import re

                        match = re.search(r"(\d+) items", operation)
                        if match:
                            item_count = int(match.group(1))
                            items_per_sec = f"{item_count/stats['mean_ms']*1000:,.0f}"

                    f.write(
                        f"{category:<25} {operation:<40} {stats['mean_ms']:>10.2f} {items_per_sec:>12}\n"
                    )

            # Version comparison section
            f.write("\n\nOPTIMIZATION IMPACT\n")
            f.write("=" * 80 + "\n")

            if OPTIMIZED_VERSION:
                f.write("This version includes optimizations:\n")
                f.write("✓ Pre-compiled regex patterns for key validation\n")
                f.write("✓ LRU caching for conflict checks and lookups\n")
                f.write("✓ Incremental file generation\n")
                f.write("✓ Cached settings and shell detection\n")
            else:
                f.write("This is the standard version without optimizations.\n")
                f.write("Compare with optimized version to see improvements.\n")

            # Detailed results
            f.write("\n\nDETAILED RESULTS\n")
            f.write("=" * 80 + "\n")

            for category, operations in sorted(self.results.items()):
                f.write(f"\n{category}:\n")
                f.write("-" * len(category) + "\n")
                for operation, stats in sorted(operations.items()):
                    f.write(f"  {operation}:\n")
                    f.write(f"    Mean:   {stats['mean_ms']:.3f}ms\n")
                    f.write(f"    Median: {stats['median_ms']:.3f}ms\n")
                    f.write(f"    Min:    {stats['min_ms']:.3f}ms\n")
                    f.write(f"    Max:    {stats['max_ms']:.3f}ms\n")
                    if stats["stdev_ms"] > 0:
                        f.write(f"    StdDev: {stats['stdev_ms']:.3f}ms\n")
                    if stats.get("notes"):
                        f.write(f"    Notes:  {stats['notes']}\n")
                    f.write("\n")

            # JSON for analysis
            json_data = {
                "timestamp": datetime.now().isoformat(),
                "version": self.version_info,
                "results": self.results,
            }

            f.write("\n\nJSON DATA\n")
            f.write("=" * 80 + "\n")
            f.write(json.dumps(json_data, indent=2))

        print(f"\n✓ Results written to: {filename}")
        return filename


def main():
    """Run intensive benchmarks"""
    print("=" * 70)
    print("SHTICK INTENSIVE PERFORMANCE BENCHMARKS")
    print(f"Version: {'OPTIMIZED' if OPTIMIZED_VERSION else 'STANDARD'}")
    print("=" * 70)
    print("Running with larger datasets to show real performance differences...")
    print()

    benchmark = IntensiveBenchmark()

    try:
        benchmark.setup()

        # Run intensive benchmarks
        benchmark.benchmark_key_validation_intensive()
        benchmark.benchmark_conflict_checking_intensive()
        benchmark.benchmark_list_operations_intensive()
        benchmark.benchmark_batch_operations()
        benchmark.benchmark_file_generation_intensive()
        benchmark.benchmark_stress_test()

        # Summary
        print("\n" + "=" * 70)
        print("INTENSIVE BENCHMARK COMPLETE")
        print("=" * 70)

        # Write results
        output_file = benchmark.write_results_to_file()

        print("\nNext steps:")
        print("1. Run this on the other branch to compare")
        print("2. Compare results:")
        print(f"   diff bench-intensive-std-*.out bench-intensive-opt-*.out")
        print("3. Look for:")
        print("   - Conflict checking improvements (caching)")
        print("   - Batch operation speedups")
        print("   - File generation improvements (incremental)")
        print("   - Overall items/second processing rates")

    finally:
        benchmark.cleanup()
        print("\n✓ Cleanup complete")


if __name__ == "__main__":
    main()
