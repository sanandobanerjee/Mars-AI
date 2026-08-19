import ast
import hashlib
from pathlib import Path
from typing import List,Optional

from src.ingestion.models import Chunk

def _make_id(file_path: str, qualified_name: str, start_line: int) -> str:
    raw = f"{file_path}::{qualified_name}::{start_line}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]

def _get_source(source_lines: List[str],node: ast.AST)->str:
    start=node.lineno-1
    end=node.end_lineno
    return "\n".join(source_lines[start:end])

def _extract_function(node: ast.FunctionDef, file_path: str, source_lines: List[str], class_name: str = None) -> Chunk:
    qualified_name = f"{class_name}.{node.name}" if class_name else node.name
    chunk_type = "method" if class_name else "function"
    docstring = ast.get_docstring(node)
    source = _get_source(source_lines, node)
    calls=_extract_calls(node)
    return Chunk(
        id=_make_id(file_path, qualified_name, node.lineno),
        type=chunk_type,
        name=node.name,
        qualified_name=qualified_name,
        file_path=file_path,
        start_line=node.lineno,
        end_line=node.end_lineno,
        docstring=docstring,
        source=source,
        calls=calls
    )

def _extract_class_summary(node: ast.ClassDef, file_path: str, source_lines: List[str]) -> Chunk:
    docstring = ast.get_docstring(node)
    method_names = [
        n.name for n in node.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    summary_source = f"class {node.name}:\n" + (f'    """{docstring}"""\n' if docstring else "")
    summary_source += f"    # methods: {', '.join(method_names)}"
    return Chunk(
        id=_make_id(file_path, node.name, node.lineno),
        type="class_summary",
        name=node.name,
        qualified_name=node.name,
        file_path=file_path,
        start_line=node.lineno,
        end_line=node.end_lineno,
        docstring=docstring,
        source=summary_source
    )

def parse_file(file_path:Path,repo_root:Path)->List[Chunk]:
    relative_path=str(file_path.relative_to(repo_root))
    try:
        source_text=file_path.read_text(encoding="utf-8")
    except(UnicodeDecodeError,OSError):
        return []

    try:
        tree=ast.parse(source_text)
    except SyntaxError:
        return []

    source_lines=source_text.splitlines()
    chunks:List[Chunk]=[]

    for node in ast.walk(tree):
        if isinstance(node,ast.ClassDef):
            chunks.append(_extract_class_summary(node,relative_path,source_lines))
            for item in node.body:
                if isinstance(item,(ast.FunctionDef,ast.AsyncFunctionDef)):
                    chunks.append(_extract_function(item,relative_path,source_lines,class_name=node.name))

    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            chunks.append(_extract_function(node,relative_path,source_lines))

    return chunks

        
def parse_repo(repo_path: Path, core_paths: List[str] = None) -> List[Chunk]:
    all_chunks: List[Chunk] = []
    search_roots = [repo_path / p for p in core_paths] if core_paths else [repo_path]

    for root in search_roots:
        for py_file in root.rglob("*.py"):
            if any(part in {"test", "tests", "__pycache__", ".venv", "venv"} for part in py_file.parts):
                continue
            all_chunks.extend(parse_file(py_file, repo_path))

    return all_chunks

def _stringify_call_func(func_node:ast.AST)->Optional[str]:
    if isinstance(func_node,ast.Name):
        return func_node.id
    if isinstance(func_node,ast.Attribute):
        base=_stringify_call_func(func_node.value)
        if base is None:
            return None
        return f"{base}.{func_node.attr}"
    return None

def _extract_calls(node:ast.AST)->List[str]:
    calls=[]
    for child in ast.walk(node):
        if isinstance(child,ast.Call):
            name=_stringify_call_func(child.func)
            if name:
                calls.append(name)
    return sorted(set(calls))

