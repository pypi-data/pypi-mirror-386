"""
Go WebSocket client generator.

Generates type-safe Go client from RPC methods.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Type

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel

from ...discovery import RPCMethodInfo
from ...utils import pydantic_to_go, to_go_method_name

logger = logging.getLogger(__name__)


class GoWebSocketGenerator:
    """
    Generator for Go WebSocket clients.

    Creates type-safe Go client with WebSocket transport.
    """

    def __init__(
        self,
        methods: List[RPCMethodInfo],
        models: List[Type[BaseModel]],
        output_dir: Path,
        config=None,
    ):
        """
        Initialize generator.

        Args:
            methods: List of discovered RPC methods
            models: List of Pydantic models to generate types for
            output_dir: Output directory for generated files
            config: Optional RPCServerConfig for environment-aware clients
        """
        self.methods = methods
        self.models = models
        self.output_dir = Path(output_dir)
        self.config = config

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
        # Create output directory structure
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create pkg/types directory for type definitions
        types_dir = self.output_dir / "pkg" / "types"
        types_dir.mkdir(parents=True, exist_ok=True)

        # Generate types (in pkg/types/)
        self._generate_types(types_dir)

        # Generate client (in root)
        self._generate_client()

        # Generate config files
        self._generate_go_mod()
        self._generate_readme()
        self._generate_gitignore()
        self._generate_makefile()

        logger.debug(f"Generated Go client in {self.output_dir}")

    def _generate_types(self, types_dir: Path):
        """Generate individual type files in pkg/types/."""
        # Template for individual type files
        type_template = self.jinja_env.get_template("type_file.go.j2")

        # Generate a separate file for each model
        for model in self.models:
            struct = pydantic_to_go(model)

            # Generate file content
            content = type_template.render(
                struct=struct,
                package_name="types",
                generated_at=datetime.now().isoformat(),
            )

            # Write to file named after the model (snake_case)
            filename = self._to_snake_case(model.__name__) + ".go"
            output_file = types_dir / filename
            output_file.write_text(content)
            logger.debug(f"Generated {output_file}")

    def _to_snake_case(self, name: str) -> str:
        """Convert PascalCase to snake_case."""
        import re
        # Insert underscore before uppercase letters (except first)
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        # Insert underscore before uppercase letters followed by lowercase
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _generate_client(self):
        """Generate client.go file."""
        template = self.jinja_env.get_template("client.go.j2")

        # Prepare methods for template
        method_infos = []
        for method in self.methods:
            method_info = {
                "original_name": method.name,
                "go_name": to_go_method_name(method.name),
                "params_type": method.param_type.__name__ if method.param_type else "map[string]interface{}",
                "result_type": method.return_type.__name__ if method.return_type else "map[string]interface{}",
                "description": method.docstring or f"Call {method.name} RPC method",
            }
            method_infos.append(method_info)

        # Prepare environment config if available
        environments = None
        if self.config:
            environments = {
                env: {
                    "websocket_url": self.config.get_endpoint(env).websocket_url,
                    "redis_url": self.config.get_endpoint(env).redis_url,
                }
                for env in self.config.list_environments()
            }

        content = template.render(
            methods=method_infos,
            environments=environments,
            package_name="rpcclient",
            generated_at=datetime.now().isoformat(),
        )

        output_file = self.output_dir / "client.go"
        output_file.write_text(content)
        logger.debug(f"Generated {output_file}")

    def _generate_go_mod(self):
        """Generate go.mod file."""
        template = self.jinja_env.get_template("go.mod.j2")

        content = template.render()

        output_file = self.output_dir / "go.mod"
        output_file.write_text(content)
        logger.debug(f"Generated {output_file}")

    def _generate_readme(self):
        """Generate README.md file."""
        template = self.jinja_env.get_template("README.md.j2")

        # Get sample method for examples
        sample_method = self.methods[0] if self.methods else None

        # Prepare environment config if available
        environments = None
        if self.config:
            environments = {
                env: {
                    "websocket_url": self.config.get_endpoint(env).websocket_url,
                    "redis_url": self.config.get_endpoint(env).redis_url,
                }
                for env in self.config.list_environments()
            }

        content = template.render(
            methods=self.methods,
            sample_method=sample_method,
            environments=environments,
        )

        output_file = self.output_dir / "README.md"
        output_file.write_text(content)
        logger.debug(f"Generated {output_file}")

    def _generate_gitignore(self):
        """Generate .gitignore file."""
        template = self.jinja_env.get_template(".gitignore.j2")

        content = template.render()

        output_file = self.output_dir / ".gitignore"
        output_file.write_text(content)
        logger.debug(f"Generated {output_file}")

    def _generate_makefile(self):
        """Generate Makefile."""
        template = self.jinja_env.get_template("Makefile.j2")

        content = template.render()

        output_file = self.output_dir / "Makefile"
        output_file.write_text(content)
        logger.debug(f"Generated {output_file}")


__all__ = ["GoWebSocketGenerator"]
