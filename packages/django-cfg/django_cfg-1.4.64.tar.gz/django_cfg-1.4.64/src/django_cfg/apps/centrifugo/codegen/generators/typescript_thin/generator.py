"""
TypeScript thin wrapper client generator.
"""

import logging
from pathlib import Path
from typing import List, Type
from pydantic import BaseModel
from jinja2 import Environment, FileSystemLoader, select_autoescape

from ...discovery import RPCMethodInfo
from ...utils import to_typescript_method_name, pydantic_to_typescript

logger = logging.getLogger(__name__)


class TypeScriptThinGenerator:
    """Generator for TypeScript thin wrapper clients."""

    def __init__(
        self,
        methods: List[RPCMethodInfo],
        models: List[Type[BaseModel]],
        output_dir: Path,
    ):
        self.methods = methods
        self.models = models
        self.output_dir = Path(output_dir)

        templates_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(self):
        """Generate all TypeScript files."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._generate_types()
        self._generate_rpc_client()
        self._generate_client()
        self._generate_index()
        self._generate_package_json()
        self._generate_tsconfig()
        self._generate_readme()

        logger.info(f"✅ Generated TypeScript client in {self.output_dir}")

    def _generate_types(self):
        """Generate types.ts file."""
        template = self.jinja_env.get_template("types.ts.j2")

        types_data = []
        for model in self.models:
            ts_interface = pydantic_to_typescript(model)
            types_data.append({
                'name': model.__name__,
                'code': ts_interface,
            })

        content = template.render(types=types_data)
        (self.output_dir / "types.ts").write_text(content)

    def _generate_rpc_client(self):
        """Generate rpc-client.ts base class."""
        template = self.jinja_env.get_template("rpc-client.ts.j2")
        content = template.render()
        (self.output_dir / "rpc-client.ts").write_text(content)

    def _generate_client(self):
        """Generate client.ts thin wrapper."""
        template = self.jinja_env.get_template("client.ts.j2")

        methods_data = []
        for method in self.methods:
            param_type = method.param_type.__name__ if method.param_type else "any"
            return_type = method.return_type.__name__ if method.return_type else "any"
            method_name_ts = to_typescript_method_name(method.name)

            methods_data.append({
                'name': method.name,
                'name_ts': method_name_ts,
                'param_type': param_type,
                'return_type': return_type,
                'docstring': method.docstring or f"Call {method.name} RPC method",
            })

        model_names = [m.__name__ for m in self.models]

        content = template.render(methods=methods_data, models=model_names)
        (self.output_dir / "client.ts").write_text(content)

    def _generate_index(self):
        """Generate index.ts file."""
        template = self.jinja_env.get_template("index.ts.j2")
        model_names = [m.__name__ for m in self.models]
        content = template.render(models=model_names)
        (self.output_dir / "index.ts").write_text(content)

    def _generate_package_json(self):
        """Generate package.json file."""
        template = self.jinja_env.get_template("package.json.j2")
        content = template.render()
        (self.output_dir / "package.json").write_text(content)

    def _generate_tsconfig(self):
        """Generate tsconfig.json file."""
        template = self.jinja_env.get_template("tsconfig.json.j2")
        content = template.render()
        (self.output_dir / "tsconfig.json").write_text(content)

    def _generate_readme(self):
        """Generate README.md file."""
        template = self.jinja_env.get_template("README.md.j2")
        methods_data = [{'name': m.name, 'name_ts': to_typescript_method_name(m.name)} for m in self.methods[:3]]
        model_names = [m.__name__ for m in self.models]
        content = template.render(methods=methods_data, models=model_names)
        (self.output_dir / "README.md").write_text(content)


__all__ = ['TypeScriptThinGenerator']
