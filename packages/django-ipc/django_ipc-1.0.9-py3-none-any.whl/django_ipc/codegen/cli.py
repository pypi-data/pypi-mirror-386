"""
CLI for django_ipc code generation.

Usage:
    python -m django_ipc codegen
    python -m django_ipc codegen --output ./clients
    python -m django_ipc codegen --typescript
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Optional

from .discovery import discover_rpc_methods_from_router, get_method_summary, extract_all_models
from .utils.type_converter import generate_typescript_types
from .generators.typescript_websocket.generator import TypeScriptWebSocketGenerator
from .generators.python_websocket.generator import PythonWebSocketGenerator
from .generators.go_websocket.generator import GoWebSocketGenerator

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
    )


def generate_clients(
    router,
    output_dir: Path,
    config: Optional[any] = None,
    typescript: bool = True,
    python: bool = False,
    go: bool = False,
    verbose: bool = False,
):
    """
    Generate WebSocket clients from RPC router.

    Args:
        router: MessageRouter instance with registered handlers
        output_dir: Output directory for generated clients
        config: Optional RPCServerConfig for environment-aware clients
        typescript: Generate TypeScript client
        python: Generate Python client
        go: Generate Go client
        verbose: Verbose logging

    Example:
        >>> from django_ipc.config import RPCServerConfig, RPCEndpointConfig
        >>> config = RPCServerConfig(
        ...     development=RPCEndpointConfig(
        ...         websocket_url="ws://localhost:8001/ws",
        ...         redis_url="redis://localhost:6379/2",
        ...     ),
        ...     production=RPCEndpointConfig(
        ...         websocket_url="wss://api.example.com/ws",
        ...         redis_url="redis://prod-redis:6379/0",
        ...     ),
        ... )
        >>> generate_clients(router, Path("./clients"), config=config)
    """
    setup_logging(verbose)

    logger.info("🚀 Starting code generation...")
    logger.info(f"📂 Output directory: {output_dir}")
    logger.info("")

    # 1. Discover methods
    logger.info("🔍 Discovering RPC methods...")
    methods = discover_rpc_methods_from_router(router)

    if not methods:
        logger.error("❌ No RPC methods found in router!")
        logger.error("   Make sure your router has registered handlers.")
        sys.exit(1)

    logger.info(get_method_summary(methods))
    logger.info("")

    # 2. Extract models
    logger.info("📦 Extracting Pydantic models...")
    models = extract_all_models(methods)
    logger.info(f"   Found {len(models)} unique models:")
    for model in models:
        logger.info(f"     • {model.__name__}")
    logger.info("")

    # 3. Show config info
    if config:
        logger.info("🌍 Using environment-aware configuration:")
        envs = config.list_environments()
        for env in envs:
            endpoint = config.get_endpoint(env)
            logger.info(f"   {env}: {endpoint.websocket_url}")
        logger.info("")

    # 4. Generate clients
    if typescript:
        logger.info("🔷 Generating TypeScript client...")
        ts_output_dir = output_dir / "typescript"
        ts_generator = TypeScriptWebSocketGenerator(
            methods=methods,
            models=models,
            output_dir=ts_output_dir,
            config=config,
        )
        ts_generator.generate()
        logger.info(f"   ✅ TypeScript client generated: {ts_output_dir}")
        logger.info("")

    if python:
        logger.info("🐍 Generating Python client...")
        py_output_dir = output_dir / "python"
        py_generator = PythonWebSocketGenerator(
            methods=methods,
            models=models,
            output_dir=py_output_dir,
            config=config,
        )
        py_generator.generate()
        logger.info(f"   ✅ Python client generated: {py_output_dir}")
        logger.info("")

    if go:
        logger.info("🔵 Generating Go client...")
        go_output_dir = output_dir / "go"
        go_generator = GoWebSocketGenerator(
            methods=methods,
            models=models,
            output_dir=go_output_dir,
            config=config,
        )
        go_generator.generate()
        logger.info(f"   ✅ Go client generated: {go_output_dir}")
        logger.info("")

    # 4. Summary
    logger.info("=" * 80)
    logger.info("✅ Code generation completed successfully!")
    logger.info("=" * 80)
    logger.info("")
    logger.info("📝 Generated files:")

    if typescript:
        ts_output_dir = output_dir / "typescript"
        logger.info(f"   TypeScript: {ts_output_dir}")
        logger.info(f"     • client.ts  - WebSocket RPC client")
        logger.info(f"     • types.ts   - TypeScript type definitions")
        logger.info(f"     • index.ts   - Barrel exports")

    if python:
        py_output_dir = output_dir / "python"
        logger.info(f"   Python: {py_output_dir}")
        logger.info(f"     • client.py  - WebSocket RPC client")
        logger.info(f"     • models.py  - Pydantic models")
        logger.info(f"     • __init__.py - Package exports")

    if go:
        go_output_dir = output_dir / "go"
        logger.info(f"   Go: {go_output_dir}")
        logger.info(f"     • client.go  - WebSocket RPC client")
        logger.info(f"     • types.go   - Go struct definitions")
        logger.info(f"     • go.mod     - Go module file")

    logger.info("")
    logger.info("🎯 Next steps:")

    if typescript:
        logger.info("   TypeScript:")
        logger.info("      import { RPCClient } from './clients/typescript'")
        logger.info("      const rpc = new RPCClient('ws://localhost:8001/ws')")
        logger.info("      await rpc.connect()")
        logger.info("      const result = await rpc.sendEmail({ ... })")

    if python:
        logger.info("")
        logger.info("   Python:")
        logger.info("      from clients.python import RPCClient")
        logger.info("      rpc = RPCClient('ws://localhost:8001/ws')")
        logger.info("      await rpc.connect()")
        logger.info("      result = await rpc.send_email(params)")

    if go:
        logger.info("")
        logger.info("   Go:")
        logger.info("      import rpc \"your-module-name\"")
        logger.info("      client := rpc.NewClientWithEnvironment(rpc.EnvDevelopment)")
        logger.info("      client.Connect()")
        logger.info("      result, err := client.SomeMethod(params)")

    logger.info("")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate WebSocket clients for django_ipc',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate TypeScript and Python clients (default)
  python -m django_ipc codegen

  # Generate only TypeScript
  python -m django_ipc codegen --typescript

  # Generate only Go
  python -m django_ipc codegen --go

  # Generate all three clients
  python -m django_ipc codegen --typescript --python --go

  # Specify output directory
  python -m django_ipc codegen --output ./generated-clients

  # Verbose output
  python -m django_ipc codegen --verbose
        """,
    )

    parser.add_argument(
        '--output',
        '-o',
        type=str,
        default='./rpc-clients',
        help='Output directory for generated clients (default: ./rpc-clients)',
    )

    parser.add_argument(
        '--typescript',
        '-t',
        action='store_true',
        help='Generate TypeScript client only',
    )

    parser.add_argument(
        '--python',
        '-p',
        action='store_true',
        help='Generate Python client only',
    )

    parser.add_argument(
        '--go',
        '-g',
        action='store_true',
        help='Generate Go client only',
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose logging',
    )

    parser.add_argument(
        '--router-path',
        type=str,
        help='Python import path to router instance (e.g., myapp.rpc.router)',
    )

    args = parser.parse_args()

    # Determine what to generate
    any_specific = args.typescript or args.python or args.go
    typescript = args.typescript or not any_specific
    python = args.python or not any_specific
    go = args.go

    output_dir = Path(args.output)

    # For POC, we'll use the example router from poc_test
    # In real usage, user would provide --router-path
    if args.router_path:
        # TODO: Import router from provided path
        logger.error("--router-path not yet implemented")
        logger.error("For now, run POC test to see generation in action")
        sys.exit(1)
    else:
        # Use POC example
        logger.info("⚠️  No --router-path provided, using POC example router")
        logger.info("")

        from .poc_test import create_example_rpc_server
        router = create_example_rpc_server()

    # Generate clients
    generate_clients(
        router=router,
        output_dir=output_dir,
        typescript=typescript,
        python=python,
        go=go,
        verbose=args.verbose,
    )

    return 0


if __name__ == '__main__':
    sys.exit(main())
