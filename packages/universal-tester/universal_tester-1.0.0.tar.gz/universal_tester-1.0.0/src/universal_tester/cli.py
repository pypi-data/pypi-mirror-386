#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI entry point for Universal Tester package
This module provides the command-line interface when installed via pip
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

def main():
    """Main CLI entry point for the universal-tester command"""
    
    # Import here to avoid circular imports
    try:
        from universal_tester import (
            get_app_info,
            format_version_info,
            process_java_zip_enhanced_core,
        )
        from universal_tester.llm import (
            LLMFactory,
            print_llm_status,
            check_llm_health,
        )
    except ImportError as e:
        print(f"❌ Error importing universal_tester package: {e}")
        print("Make sure the package is properly installed: pip install universal-tester")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description='Universal Tester - AI-powered test generation for Java/Kotlin',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  universal-tester project.zip                    # Generate tests for project
  universal-tester project.zip -o ./my_tests      # Specify output directory
  universal-tester project.zip -v                 # Verbose output
  universal-tester --version                      # Show version
  universal-tester --health                       # Check LLM health
        """
    )
    
    parser.add_argument(
        'zip_file',
        nargs='?',
        help='Path to the Java/Kotlin project ZIP file'
    )
    
    parser.add_argument(
        '-o', '--output',
        dest='output_dir',
        help='Output directory for generated tests (default: ./enhanced_junit_tests_output)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--version',
        action='store_true',
        help='Show version information'
    )
    
    parser.add_argument(
        '--health',
        action='store_true',
        help='Check LLM health status'
    )
    
    parser.add_argument(
        '--info',
        action='store_true',
        help='Show application information'
    )
    
    args = parser.parse_args()
    
    # Handle version
    if args.version:
        print(format_version_info())
        sys.exit(0)
    
    # Handle info
    if args.info:
        app_info = get_app_info()
        print(f"\n{app_info['name']} v{app_info['version']}")
        print(f"{app_info['description']}\n")
        print(f"Author: {app_info['author']}")
        print(f"Support: {app_info['support_email']}\n")
        print("Supported Languages:")
        for lang in app_info['supported_languages']:
            print(f"  • {lang}")
        print("\nSupported Frameworks:")
        for framework in app_info['supported_frameworks']:
            print(f"  • {framework}")
        sys.exit(0)
    
    # Handle health check
    if args.health:
        print("🏥 Checking LLM Health...\n")
        print_llm_status()
        is_healthy = check_llm_health()
        sys.exit(0 if is_healthy else 1)
    
    # Require zip file for processing
    if not args.zip_file:
        parser.print_help()
        print("\n❌ Error: Please provide a ZIP file path or use --help for options")
        sys.exit(1)
    
    # Validate zip file
    if not os.path.exists(args.zip_file):
        print(f"❌ Error: ZIP file not found: {args.zip_file}")
        sys.exit(1)
    
    if not args.zip_file.lower().endswith('.zip'):
        print(f"❌ Error: File must be a ZIP file: {args.zip_file}")
        sys.exit(1)
    
    # Set logging level
    if args.verbose:
        os.environ['LOG_LEVEL'] = 'DEBUG'
    
    # Process the project
    print(f"🔄 Processing Java/Kotlin project: {os.path.basename(args.zip_file)}")
    print("=" * 60)
    
    async def run_processing():
        try:
            # Create LLM instance
            llm = LLMFactory.create_llm()
            
            # Process the ZIP file
            results = await process_java_zip_enhanced_core(
                zip_file_path=args.zip_file,
                llm=llm,
                output_dir=args.output_dir
            )
            
            print("\n" + "=" * 60)
            print("✅ Processing complete!")
            print("=" * 60)
            print(f"\n📊 Results:")
            print(f"  • Tests generated: {results.get('tests_generated', 0)}")
            print(f"  • Files processed: {results.get('files_processed', 0)}")
            print(f"  • Output: {results.get('output_zip', 'N/A')}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error during processing: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    # Run async processing
    success = asyncio.run(run_processing())
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
