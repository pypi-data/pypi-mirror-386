"""
Command-line interface for the SW Registry Stack Python SDK.
"""

import asyncio
import argparse
import json
import logging
import sys
from typing import Optional
from . import OperatorRegistry
from .exceptions import SdkError


def setup_logging(debug: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def print_json(data: any, pretty: bool = True) -> None:
    """Print data as JSON."""
    if pretty:
        print(json.dumps(data, indent=2, default=str))
    else:
        print(json.dumps(data, default=str))


async def cmd_list(args: argparse.Namespace) -> None:
    """List operators command."""
    registry = OperatorRegistry({
        "base_path": args.base_path,
        "bridge_lib_path": args.bridge_lib_path,
        "debug": args.debug
    })
    
    try:
        await registry.initialize()
        
        from .types import OperatorListOptions
        options = OperatorListOptions(
            remote=args.remote,
            page=args.page,
            page_size=args.page_size,
            operator=args.operator,
            versions=args.versions
        )
        
        result = await registry.list(options)
        print_json(result.dict(), args.pretty)
        
    except SdkError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await registry.close()


async def cmd_install(args: argparse.Namespace) -> None:
    """Install operator command."""
    registry = OperatorRegistry({
        "base_path": args.base_path,
        "bridge_lib_path": args.bridge_lib_path,
        "debug": args.debug
    })
    
    try:
        await registry.initialize()
        
        from .types import OperatorInstallOptions
        options = OperatorInstallOptions(
            platform=args.platform,
            force=args.force
        )
        
        result = await registry.install(args.name_version, options)
        print_json(result.dict(), args.pretty)
        
    except SdkError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await registry.close()


async def cmd_uninstall(args: argparse.Namespace) -> None:
    """Uninstall operator command."""
    registry = OperatorRegistry({
        "base_path": args.base_path,
        "bridge_lib_path": args.bridge_lib_path,
        "debug": args.debug
    })
    
    try:
        await registry.initialize()
        
        result = await registry.uninstall(args.name, args.version)
        print_json(result.dict(), args.pretty)
        
    except SdkError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await registry.close()


async def cmd_info(args: argparse.Namespace) -> None:
    """Get operator info command."""
    registry = OperatorRegistry({
        "base_path": args.base_path,
        "bridge_lib_path": args.bridge_lib_path,
        "debug": args.debug
    })
    
    try:
        await registry.initialize()
        
        from .types import OperatorInfoOptions
        options = OperatorInfoOptions(remote=args.remote)
        
        result = await registry.info(args.name_version, options)
        print_json(result.dict(), args.pretty)
        
    except SdkError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await registry.close()


async def cmd_push(args: argparse.Namespace) -> None:
    """Push operator command."""
    registry = OperatorRegistry({
        "base_path": args.base_path,
        "bridge_lib_path": args.bridge_lib_path,
        "debug": args.debug
    })
    
    try:
        await registry.initialize()
        
        from .types import OperatorPushOptions
        options = OperatorPushOptions(local=args.local_only)
        
        result = await registry.push(args.name_version, args.tar_path, options)
        print_json(result.dict(), args.pretty)
        
    except SdkError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await registry.close()


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="SW Registry Stack Python SDK CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Global options
    parser.add_argument(
        "--base-path",
        default="/opt/operators",
        help="Base path for operations (default: /opt/operators)"
    )
    parser.add_argument(
        "--bridge-lib-path",
        help="Path to the native bridge library"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty print JSON output"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List operators")
    list_parser.add_argument("--remote", action="store_true", help="List remote operators")
    list_parser.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    list_parser.add_argument("--page-size", type=int, default=25, help="Page size (default: 25)")
    list_parser.add_argument("--operator", help="Filter by operator name")
    list_parser.add_argument("--versions", action="store_true", help="List versions")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install an operator")
    install_parser.add_argument("name_version", help="Operator name@version (e.g., signalgenerator@1.0.0)")
    install_parser.add_argument("--platform", help="Target platform (e.g., linux/amd64)")
    install_parser.add_argument("--force", action="store_true", help="Force reinstall")
    
    # Uninstall command
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall an operator")
    uninstall_parser.add_argument("name", help="Operator name")
    uninstall_parser.add_argument("version", help="Operator version")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Get operator information")
    info_parser.add_argument("name_version", help="Operator name@version")
    info_parser.add_argument("--remote", action="store_true", help="Get info from remote registry")
    
    # Push command
    push_parser = subparsers.add_parser("push", help="Push an operator")
    push_parser.add_argument("name_version", help="Operator name@version")
    push_parser.add_argument("tar_path", help="Path to operator tar.gz file")
    push_parser.add_argument("--local-only", action="store_true", help="Only register locally")
    
    return parser


async def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    setup_logging(args.debug)
    
    # Route to appropriate command
    command_map = {
        "list": cmd_list,
        "install": cmd_install,
        "uninstall": cmd_uninstall,
        "info": cmd_info,
        "push": cmd_push,
    }
    
    if args.command in command_map:
        await command_map[args.command](args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
