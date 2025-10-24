"""
Command-line interface for the petepak package.
"""

import argparse
import sys
from typing import List, Optional

from .core import PetepakClass
from .utils import helper_function, format_message


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the CLI.
    
    Args:
        args: Command line arguments (for testing)
        
    Returns:
        int: Exit code
    """
    parser = argparse.ArgumentParser(
        description="Petepak - A Python package CLI",
        prog="petepak"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="petepak 0.1.0"
    )
    
    parser.add_argument(
        "--name",
        type=str,
        default="Petepak",
        help="Name for the Petepak instance (default: Petepak)"
    )
    
    parser.add_argument(
        "--double",
        type=int,
        help="Double the given number"
    )
    
    parser.add_argument(
        "--message",
        type=str,
        help="Format a message with prefix"
    )
    
    parsed_args = parser.parse_args(args)
    
    try:
        # Create PetepakClass instance
        petepak = PetepakClass(parsed_args.name)
        
        # Print greeting
        print(petepak.greet())
        
        # Handle double option
        if parsed_args.double is not None:
            result = helper_function(parsed_args.double)
            print(f"Double of {parsed_args.double} is {result}")
        
        # Handle message option
        if parsed_args.message:
            formatted = format_message(parsed_args.message)
            print(formatted)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
