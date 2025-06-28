#!/usr/bin/env python3
"""
Validate OpenTelemetry coverage across the uvmgr codebase.

This script analyzes all Python files to determine what percentage
of functions and classes have telemetry instrumentation.
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass, field


@dataclass
class FunctionInfo:
    """Information about a function."""
    name: str
    module: str
    line: int
    is_instrumented: bool = False
    has_span: bool = False
    has_metrics: bool = False
    is_command: bool = False
    is_operation: bool = False
    decorators: List[str] = field(default_factory=list)


@dataclass
class ModuleInfo:
    """Information about a module."""
    path: Path
    functions: List[FunctionInfo] = field(default_factory=list)
    has_telemetry_import: bool = False
    uses_subprocess: bool = False
    subprocess_instrumented: bool = False


class TelemetryCoverageAnalyzer:
    """Analyze telemetry coverage in Python code."""
    
    def __init__(self, root_path: Path):
        """Initialize analyzer with project root path."""
        self.root_path = root_path
        self.modules: Dict[str, ModuleInfo] = {}
        self.telemetry_patterns = {
            'span_creation': ['with span(', 'with child_span('],
            'metric_calls': ['metric_counter(', 'metric_histogram(', 'metric_gauge(', '_record_counter(', '_record_histogram('],
            'decorators': ['@instrument_command', '@instrument_operation', '@timed'],
            'telemetry_imports': ['from uvmgr.core.instrumentation import', 'from uvmgr.core.telemetry import'],
            'subprocess': ['subprocess.run(', 'subprocess.call(', 'subprocess.Popen('],
            'instrumented_subprocess': ['run_logged(', 'with span(', 'with child_span('],
        }
    
    def analyze_file(self, file_path: Path) -> ModuleInfo:
        """Analyze a single Python file for telemetry coverage."""
        module_info = ModuleInfo(path=file_path)
        
        try:
            content = file_path.read_text()
            tree = ast.parse(content)
            
            # Check for telemetry imports
            module_info.has_telemetry_import = any(
                pattern in content for pattern in self.telemetry_patterns['telemetry_imports']
            )
            
            # Check for subprocess usage
            module_info.uses_subprocess = any(
                pattern in content for pattern in self.telemetry_patterns['subprocess']
            )
            
            # Check if subprocess is instrumented
            if module_info.uses_subprocess:
                module_info.subprocess_instrumented = any(
                    pattern in content for pattern in self.telemetry_patterns['instrumented_subprocess']
                )
            
            # Extract module path relative to src
            rel_path = file_path.relative_to(self.root_path)
            module_name = str(rel_path).replace('/', '.').replace('.py', '')
            
            # Walk the AST
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = FunctionInfo(
                        name=node.name,
                        module=module_name,
                        line=node.lineno
                    )
                    
                    # Check decorators
                    for decorator in node.decorator_list:
                        decorator_str = ast.unparse(decorator) if hasattr(ast, 'unparse') else ''
                        func_info.decorators.append(decorator_str)
                        
                        # Check for instrumentation decorators
                        if any(pattern in decorator_str for pattern in ['instrument_command', 'instrument_operation', 'timed']):
                            func_info.is_instrumented = True
                        
                        if 'command' in decorator_str:
                            func_info.is_command = True
                    
                    # Check function body for telemetry
                    func_content = ast.unparse(node) if hasattr(ast, 'unparse') else ''
                    
                    # Check for span usage
                    func_info.has_span = any(
                        pattern in func_content for pattern in self.telemetry_patterns['span_creation']
                    )
                    
                    # Check for metrics usage
                    func_info.has_metrics = any(
                        pattern in func_content for pattern in self.telemetry_patterns['metric_calls']
                    )
                    
                    # Determine if instrumented
                    if func_info.has_span or func_info.has_metrics or func_info.is_instrumented:
                        func_info.is_instrumented = True
                    
                    # Determine if it's an operation
                    if module_name.startswith('src.uvmgr.ops'):
                        func_info.is_operation = True
                    
                    # Skip private functions and test functions
                    if not func_info.name.startswith('_') and not func_info.name.startswith('test_'):
                        module_info.functions.append(func_info)
            
            return module_info
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return module_info
    
    def analyze_directory(self, directory: Path, pattern: str = "*.py"):
        """Analyze all Python files in a directory."""
        for py_file in directory.rglob(pattern):
            # Skip test files and __pycache__
            if any(part in str(py_file) for part in ['__pycache__', 'test_', 'tests/', '.venv/', 'weaver-forge/']):
                continue
            
            rel_path = py_file.relative_to(self.root_path)
            module_info = self.analyze_file(py_file)
            self.modules[str(rel_path)] = module_info
    
    def generate_report(self) -> Dict[str, any]:
        """Generate coverage report."""
        # Categorize modules
        command_modules = []
        ops_modules = []
        runtime_modules = []
        core_modules = []
        other_modules = []
        
        for path, module in self.modules.items():
            if 'commands/' in path:
                command_modules.append((path, module))
            elif 'ops/' in path:
                ops_modules.append((path, module))
            elif 'runtime/' in path:
                runtime_modules.append((path, module))
            elif 'core/' in path:
                core_modules.append((path, module))
            else:
                other_modules.append((path, module))
        
        # Generate report
        report = {
            'summary': self._calculate_summary(),
            'by_layer': {
                'commands': self._analyze_modules(command_modules),
                'operations': self._analyze_modules(ops_modules),
                'runtime': self._analyze_modules(runtime_modules),
                'core': self._analyze_modules(core_modules),
                'other': self._analyze_modules(other_modules),
            },
            'subprocess_usage': self._analyze_subprocess_usage(),
            'missing_instrumentation': self._find_missing_instrumentation(),
        }
        
        return report
    
    def _calculate_summary(self) -> Dict[str, any]:
        """Calculate overall summary statistics."""
        total_functions = 0
        instrumented_functions = 0
        command_functions = 0
        instrumented_commands = 0
        
        for module in self.modules.values():
            for func in module.functions:
                total_functions += 1
                if func.is_instrumented:
                    instrumented_functions += 1
                if func.is_command:
                    command_functions += 1
                    if func.is_instrumented:
                        instrumented_commands += 1
        
        coverage = (instrumented_functions / total_functions * 100) if total_functions > 0 else 0
        command_coverage = (instrumented_commands / command_functions * 100) if command_functions > 0 else 0
        
        return {
            'total_modules': len(self.modules),
            'total_functions': total_functions,
            'instrumented_functions': instrumented_functions,
            'coverage_percent': coverage,
            'command_functions': command_functions,
            'instrumented_commands': instrumented_commands,
            'command_coverage_percent': command_coverage,
        }
    
    def _analyze_modules(self, modules: List[Tuple[str, ModuleInfo]]) -> Dict[str, any]:
        """Analyze a group of modules."""
        total_functions = 0
        instrumented_functions = 0
        modules_with_telemetry = 0
        
        for path, module in modules:
            if module.has_telemetry_import:
                modules_with_telemetry += 1
            
            for func in module.functions:
                total_functions += 1
                if func.is_instrumented:
                    instrumented_functions += 1
        
        coverage = (instrumented_functions / total_functions * 100) if total_functions > 0 else 0
        
        return {
            'module_count': len(modules),
            'modules_with_telemetry': modules_with_telemetry,
            'total_functions': total_functions,
            'instrumented_functions': instrumented_functions,
            'coverage_percent': coverage,
        }
    
    def _analyze_subprocess_usage(self) -> List[Dict[str, any]]:
        """Find modules using subprocess directly."""
        subprocess_modules = []
        
        for path, module in self.modules.items():
            if module.uses_subprocess:
                subprocess_modules.append({
                    'path': path,
                    'instrumented': module.subprocess_instrumented,
                })
        
        return subprocess_modules
    
    def _find_missing_instrumentation(self) -> Dict[str, List[str]]:
        """Find functions that should be instrumented but aren't."""
        missing = {
            'commands': [],
            'operations': [],
            'high_priority': [],
        }
        
        for path, module in self.modules.items():
            for func in module.functions:
                if not func.is_instrumented:
                    if func.is_command:
                        missing['commands'].append(f"{path}::{func.name}")
                    elif func.is_operation:
                        missing['operations'].append(f"{path}::{func.name}")
                    
                    # High priority: commands and public operations
                    if (func.is_command or (func.is_operation and not func.name.startswith('_'))):
                        missing['high_priority'].append(f"{path}::{func.name}")
        
        return missing


def print_report(report: Dict[str, any]):
    """Print a formatted coverage report."""
    print("\n" + "=" * 80)
    print("📊 OpenTelemetry Coverage Report for uvmgr")
    print("=" * 80)
    
    # Summary
    summary = report['summary']
    print(f"\n📈 Overall Coverage: {summary['coverage_percent']:.1f}%")
    print(f"   Total Functions: {summary['total_functions']}")
    print(f"   Instrumented: {summary['instrumented_functions']}")
    print(f"\n🎯 Command Coverage: {summary['command_coverage_percent']:.1f}%")
    print(f"   Command Functions: {summary['command_functions']}")
    print(f"   Instrumented Commands: {summary['instrumented_commands']}")
    
    # By layer
    print("\n📂 Coverage by Layer:")
    print("-" * 40)
    for layer, stats in report['by_layer'].items():
        if stats['module_count'] > 0:
            print(f"\n{layer.upper()}:")
            print(f"  Modules: {stats['module_count']} ({stats['modules_with_telemetry']} with telemetry imports)")
            print(f"  Functions: {stats['total_functions']} ({stats['instrumented_functions']} instrumented)")
            print(f"  Coverage: {stats['coverage_percent']:.1f}%")
    
    # Subprocess usage
    if report['subprocess_usage']:
        print("\n⚠️  Direct Subprocess Usage:")
        print("-" * 40)
        for module in report['subprocess_usage']:
            status = "✅ instrumented" if module['instrumented'] else "❌ needs fixing"
            print(f"  {module['path']} - {status}")
    
    # Missing instrumentation
    missing = report['missing_instrumentation']
    if missing['high_priority']:
        print(f"\n🔴 High Priority Missing Instrumentation ({len(missing['high_priority'])}):")
        print("-" * 40)
        for item in missing['high_priority'][:10]:  # Show first 10
            print(f"  - {item}")
        if len(missing['high_priority']) > 10:
            print(f"  ... and {len(missing['high_priority']) - 10} more")
    
    # Recommendations
    print("\n💡 Recommendations:")
    print("-" * 40)
    
    if summary['command_coverage_percent'] < 100:
        print("1. Instrument all command functions with @instrument_command")
    
    if report['subprocess_usage']:
        uninstrumented = [m for m in report['subprocess_usage'] if not m['instrumented']]
        if uninstrumented:
            print("2. Replace subprocess.run() with run_logged() in:")
            for module in uninstrumented[:3]:
                print(f"   - {module['path']}")
    
    if summary['coverage_percent'] < 80:
        print("3. Add telemetry to critical operations in the ops/ layer")
    
    print("\n✅ Target: 100% coverage for commands, >80% for operations")


def main():
    """Main entry point."""
    # Determine project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent  # Up to uvmgr root
    src_path = project_root / 'src'
    
    if not src_path.exists():
        print(f"❌ Source directory not found: {src_path}")
        return 1
    
    print(f"🔍 Analyzing telemetry coverage in: {src_path}")
    
    # Create analyzer
    analyzer = TelemetryCoverageAnalyzer(src_path)
    
    # Analyze all Python files
    analyzer.analyze_directory(src_path)
    
    # Generate report
    report = analyzer.generate_report()
    
    # Print report
    print_report(report)
    
    # Determine exit code
    summary = report['summary']
    if summary['command_coverage_percent'] < 100:
        print(f"\n❌ Command coverage is below 100%")
        return 1
    elif summary['coverage_percent'] < 80:
        print(f"\n⚠️  Overall coverage is below 80%")
        return 1
    else:
        print(f"\n✅ Coverage targets met!")
        return 0


if __name__ == '__main__':
    sys.exit(main())