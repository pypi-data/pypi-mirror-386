"""
CLI for running tests from YAML config
"""

import argparse
import sys
import logging
import traceback
import shutil
from pathlib import Path
try:
    import pkg_resources
except ImportError:
    from importlib import resources as pkg_resources

from cocotb_yaml_runner.module_runner import (
    run_test_from_yaml,
    run_test_suite_from_yaml,
    list_available_targets,
    YamlConfig
)

def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def init_project(args):
    """Initialize a new project with template files."""
    logger = logging.getLogger(__name__)

    # Define the template files to create
    templates = {
        'modules.yaml': """# modules.yaml - YAML-based test configuration
# This file defines your HDL modules, tests, and build configuration

libraries:
  # Define reusable libraries of SystemVerilog files
  common_types:
    description: "Common SystemVerilog types and definitions"
    sources:
      - "rtl/common/my_typedef.sv"

  common_interfaces:
    description: "Common SystemVerilog interfaces"
    sources:
      - "rtl/common/my_if.sv"

modules:
  # Define your HDL modules and their dependencies
  my_module:
    description: "Example module using typedef"
    sources:
      - "rtl/my_module.sv"
    deps:
      - "common_types"
    toplevel: "my_module"

tests:
  # Define your test configurations
  test_my_module:
    description: "Test my module"
    target_module: "my_module"
    testbench:
      wrapper: "tb/my_module_tb.sv"
      toplevel: "my_module_tb"
      cocotb_module: "tb.test_my_module"
    test_variants:
      - name: "basic"
        defines:
          TEST_BASIC: 1

test_suites:
  # Group tests together
  unit_tests:
    description: "All unit tests"
    tests:
      - "test_my_module"

config:
  # Global simulation configuration
  simulator: "verilator"
  default_timescale: "1ns/1ps"
  default_language: "SystemVerilog"

  verilator:
    flags:
      - "--trace"
      - "--trace-structs"
      - "--trace-params"
      - "-CFLAGS"
      - "-std=c++17"
      - "-LDFLAGS"
      - "-std=c++17"

  vcd:
    enable: true
    filename: "dump.vcd"
    depth: 99

  global_defines:
    SIMULATION: 1
""",
        'tox.ini': """[tox]
skipsdist = True
envlist = py311

[testenv]
setenv =
    SIM = verilator
    TIMEUNIT = "1ns"
    TIMEPREC = "100ps"
    PYTHONPATH = {toxinidir}

deps =
    pytest
    pytest-xdist
    cocotb-test >= 0.2.0
    cocotb >= 1.8.0
    PyYAML >= 5.4.1
    cocotb-yaml-runner

# Run all tests using pytest (traditional method)
commands = pytest tb/ -v {posargs}

# Run specific test using YAML config
[testenv:test]
commands = cocotb-yaml --test {posargs}

# Run test suite using YAML config
[testenv:suite]
commands = cocotb-yaml --suite {posargs}

# List all available targets from YAML
[testenv:list]
commands = cocotb-yaml --list

[pytest]
testpaths = tb
addopts = --import-mode prepend
markers =
    basic: Basic functionality tests
"""
    }

    created_files = []
    skipped_files = []

    for filename, content in templates.items():
        target_path = Path(filename)

        if target_path.exists() and not args.force:
            logger.warning(f"File {filename} already exists. Use --force to overwrite.")
            skipped_files.append(filename)
            continue

        try:
            with open(target_path, 'w') as f:
                f.write(content)
            logger.info(f"Created {filename}")
            created_files.append(filename)
        except Exception as e:
            logger.error(f"Failed to create {filename}: {e}")
            return 1

    # Summary
    if created_files:
        print(f"\n✓ Successfully created: {', '.join(created_files)}")
    if skipped_files:
        print(f"⚠ Skipped existing files: {', '.join(skipped_files)}")

    if created_files:
        print("\nNext steps:")
        print("1. Customize modules.yaml for your project structure")
        print("2. Run 'cocotb-yaml --list' to verify configuration")
        print("3. Create your RTL files and testbenches")
        print("4. Run tests with 'cocotb-yaml --test <test_name>'")

    return 0

def main():
    parser = argparse.ArgumentParser(
        description="Run SystemVerilog tests using YAML config",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Initialize a new project
    cocotb-yaml init

    # List available targets
    cocotb-yaml --list

    # Run specific test
    cocotb-yaml --test=[test_name]

    # Run specific test variant
    cocotb-yaml --test=[test_name] --variant=[e.g., basic]

    # Run test suite
    cocotb-yaml --suite=unit_tests

    # Via tox
    tox -e test -- [test_name] --variant=wide
    tox -e suite -- unit_tests
        """
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize project with template files')
    init_parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing files'
    )

    # Test/suite commands (for backward compatibility, also add as main options)
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        '--test',
        help='Test to run from YAML config (e.g. test_[module_name])'
    )
    action_group.add_argument(
        '--suite',
        help='Test suite to run from YAML config'
    )
    action_group.add_argument(
        '--list',
        action='store_true',
        help='List all available targets'
    )

    parser.add_argument(
        '--variant',
        help='Specific test variant to run'
    )
    parser.add_argument(
        '--config',
        default='modules.yaml',
        help='Path to YAML config file (default: modules.yaml)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be run without actually running it'
    )

    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    if args.command == 'init':
        return init_project(args)

    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Config file {config_path} not found")
        if not args.command:
            logger.info("Hint: Run 'cocotb-yaml init' to create a template config file")
        return 1

    try:
        if args.list:
            list_available_targets(args.config)
            return 0

        elif args.test:
            if args.dry_run:
                yaml_config = YamlConfig(args.config)
                test_config = yaml_config.get_test(args.test)

                if test_config:
                    print(f"Would run test: {args.test}")
                    if args.variant:
                        print(f"  Variant: {args.variant}")
                    print(f"  Target module: {test_config.target_module}")
                    print(f"  Testbench: {test_config.testbench_toplevel}")
                    print(f"  Sources: {test_config.get_all_sources()}")
                else:
                    logger.error(f"Test {args.test} not found")
                    return 1
            else:
                result = run_test_from_yaml(args.test, args.variant, args.config)
                return result
            return 0

        elif args.suite:
            if args.dry_run:
                yaml_config = YamlConfig(args.config)
                test_names = yaml_config.get_test_suite(args.suite)
                print(f"Would run test suite: {args.suite}")
                print(f"  Tests: {test_names}")
            else:
                result = run_test_suite_from_yaml(args.suite, args.config)
                return result
            return 0

        else:
            parser.print_help()
            return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())