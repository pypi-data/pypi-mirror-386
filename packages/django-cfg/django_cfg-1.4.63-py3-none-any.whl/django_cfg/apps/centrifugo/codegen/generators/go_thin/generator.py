"""
Go thin wrapper client generator.

Generates Go structs + thin wrapper over CentrifugoRPCClient.
"""

import logging
from pathlib import Path
from typing import List, Type
from pydantic import BaseModel
from jinja2 import Environment, FileSystemLoader, select_autoescape

from ...discovery import RPCMethodInfo
from ...utils import to_go_method_name, pydantic_to_go

logger = logging.getLogger(__name__)


class GoThinGenerator:
    """
    Generator for Go thin wrapper clients.

    Creates:
    - types.go: Go struct definitions
    - rpc_client.go: Base CentrifugoRPCClient
    - client.go: Thin wrapper with typed methods
    - go.mod: Go module file
    - README.md: Usage documentation
    """

    def __init__(
        self,
        methods: List[RPCMethodInfo],
        models: List[Type[BaseModel]],
        output_dir: Path,
        package_name: str = "centrifugo_client",
        module_path: str = "example.com/centrifugo_client",
    ):
        """
        Initialize generator.

        Args:
            methods: List of discovered RPC methods
            models: List of Pydantic models
            output_dir: Output directory for generated files
            package_name: Go package name
            module_path: Go module path for go.mod
        """
        self.methods = methods
        self.models = models
        self.output_dir = Path(output_dir)
        self.package_name = package_name
        self.module_path = module_path

        # Setup Jinja2 environment
        templates_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(self):
        """Generate all Go files."""
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Generate types
        self._generate_types()

        # Generate RPC client base
        self._generate_rpc_client()

        # Generate thin wrapper
        self._generate_client()

        # Generate config files
        self._generate_go_mod()
        self._generate_readme()

        logger.info(f"✅ Generated Go client in {self.output_dir}")

    def _generate_types(self):
        """Generate types.go file with Go struct definitions."""
        template = self.jinja_env.get_template("types.go.j2")

        # Convert Pydantic models to Go struct info
        types_data = []
        for model in self.models:
            struct_info = pydantic_to_go(model)
            types_data.append(struct_info)

        content = template.render(
            package_name=self.package_name,
            types=types_data,
        )

        output_file = self.output_dir / "types.go"
        output_file.write_text(content)
        logger.debug(f"Generated {output_file}")

    def _generate_rpc_client(self):
        """Generate rpc_client.go base class."""
        template = self.jinja_env.get_template("rpc_client.go.j2")
        content = template.render(package_name=self.package_name)

        output_file = self.output_dir / "rpc_client.go"
        output_file.write_text(content)
        logger.debug(f"Generated {output_file}")

    def _generate_client(self):
        """Generate client.go thin wrapper."""
        template = self.jinja_env.get_template("client.go.j2")

        # Prepare methods for template
        methods_data = []
        for method in self.methods:
            param_type = method.param_type.__name__ if method.param_type else "map[string]interface{}"
            return_type = method.return_type.__name__ if method.return_type else "map[string]interface{}"

            # Convert method name to valid Go identifier (PascalCase)
            method_name_go = to_go_method_name(method.name)

            methods_data.append({
                'name': method.name,  # Original name for RPC call
                'name_go': method_name_go,  # Go-safe name
                'param_type': param_type,
                'return_type': return_type,
                'docstring': method.docstring or f"Call {method.name} RPC method",
            })

        content = template.render(
            package_name=self.package_name,
            methods=methods_data,
        )

        output_file = self.output_dir / "client.go"
        output_file.write_text(content)
        logger.debug(f"Generated {output_file}")

    def _generate_go_mod(self):
        """Generate go.mod file."""
        template = self.jinja_env.get_template("go.mod.j2")
        content = template.render(module_path=self.module_path)

        output_file = self.output_dir / "go.mod"
        output_file.write_text(content)
        logger.debug(f"Generated {output_file}")

    def _generate_readme(self):
        """Generate README.md file."""
        template = self.jinja_env.get_template("README.md.j2")

        # Prepare methods for examples
        methods_data = []
        for method in self.methods[:3]:  # First 3 methods for examples
            methods_data.append({
                'name': method.name,
                'name_go': to_go_method_name(method.name),
            })

        content = template.render(
            package_name=self.package_name,
            module_path=self.module_path,
            methods=methods_data,
        )

        output_file = self.output_dir / "README.md"
        output_file.write_text(content)
        logger.debug(f"Generated {output_file}")


__all__ = ['GoThinGenerator']
