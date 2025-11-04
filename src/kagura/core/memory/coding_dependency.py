"""Automatic dependency graph from Python code.

Parses Python files using AST to extract import statements and build
dependency graphs automatically.
"""

import ast
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """Analyze Python file dependencies using AST.

    Extracts import statements and builds dependency graphs.

    Attributes:
        project_root: Root directory of the project
        dependencies: Discovered dependencies (file -> list[imported_files])
    """

    def __init__(self, project_root: Path | str):
        """Initialize dependency analyzer.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.dependencies: dict[str, list[str]] = {}

    def analyze_file(self, file_path: Path | str) -> list[str]:
        """Analyze a single Python file for imports.

        Args:
            file_path: Path to Python file

        Returns:
            List of imported module paths

        Example:
            >>> analyzer = DependencyAnalyzer("/path/to/project")
            >>> imports = analyzer.analyze_file("src/auth.py")
            >>> print(imports)
            ['src/models/user.py', 'src/utils/jwt.py']
        """
        file_path = Path(file_path)

        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return []

        if not file_path.suffix == ".py":
            logger.warning(f"Not a Python file: {file_path}")
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source, filename=str(file_path))
            imports = self._extract_imports(tree, file_path)

            # Cache results
            rel_path = file_path.relative_to(self.project_root)
            self.dependencies[str(rel_path)] = imports

            return imports

        except SyntaxError as e:
            logger.error(f"Syntax error in {file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return []

    def _extract_imports(self, tree: ast.AST, source_file: Path) -> list[str]:
        """Extract import statements from AST.

        Args:
            tree: AST tree
            source_file: Source file path (for relative import resolution)

        Returns:
            List of imported module paths
        """
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                # import foo.bar
                for alias in node.names:
                    module_path = self._resolve_module_path(alias.name, source_file)
                    if module_path:
                        imports.append(module_path)

            elif isinstance(node, ast.ImportFrom):
                # from foo.bar import baz
                if node.module:
                    module_path = self._resolve_module_path(node.module, source_file)
                    if module_path:
                        imports.append(module_path)

        return list(set(imports))  # Remove duplicates

    def _resolve_module_path(self, module_name: str, source_file: Path) -> str | None:
        """Resolve module name to file path.

        Args:
            module_name: Module name (e.g., "kagura.core.memory")
            source_file: Source file doing the import

        Returns:
            Relative file path or None if not in project

        Example:
            >>> analyzer._resolve_module_path("kagura.core.memory", Path("src/main.py"))
            'src/kagura/core/memory/__init__.py'
        """
        # Convert module name to path
        # e.g., "kagura.core.memory" → "kagura/core/memory"
        module_path_str = module_name.replace(".", "/")

        # Try different possibilities
        candidates = [
            self.project_root / f"{module_path_str}.py",
            self.project_root / module_path_str / "__init__.py",
            self.project_root / "src" / f"{module_path_str}.py",
            self.project_root / "src" / module_path_str / "__init__.py",
        ]

        for candidate in candidates:
            if candidate.exists():
                try:
                    rel_path = candidate.relative_to(self.project_root)
                    return str(rel_path)
                except ValueError:
                    continue

        # Not a local import (external library)
        return None

    def analyze_project(
        self, extensions: list[str] | None = None
    ) -> dict[str, list[str]]:
        """Analyze entire project for dependencies.

        Args:
            extensions: File extensions to analyze (default: [".py"])

        Returns:
            Dictionary mapping files to their dependencies

        Example:
            >>> analyzer = DependencyAnalyzer("/path/to/project")
            >>> deps = analyzer.analyze_project()
            >>> print(deps)
            {
                'src/auth.py': ['src/models/user.py', 'src/utils/jwt.py'],
                'src/main.py': ['src/auth.py', 'src/config.py'],
                ...
            }
        """
        extensions = extensions or [".py"]

        # Find all Python files
        python_files = []
        for ext in extensions:
            python_files.extend(self.project_root.rglob(f"*{ext}"))

        logger.info(f"Found {len(python_files)} Python files to analyze")

        # Analyze each file
        for file_path in python_files:
            self.analyze_file(file_path)

        return self.dependencies

    def get_reverse_dependencies(self) -> dict[str, list[str]]:
        """Get reverse dependency map (who imports this file).

        Returns:
            Dictionary mapping files to files that import them

        Example:
            >>> analyzer.analyze_project()
            >>> reverse_deps = analyzer.get_reverse_dependencies()
            >>> print(reverse_deps['src/models/user.py'])
            ['src/auth.py', 'src/api/users.py']  # Files that import user.py
        """
        reverse_deps: dict[str, list[str]] = {}

        for file, imports in self.dependencies.items():
            for imported in imports:
                if imported not in reverse_deps:
                    reverse_deps[imported] = []
                reverse_deps[imported].append(file)

        return reverse_deps

    def find_circular_dependencies(self) -> list[list[str]]:
        """Find circular import dependencies.

        Returns:
            List of circular dependency chains

        Example:
            >>> cycles = analyzer.find_circular_dependencies()
            >>> for cycle in cycles:
            ...     print(" → ".join(cycle))
            src/a.py → src/b.py → src/c.py → src/a.py
        """
        import networkx as nx

        # Build directed graph
        G = nx.DiGraph()

        for file, imports in self.dependencies.items():
            G.add_node(file)
            for imported in imports:
                G.add_node(imported)
                G.add_edge(file, imported)

        # Find cycles
        try:
            cycles = list(nx.simple_cycles(G))
            if cycles:
                logger.warning(f"Found {len(cycles)} circular dependencies")
            return cycles
        except Exception as e:
            logger.error(f"Error finding cycles: {e}")
            return []

    def get_import_depth(self, file_path: str) -> int:
        """Get maximum import depth for a file.

        Args:
            file_path: File to analyze

        Returns:
            Maximum depth (0 = no imports, 1 = imports only external, etc.)

        Example:
            >>> depth = analyzer.get_import_depth("src/main.py")
            >>> print(f"Import depth: {depth}")
            Import depth: 3  # main → auth → models → base
        """
        import networkx as nx

        # Build graph
        G = nx.DiGraph()
        for file, imports in self.dependencies.items():
            for imported in imports:
                G.add_edge(file, imported)

        if file_path not in G:
            return 0

        # Find longest path from this file
        try:
            # Get all reachable nodes
            reachable = nx.descendants(G, file_path)

            if not reachable:
                return 1 if self.dependencies.get(file_path) else 0

            # Find longest path
            max_depth = 0
            for target in reachable:
                try:
                    paths = list(nx.all_simple_paths(G, file_path, target))
                    if paths:
                        max_depth = max(max_depth, max(len(p) for p in paths))
                except nx.NetworkXNoPath:
                    continue

            return max_depth

        except Exception as e:
            logger.error(f"Error calculating depth: {e}")
            return 0

    def get_affected_files(self, changed_file: str) -> list[str]:
        """Get files affected by changing this file.

        Args:
            changed_file: File that will be changed

        Returns:
            List of files that import (directly or transitively) the changed file

        Example:
            >>> affected = analyzer.get_affected_files("src/models/user.py")
            >>> print(affected)
            ['src/auth.py', 'src/api/users.py', 'src/main.py']
        """
        reverse_deps = self.get_reverse_dependencies()

        affected = set()
        to_check = [changed_file]

        while to_check:
            current = to_check.pop(0)
            importers = reverse_deps.get(current, [])

            for importer in importers:
                if importer not in affected:
                    affected.add(importer)
                    to_check.append(importer)  # Check transitive dependencies

        return sorted(list(affected))

    def suggest_refactor_order(self, files: list[str]) -> list[str]:
        """Suggest order to refactor files based on dependencies.

        Refactor in reverse dependency order: leaf files first, root files last.

        Args:
            files: Files to refactor

        Returns:
            Files sorted by refactoring order (safest first)

        Example:
            >>> order = analyzer.suggest_refactor_order([
            ...     "src/main.py",
            ...     "src/auth.py",
            ...     "src/models/user.py"
            ... ])
            >>> print(order)
            ['src/models/user.py', 'src/auth.py', 'src/main.py']
            # Refactor user.py first (no dependencies on others in this list)
        """
        import networkx as nx

        # Build subgraph with only specified files
        G = nx.DiGraph()

        for file in files:
            G.add_node(file)
            if file in self.dependencies:
                for imported in self.dependencies[file]:
                    if imported in files:  # Only include if in refactor list
                        G.add_edge(file, imported)

        # Topological sort (dependencies first)
        try:
            return list(reversed(list(nx.topological_sort(G))))
        except nx.NetworkXError:
            # Has cycles, return as-is with warning
            logger.warning(
                "Circular dependencies detected, cannot determine safe order"
            )
            return files
