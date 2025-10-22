"""
Command Line Interface for Excel2PyRAL Converter

This module provides the main CLI entry point for converting Excel register 
specifications to PyUVM RAL models.
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional

from . import ExcelToPyRALConverter, ExcelToSystemRDLImporter, SystemRDLCompiler, __version__

def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Convert Excel register specifications to PyUVM RAL models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic conversion
  pyral registers.xlsx
  
  # Specify output directory
  pyral registers.xlsx -o output/
  
  # Keep intermediate SystemRDL file
  pyral registers.xlsx --keep-rdl
  
  # Custom top-level name and package name
  pyral registers.xlsx --top-name chip_top --package-name chip_ral_pkg
  
  # Use custom sheet names
  pyral registers.xlsx --submodule-sheet Hierarchy --default-sheet defaults

Excel File Format:
  Required sheets:
    - 'Submodules': Contains submodule hierarchy with columns:
      * Submodule Name, Instances, Base Addresses
    - One sheet per submodule with register definitions:
      * Register Name, Offset, Field Name, Field Bits, [optional columns]
  
  Optional sheets:
    - 'default': Contains default properties with columns:
      * SW Access, HW Access, Access Width, Reg Width

For more information, visit: https://github.com/SanCodex/excel2pyral
        """
    )
    
    # Version
    parser.add_argument(
        "--version",
        action="version", 
        version=f"excel2pyral {__version__}"
    )
    
    # Input file (required)
    parser.add_argument(
        "excel_file",
        help="Path to Excel file containing register specifications"
    )
    
    # Output options
    output_group = parser.add_argument_group("output options")
    output_group.add_argument(
        "-o", "--output",
        dest="output",
        default="output",
        help="Output directory for generated files (default: output)"
    )
    output_group.add_argument(
        "-r", "--keep-rdl",
        action="store_true",
        help="Keep intermediate SystemRDL file"
    )
    
    # Naming options
    naming_group = parser.add_argument_group("naming options")
    naming_group.add_argument(
        "-t", "--top-name",
        help="Override top-level addrmap name (default: from filename)"
    )
    naming_group.add_argument(
        "--package-name",
        help="Name for generated UVM package (default: {top}_ral)"
    )
    
    # PyUVM options
    pyuvm_group = parser.add_argument_group("PyUVM options")
    pyuvm_group.add_argument(
        "--enhanced-classes",
        action="store_true",
        default=True,
        help="Use enhanced PyUVM classes (default: True)"
    )
    
    # Sheet configuration
    sheet_group = parser.add_argument_group("Excel sheet options")
    sheet_group.add_argument(
        "--submodule-sheet",
        default="Submodules",
        help="Name of sheet containing submodule hierarchy (default: Submodules)"
    )
    sheet_group.add_argument(
        "--default-sheet", 
        default="default",
        help="Name of sheet containing default properties (default: default)"
    )
    
    # Verbosity
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true", 
        help="Suppress all output except errors"
    )
    
    return parser

def validate_args(args):
    """Validate command line arguments."""
    # Check Excel file exists
    if not os.path.exists(args.excel_file):
        return f"Excel file not found: {args.excel_file}"
    
    # Check extension
    if not args.excel_file.lower().endswith(('.xlsx', '.xls')):
        return f"Excel file must have .xlsx or .xls extension: {args.excel_file}"
        
    return None

def main():
    """Main entry point for pyral command."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Validate arguments
    error = validate_args(args)
    if error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    
    # Configure output verbosity  
    if args.quiet:
        import logging
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create converter with all components
        converter = ExcelToPyRALConverter()
        
        if not args.quiet:
            print(f"🚀 excel2pyral PyUVM RAL Generator v{__version__}")
            print(f"📊 Input: {args.excel_file}")
            print(f"📁 Output: {args.output}")
            if args.keep_rdl:
                print("🔍 Keeping intermediate SystemRDL file")
            print()
            
        # Convert Excel to PyUVM RAL
        result = converter.convert(
            excel_file=args.excel_file,
            output=args.output,
            top_name=args.top_name,
            package_name=args.package_name,
            submodule_sheet=args.submodule_sheet,
            default_sheet=args.default_sheet,
            keep_rdl=args.keep_rdl,
            use_enhanced_classes=args.enhanced_classes
        )
        
        if not args.quiet:
            print()
            print("📋 Conversion Summary:")
            print(f"   Excel file:  {args.excel_file}")
            print(f"   PyUVM RAL:   {result['pyuvm_file']}")
            if args.keep_rdl:
                print(f"   SystemRDL:   {result['systemrdl_file']}")
            print(f"   Directory:   {args.output}")
            print()
            print("✅ Conversion completed successfully!")
            
    except KeyboardInterrupt:
        if not args.quiet:
            print("\n⚠️  Conversion interrupted by user")
        sys.exit(130)
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}", file=sys.stderr)
        sys.exit(2)
        
    except ValueError as e:
        print(f"❌ Conversion error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(3)
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(4)

def create_genrdl_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser specifically for genrdl command."""
    parser = argparse.ArgumentParser(
        description="Convert Excel register specifications to SystemRDL with built-in validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic conversion to SystemRDL (includes validation)
  genrdl registers.xlsx
  
  # Specify output directory
  genrdl registers.xlsx -o output/
  
  # Custom top-level name
  genrdl registers.xlsx --top-name chip_top
  
  # Use custom sheet names and show validation details
  genrdl registers.xlsx --submodule-sheet Hierarchy --default-sheet defaults -v
        """
    )
    
    # Version
    parser.add_argument(
        "--version",
        action="version", 
        version=f"excel2pyral {__version__}"
    )
    
    # Input file (required)
    parser.add_argument(
        "excel_file",
        help="Path to Excel file containing register specifications"
    )
    
    # Output options
    output_group = parser.add_argument_group("output options")
    output_group.add_argument(
        "-o", "--output",
        dest="output",
        default="output",
        help="Output directory for generated files (default: output)"
    )
    
    # Naming options
    naming_group = parser.add_argument_group("naming options")
    naming_group.add_argument(
        "-t", "--top-name",
        help="Override top-level addrmap name (default: from filename)"
    )
    
    # Sheet configuration
    sheet_group = parser.add_argument_group("Excel sheet options")
    sheet_group.add_argument(
        "--submodule-sheet",
        default="Submodules",
        help="Name of sheet containing submodule hierarchy (default: Submodules)"
    )
    sheet_group.add_argument(
        "--default-sheet", 
        default="default",
        help="Name of sheet containing default properties (default: default)"
    )
    
    # Verbosity
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true", 
        help="Suppress all output except errors"
    )
    
    return parser

def genrdl_main():
    """Entry point for genrdl command to generate and validate SystemRDL file."""
    parser = create_genrdl_parser()
    args = parser.parse_args()
    
    # Validate arguments
    error = validate_args(args)
    if error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    
    # Configure output verbosity
    if args.quiet:
        import logging
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create necessary components
        importer = ExcelToSystemRDLImporter()
        compiler = SystemRDLCompiler()
        
        if not args.quiet:
            print(f"🚀 excel2pyral SystemRDL Generator v{__version__}")
            print(f"📊 Input: {args.excel_file}")
            print(f"📁 Output: {args.output}")
            print("🔍 SystemRDL validation enabled")
            print()
        
        # Create output directory
        os.makedirs(args.output, exist_ok=True)
        
        # Derive top name if not provided
        if not args.top_name:
            args.top_name = os.path.splitext(os.path.basename(args.excel_file))[0]
        
        # Convert Excel to SystemRDL
        systemrdl_content = importer.excel_to_systemrdl(
            excel_file=args.excel_file,
            top_name=args.top_name,
            submodule_sheet=args.submodule_sheet,
            default_sheet=args.default_sheet
        )
        
        # Write SystemRDL file
        rdl_file = os.path.join(args.output, f"{args.top_name}.rdl")
        with open(rdl_file, 'w', encoding='utf-8') as f:
            f.write(systemrdl_content)
        
        # Always validate with SystemRDL compiler
        if not args.quiet:
            print("\n🔍 Validating SystemRDL...")
        compiler.compile(rdl_file)
        if not args.quiet:
            print("✓ SystemRDL validation passed")
        
        if not args.quiet:
            print()
            print("📋 Conversion Summary:")
            print(f"   Excel file: {args.excel_file}")
            print(f"   SystemRDL:  {rdl_file}")
            print(f"   Directory:  {args.output}")
            print()
            print("✅ SystemRDL generation and validation completed successfully!")
            
    except KeyboardInterrupt:
        if not args.quiet:
            print("\n⚠️  Generation interrupted by user")
        sys.exit(130)
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}", file=sys.stderr)
        sys.exit(2)
        
    except ValueError as e:
        print(f"❌ Generation error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(3)
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(4)

if __name__ == "__main__":
    main()