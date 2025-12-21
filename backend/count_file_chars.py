#!/usr/bin/env python3
"""
Simple script to count characters and words in files before upload.
Usage: python count_file_chars.py <file_path> [<file_path2> ...]
"""

import sys
import os
from pathlib import Path


def count_file_stats(file_path):
    """Count characters, words, and lines in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        char_count = len(content)
        word_count = len(content.split())
        line_count = len(content.splitlines())
        
        return {
            'path': file_path,
            'chars': char_count,
            'words': word_count,
            'lines': line_count,
            'size_mb': os.path.getsize(file_path) / (1024 * 1024),
            'error': None
        }
    except Exception as e:
        return {
            'path': file_path,
            'chars': 0,
            'words': 0,
            'lines': 0,
            'size_mb': 0,
            'error': str(e)
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: python count_file_chars.py <file_path> [<file_path2> ...]")
        print("\nExample: python count_file_chars.py document.pdf report.txt")
        sys.exit(1)
    
    total_chars = 0
    total_words = 0
    total_files = 0
    
    print("\n" + "="*80)
    print(f"{'File Name':<40} {'Chars':>10} {'Words':>10} {'Size (MB)':>12}")
    print("="*80)
    
    for file_arg in sys.argv[1:]:
        file_path = Path(file_arg)
        
        if file_path.is_dir():
            # Process all files in directory
            for f in file_path.rglob('*'):
                if f.is_file():
                    stats = count_file_stats(str(f))
                    if not stats['error']:
                        display_name = f.name[:40]
                        print(f"{display_name:<40} {stats['chars']:>10,} {stats['words']:>10,} {stats['size_mb']:>12.2f}")
                        total_chars += stats['chars']
                        total_words += stats['words']
                        total_files += 1
                    else:
                        print(f"{f.name:<40} ERROR: {stats['error']}")
        else:
            # Process single file
            stats = count_file_stats(file_arg)
            if not stats['error']:
                display_name = Path(file_arg).name[:40]
                print(f"{display_name:<40} {stats['chars']:>10,} {stats['words']:>10,} {stats['size_mb']:>12.2f}")
                total_chars += stats['chars']
                total_words += stats['words']
                total_files += 1
            else:
                print(f"{file_arg:<40} ERROR: {stats['error']}")
    
    print("="*80)
    print(f"{'TOTAL':<40} {total_chars:>10,} {total_words:>10,}")
    print(f"Files processed: {total_files}")
    print(f"Avg chars per file: {total_chars // total_files if total_files > 0 else 0:,}")
    print(f"Avg words per file: {total_words // total_files if total_files > 0 else 0:,}")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
