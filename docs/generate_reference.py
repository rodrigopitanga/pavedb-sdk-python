# (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com>
# SPDX-License-Identifier: Apache-2.0

"""Generate the SDK API reference and runnable examples index."""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "pavesdk"
API_REFERENCE = ROOT / "docs" / "reference" / "api.md"
EXAMPLES_REFERENCE = ROOT / "docs" / "reference" / "examples.md"


def module_tree(module: str) -> ast.Module:
    if module == "pavesdk":
        path = PACKAGE / "__init__.py"
    else:
        path = PACKAGE.joinpath(*module.removeprefix("pavesdk.").split("."))
        path = path.with_suffix(".py")
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def public_exports(tree: ast.Module) -> list[str]:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in node.targets
        ):
            names = ast.literal_eval(node.value)
            if isinstance(names, list) and all(isinstance(name, str) for name in names):
                return names
    raise ValueError("pavesdk.__all__ must be a literal list of public names")


def imported_names(tree: ast.Module) -> dict[str, tuple[str, str]]:
    names = {}
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or node.level != 1 or not node.module:
            continue
        module = f"pavesdk.{node.module}"
        for imported in node.names:
            names[imported.asname or imported.name] = (module, imported.name)
    return names


def declaration(tree: ast.Module, name: str) -> ast.AST:
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name == name:
            return node
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            return node
    raise ValueError(f"could not find declaration for {name}")


def prose(node: ast.AST) -> str:
    value = ast.get_docstring(node) or "No documentation is available."
    return "\n\n".join(
        textwrap.fill(" ".join(paragraph.split()), width=88)
        for paragraph in value.split("\n\n")
    )


def argument_text(argument: ast.arg, default: ast.expr | None = None) -> str:
    result = argument.arg
    if argument.annotation is not None:
        result += f": {ast.unparse(argument.annotation)}"
    if default is not None:
        result += f" = {ast.unparse(default)}"
    return result


def parameters(arguments: ast.arguments) -> list[str]:
    positional = [*arguments.posonlyargs, *arguments.args]
    defaults = [None] * (len(positional) - len(arguments.defaults))
    defaults.extend(arguments.defaults)
    values = [
        argument_text(argument, default)
        for argument, default in zip(positional, defaults)
    ]
    if arguments.posonlyargs:
        values.insert(len(arguments.posonlyargs), "/")
    if arguments.vararg is not None:
        values.append(f"*{argument_text(arguments.vararg)}")
    elif arguments.kwonlyargs:
        values.append("*")
    values.extend(
        argument_text(argument, default)
        for argument, default in zip(arguments.kwonlyargs, arguments.kw_defaults)
    )
    if arguments.kwarg is not None:
        values.append(f"**{argument_text(arguments.kwarg)}")
    return values


def signature_lines(
    node: ast.FunctionDef,
    *,
    name: str | None = None,
    drop_first: bool = False,
    include_return: bool = True,
) -> list[str]:
    values = parameters(node.args)
    if drop_first:
        values = values[1:]
    suffix = ""
    if include_return and node.returns is not None:
        suffix = f" -> {ast.unparse(node.returns)}"
    label = name or node.name
    compact = f"{label}({', '.join(values)}){suffix}"
    if len(compact) <= 88:
        return [compact]
    return [f"{label}(", *[f"    {value}," for value in values], f"){suffix}"]


def function_reference(name: str, node: ast.FunctionDef) -> list[str]:
    return [
        f"## `pavesdk.{name}`",
        "",
        "```python",
        *signature_lines(node),
        "```",
        "",
        prose(node),
        "",
    ]


def class_reference(name: str, node: ast.ClassDef) -> list[str]:
    lines = [f"## `pavesdk.{name}`", "", prose(node), ""]
    constructor = next(
        (
            method
            for method in node.body
            if isinstance(method, ast.FunctionDef) and method.name == "__init__"
        ),
        None,
    )
    if constructor is not None and ast.get_docstring(constructor):
        lines.extend(
            [
                "```python",
                *signature_lines(
                    constructor,
                    name=name,
                    drop_first=True,
                    include_return=False,
                ),
                "```",
                "",
                prose(constructor),
                "",
            ]
        )
    for method in node.body:
        if not isinstance(method, ast.FunctionDef) or method.name.startswith("_"):
            continue
        lines.extend(
            [
                f"### `{name}.{method.name}`",
                "",
                "```python",
                *signature_lines(method),
                "```",
                "",
                prose(method),
                "",
            ]
        )
    return lines


def value_reference(name: str, node: ast.AST) -> list[str]:
    if name == "__version__":
        value = "Installed `pavedb-sdk` distribution version."
    elif isinstance(node, ast.Assign):
        value = f"`{ast.unparse(node.value)}`"
    else:
        value = "No documentation is available."
    return [f"## `pavesdk.{name}`", "", value, ""]


def api_reference() -> str:
    tree = module_tree("pavesdk")
    imports = imported_names(tree)
    lines = [
        "<!-- (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com> -->",
        "<!-- SPDX-License-Identifier: Apache-2.0 -->",
        "<!-- Regenerate: python docs/generate_reference.py -->",
        "",
        "# PaveDB Python SDK API Reference",
        "",
        "This reference is generated from `pavesdk.__all__`, the SDK public API "
        "boundary.",
        "",
    ]
    for name in public_exports(tree):
        module, source_name = imports.get(name, ("pavesdk", name))
        node = declaration(module_tree(module), source_name)
        if isinstance(node, ast.FunctionDef):
            lines.extend(function_reference(name, node))
        elif isinstance(node, ast.ClassDef):
            lines.extend(class_reference(name, node))
        else:
            lines.extend(value_reference(name, node))
    return "\n".join(lines).rstrip() + "\n"


def example_modules() -> list[str]:
    modules = []
    for path in sorted((PACKAGE / "examples").rglob("*.py")):
        if path.name in {"__init__.py", "__main__.py"}:
            continue
        relative = path.relative_to(PACKAGE).with_suffix("")
        modules.append(f"pavesdk.{'.'.join(relative.parts)}")
    return modules


def examples_reference() -> str:
    lines = [
        "<!-- (C) 2026 Rodrigo Rodrigues da Silva <rodrigo@flowlexi.com> -->",
        "<!-- SPDX-License-Identifier: Apache-2.0 -->",
        "<!-- Regenerate: python docs/generate_reference.py -->",
        "",
        "# PaveDB Python SDK Examples",
        "",
        "Each bundled example is importable and runnable as a module.",
        "",
    ]
    for module in example_modules():
        source = f"{module.replace('.', '/')}.py"
        lines.extend(
            [
                f"## `{module}`",
                "",
                f"Source: `{source}`",
                "",
                "```bash",
                f"python -m {module}",
                "```",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def rendered_references() -> dict[Path, str]:
    return {
        API_REFERENCE: api_reference(),
        EXAMPLES_REFERENCE: examples_reference(),
    }


def generate() -> None:
    for path, content in rendered_references().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def check() -> int:
    references = rendered_references()
    stale = [
        str(path.relative_to(ROOT))
        for path, content in references.items()
        if not path.is_file() or path.read_text(encoding="utf-8") != content
    ]
    if stale:
        print(
            "Generated documentation is stale: "
            f"{', '.join(stale)}. Run python docs/generate_reference.py.",
            file=sys.stderr,
        )
        return 1

    for module in example_modules():
        command = f"python -m {module}"
        if command not in references[EXAMPLES_REFERENCE]:
            print(f"Missing documented command: {command}", file=sys.stderr)
            return 1
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import importlib, sys; importlib.import_module(sys.argv[1])",
                module,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode:
            print(f"Could not import {module}: {result.stderr}", file=sys.stderr)
            return result.returncode

    print(f"Documentation is current; imported {', '.join(example_modules())}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify generated files")
    args = parser.parse_args()
    if args.check:
        return check()
    generate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
