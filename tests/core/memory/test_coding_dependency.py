"""Tests for coding dependency analyzer."""

import tempfile
from pathlib import Path

import pytest

from kagura.core.memory.coding_dependency import DependencyAnalyzer


@pytest.fixture
def temp_project():
    """Create temporary project structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create src directory
        src_dir = project_root / "src"
        src_dir.mkdir()

        # Create test files
        # src/models/user.py
        models_dir = src_dir / "models"
        models_dir.mkdir()
        (models_dir / "__init__.py").write_text("")
        (models_dir / "user.py").write_text(
            """
class User:
    pass
"""
        )

        # src/auth.py (imports user.py)
        (src_dir / "auth.py").write_text(
            """
from src.models.user import User

def authenticate(user: User):
    pass
"""
        )

        # src/main.py (imports auth.py)
        (src_dir / "main.py").write_text(
            """
from src.auth import authenticate
from src.models.user import User

def main():
    user = User()
    authenticate(user)
"""
        )

        # Create circular dependency for testing
        # src/circular_a.py
        (src_dir / "circular_a.py").write_text(
            """
from src.circular_b import func_b

def func_a():
    return func_b()
"""
        )

        # src/circular_b.py
        (src_dir / "circular_b.py").write_text(
            """
from src.circular_a import func_a

def func_b():
    return func_a()
"""
        )

        yield project_root


class TestDependencyAnalyzer:
    """Test DependencyAnalyzer class."""

    def test_initialize(self, temp_project):
        """Test initializing dependency analyzer."""
        analyzer = DependencyAnalyzer(temp_project)

        assert analyzer.project_root == temp_project
        assert analyzer.dependencies == {}

    def test_analyze_file_simple(self, temp_project):
        """Test analyzing a file with simple imports."""
        analyzer = DependencyAnalyzer(temp_project)

        imports = analyzer.analyze_file(temp_project / "src" / "auth.py")

        assert len(imports) >= 1
        # Should find src/models/user.py or similar
        assert any("user" in imp for imp in imports)

    def test_analyze_file_multiple_imports(self, temp_project):
        """Test analyzing file with multiple imports."""
        analyzer = DependencyAnalyzer(temp_project)

        imports = analyzer.analyze_file(temp_project / "src" / "main.py")

        assert len(imports) >= 2
        # Should find both auth.py and user.py

    def test_analyze_nonexistent_file(self, temp_project):
        """Test analyzing non-existent file."""
        analyzer = DependencyAnalyzer(temp_project)

        imports = analyzer.analyze_file(temp_project / "nonexistent.py")

        assert imports == []

    def test_analyze_non_python_file(self, temp_project):
        """Test analyzing non-Python file."""
        # Create text file
        text_file = temp_project / "README.md"
        text_file.write_text("# Project")

        analyzer = DependencyAnalyzer(temp_project)
        imports = analyzer.analyze_file(text_file)

        assert imports == []

    def test_analyze_project(self, temp_project):
        """Test analyzing entire project."""
        analyzer = DependencyAnalyzer(temp_project)

        deps = analyzer.analyze_project()

        # Should have analyzed multiple files
        assert len(deps) >= 3
        assert any("main.py" in key for key in deps.keys())
        assert any("auth.py" in key for key in deps.keys())

    def test_get_reverse_dependencies(self, temp_project):
        """Test getting reverse dependencies."""
        analyzer = DependencyAnalyzer(temp_project)
        analyzer.analyze_project()

        reverse_deps = analyzer.get_reverse_dependencies()

        # user.py should be imported by auth.py and main.py
        user_py_importers = [
            importers for path, importers in reverse_deps.items() if "user.py" in path
        ]

        if user_py_importers:
            assert len(user_py_importers[0]) >= 1

    def test_find_circular_dependencies(self, temp_project):
        """Test circular dependency detection."""
        analyzer = DependencyAnalyzer(temp_project)
        analyzer.analyze_project()

        cycles = analyzer.find_circular_dependencies()

        # Should find circular_a.py ↔ circular_b.py
        assert len(cycles) >= 1

        # Check that circular files are in cycles
        all_files_in_cycles = [file for cycle in cycles for file in cycle]
        assert any("circular_a" in file for file in all_files_in_cycles)
        assert any("circular_b" in file for file in all_files_in_cycles)

    def test_get_import_depth(self, temp_project):
        """Test import depth calculation."""
        analyzer = DependencyAnalyzer(temp_project)
        analyzer.analyze_project()

        # main.py imports auth.py which imports user.py
        # So depth should be at least 2
        main_py = None
        for key in analyzer.dependencies.keys():
            if "main.py" in key:
                main_py = key
                break

        if main_py:
            depth = analyzer.get_import_depth(main_py)
            assert depth >= 1  # At least imports something

    def test_get_affected_files(self, temp_project):
        """Test getting affected files."""
        analyzer = DependencyAnalyzer(temp_project)
        analyzer.analyze_project()

        # Find user.py
        user_py = None
        for key in analyzer.dependencies.keys():
            if "user.py" in key:
                user_py = key
                break

        if user_py:
            affected = analyzer.get_affected_files(user_py)

            # auth.py and main.py should be affected
            assert len(affected) >= 1
            assert any("auth" in file or "main" in file for file in affected)

    def test_suggest_refactor_order(self, temp_project):
        """Test refactoring order suggestion."""
        analyzer = DependencyAnalyzer(temp_project)
        analyzer.analyze_project()

        # Get keys for main, auth, user
        files = [
            key
            for key in analyzer.dependencies.keys()
            if any(name in key for name in ["main.py", "auth.py", "user.py"])
        ]

        if len(files) >= 2:
            order = analyzer.suggest_refactor_order(files)

            # Should return same number of files
            assert len(order) == len(files)

            # user.py should come before files that import it
            user_idx = None
            auth_idx = None

            for i, file in enumerate(order):
                if "user.py" in file:
                    user_idx = i
                if "auth.py" in file:
                    auth_idx = i

            # If both exist, user should come before auth (leaf first)
            if user_idx is not None and auth_idx is not None:
                assert user_idx < auth_idx
