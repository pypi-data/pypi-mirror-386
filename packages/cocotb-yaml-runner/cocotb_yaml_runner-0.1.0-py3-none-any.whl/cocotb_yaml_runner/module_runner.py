"""
Module runner reads the YAML config file and sets up cocotb tests with VCD support
Based on working cocotb.runner pattern
"""

import os
import logging
import yaml
import shutil
from typing import Dict, List, Any, Optional
from pathlib import Path

from cocotb.runner import get_runner, get_results

logger = logging.getLogger(__name__)

class ModuleConfig:
    """Represents a module configuration from YAML"""

    def __init__(self, name: str, config: Dict[str, Any], yaml_config: 'YamlConfig'):
        self.name = name
        self.config = config
        self.yaml_config = yaml_config

    @property
    def sources(self) -> List[str]:
        """Get all source files including dependencies"""
        sources = list(self.config.get('sources', []))

        for dep in self.config.get('deps', []):
            dep_sources = self.yaml_config.get_library_sources(dep)
            sources.extend(dep_sources)

        return sources

    @property
    def toplevel(self) -> str:
        return self.config.get('toplevel', self.name)

    @property
    def parameters(self) -> Dict[str, Any]:
        return self.config.get('parameters', {})

class TestConfig:
    """Represents a test configuration from YAML"""

    def __init__(self, name: str, config: Dict[str, Any], yaml_config: 'YamlConfig'):
        self.name = name
        self.config = config
        self.yaml_config = yaml_config

    @property
    def target_module(self) -> str:
        return self.config['target_module']

    @property
    def wrapper_file(self) -> str:
        return self.config['testbench']['wrapper']

    @property
    def testbench_toplevel(self) -> str:
        return self.config['testbench']['toplevel']

    @property
    def cocotb_module(self) -> str:
        return self.config['testbench']['cocotb_module']

    @property
    def test_variants(self) -> List[Dict[str, Any]]:
        return self.config.get('test_variants', [{'name': 'default'}])

    def get_all_sources(self) -> List[str]:
        sources = []

        sources.append(self.wrapper_file)
        module_config = self.yaml_config.get_module(self.target_module)
        if module_config:
            sources.extend(module_config.sources)

        return sources

class YamlConfig:
    """Main configuration manager that reads and parses the YAML file"""

    def __init__(self, config_file: str = "modules.yaml"):
        self.config_file = Path(config_file)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_file.exists():
            raise FileNotFoundError(f"Configuration file {self.config_file} not found")

        with open(self.config_file, 'r') as f:
            config = yaml.safe_load(f)

        logger.info(f"Loaded configuration from {self.config_file}")
        return config

    def get_library_sources(self, library_name: str) -> List[str]:
        libraries = self.config.get('libraries', {})

        if library_name not in libraries:
            logger.warning(f"Library '{library_name}' not found")
            return []

        library = libraries[library_name]
        sources = list(library.get('sources', []))

        for dep in library.get('deps', []):
            dep_sources = self.get_library_sources(dep)
            sources.extend(dep_sources)

        seen = set()
        unique_sources = []
        for source in sources:
            if source not in seen:
                seen.add(source)
                unique_sources.append(source)

        return unique_sources

    def get_module(self, module_name: str) -> Optional[ModuleConfig]:
        modules = self.config.get('modules', {})

        if module_name not in modules:
            logger.error(f"Module '{module_name}' not found")
            return None

        return ModuleConfig(module_name, modules[module_name], self)

    def get_test(self, test_name: str) -> Optional[TestConfig]:
        tests = self.config.get('tests', {})

        if test_name not in tests:
            logger.error(f"Test '{test_name}' not found")
            return None

        return TestConfig(test_name, tests[test_name], self)

    def get_test_suite(self, suite_name: str) -> List[str]:
        test_suites = self.config.get('test_suites', {})

        if suite_name not in test_suites:
            logger.error(f"Test suite '{suite_name}' not found")
            return []

        return test_suites[suite_name].get('tests', [])

    def list_modules(self) -> List[str]:
        return list(self.config.get('modules', {}).keys())

    def list_tests(self) -> List[str]:
        return list(self.config.get('tests', {}).keys())

    def list_test_suites(self) -> List[str]:
        return list(self.config.get('test_suites', {}).keys())

def run_test_from_yaml(test_name: str, variant: str = None, config_file: str = "modules.yaml") -> int:
    """
    Runs a test specified in the YAML config using cocotb.runner

    Args:
        test_name: Name of the test to run
        variant: Specific test variant to run (optional)
        config_file: Path to YAML config file

    Returns:
        0 if successful, 1 if failed
    """

    yaml_config = YamlConfig(config_file)
    test_config = yaml_config.get_test(test_name)

    if not test_config:
        logger.error(f"Test '{test_name}' not found in configuration")
        return 1

    sources = test_config.get_all_sources()
    logger.info(f"Source files: {sources}")

    global_config = yaml_config.config.get('config', {})
    simulator = global_config.get('simulator', 'verilator')
    global_defines = global_config.get('global_defines', {})

    vcd_config = global_config.get('vcd', {})
    vcd_enabled = vcd_config.get('enable', False)

    variants_to_run = test_config.test_variants
    if variant:
        variants_to_run = [v for v in variants_to_run if v.get('name') == variant]
        if not variants_to_run:
            logger.error(f"Variant '{variant}' not found for test '{test_name}'")
            return 1

    failed_variants = []
    for variant_config in variants_to_run:
        variant_name = variant_config.get('name', 'default')
        logger.info(f"Running test {test_name} variant {variant_name}")

        parameters = variant_config.get('parameters', {})
        defines = {**global_defines, **variant_config.get('defines', {})}

        test_dir = Path(f"run_dir/{test_name}_{variant_name}")
        test_dir.mkdir(parents=True, exist_ok=True)

        run_dir_root = Path("run_dir")
        run_dir_root.mkdir(parents=True, exist_ok=True)

        cocotb_module_parts = test_config.cocotb_module.split('.')
        test_files_dir = Path('.').joinpath(*cocotb_module_parts[:-1])

        build_args = [
            "-Wno-GENUNNAMED",
            "-Wno-WIDTHEXPAND",
            "-Wno-WIDTHTRUNC",
            "-Wno-UNOPTFLAT",
            "--assert",
            "--stats",
            "-O2",
            "-build-jobs", "8",
            "-Wno-fatal",
            "-Wno-lint",
            "-Wno-style",
        ]

        if simulator == 'verilator':
            verilator_config = global_config.get('verilator', {})
            custom_flags = verilator_config.get('flags', [])
            build_args.extend(custom_flags)

        project_root = Path.cwd()
        includes = [
            str(project_root),
            str(project_root / "rtl"),
        ]

        try:
            runner = get_runner(simulator)

            logger.info(f'Running CocoTB test:')
            logger.info(f"  Sources: {sources}")
            logger.info(f"  Toplevel: {test_config.testbench_toplevel}")
            logger.info(f"  Module: {test_config.cocotb_module}")
            logger.info(f"  Parameters: {parameters}")
            logger.info(f"  Defines: {defines}")
            logger.info(f"  Build args: {build_args}")
            logger.info(f"  Test dir: {test_dir}")
            logger.info(f"  VCD enabled: {vcd_enabled}")

            runner.build(
                verilog_sources=sources,
                includes=includes,
                hdl_toplevel=test_config.testbench_toplevel,
                build_args=build_args,
                parameters=parameters,
                defines=defines,
                build_dir=test_dir,
                waves=vcd_enabled
            )

            original_cwd = Path.cwd()

            try:
                os.chdir(project_root)
                logger.info(f"Changed working directory to: {project_root}")

                results_xml_path = runner.test(
                    hdl_toplevel=test_config.testbench_toplevel,
                    hdl_toplevel_lang="verilog",
                    test_module=test_config.cocotb_module,
                    test_dir=str(project_root),
                    build_dir=str(test_dir),
                    waves=vcd_enabled
                )

            finally:
                os.chdir(original_cwd)
                logger.info(f"Restored working directory to: {original_cwd}")

            try:
                if results_xml_path and Path(results_xml_path).exists():
                    num_tests, num_failed = get_results(Path(results_xml_path))
                    if num_failed > 0:
                        logger.error(f"✗ Test {test_name} variant {variant_name} FAILED: {num_failed} out of {num_tests} test(s) failed")
                        failed_variants.append(f"{test_name}_{variant_name}")
                    else:
                        logger.info(f"✓ Test {test_name} variant {variant_name} PASSED: {num_tests} test(s) passed")
                else:
                    logger.error(f"✗ Test {test_name} variant {variant_name} FAILED: Results XML file not found")
                    failed_variants.append(f"{test_name}_{variant_name}")
            except Exception as xml_error:
                logger.error(f"✗ Test {test_name} variant {variant_name} FAILED: Could not parse results: {xml_error}")
                failed_variants.append(f"{test_name}_{variant_name}")

            if vcd_enabled:
                dump_extensions = ['.vcd', '.fst', '.ghw']
                for ext in dump_extensions:
                    dump_files = list(run_dir_root.glob(f'*{ext}'))
                    for dump_file in dump_files:
                        new_name = f"{test_name}_{variant_name}{ext}"
                        dest_path = run_dir_root / new_name

                        try:
                            shutil.copy(str(dump_file), str(dest_path))
                            logger.info(f"Waveform saved: {new_name}")
                        except Exception as e:
                            logger.warning(f"Could not copy dump file {dump_file}: {e}")

            logger.info(f"✓ Test {test_name} variant {variant_name} PASSED")

        except Exception as e:
            logger.error(f"✗ Test {test_name} variant {variant_name} FAILED: {e}")
            failed_variants.append(f"{test_name}_{variant_name}")

    if failed_variants:
        logger.error(f"Failed variants: {failed_variants}")
        return 1
    else:
        logger.info(f"All variants of test {test_name} passed!")
        return 0

def run_test_suite_from_yaml(suite_name: str, config_file: str = "modules.yaml") -> int:
    """
    Run all tests in a test suite

    Args:
        suite_name: Name of the test suite to run
        config_file: Path to YAML configuration file

    Returns:
        0 if all tests passed, 1 if any failed
    """
    yaml_config = YamlConfig(config_file)
    test_names = yaml_config.get_test_suite(suite_name)

    if not test_names:
        logger.error(f"Test suite '{suite_name}' not found or empty")
        return 1

    logger.info(f"Running test suite '{suite_name}' with {len(test_names)} tests")

    passed = 0
    failed = 0
    failed_tests = []

    for test_name in test_names:
        try:
            result = run_test_from_yaml(test_name, config_file=config_file)
            if result == 0:
                passed += 1
            else:
                failed += 1
                failed_tests.append(test_name)
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            failed += 1
            failed_tests.append(test_name)

    logger.info(f"Test suite '{suite_name}' completed: {passed} passed, {failed} failed")

    if failed > 0:
        logger.error(f"Failed tests: {failed_tests}")
        return 1
    else:
        logger.info(f"All tests in suite '{suite_name}' passed!")
        return 0

def list_available_targets(config_file: str = "modules.yaml") -> None:
    try:
        yaml_config = YamlConfig(config_file)

        print("\n=== Available Modules ===")
        modules = yaml_config.config.get('modules', {})
        for module in yaml_config.list_modules():
            module_config = modules[module]
            print(f"  {module}: {module_config.get('description', 'No description')}")

        print("\n=== Available Tests ===")
        tests = yaml_config.config.get('tests', {})
        for test in yaml_config.list_tests():
            test_config = tests[test]
            print(f"  {test}: {test_config.get('description', 'No description')}")

            for variant in test_config.get('test_variants', []):
                variant_name = variant.get('name', 'default')
                print(f"    - {variant_name}")

        print("\n=== Available Test Suites ===")
        test_suites = yaml_config.config.get('test_suites', {})
        for suite in yaml_config.list_test_suites():
            suite_config = test_suites[suite]
            print(f"  {suite}: {suite_config.get('description', 'No description')}")

        print("\n=== VCD Configuration ===")
        vcd_config = yaml_config.config.get('config', {}).get('vcd', {})
        if vcd_config.get('enable', False):
            print(f"  VCD dumping: ENABLED")
            print(f"  Trace files will be saved in build directories")
        else:
            print(f"  VCD dumping: DISABLED")

    except Exception as e:
        print(f"Error loading configuration: {e}")
        print("Make sure you have a 'modules.yaml' file in your project root.")