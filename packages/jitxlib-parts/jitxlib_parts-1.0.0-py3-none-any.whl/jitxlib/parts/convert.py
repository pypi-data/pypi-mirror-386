import os
import ast
import jitx
import logging
from collections.abc import Sequence, Mapping
from collections import deque
from .commands import PartJSON
from ._types.component import ComponentCode, Category
from ._types.main import to_component, download_model3d_files
from ._sanitize import (
    python_component_name,
    python_manufacturer_folder,
)
from ._convert_utils import component_code_to_ast_module, StdLibSymbolType

logger = logging.getLogger(__name__)


# ================ Utilities to handle module paths ================
#     Functions: generate_python_file_description,
# ==================================================================
def generate_python_file_description(component_code: ComponentCode) -> str:
    """
    Generate a description for the generated Python code written to the file, including
    instructions on how to import the component.
    """
    component_name = python_component_name(component_code.mpn, component_code.name)
    mpn = component_code.mpn or "<MPN>"
    manufacturer = (
        python_manufacturer_folder(component_code.manufacturer)
        if component_code.manufacturer
        else "MANUFACTURER"
    )

    description_lines = [
        "# This file is generated based on the parts database query below:",
        "#     from jitx.circuit import Circuit",
        "#     from jitxlib.parts import Part",
        "#     class Example(Circuit):",
        "#         def __init__(self):",
        f'#            self.part = Part(mpn="{mpn}", manufacturer="{manufacturer}")',
        "#",
        f"# File Location: components/{manufacturer}/{component_name}.py",
        "# To use this component:",
        f"#     from .components.{manufacturer} import {component_name}",
        "#     class Example(Circuit):",
        f"#         u1 = {component_name}.Device()",
        "",
    ]
    return "\n".join(description_lines)


# ================ Utilities to process AST Models ================
#     Functions: extract_subclasses_from_ast_module, ast_module_to_string
# =================================================================


# Extracts all class names in the AST that inherit from a given base class name.
def extract_subclasses_from_ast_module(
    ast_module: ast.Module, base_class_name: str
) -> Sequence[str]:
    subclass_names = []
    for node in ast_module.body:
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if (isinstance(base, ast.Name) and base.id == base_class_name) or (
                    isinstance(base, ast.Attribute) and base.attr == base_class_name
                ):
                    subclass_names.append(node.name)
    return subclass_names


# Unparse an AST module and optionally format the output to PEP8 using black
# Return the unparsed (and optionally formatted) source code.
def ast_module_to_string(module_ast: ast.Module, format_pep8: bool = True) -> str:
    code_string = ast.unparse(module_ast)
    if format_pep8:
        try:
            import black

            code_string = black.format_str(code_string, mode=black.FileMode())
        except Exception:
            logger.exception("Failed to format the code using black")
    return code_string


# ======== compare_ast_with_ast_from_unparse ========
# Compare the AST we created from the ComponentCode
# with the AST derived from parsing the python file, generated from the AST we created.
# Convert all Constant(value=-X) including -0.0 into UnaryOp(op=USub(), operand=Constant(value=X))
def rewrite_negative_constants(tree: ast.Module) -> ast.Module:
    import math

    class RewriteNegativeConstants(ast.NodeTransformer):
        def visit_Constant(self, node: ast.Constant) -> ast.AST:
            val = node.value
            if isinstance(val, (int, float)) and (
                val < 0 or (val == 0.0 and math.copysign(1.0, val) == -1.0)
            ):
                return ast.UnaryOp(op=ast.USub(), operand=ast.Constant(value=abs(val)))
            return node

    return RewriteNegativeConstants().visit(tree)


# Compare the AST of a Python file with the provided AST module.
# - If output_path is provided, write the unified diff in output_path + ."diff_ast".
# - Returns True if the ASTs match, False otherwise.
def compare_ast_with_ast_from_unparse(
    ast_module: ast.Module, output_path: str | None = None
) -> bool:
    import os
    import difflib

    def strip_ast_locations(module: ast.Module) -> ast.Module:
        for node in ast.walk(module):
            for attribute in ("lineno", "col_offset", "end_lineno", "end_col_offset"):
                if hasattr(node, attribute):
                    delattr(node, attribute)
        return module

    # unparse to source_code and then parse to AST
    try:
        source_code = ast_module_to_string(ast_module)
        ast_from_parsed_code = ast.parse(source_code)
    except SyntaxError:
        logger.exception("Failed to parse the source code")
        return False

    # Strip locations from both ASTs
    ast_from_parsed_code = strip_ast_locations(ast_from_parsed_code)
    ast_module = strip_ast_locations(ast_module)
    # normalize ast_module for easier comparison
    ast_module = rewrite_negative_constants(ast_module)

    dump_ast_from_parsed_code = ast.dump(
        ast_from_parsed_code, include_attributes=True, indent=4
    )
    dump_ast_module = ast.dump(ast_module, include_attributes=True, indent=4)

    if dump_ast_from_parsed_code == dump_ast_module:
        logger.info("The ASTs match.")
        return True

    if isinstance(output_path, str):
        diff = list(
            difflib.unified_diff(
                dump_ast_from_parsed_code.splitlines(),
                dump_ast_module.splitlines(),
                fromfile=f"{output_path} (parsed)",
                tofile="ast_module (generated)",
                lineterm="",
            )
        )
        # Clean up old files from previous run if any
        for ext in [".dump_ast_from_parsed_code", ".dump_ast_module", ".diff_ast"]:
            try:
                os.remove(output_path + ext)
            except FileNotFoundError:
                pass
        with open(
            output_path + ".fdump_ast_from_parsed_code", "w", encoding="utf-8"
        ) as f:
            f.write(dump_ast_from_parsed_code)
        with open(output_path + ".dump_ast_module", "w", encoding="utf-8") as f:
            f.write(dump_ast_module)
        with open(output_path + ".diff_ast", "w", encoding="utf-8") as f:
            for line in diff:
                if (
                    line.startswith("+")
                    or line.startswith("-")
                    or line.startswith("@@")
                ):
                    print(line)
                    f.write(line + "\n")
        logger.info(f"📄 Diff written to {output_path}.diff_ast")
    raise AssertionError("AST mismatch detected!")


# ================ Utilities to compile python source code ================
#     Functions: get_namespace_from_source_code, compile_subclasses_from_source_code etc
# =================================================================


def get_namespace_from_source_code(
    source_code: str, source_file: str = "dummy"
) -> Mapping[str, object]:
    code = compile(source_code, filename=source_file, mode="exec")
    namespace: dict[str, object] = {}
    exec(code, namespace, namespace)  # Use namespace for both globals and locals
    return namespace


# Load and compile the Python source code (in string)
# Return the object of the given class name.
def compile_class_from_source_code(
    source_code: str, class_name: str, source_file: str = "dummy"
) -> type:
    namespace = get_namespace_from_source_code(source_code, source_file=source_file)
    if class_name not in namespace:
        raise ValueError(f"Class '{class_name}' not found in the given source code")
    obj = namespace[class_name]
    if not isinstance(obj, type):
        raise ValueError(f"'{class_name}' is an instance not a class")
    return obj


def get_subclasses_from_namespace[T](
    namespace: Mapping[str, object], base_class: type[T]
) -> Sequence[type[T]]:
    return [
        obj
        for obj in namespace.values()
        if (
            isinstance(obj, type)
            and issubclass(obj, base_class)
            and obj is not base_class
        )
    ]


# Compile source code, find all classes that subclass `base_class`.
def compile_subclasses_from_source_code[T](
    source_code: str, base_class: type[T]
) -> Sequence[type[T]]:
    namespace = get_namespace_from_source_code(source_code)
    return get_subclasses_from_namespace(namespace, base_class)


def read_from_file(path: str) -> str:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def compile_subclasses_from_file[T](
    source_file: str,
    base_class: type[T],
) -> Sequence[type[T]]:
    source_code = read_from_file(source_file)
    namespace = get_namespace_from_source_code(source_code, source_file=source_file)
    return get_subclasses_from_namespace(namespace, base_class)


def insert_model3d_dir(component: ComponentCode, model3d_dir: str) -> ComponentCode:
    """
    Modify ComponentCode to place the Model3D files under the model3d_dir folder.

    Example:
        This function would change the filename in a Model3D statement
        "jitx-01234.stp" to "model3d_dir/jitx-01234.stp".
    """
    if component.landpattern is not None:
        for model3d in component.landpattern.model3ds:
            model3d.filename = model3d_dir + "/" + model3d.filename

    return component


# ========= MAIN FUNCTIONS =========
# Convert the ComponentCode (from parts-db) to a jitx.Component type
#   - Convert to AST and unparse to python source code.
#   Case 1: Create the Component object on the fly and return the compiled Component object.
#     - When the DB part is created on the fly, set local_model3d_file to False (default).
#       So, the model3d files are download to "VSCode_Project_Root/3d-models".
#   Case 2: Write the unparsed python code to file for the "Create Component" button.
#     - When the output file (output_path) is generated for the create_component call,
#       set local_model3d_file to True. The model3d files are downloaded to the same folder where the Landpattern class is located.
def convert_component_core(
    component_code: ComponentCode,
    component_name: str | None = None,
    output_path: str | None = None,
    local_model3d_file: bool = False,
    use_jitxstd_symbol: StdLibSymbolType | None = None,
) -> type[jitx.Component] | None:
    # === Handle Model3D files when the output_path will be generated.
    #    1. Download the Model3D files to this folder where output_path is located
    failed_model3ds = []
    if local_model3d_file:
        if output_path is None:
            raise ValueError("output_path is required when local_model3d_file is True")
        failed_model3ds = download_model3d_files(
            component_code, os.path.dirname(output_path)
        )

    else:
        # === Handle Model3D files when the DB part is created on the fly
        # Change the Model3D filename from "jitx-01234.stp" to "./3d-models/jitx-01234.stp".
        # NOTE: The Model3D files will be downloaded to this folder "./3d-models" after the components are written.
        root_path = "."
        model3d_dir = os.path.join(root_path, "3d-models")
        component_code = insert_model3d_dir(component_code, model3d_dir)
        failed_model3ds = download_model3d_files(component_code)

    # === Construct the AST Module from the ComponentCode
    ast_module = component_code_to_ast_module(
        component_code,
        component_name=component_name,
        use_jitxstd_symbol=use_jitxstd_symbol,
        missing_3d_models=failed_model3ds,
    )

    # === Compare ast_module with AST parsed from output_path
    # compare_ast_with_ast_from_unparse(ast_module, "output_path.py")

    # === Unparse the AST Module to Python source code (in string) and add the file description
    source_code = ast_module_to_string(ast_module)
    if output_path is not None:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(generate_python_file_description(component_code))
            f.write(source_code)

    if local_model3d_file:
        # === Handle Model3D files when the output_path is given.
        if output_path is None:
            raise ValueError("output_path is required when local_model3d_file is True")
        # Download the Model3D files to this folder where output_path is located
        download_model3d_files(component_code, os.path.dirname(output_path))
        return None
    else:
        # === Handle Model3D files when the DB part is created on the fly
        # Download the Model3D files to this folder "./3d-models".
        download_model3d_files(component_code)

        # Compile the Python source code (in string) and extract the subclass of 'Component'
        subclasses = compile_subclasses_from_source_code(source_code, jitx.Component)
        if not subclasses:
            raise ValueError("No subclass of 'Component' found in AST.")
        compiled_component = subclasses[0]

        # === Return the compiled Component object
        return compiled_component


def convert_component(
    component_code: ComponentCode,
    component_name: str | None = None,
    output_path: str | None = None,
    use_jitxstd_symbol: StdLibSymbolType | None = None,
) -> type[jitx.Component]:
    compiled_component = convert_component_core(
        component_code,
        component_name,
        output_path,
        local_model3d_file=False,
        use_jitxstd_symbol=use_jitxstd_symbol,
    )
    if compiled_component is None:
        raise ValueError("No subclass of 'Component' found in AST.")
    return compiled_component


MARKER_FILENAME = ".import-target-folder.jitx"


def write_marker_file(root_path: str, rel_path_to_init: str) -> None:
    """
    Write a marker file in root_path that declares the import target folder.
    """
    marker_file = os.path.join(root_path, MARKER_FILENAME)
    marker_file_template = (
        "# The importer will put imported files in the import_target folder specified below.\n"
        "# If this file '.import-target-folder.jitx' is not found, we will look for the first python package we can find\n"
        "# and create this file to specify the import_target folder used by the importer.\n"
        f"import_target = {rel_path_to_init}\n"
    )
    with open(marker_file, "w", encoding="utf-8") as f:
        f.write(marker_file_template)


def read_import_target_from_marker_file(root_path: str) -> str | None:
    """
    Read the import_target folder from the marker file if exists.

    Returns:
        str | None: relative path to the package if valid, otherwise None.
    """
    marker_file_path = os.path.join(root_path, MARKER_FILENAME)
    if not os.path.exists(marker_file_path):
        return None

    with open(marker_file_path, "r", encoding="utf-8") as marker_file:
        for line in marker_file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key == "import_target":
                if os.path.isdir(os.path.join(root_path, value)):
                    return value
                else:
                    logger.warning(
                        f"The import_target folder '{value}' does not exist or is not a directory."
                    )
                    return None
    return None


def determine_import_target_folder(start_path=".") -> str:
    """
    Determine the path to the source package, containing the __init__.py file, to use as the import_target folder.

    Perform a breadth-first search from `start_path` to find the top-most
    directory that contains an __init__.py file.
    Use a marker file to cache the result to avoid repeated searches.

    Returns:
        str: relative path to the found package directory
    """
    import_target = read_import_target_from_marker_file(start_path)
    if import_target is not None:
        return import_target
    start_path = os.path.abspath(start_path)
    queue = deque([start_path])
    while queue:
        current_dir = queue.popleft()
        init_file = os.path.join(current_dir, "__init__.py")

        if os.path.isfile(init_file):
            rel_path_to_init = os.path.relpath(current_dir, start_path)
            write_marker_file(start_path, rel_path_to_init)
            return rel_path_to_init

        try:
            for entry in os.scandir(current_dir):
                if entry.is_dir() and not entry.name.startswith("."):
                    queue.append(entry.path)
        except PermissionError:
            pass  # skip unreadable directories

    raise FileNotFoundError("No package with __init__.py found under " + start_path)


# For the "Create Component" button in the Component Card of the Explorer
# The same behavior as save_component in tools/explorer-code-generator.stanza
#        save-component (part-json-input: JObject, root-path:String|False)
#                       ->  JObject(["package" => package_reference "path" => module_path])
#    and create-component-file in tools/explorer-code-generator.stanza
#        defn create-component-file (c:ComponentCode, query-params:Tuple<KeyValue<String, ?>>, root-path:String|False)
#                        -> [package_reference module_path]:
# Returns (package-reference path-to-python-file) where
#    package-reference = "from components.manufacturer.mpn import Componentmpn"
#    path-to-python-file = "components/manufacturer/mpn import.py"
def create_component(part_json: PartJSON) -> tuple[str, str]:
    # Presumption: The CWD is the project folder.
    root_path = "."

    # === Convert to 'Part' and also applies make_model_3d_relative ito Model3D statements
    part_obj = to_component(part_json)
    component_code = part_obj.component

    # === Determine the file path for the generated Python code and create folders as needed
    component_name = python_component_name(component_code.mpn, component_code.name)
    manufacturer = (
        python_manufacturer_folder(component_code.manufacturer)
        if component_code.manufacturer
        else "MANUFACTURER"
    )

    # === The folder to place the components file is the top package, containing the __init__.py file
    import_target_folder = determine_import_target_folder(root_path)

    # === Determine the file path for the generated Python code
    output_python_path = os.path.join(
        root_path,
        import_target_folder,
        "components",
        manufacturer,
        f"{component_name}.py",
    )
    os.makedirs(os.path.dirname(output_python_path), exist_ok=True)

    # === Create "components/__init__.py" and "components/manufacturer/__init__.py" if needed
    components_init_path = os.path.join(
        root_path, import_target_folder, "components", "__init__.py"
    )
    if not os.path.isfile(components_init_path):
        with open(components_init_path, "w") as f:
            f.write("")
    manufacturer_init_path = os.path.join(
        root_path, import_target_folder, "components", manufacturer, "__init__.py"
    )
    if not os.path.isfile(manufacturer_init_path):
        with open(manufacturer_init_path, "w") as f:
            f.write("")

    # === Compile + write component Python source
    convert_component_core(
        component_code,
        output_path=output_python_path,
        local_model3d_file=True,
        use_jitxstd_symbol=get_jitxstd_symbol(part_obj.category),
    )

    # === Create the package reference for the "Copy to Clipboard" button
    package_reference = f"from .components.{manufacturer} import {component_name}"
    relative_output_python_path = os.path.join(
        import_target_folder, "components", manufacturer, f"{component_name}.py"
    )

    return package_reference, relative_output_python_path


# Does not support Category.POLARIZED_CAPACITOR
def get_jitxstd_symbol(category: Category | None) -> StdLibSymbolType | None:
    match category:
        case Category.RESISTOR:
            return StdLibSymbolType.Resistor
        case Category.INDUCTOR:
            return StdLibSymbolType.Inductor
        case Category.CAPACITOR:
            return StdLibSymbolType.Capacitor
        case _:
            return None
