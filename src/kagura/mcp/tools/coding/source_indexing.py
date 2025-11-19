"""Source code indexing and search MCP tools.

Indexes source code into RAG for semantic search and retrieval.
"""

from __future__ import annotations

import ast
import fnmatch
import logging
from pathlib import Path

from kagura import tool
from kagura.utils.common.mcp_helpers import parse_json_list, to_int
from kagura.mcp.tools.coding.common import get_coding_memory

logger = logging.getLogger(__name__)


@tool
async def coding_index_source_code(
    user_id: str,
    project_id: str,
    directory: str,
    file_patterns: str = '["**/*.py"]',
    exclude_patterns: str = '["**/__pycache__/**", "**/test_*.py", "**/.venv/**"]',
    language: str = "python",
) -> str:
    """Index source code files into RAG for semantic code search.

    Scans a directory for source files, parses them (using AST for Python),
    chunks by function/class, and stores in RAG with metadata.

    Use this tool to enable semantic code search across your project.
    Useful for:
    - Understanding large codebases
    - Finding implementation examples
    - Locating where features are implemented
    - Cross-referencing related code

    Args:
        user_id: User identifier (developer)
        project_id: Project identifier
        directory: Root directory to scan (e.g., "src/", "/path/to/project/src")
        file_patterns: JSON array of glob patterns to include (default: ["**/*.py"])
        exclude_patterns: JSON array of glob patterns to exclude
        language: Programming language (currently only "python" supported)

    Returns:
        Indexing summary with file count, chunks, and stats

    Examples:
        # Index Python source code
        await coding_index_source_code(
            user_id="kiyota",
            project_id="kagura-ai",
            directory="/home/jfk/works/kagura-ai/src"
        )

        # Index with custom patterns
        await coding_index_source_code(
            user_id="kiyota",
            project_id="my-project",
            directory="./src",
            file_patterns='["**/*.py", "**/*.pyx"]',
            exclude_patterns='["**/tests/**", "**/__pycache__/**"]'
        )
    """
    # Parse patterns using common helper
    include_patterns = parse_json_list(file_patterns, param_name="file_patterns")
    exclude_patterns_list = parse_json_list(
        exclude_patterns, param_name="exclude_patterns"
    )

    if language != "python":
        return (
            f"❌ Error: Only 'python' language is currently supported (got: {language})"
        )

    # Get CodingMemoryManager
    memory = get_coding_memory(user_id, project_id)

    # Scan directory for files
    dir_path = Path(directory).resolve()
    if not dir_path.exists():
        return f"❌ Error: Directory not found: {directory}"

    logger.info(f"Scanning directory: {dir_path}")

    # Find matching files
    matched_files = []
    for pattern in include_patterns:
        matched_files.extend(dir_path.glob(pattern))

    # Filter exclusions
    filtered_files = []
    for file in matched_files:
        should_exclude = False
        for exclude_pattern in exclude_patterns_list:
            if fnmatch.fnmatch(str(file), exclude_pattern):
                should_exclude = True
                break
        if not should_exclude and file.is_file():
            filtered_files.append(file)

    if not filtered_files:
        return f"⚠️ No files found matching patterns in {directory}"

    logger.info(f"Found {len(filtered_files)} files to index")

    # Index each file
    total_chunks = 0
    indexed_files = 0
    errors = []

    for file_path in filtered_files:
        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            # Parse AST
            tree = ast.parse(source, filename=str(file_path))

            # Extract chunks (functions, classes, module docstring)
            chunks = _extract_code_chunks(source, tree, file_path)

            # Store each chunk in RAG
            for chunk in chunks:
                content = (
                    f"File: {chunk['file_path']}\n"
                    f"Type: {chunk['type']}\n"
                    f"Name: {chunk['name']}\n"
                    f"Lines: {chunk['line_start']}-{chunk['line_end']}\n\n"
                    f"{chunk['content']}"
                )

                metadata = {
                    "type": "source_code",
                    "file_path": str(chunk["file_path"]),
                    "line_start": chunk["line_start"],
                    "line_end": chunk["line_end"],
                    "chunk_type": chunk["type"],
                    "name": chunk["name"],
                    "language": language,
                }

                # Store in RAG
                memory.store_semantic(content=content, metadata=metadata)
                total_chunks += 1

            indexed_files += 1

        except SyntaxError as e:
            errors.append(f"{file_path.name}: Syntax error at line {e.lineno}")
        except Exception as e:
            errors.append(f"{file_path.name}: {str(e)[:100]}")

    # Build result
    result = "✅ Source Code Indexing Complete\n\n"
    result += f"**Project:** {project_id}\n"
    result += f"**Directory:** {directory}\n"
    result += f"**Files indexed:** {indexed_files}/{len(filtered_files)}\n"
    result += f"**Code chunks:** {total_chunks}\n"
    result += f"**Language:** {language}\n\n"

    if errors:
        result += f"**Errors ({len(errors)}):**\n"
        for error in errors[:5]:
            result += f"- {error}\n"
        if len(errors) > 5:
            result += f"- ... and {len(errors) - 5} more\n"
        result += "\n"

    result += "💡 **Next:** Use coding_search_source_code() to find code semantically"

    return result


def _extract_code_chunks(
    source: str,
    tree: ast.AST,
    file_path: Path,
    overlap_lines: int = 5,
) -> list[dict]:
    """Extract code chunks from AST for indexing with overlap.

    Args:
        source: Source code string
        tree: AST tree
        file_path: Path to source file
        overlap_lines: Number of lines to overlap before/after (default: 5)

    Returns:
        List of chunk dictionaries with overlapping context
    """
    chunks = []
    source_lines = source.splitlines()
    total_lines = len(source_lines)

    # Extract imports for context
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}")

    imports_context = "Imports: " + ", ".join(imports[:10]) if imports else ""

    # Module-level docstring + imports (full file overview)
    if (
        isinstance(tree, ast.Module)
        and hasattr(tree, "body")
        and tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
    ):
        docstring = tree.body[0].value.value
        if isinstance(docstring, str):
            chunks.append(
                {
                    "file_path": str(file_path),
                    "type": "module",
                    "name": file_path.stem,
                    "line_start": 1,
                    "line_end": len(docstring.split("\n")),
                    "content": f"{docstring}\n\n{imports_context}",
                    "imports": imports,
                }
            )

    # Find all top-level classes for context
    classes_info = {}
    if isinstance(tree, ast.Module) and hasattr(tree, "body"):
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                classes_info[node.name] = {
                    "line_start": node.lineno,
                    "line_end": node.end_lineno or node.lineno,
                    "docstring": ast.get_docstring(node) or "",
                }

    # Functions and classes with overlap
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Function/method
            func_name = node.name
            line_start = node.lineno
            line_end = node.end_lineno or line_start

            # Add overlap context
            overlap_start = max(1, line_start - overlap_lines)
            overlap_end = min(total_lines, line_end + overlap_lines)

            # Extract function with overlap
            func_source_with_overlap = "\n".join(
                source_lines[overlap_start - 1 : overlap_end]
            )

            # Get docstring
            docstring = ast.get_docstring(node) or ""

            # Find parent class if method
            parent_class = None
            for class_name, class_info in classes_info.items():
                if (
                    line_start >= class_info["line_start"]
                    and line_end <= class_info["line_end"]
                ):
                    parent_class = class_name
                    break

            context = f"Function: {func_name}"
            if parent_class:
                context = f"Class: {parent_class}, Method: {func_name}"

            chunks.append(
                {
                    "file_path": str(file_path),
                    "type": "function" if not parent_class else "method",
                    "name": func_name,
                    "line_start": line_start,
                    "line_end": line_end,
                    "content": (
                        f"{context}\n"
                        f"{imports_context}\n\n"
                        f"Code (with {overlap_lines}-line overlap):\n"
                        f"{func_source_with_overlap}\n\n"
                        f"Docstring:\n{docstring}"
                    ),
                    "parent_class": parent_class,
                    "imports": imports,
                }
            )

        elif isinstance(node, ast.ClassDef):
            # Class definition with all methods
            class_name = node.name
            line_start = node.lineno
            line_end = node.end_lineno or line_start

            # Add overlap
            overlap_start = max(1, line_start - overlap_lines)
            overlap_end = min(total_lines, line_end + overlap_lines)

            # Extract class source with overlap
            class_source = "\n".join(source_lines[overlap_start - 1 : overlap_end])

            # Get docstring
            docstring = ast.get_docstring(node) or ""

            # List methods with signatures
            methods = []
            for m in node.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Get method signature
                    args = [a.arg for a in m.args.args]
                    methods.append(f"{m.name}({', '.join(args)})")

            chunks.append(
                {
                    "file_path": str(file_path),
                    "type": "class",
                    "name": class_name,
                    "line_start": line_start,
                    "line_end": line_end,
                    "content": (
                        f"Class: {class_name}\n"
                        f"{imports_context}\n\n"
                        f"Code (with {overlap_lines}-line overlap):\n"
                        f"{class_source}\n\n"
                        f"Docstring:\n{docstring}\n\n"
                        f"Methods ({len(methods)}):\n"
                        + "\n".join(f"- {m}" for m in methods)
                    ),
                    "methods": methods,
                    "imports": imports,
                }
            )

    return chunks


@tool
async def coding_search_source_code(
    user_id: str,
    project_id: str,
    query: str,
    k: str | int = 5,
    file_filter: str | None = None,
) -> str:
    """Search indexed source code semantically.

    Finds code chunks relevant to the query using semantic search.
    Returns file paths, line ranges, and code snippets.

    Use this tool to:
    - Find implementation examples
    - Locate where a feature is implemented
    - Understand how something works
    - Find related code across the project

    Args:
        user_id: User identifier
        project_id: Project identifier
        query: Search query (e.g., "memory manager implementation", "authentication logic")
        k: Number of results to return (default: 5)
        file_filter: Optional file path filter (e.g., "src/kagura/core/**")

    Returns:
        Search results with file paths, line numbers, and code snippets

    Examples:
        # Find memory implementation
        await coding_search_source_code(
            user_id="kiyota",
            project_id="kagura-ai",
            query="memory manager store implementation"
        )

        # Search in specific directory
        await coding_search_source_code(
            user_id="kiyota",
            project_id="kagura-ai",
            query="RAG search",
            file_filter="src/kagura/core/**"
        )
    """
    memory = get_coding_memory(user_id, project_id)

    # Convert k to int using common helper
    k_int = to_int(k, default=5, min_val=1, max_val=50, param_name="k")

    # Perform semantic search using appropriate method
    if memory.rag and memory.lexical_searcher:
        # Use hybrid search if available
        results = memory.recall_hybrid(
            query=query,
            top_k=k_int,
            scope="persistent",
        )
    elif memory.rag:
        # Fallback to RAG-only search
        results = memory.search_memory(
            query=query,
            limit=k_int,
        )
    else:
        return "❌ RAG not available. Semantic search requires ChromaDB and sentence-transformers."

    if not results:
        return f"⚠️ No results found for query: '{query}'\n\nMake sure you've indexed the source code first with coding_index_source_code()"

    # Filter by file path if specified
    if file_filter:
        results = [
            r
            for r in results
            if fnmatch.fnmatch(r.get("metadata", {}).get("file_path", ""), file_filter)
        ]

    if not results:
        return f"⚠️ No results found matching file filter: {file_filter}"

    # Format results
    result = f"🔍 Source Code Search Results: '{query}'\n\n"
    result += f"**Found {len(results)} relevant code chunks:**\n\n"

    for i, res in enumerate(results, 1):
        metadata = res.get("metadata", {})
        if metadata.get("type") != "source_code":
            continue  # Skip non-source-code memories

        file_path = metadata.get("file_path", "unknown")
        line_start = metadata.get("line_start", 0)
        line_end = metadata.get("line_end", 0)
        chunk_type = metadata.get("chunk_type", "unknown")
        name = metadata.get("name", "")
        score = res.get("score", 0.0)

        content_preview = res.get("content", "")[:300]

        result += f"**{i}. {file_path}:{line_start}-{line_end}**\n"
        result += f"   Type: {chunk_type} `{name}`\n"
        result += f"   Score: {score:.3f}\n"
        result += f"   Preview:\n```\n{content_preview}\n```\n\n"

    result += "\n💡 **Tip:** Open files in your editor to see full implementation"

    return result
