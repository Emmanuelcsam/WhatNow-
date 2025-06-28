#!/usr/bin/env python3
"""
PDF Text Scanner - Enhanced Version
Scans PDF documents for specified text and extracts paragraphs containing that text.

Features:
- Interactive setup with user-friendly prompts
- Recursive subdirectory scanning at any depth
- Smart paragraph extraction with context
- Multiple output formats (TXT, CSV, JSON, Summary)
- Progress tracking with detailed logging
- Error recovery and robust file handling
- Support for regex and case-sensitive searches

Usage:
    python pdf_scanner.py

Requirements:
    pip install pdfplumber tqdm colorama
"""

import os
import re
import csv
import sys
import json
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import logging

# Try to import required libraries
try:
    import pdfplumber
    from tqdm import tqdm
    from colorama import init, Fore, Style
    init(autoreset=True)  # Initialize colorama
except ImportError as e:
    print("Required libraries not found. Please install them using:")
    print("pip install pdfplumber tqdm colorama")
    print(f"\nError details: {e}")
    sys.exit(1)


class PDFTextScanner:
    """Enhanced PDF text scanner with improved features and error handling."""
    
    def __init__(self, search_text: str, pdf_directory: str, output_directory: str = "results"):
        """Initialize the PDF scanner with configuration."""
        self.search_text = search_text
        self.pdf_directory = Path(pdf_directory).resolve()
        self.output_directory = Path(output_directory).resolve()
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        # Configuration flags
        self.include_subdirs = False
        self.case_sensitive = False
        self.use_regex = False
        
        # Results storage
        self.results = []
        self.failed_files = []
        self.processed_files = 0
        self.total_files = 0
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Configure comprehensive logging system."""
        log_filename = f"scan_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_file = self.output_directory / log_filename
        
        # Create a custom logger
        self.logger = logging.getLogger('PDFScanner')
        self.logger.setLevel(logging.DEBUG)
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler for important messages only
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"Logging initialized. Log file: {log_file}")
        
    def get_pdf_files(self, include_subdirs: bool = False) -> List[Path]:
        """
        Get all PDF files from the specified directory.
        
        Args:
            include_subdirs: Whether to recursively search subdirectories
            
        Returns:
            List of PDF file paths
        """
        try:
            if include_subdirs:
                # Recursive search
                pdf_files = list(self.pdf_directory.rglob("*.pdf"))
                pdf_files.extend(self.pdf_directory.rglob("*.PDF"))  # Case variations
                self.logger.info(f"Searching recursively in {self.pdf_directory}")
            else:
                # Non-recursive search
                pdf_files = list(self.pdf_directory.glob("*.pdf"))
                pdf_files.extend(self.pdf_directory.glob("*.PDF"))
                self.logger.info(f"Searching in {self.pdf_directory} (top-level only)")
            
            # Remove duplicates and sort
            pdf_files = sorted(list(set(pdf_files)))
            
            if pdf_files:
                # Log directory structure information
                dirs = set(f.parent for f in pdf_files)
                self.logger.info(f"Found {len(pdf_files)} PDF files in {len(dirs)} directories")
            else:
                self.logger.warning(f"No PDF files found in {self.pdf_directory}")
                
            return pdf_files
            
        except Exception as e:
            self.logger.error(f"Error scanning for PDF files: {e}")
            return []
            
    def extract_paragraph(self, text: str, position: int, 
                         context_chars: int = 300) -> Tuple[str, int, int]:
        """
        Extract a paragraph around the found text with improved logic.
        
        Args:
            text: Full page text
            position: Position of found text
            context_chars: Number of characters to include as context
            
        Returns:
            Tuple of (paragraph, start_pos, end_pos)
        """
        if not text:
            return "", 0, 0
            
        # Define paragraph boundaries
        paragraph_patterns = [
            r'\n\s*\n',           # Double newline
            r'\n(?=[A-Z])',       # Newline followed by capital letter
            r'\.\s+(?=[A-Z])',    # Period followed by capital letter
            r'[.!?]\s*\n',        # Sentence ending followed by newline
        ]
        
        # Find all potential paragraph breaks
        breaks = set([0, len(text)])
        for pattern in paragraph_patterns:
            for match in re.finditer(pattern, text):
                breaks.add(match.start())
                breaks.add(match.end())
        
        breaks = sorted(list(breaks))
        
        # Find the paragraph containing our position
        para_start = 0
        para_end = len(text)
        
        for i in range(len(breaks) - 1):
            if breaks[i] <= position < breaks[i + 1]:
                para_start = breaks[i]
                para_end = breaks[i + 1]
                
                # Expand to include more context if paragraph is too small
                while para_end - para_start < context_chars and (
                    para_start > 0 or para_end < len(text)
                ):
                    if para_start > 0:
                        # Find previous break
                        idx = breaks.index(para_start)
                        if idx > 0:
                            para_start = breaks[idx - 1]
                    if para_end < len(text) and para_end - para_start < context_chars:
                        # Find next break
                        idx = breaks.index(para_end)
                        if idx < len(breaks) - 1:
                            para_end = breaks[idx + 1]
                            
                break
                
        # Clean up the paragraph
        paragraph = text[para_start:para_end].strip()
        
        # Remove excessive whitespace
        paragraph = re.sub(r'\s+', ' ', paragraph)
        
        return paragraph, para_start, para_end
        
    def search_in_pdf(self, pdf_path: Path) -> List[Dict]:
        """
        Search for text in a single PDF file with improved error handling.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of results found in this PDF
        """
        file_results = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        # Extract text with fallback options
                        text = page.extract_text()
                        
                        if not text:
                            # Try alternative extraction methods
                            text = page.extract_text(layout=True)
                            
                        if not text:
                            self.logger.debug(f"No text found on page {page_num} of {pdf_path.name}")
                            continue
                            
                        # Prepare search pattern
                        if self.use_regex:
                            pattern = self.search_text
                        else:
                            pattern = re.escape(self.search_text)
                            
                        flags = 0 if self.case_sensitive else re.IGNORECASE
                        
                        # Find all occurrences
                        matches = list(re.finditer(pattern, text, flags))
                        
                        for match_num, match in enumerate(matches, 1):
                            position = match.start()
                            paragraph, para_start, para_end = self.extract_paragraph(
                                text, position
                            )
                            
                            # Calculate relative path for better organization
                            try:
                                relative_path = pdf_path.relative_to(self.pdf_directory)
                            except ValueError:
                                relative_path = pdf_path.name
                                
                            result = {
                                'filename': pdf_path.name,
                                'filepath': str(relative_path),
                                'full_path': str(pdf_path),
                                'page': page_num,
                                'total_pages': total_pages,
                                'search_term': self.search_text,
                                'found_text': match.group(),
                                'paragraph': paragraph,
                                'position': position,
                                'match_number': match_num,
                                'timestamp': datetime.now().isoformat()
                            }
                            
                            file_results.append(result)
                            
                    except Exception as e:
                        self.logger.error(f"Error processing page {page_num} of {pdf_path.name}: {e}")
                        continue
                        
        except Exception as e:
            self.logger.error(f"Error opening PDF {pdf_path}: {e}")
            self.failed_files.append({
                'file': str(pdf_path),
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            
        return file_results
        
    def scan_all_pdfs(self, case_sensitive: bool = False, 
                     use_regex: bool = False, 
                     include_subdirs: bool = False):
        """
        Scan all PDF files with improved progress tracking and error recovery.
        """
        self.case_sensitive = case_sensitive
        self.use_regex = use_regex
        self.include_subdirs = include_subdirs
        
        pdf_files = self.get_pdf_files(include_subdirs)
        self.total_files = len(pdf_files)
        
        if not pdf_files:
            print(f"{Fore.YELLOW}No PDF files found to scan.{Style.RESET_ALL}")
            return
            
        print(f"\n{Fore.GREEN}Found {self.total_files} PDF files to scan{Style.RESET_ALL}")
        print(f"Searching for: '{Fore.CYAN}{self.search_text}{Style.RESET_ALL}'")
        
        # Process each PDF with progress bar
        with tqdm(total=self.total_files, desc="Scanning PDFs", unit="file") as pbar:
            for pdf_file in pdf_files:
                pbar.set_description(f"Scanning: {pdf_file.name[:30]}...")
                
                results = self.search_in_pdf(pdf_file)
                self.results.extend(results)
                self.processed_files += 1
                
                if results:
                    tqdm.write(
                        f"{Fore.GREEN}✓ Found {len(results)} occurrences in "
                        f"{pdf_file.name}{Style.RESET_ALL}"
                    )
                    
                pbar.update(1)
                
        # Summary
        print(f"\n{Fore.CYAN}Scan Complete!{Style.RESET_ALL}")
        print(f"Files processed: {self.processed_files}/{self.total_files}")
        print(f"Total occurrences found: {len(self.results)}")
        if self.failed_files:
            print(f"{Fore.YELLOW}Failed to process {len(self.failed_files)} files{Style.RESET_ALL}")
            
    def save_txt_results(self) -> Path:
        """Save results to a formatted text file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        txt_file = self.output_directory / f"results_{timestamp}.txt"
        
        with open(txt_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("PDF TEXT SEARCH RESULTS\n")
            f.write("=" * 80 + "\n")
            f.write(f"Search Term: '{self.search_text}'\n")
            f.write(f"Search Type: {'Regex' if self.use_regex else 'Plain Text'}\n")
            f.write(f"Case Sensitive: {'Yes' if self.case_sensitive else 'No'}\n")
            f.write(f"Include Subdirectories: {'Yes' if self.include_subdirs else 'No'}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Files Scanned: {self.total_files}\n")
            f.write(f"Total Occurrences: {len(self.results)}\n")
            f.write("=" * 80 + "\n\n")
            
            # Group results by file
            file_groups = defaultdict(list)
            for result in self.results:
                file_groups[result['filepath']].append(result)
                
            # Write results
            for filepath, file_results in sorted(file_groups.items()):
                f.write(f"\nFILE: {filepath}\n")
                f.write(f"Occurrences in this file: {len(file_results)}\n")
                f.write("-" * 80 + "\n")
                
                for i, result in enumerate(file_results, 1):
                    f.write(f"\nOccurrence {i}:\n")
                    f.write(f"  Page: {result['page']} of {result['total_pages']}\n")
                    f.write(f"  Found: '{result['found_text']}'\n")
                    f.write(f"  Position: character {result['position']}\n")
                    f.write(f"\n  Context:\n")
                    
                    # Wrap paragraph text
                    paragraph_lines = self._wrap_text(result['paragraph'], 76)
                    for line in paragraph_lines:
                        f.write(f"    {line}\n")
                        
                f.write("\n" + "=" * 80 + "\n")
                
            # Add failed files section if any
            if self.failed_files:
                f.write("\n\nFAILED FILES\n")
                f.write("=" * 80 + "\n")
                for failed in self.failed_files:
                    f.write(f"\nFile: {failed['file']}\n")
                    f.write(f"Error: {failed['error']}\n")
                    
        self.logger.info(f"Text results saved to: {txt_file}")
        return txt_file
        
    def save_csv_results(self) -> Path:
        """Save results to CSV with improved formatting."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = self.output_directory / f"results_{timestamp}.csv"
        
        if not self.results:
            self.logger.warning("No results to save to CSV")
            return csv_file
            
        fieldnames = [
            'filename', 'filepath', 'page', 'total_pages', 
            'search_term', 'found_text', 'position', 
            'paragraph_preview', 'full_paragraph'
        ]
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.results:
                row = {
                    'filename': result['filename'],
                    'filepath': result['filepath'],
                    'page': result['page'],
                    'total_pages': result['total_pages'],
                    'search_term': result['search_term'],
                    'found_text': result['found_text'],
                    'position': result['position'],
                    'paragraph_preview': result['paragraph'][:200] + '...' 
                        if len(result['paragraph']) > 200 else result['paragraph'],
                    'full_paragraph': result['paragraph']
                }
                writer.writerow(row)
                
        self.logger.info(f"CSV results saved to: {csv_file}")
        return csv_file
        
    def save_json_results(self) -> Path:
        """Save results to JSON for programmatic access."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = self.output_directory / f"results_{timestamp}.json"
        
        data = {
            'metadata': {
                'search_term': self.search_text,
                'search_type': 'regex' if self.use_regex else 'plain_text',
                'case_sensitive': self.case_sensitive,
                'include_subdirs': self.include_subdirs,
                'scan_date': datetime.now().isoformat(),
                'total_files': self.total_files,
                'processed_files': self.processed_files,
                'total_occurrences': len(self.results)
            },
            'results': self.results,
            'failed_files': self.failed_files
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        self.logger.info(f"JSON results saved to: {json_file}")
        return json_file
        
    def generate_summary(self) -> Path:
        """Generate an enhanced summary report."""
        summary_file = self.output_directory / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # Analyze results
        file_groups = defaultdict(list)
        page_distribution = defaultdict(int)
        
        for result in self.results:
            file_groups[result['filepath']].append(result)
            page_distribution[result['page']] += 1
            
        with open(summary_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("SEARCH SUMMARY REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Search Term: '{self.search_text}'\n")
            f.write("\n")
            
            # Statistics
            f.write("STATISTICS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total PDF files scanned: {self.total_files}\n")
            f.write(f"Files successfully processed: {self.processed_files}\n")
            f.write(f"Files with matches: {len(file_groups)}\n")
            f.write(f"Total occurrences found: {len(self.results)}\n")
            if self.results:
                avg_per_file = len(self.results) / len(file_groups)
                f.write(f"Average occurrences per file: {avg_per_file:.1f}\n")
            f.write("\n")
            
            # Files with most occurrences
            if file_groups:
                f.write("TOP FILES BY OCCURRENCES\n")
                f.write("-" * 40 + "\n")
                sorted_files = sorted(
                    file_groups.items(), 
                    key=lambda x: len(x[1]), 
                    reverse=True
                )[:10]
                
                for filepath, occurrences in sorted_files:
                    f.write(f"{filepath}: {len(occurrences)} occurrences\n")
                f.write("\n")
                
            # Directory breakdown if using subdirectories
            if self.include_subdirs and file_groups:
                f.write("DIRECTORY BREAKDOWN\n")
                f.write("-" * 40 + "\n")
                
                dir_stats = defaultdict(lambda: {'files': 0, 'occurrences': 0})
                for filepath, occurrences in file_groups.items():
                    dir_path = str(Path(filepath).parent)
                    if dir_path == '.':
                        dir_path = '[Main Directory]'
                    dir_stats[dir_path]['files'] += 1
                    dir_stats[dir_path]['occurrences'] += len(occurrences)
                    
                for dir_path, stats in sorted(dir_stats.items()):
                    f.write(f"{dir_path}:\n")
                    f.write(f"  Files with matches: {stats['files']}\n")
                    f.write(f"  Total occurrences: {stats['occurrences']}\n")
                f.write("\n")
                
            # Failed files
            if self.failed_files:
                f.write("FAILED FILES\n")
                f.write("-" * 40 + "\n")
                for failed in self.failed_files:
                    f.write(f"{failed['file']}: {failed['error']}\n")
                    
        self.logger.info(f"Summary saved to: {summary_file}")
        return summary_file
        
    def _wrap_text(self, text: str, width: int) -> List[str]:
        """Wrap text to specified width."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + len(current_line) <= width:
                current_line.append(word)
                current_length += len(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
                
        if current_line:
            lines.append(' '.join(current_line))
            
        return lines


class InteractiveSetup:
    """Handle interactive setup with improved user experience."""
    
    @staticmethod
    def get_user_input(prompt: str, default: str = None, 
                      valid_options: List[str] = None, 
                      allow_empty: bool = False) -> str:
        """
        Get user input with validation and default handling.
        """
        if default:
            prompt += f" [{Fore.GREEN}{default}{Style.RESET_ALL}]"
        prompt += ": "
        
        while True:
            try:
                user_input = input(prompt).strip()
                
                # Remove quotes if present
                if user_input and len(user_input) >= 2:
                    if (user_input[0] == user_input[-1]) and user_input[0] in ['"', "'"]:
                        user_input = user_input[1:-1]
                        
                # Use default if empty
                if not user_input and default:
                    return default
                    
                # Validate against options
                if valid_options:
                    if user_input.lower() in [opt.lower() for opt in valid_options]:
                        return user_input.lower()
                    else:
                        print(f"{Fore.RED}Please choose one of: {', '.join(valid_options)}{Style.RESET_ALL}")
                        continue
                        
                # Check if empty input is allowed
                if user_input or allow_empty:
                    return user_input
                else:
                    print(f"{Fore.RED}This field is required.{Style.RESET_ALL}")
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Setup cancelled by user.{Style.RESET_ALL}")
                sys.exit(0)
                
    @staticmethod
    def validate_directory(path_str: str) -> Tuple[bool, Path, str]:
        """
        Validate directory path and provide helpful feedback.
        
        Returns:
            Tuple of (is_valid, resolved_path, message)
        """
        # Expand user home directory
        path_str = os.path.expanduser(path_str)
        
        # Handle Windows paths
        path_str = path_str.replace('\\', '/')
        
        try:
            path = Path(path_str).resolve()
            
            if not path.exists():
                return False, path, f"Directory does not exist: {path}"
                
            if not path.is_dir():
                return False, path, f"Path is not a directory: {path}"
                
            # Check for PDF files
            pdf_files = list(path.glob("*.pdf")) + list(path.glob("*.PDF"))
            pdf_files_recursive = list(path.rglob("*.pdf")) + list(path.rglob("*.PDF"))
            
            if not pdf_files_recursive:
                return False, path, "No PDF files found in directory or subdirectories"
                
            message = f"Found {len(pdf_files)} PDFs in main directory"
            if len(pdf_files_recursive) > len(pdf_files):
                message += f", {len(pdf_files_recursive) - len(pdf_files)} in subdirectories"
                
            return True, path, message
            
        except Exception as e:
            return False, None, f"Error processing path: {e}"
            
    @staticmethod
    def display_banner():
        """Display welcome banner."""
        print(f"\n{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}PDF TEXT SCANNER - Enhanced Version{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        print("\nThis tool searches through PDF files for specified text")
        print("and extracts the paragraphs where that text appears.\n")
        
    @staticmethod
    def run_setup() -> Dict:
        """Run the complete interactive setup process."""
        InteractiveSetup.display_banner()
        
        # Get search text
        print(f"{Fore.YELLOW}STEP 1: Search Configuration{Style.RESET_ALL}")
        search_text = InteractiveSetup.get_user_input(
            "Enter the text to search for"
        )
        
        # Get PDF directory
        print(f"\n{Fore.YELLOW}STEP 2: Select PDF Directory{Style.RESET_ALL}")
        print("Enter the full path to your PDF directory.")
        print("Examples:")
        print("  • /home/user/Documents/PDFs")
        print("  • C:\\Users\\Name\\Documents")
        print("  • ./pdfs")
        print("  • ~/Downloads/Articles\n")
        
        while True:
            pdf_dir = InteractiveSetup.get_user_input(
                "Enter PDF directory path", "."
            )
            
            is_valid, path, message = InteractiveSetup.validate_directory(pdf_dir)
            
            if is_valid:
                print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
                pdf_dir = str(path)
                break
            else:
                print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")
                
                # Offer to create directory if it doesn't exist
                if path and not path.exists():
                    create = InteractiveSetup.get_user_input(
                        "Create this directory?", "n", ["y", "n"]
                    )
                    if create == "y":
                        try:
                            path.mkdir(parents=True, exist_ok=True)
                            print(f"{Fore.GREEN}✓ Directory created{Style.RESET_ALL}")
                            continue
                        except Exception as e:
                            print(f"{Fore.RED}Failed to create directory: {e}{Style.RESET_ALL}")
                            
                retry = InteractiveSetup.get_user_input(
                    "Try another directory?", "y", ["y", "n"]
                )
                if retry == "n":
                    print("Setup cancelled.")
                    sys.exit(0)
                    
        # Get output directory
        print(f"\n{Fore.YELLOW}STEP 3: Output Configuration{Style.RESET_ALL}")
        output_dir = InteractiveSetup.get_user_input(
            "Enter output directory for results", "results"
        )
        
        # Search options
        print(f"\n{Fore.YELLOW}STEP 4: Search Options{Style.RESET_ALL}")
        case_sensitive = InteractiveSetup.get_user_input(
            "Case-sensitive search?", "n", ["y", "n"]
        ) == "y"
        
        use_regex = InteractiveSetup.get_user_input(
            "Use regex pattern matching?", "n", ["y", "n"]
        ) == "y"
        
        # Check for subdirectories
        path = Path(pdf_dir)
        pdf_files_main = list(path.glob("*.pdf")) + list(path.glob("*.PDF"))
        pdf_files_all = list(path.rglob("*.pdf")) + list(path.rglob("*.PDF"))
        
        include_subdirs = False
        if len(pdf_files_all) > len(pdf_files_main):
            subdirs_count = len(set(f.parent for f in pdf_files_all)) - 1
            print(f"\n{Fore.CYAN}📁 Subdirectory Detection{Style.RESET_ALL}")
            print(f"Main directory: {len(pdf_files_main)} PDFs")
            print(f"Subdirectories: {len(pdf_files_all) - len(pdf_files_main)} PDFs in {subdirs_count} folders")
            print(f"Total available: {len(pdf_files_all)} PDFs")
            
            include_subdirs = InteractiveSetup.get_user_input(
                "Include all subdirectories?", "y", ["y", "n"]
            ) == "y"
            
        # Output format options
        print(f"\n{Fore.YELLOW}STEP 5: Output Formats{Style.RESET_ALL}")
        print("Select which output formats to generate:")
        
        generate_txt = InteractiveSetup.get_user_input(
            "Generate detailed TXT report?", "y", ["y", "n"]
        ) == "y"
        
        generate_csv = InteractiveSetup.get_user_input(
            "Generate CSV for data analysis?", "y", ["y", "n"]
        ) == "y"
        
        generate_json = InteractiveSetup.get_user_input(
            "Generate JSON for programmatic access?", "n", ["y", "n"]
        ) == "y"
        
        generate_summary = InteractiveSetup.get_user_input(
            "Generate summary report?", "y", ["y", "n"]
        ) == "y"
        
        # Ensure at least one output format
        if not any([generate_txt, generate_csv, generate_json, generate_summary]):
            print(f"{Fore.YELLOW}No output formats selected. Defaulting to TXT.{Style.RESET_ALL}")
            generate_txt = True
            
        return {
            'search_text': search_text,
            'pdf_directory': pdf_dir,
            'output_directory': output_dir,
            'case_sensitive': case_sensitive,
            'use_regex': use_regex,
            'include_subdirs': include_subdirs,
            'generate_txt': generate_txt,
            'generate_csv': generate_csv,
            'generate_json': generate_json,
            'generate_summary': generate_summary
        }


def display_results_preview(scanner: PDFTextScanner):
    """Display a preview of results after scanning."""
    if not scanner.results:
        return
        
    print(f"\n{Fore.CYAN}RESULTS PREVIEW{Style.RESET_ALL}")
    print("=" * 70)
    
    # Group by file
    file_groups = defaultdict(list)
    for result in scanner.results:
        file_groups[result['filepath']].append(result)
        
    # Show up to 5 files
    for i, (filepath, occurrences) in enumerate(sorted(file_groups.items())[:5]):
        print(f"\n{Fore.GREEN}{filepath}{Style.RESET_ALL}")
        print(f"  Occurrences: {len(occurrences)}")
        print(f"  Pages: {', '.join(str(r['page']) for r in occurrences[:10])}")
        if len(occurrences) > 10:
            print(f"  ... and {len(occurrences) - 10} more")
            
    if len(file_groups) > 5:
        print(f"\n... and {len(file_groups) - 5} more files")
        

def main():
    """Main entry point with enhanced error handling."""
    try:
        # Get configuration
        config = InteractiveSetup.run_setup()
        
        # Display configuration summary
        print(f"\n{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}CONFIGURATION SUMMARY{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
        print(f"Search Text: '{config['search_text']}'")
        print(f"PDF Directory: {config['pdf_directory']}")
        print(f"Include Subdirectories: {'Yes (recursive)' if config['include_subdirs'] else 'No'}")
        print(f"Case Sensitive: {'Yes' if config['case_sensitive'] else 'No'}")
        print(f"Regex Mode: {'Yes' if config['use_regex'] else 'No'}")
        
        formats = []
        if config['generate_txt']: formats.append("TXT")
        if config['generate_csv']: formats.append("CSV")
        if config['generate_json']: formats.append("JSON")
        if config['generate_summary']: formats.append("Summary")
        print(f"Output Formats: {', '.join(formats)}")
        print(f"Output Directory: {config['output_directory']}")
        
        # Confirm
        proceed = InteractiveSetup.get_user_input(
            f"\n{Fore.YELLOW}Proceed with scan?{Style.RESET_ALL}", "y", ["y", "n"]
        )
        
        if proceed == "n":
            print("Scan cancelled.")
            return
            
        # Create scanner
        scanner = PDFTextScanner(
            config['search_text'],
            config['pdf_directory'],
            config['output_directory']
        )
        
        # Perform scan
        print(f"\n{Fore.CYAN}Starting scan...{Style.RESET_ALL}\n")
        start_time = time.time()
        
        scanner.scan_all_pdfs(
            case_sensitive=config['case_sensitive'],
            use_regex=config['use_regex'],
            include_subdirs=config['include_subdirs']
        )
        
        elapsed_time = time.time() - start_time
        
        # Save results
        if scanner.results:
            print(f"\n{Fore.CYAN}Saving results...{Style.RESET_ALL}")
            
            saved_files = []
            if config['generate_txt']:
                saved_files.append(scanner.save_txt_results())
            if config['generate_csv']:
                saved_files.append(scanner.save_csv_results())
            if config['generate_json']:
                saved_files.append(scanner.save_json_results())
            if config['generate_summary']:
                saved_files.append(scanner.generate_summary())
                
            # Display results preview
            display_results_preview(scanner)
            
            # Final summary
            print(f"\n{Fore.GREEN}{'=' * 70}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}SCAN COMPLETE!{Style.RESET_ALL}")
            print(f"{Fore.GREEN}{'=' * 70}{Style.RESET_ALL}")
            print(f"Time elapsed: {elapsed_time:.1f} seconds")
            print(f"Files processed: {scanner.processed_files}")
            print(f"Total occurrences: {len(scanner.results)}")
            print(f"\nResults saved to: {scanner.output_directory}")
            for file in saved_files:
                print(f"  • {file.name}")
                
        else:
            print(f"\n{Fore.YELLOW}No occurrences found.{Style.RESET_ALL}")
            
        if scanner.failed_files:
            print(f"\n{Fore.YELLOW}Warning: {len(scanner.failed_files)} files could not be processed.{Style.RESET_ALL}")
            print("Check the log file for details.")
            
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Scan interrupted by user.{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}An error occurred: {e}{Style.RESET_ALL}")
        print(f"Full error details:\n{traceback.format_exc()}")
        sys.exit(1)
    finally:
        print(f"\n{Fore.CYAN}Press Enter to exit...{Style.RESET_ALL}")
        input()


if __name__ == "__main__":
    main()