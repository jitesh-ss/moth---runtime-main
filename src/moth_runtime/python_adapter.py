"""Deterministic Python 3.11 AST-to-field compiler; never imports code."""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path
from typing import Any

from .canonical import digest, meaning_id, sha256_bytes
from .model import CompilationError, Meaning, MeaningType, Provenance, SemanticEdge, Source


def compile_python_tree(
    root: Path, existing: dict[str, Meaning], by_name: dict[tuple[MeaningType, str], str],
) -> tuple[list[Meaning], list[SemanticEdge], dict[str, Source]]:
    selected_root = root.resolve()
    if not selected_root.is_dir():
        raise CompilationError("Python source root is not a directory")
    relation_ids = {
        name: by_name.get((MeaningType.RELATION, name.casefold()))
        for name in ("contains", "defines", "imports", "calls", "inherits", "decorated-by", "references", "tests")
    }
    if any(value is None for value in relation_ids.values()):
        raise CompilationError("Python compilation requires all frozen code relations")

    records: dict[str, Meaning] = {}
    owners: dict[str, list[Provenance]] = defaultdict(list)
    edge_owners: dict[tuple[str, str, str], list[Provenance]] = defaultdict(list)
    sources: dict[str, Source] = {}

    def declare(kind: MeaningType, name: str, payload: dict[str, Any], owner: Provenance) -> str:
        canonical_payload = {"name": name, **payload}
        identifier = meaning_id(kind.value, canonical_payload)
        owners[identifier].append(owner)
        records[identifier] = Meaning(identifier, kind, name, canonical_payload, ())
        return identifier

    def edge(relation: str, source_id: str, destination_id: str, owner: Provenance) -> None:
        edge_owners[(str(relation_ids[relation]), source_id, destination_id)].append(owner)

    for path in sorted(selected_root.rglob("*.py")):
        resolved = path.resolve()
        if path.is_symlink() or not resolved.is_relative_to(selected_root):
            raise CompilationError("Python source symlink escapes are unsupported")
        raw = path.read_bytes()
        if len(raw) > 16 * 1024 * 1024:
            raise CompilationError("Python source exceeds 16 MiB")
        try:
            text = raw.decode("utf-8", errors="strict")
            tree = ast.parse(text, filename=path.as_posix(), type_comments=True)
        except (UnicodeDecodeError, SyntaxError) as exc:
            raise CompilationError(f"invalid Python source: {path}") from exc
        relative = path.relative_to(selected_root).as_posix()
        source_id = "python/" + relative
        source_hash = sha256_bytes(raw)
        sources[source_id] = Source(source_id, text, source_hash)
        lines = text.splitlines(keepends=True)
        char_starts = [0]
        byte_starts = [0]
        for line in lines:
            char_starts.append(char_starts[-1] + len(line))
            byte_starts.append(byte_starts[-1] + len(line.encode("utf-8")))

        def offsets(node: ast.AST) -> tuple[int, int, int, int]:
            line_index = max(0, int(getattr(node, "lineno", 1)) - 1)
            end_line_index = max(0, int(getattr(node, "end_lineno", line_index + 1)) - 1)
            start_byte_column = int(getattr(node, "col_offset", 0))
            end_byte_column = int(getattr(node, "end_col_offset", start_byte_column))
            start_prefix = lines[line_index].encode("utf-8")[:start_byte_column].decode("utf-8") if lines else ""
            end_prefix = lines[end_line_index].encode("utf-8")[:end_byte_column].decode("utf-8") if lines else ""
            char_start = char_starts[line_index] + len(start_prefix)
            char_end = char_starts[end_line_index] + len(end_prefix)
            byte_start = byte_starts[line_index] + start_byte_column
            byte_end = byte_starts[end_line_index] + end_byte_column
            return char_start, char_end, byte_start, byte_end

        def provenance(node: ast.AST) -> Provenance:
            char_start, char_end, byte_start, byte_end = offsets(node)
            span_hash = sha256_bytes(raw[byte_start:byte_end])
            return Provenance(
                source_id, source_hash, span_hash, char_start, char_end,
                byte_start, byte_end, int(getattr(node, "lineno", 1)),
                int(getattr(node, "col_offset", 0)) + 1,
                "4.7.1",
            )

        module_name = relative[:-3].replace("/", ".") if relative.endswith(".py") else relative.replace("/", ".")
        module_owner = Provenance(
            source_id, source_hash, source_hash, 0, len(text), 0, len(raw), 1, 1,
            "4.7.1",
        )
        file_id = declare(MeaningType.CODE_FILE, relative, {
            "path": relative, "file_sha256": source_hash, "language": "python",
        }, module_owner)
        module_id = declare(MeaningType.CODE_SYMBOL, module_name, {
            "symbol_kind": "module", "qualified_name": module_name, "file_id": file_id,
        }, module_owner)
        edge("contains", file_id, module_id, module_owner)
        edge("defines", file_id, module_id, module_owner)

        local_by_simple: dict[str, str] = {}
        node_to_symbol: dict[int, str] = {}
        parent_by_node: dict[int, str] = {}

        def walk_definitions(body: list[ast.stmt], parent_id: str, prefix: str) -> None:
            for node in body:
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue
                qualified = f"{prefix}.{node.name}"
                owner = provenance(node)
                symbol_kind = "class" if isinstance(node, ast.ClassDef) else (
                    "async-function" if isinstance(node, ast.AsyncFunctionDef) else "function"
                )
                symbol_id = declare(MeaningType.CODE_SYMBOL, qualified, {
                    "symbol_kind": symbol_kind, "qualified_name": qualified,
                    "file_id": file_id,
                }, owner)
                node_to_symbol[id(node)] = symbol_id
                parent_by_node[id(node)] = parent_id
                local_by_simple.setdefault(node.name, symbol_id)
                edge("contains", file_id, symbol_id, owner)
                edge("defines", parent_id, symbol_id, owner)
                char_start, char_end, byte_start, byte_end = offsets(node)
                span_id = declare(MeaningType.CODE_SPAN, f"{relative}:{byte_start}:{byte_end}", {
                    "file_id": file_id, "symbol_id": symbol_id,
                    "start_byte": byte_start, "end_byte": byte_end,
                    "start_char": char_start, "end_char": char_end,
                    "span_sha256": sha256_bytes(raw[byte_start:byte_end]),
                }, owner)
                edge("contains", symbol_id, span_id, owner)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for argument in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs):
                        arg_owner = provenance(argument)
                        arg_id = declare(MeaningType.CODE_SYMBOL, f"{qualified}:{argument.arg}", {
                            "symbol_kind": "parameter", "qualified_name": f"{qualified}:{argument.arg}",
                            "file_id": file_id,
                        }, arg_owner)
                        edge("defines", symbol_id, arg_id, arg_owner)
                walk_definitions(node.body, symbol_id, qualified)

        walk_definitions(tree.body, module_id, module_name)

        external: dict[str, str] = {}

        def external_symbol(name: str, owner: Provenance, symbol_kind: str = "external") -> str:
            if name in external:
                owners[external[name]].append(owner)
                return external[name]
            identifier = declare(MeaningType.CODE_SYMBOL, f"external:{name}", {
                "symbol_kind": symbol_kind, "qualified_name": name, "external": True,
            }, owner)
            external[name] = identifier
            return identifier

        def expression_name(node: ast.AST) -> str | None:
            if isinstance(node, ast.Name):
                return node.id
            if isinstance(node, ast.Attribute):
                base = expression_name(node.value)
                return f"{base}.{node.attr}" if base else node.attr
            return None

        # Track the nearest compiled definition for calls and references.
        stack: list[str] = [module_id]

        class Visitor(ast.NodeVisitor):
            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                symbol_id = node_to_symbol[id(node)]
                owner = provenance(node)
                for decorator in node.decorator_list:
                    name = expression_name(decorator)
                    if name:
                        destination = local_by_simple.get(name) or external_symbol(name, owner, "decorator")
                        edge("decorated-by", symbol_id, destination, owner)
                stack.append(symbol_id)
                self.generic_visit(node)
                stack.pop()

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
                symbol_id = node_to_symbol[id(node)]
                owner = provenance(node)
                for decorator in node.decorator_list:
                    name = expression_name(decorator)
                    if name:
                        destination = local_by_simple.get(name) or external_symbol(name, owner, "decorator")
                        edge("decorated-by", symbol_id, destination, owner)
                stack.append(symbol_id)
                self.generic_visit(node)
                stack.pop()

            def visit_ClassDef(self, node: ast.ClassDef) -> None:
                symbol_id = node_to_symbol[id(node)]
                owner = provenance(node)
                for base in node.bases:
                    name = expression_name(base)
                    if name:
                        destination = local_by_simple.get(name) or external_symbol(name, owner)
                        edge("inherits", symbol_id, destination, owner)
                for decorator in node.decorator_list:
                    name = expression_name(decorator)
                    if name:
                        edge("decorated-by", symbol_id, external_symbol(name, owner, "decorator"), owner)
                stack.append(symbol_id)
                self.generic_visit(node)
                stack.pop()

            def visit_Import(self, node: ast.Import) -> None:
                owner = provenance(node)
                for alias in node.names:
                    edge("imports", module_id, external_symbol(alias.name, owner, "module"), owner)

            def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
                owner = provenance(node)
                prefix = node.module or ""
                for alias in node.names:
                    name = f"{prefix}.{alias.name}".strip(".")
                    edge("imports", module_id, external_symbol(name, owner), owner)

            def visit_Call(self, node: ast.Call) -> None:
                owner = provenance(node)
                name = expression_name(node.func)
                if name:
                    destination = local_by_simple.get(name.split(".")[-1]) or external_symbol(name, owner)
                    edge("calls", stack[-1], destination, owner)
                    current = records.get(stack[-1])
                    if current and str(current.payload.get("qualified_name", "")).split(".")[-1].startswith("test_"):
                        edge("tests", stack[-1], destination, owner)
                self.generic_visit(node)

            def visit_Name(self, node: ast.Name) -> None:
                if isinstance(node.ctx, ast.Load):
                    owner = provenance(node)
                    destination = local_by_simple.get(node.id) or external_symbol(node.id, owner)
                    edge("references", stack[-1], destination, owner)

        Visitor().visit(tree)

    final_meanings = [
        Meaning(identifier, item.kind, item.name, item.payload, tuple(sorted(set(owners[identifier]))))
        for identifier, item in sorted(records.items())
    ]
    final_edges = [
        SemanticEdge(
            digest("moth-capability-edge/4.7", {
                "relation_id": relation_id, "source_id": source_id, "destination_id": destination_id,
            }), relation_id, source_id, destination_id, tuple(sorted(set(edge_owners[key]))),
        )
        for key in sorted(edge_owners)
        for relation_id, source_id, destination_id in [key]
    ]
    return final_meanings, final_edges, sources

