#!/usr/bin/env python3
"""
Advanced OSINT Scraper
Integrates Maigret, Recon-ng, and SpiderFoot for comprehensive intelligence gathering
"""

import os
import sys
import json
import subprocess
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse

# Third-party imports
import requests
from colorama import init, Fore, Style

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Local imports (with fallback handling)
try:
    from osint_utilities import OSINTUtilities
except ImportError:
    print("Warning: osint_utilities module not found. Some features may be limited.")
    OSINTUtilities = None

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Load environment variables with fallback
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables will be loaded from system only.")
    load_dotenv = lambda: None

class OSINTConfig:
    """Configuration management for OSINT tools"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.tools_dir = self.base_dir / "tools"
        self.output_dir = self.base_dir / "output"
        self.logs_dir = self.base_dir / "logs"
        
        # Create directories
        for directory in [self.tools_dir, self.output_dir, self.logs_dir]:
            directory.mkdir(exist_ok=True)
            
        # Tool paths
        self.maigret_path = self.tools_dir / "maigret"
        self.recon_ng_path = self.tools_dir / "recon-ng"
        self.spiderfoot_path = self.tools_dir / "spiderfoot"
        
        # API Keys (only free APIs)
        self.api_keys = {
            # All APIs below are free to use
            'openstreetmap': True,  # Free geocoding service
            'overpass': True,       # Free OpenStreetMap data
            # Note: Paid APIs have been removed to keep this tool completely free
        }

class OSINTLogger:
    """Custom logger for OSINT operations"""
    
    def __init__(self, log_dir: Path):
        self.log_file = log_dir / f"osint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def info(self, message: str):
        self.logger.info(f"{Fore.GREEN}[INFO]{Style.RESET_ALL} {message}")
    
    def warning(self, message: str):
        self.logger.warning(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} {message}")
    
    def error(self, message: str):
        self.logger.error(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {message}")
    
    def success(self, message: str):
        self.logger.info(f"{Fore.CYAN}[SUCCESS]{Style.RESET_ALL} {message}")

class ToolManager:
    """Manages installation and execution of OSINT tools"""
    
    def __init__(self, config: OSINTConfig, logger: OSINTLogger):
        self.config = config
        self.logger = logger
    
    def check_tool_installation(self, tool_name: str) -> bool:
        """Check if a tool is installed"""
        tool_paths = {
            'maigret': self.config.maigret_path,
            'recon-ng': self.config.recon_ng_path,
            'spiderfoot': self.config.spiderfoot_path
        }
        
        if tool_name in tool_paths:
            return tool_paths[tool_name].exists()
        
        # Check if tool is available in PATH
        try:
            subprocess.run([tool_name, '--help'], 
                         capture_output=True, check=True, timeout=10)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def install_maigret(self) -> bool:
        """Install Maigret"""
        try:
            self.logger.info("Installing Maigret...")
            
            # Clone Maigret repository
            cmd = ["git", "clone", "https://github.com/soxoj/maigret.git", str(self.config.maigret_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                self.logger.error(f"Failed to clone Maigret: {result.stderr}")
                return False
            
            # Install dependencies
            pip_cmd = [sys.executable, "-m", "pip", "install", "-r", 
                      str(self.config.maigret_path / "requirements.txt")]
            result = subprocess.run(pip_cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                self.logger.error(f"Failed to install Maigret dependencies: {result.stderr}")
                return False
            
            self.logger.success("Maigret installed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error installing Maigret: {str(e)}")
            return False
    
    def install_recon_ng(self) -> bool:
        """Install Recon-ng"""
        try:
            self.logger.info("Installing Recon-ng...")
            
            # Clone Recon-ng repository
            cmd = ["git", "clone", "https://github.com/lanmaster53/recon-ng.git", str(self.config.recon_ng_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                self.logger.error(f"Failed to clone Recon-ng: {result.stderr}")
                return False
            
            # Install dependencies
            pip_cmd = [sys.executable, "-m", "pip", "install", "-r", 
                      str(self.config.recon_ng_path / "REQUIREMENTS")]
            result = subprocess.run(pip_cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                self.logger.error(f"Failed to install Recon-ng dependencies: {result.stderr}")
                return False
            
            self.logger.success("Recon-ng installed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error installing Recon-ng: {str(e)}")
            return False
    
    def install_spiderfoot(self) -> bool:
        """Install SpiderFoot"""
        try:
            self.logger.info("Installing SpiderFoot...")
            
            # Clone SpiderFoot repository
            cmd = ["git", "clone", "https://github.com/smicallef/spiderfoot.git", str(self.config.spiderfoot_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                self.logger.error(f"Failed to clone SpiderFoot: {result.stderr}")
                return False
            
            # Install dependencies
            pip_cmd = [sys.executable, "-m", "pip", "install", "-r", 
                      str(self.config.spiderfoot_path / "requirements.txt")]
            result = subprocess.run(pip_cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                self.logger.error(f"Failed to install SpiderFoot dependencies: {result.stderr}")
                return False
            
            self.logger.success("SpiderFoot installed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error installing SpiderFoot: {str(e)}")
            return False
    
    def setup_tools(self) -> Dict[str, bool]:
        """Setup all OSINT tools"""
        tools_status = {}
        
        # Check and install Maigret
        if not self.check_tool_installation('maigret'):
            tools_status['maigret'] = self.install_maigret()
        else:
            tools_status['maigret'] = True
            self.logger.info("Maigret already installed")
        
        # Check and install Recon-ng
        if not self.check_tool_installation('recon-ng'):
            tools_status['recon-ng'] = self.install_recon_ng()
        else:
            tools_status['recon-ng'] = True
            self.logger.info("Recon-ng already installed")
        
        # Check and install SpiderFoot
        if not self.check_tool_installation('spiderfoot'):
            tools_status['spiderfoot'] = self.install_spiderfoot()
        else:
            tools_status['spiderfoot'] = True
            self.logger.info("SpiderFoot already installed")
        
        return tools_status

class MaigretIntegration:
    """Integration with Maigret for username enumeration"""
    
    def __init__(self, config: OSINTConfig, logger: OSINTLogger):
        self.config = config
        self.logger = logger
        self.maigret_script = self.config.maigret_path / "maigret.py"
    
    def search_username(self, username: str, output_dir: Path) -> Dict:
        """Search for username across social media platforms"""
        try:
            self.logger.info(f"Running Maigret search for username: {username}")
            
            output_file = output_dir / f"maigret_{username}_{int(time.time())}"
            
            cmd = [
                sys.executable, str(self.maigret_script),
                username,
                "--folderoutput", str(output_file),
                "--json", str(output_file / f"{username}.json"),
                "--timeout", "30"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                self.logger.success(f"Maigret search completed for {username}")
                
                # Parse JSON output
                json_file = output_file / f"{username}.json"
                if json_file.exists():
                    with open(json_file, 'r') as f:
                        return json.load(f)
            else:
                self.logger.error(f"Maigret search failed: {result.stderr}")
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error running Maigret: {str(e)}")
            return {}

class ReconNGIntegration:
    """Integration with Recon-ng for reconnaissance"""
    
    def __init__(self, config: OSINTConfig, logger: OSINTLogger):
        self.config = config
        self.logger = logger
        # Updated to use the correct Recon-ng entry point
        self.recon_script = self.config.recon_ng_path / "recon-ng"
        # Fallback for Windows
        if not self.recon_script.exists():
            self.recon_script = self.config.recon_ng_path / "recon-ng.py"
    
    def create_workspace(self, workspace_name: str) -> bool:
        """Create a new Recon-ng workspace"""
        try:
            cmd = [
                sys.executable, str(self.recon_script),
                "-w", workspace_name,
                "-x", "exit"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Error creating Recon-ng workspace: {str(e)}")
            return False
    
    def run_domain_recon(self, domain: str, workspace_name: str) -> Dict:
        """Run domain reconnaissance using Recon-ng"""
        try:
            self.logger.info(f"Running Recon-ng domain reconnaissance for: {domain}")
            
            # Create workspace
            if not self.create_workspace(workspace_name):
                self.logger.error("Failed to create Recon-ng workspace")
                return {}
            
            # Run reconnaissance modules
            commands = [
                f"use recon/domains-hosts/hackertarget",
                f"set SOURCE {domain}",
                "run",
                f"use recon/hosts-hosts/resolve",
                "run",
                "show hosts"
            ]
            
            cmd_file = self.config.output_dir / f"recon_commands_{int(time.time())}.txt"
            with open(cmd_file, 'w') as f:
                f.write('\n'.join(commands))
            
            cmd = [
                sys.executable, str(self.recon_script),
                "-w", workspace_name,
                "-r", str(cmd_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.success(f"Recon-ng domain reconnaissance completed for {domain}")
                return {"output": result.stdout, "error": result.stderr}
            else:
                self.logger.error(f"Recon-ng failed: {result.stderr}")
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error running Recon-ng: {str(e)}")
            return {}

class SpiderFootIntegration:
    """Integration with SpiderFoot for automated OSINT scanning"""
    
    def __init__(self, config: OSINTConfig, logger: OSINTLogger):
        self.config = config
        self.logger = logger
        self.spiderfoot_script = self.config.spiderfoot_path / "sf.py"
    
    def run_scan(self, target: str, scan_type: str = "all") -> Dict:
        """Run SpiderFoot scan"""
        try:
            self.logger.info(f"Running SpiderFoot scan for: {target}")
            
            output_file = self.config.output_dir / f"spiderfoot_{target.replace('.', '_')}_{int(time.time())}.json"
            
            cmd = [
                sys.executable, str(self.spiderfoot_script),
                "-s", target,
                "-t", scan_type,
                "-j",
                "-o", str(output_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)  # 30 minutes timeout
            
            if result.returncode == 0:
                self.logger.success(f"SpiderFoot scan completed for {target}")
                
                if output_file.exists():
                    with open(output_file, 'r') as f:
                        return json.load(f)
            else:
                self.logger.error(f"SpiderFoot scan failed: {result.stderr}")
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error running SpiderFoot: {str(e)}")
            return {}

class OSINTTarget:
    """Represents an OSINT investigation target"""
    
    def __init__(self, full_name: str = "", email: str = "", 
                 social_handles: List[str] = None, address: str = "", 
                 coordinates: Tuple[float, float] = None):
        self.full_name = full_name
        self.email = email
        self.social_handles = social_handles or []
        self.address = address
        self.coordinates = coordinates  # (latitude, longitude)
        
        # Derived information
        self.domain = email.split('@')[1] if email and '@' in email else ""
        self.username_variants = self._generate_username_variants()
    
    def _generate_username_variants(self) -> List[str]:
        """Generate possible username variants from full name"""
        if not self.full_name:
            return []
        
        name_parts = self.full_name.lower().split()
        if len(name_parts) < 2:
            return [self.full_name.lower()]
        
        variants = []
        first, last = name_parts[0], name_parts[-1]
        
        # Common username patterns
        variants.extend([
            first + last,
            first + '.' + last,
            first + '_' + last,
            first + last[0],
            first[0] + last,
            last + first,
            last + '.' + first,
            last + '_' + first
        ])
        
        # Add social media handles
        variants.extend(self.social_handles)
        
        return list(set(variants))  # Remove duplicates

class OSINTScraper:
    """Main OSINT scraper class"""
    
    def __init__(self):
        self.config = OSINTConfig()
        self.logger = OSINTLogger(self.config.logs_dir)
        self.tool_manager = ToolManager(self.config, self.logger)
        
        # Initialize tool integrations
        self.maigret = MaigretIntegration(self.config, self.logger)
        self.recon_ng = ReconNGIntegration(self.config, self.logger)
        self.spiderfoot = SpiderFootIntegration(self.config, self.logger)
        
        # Initialize utilities with API keys (with fallback)
        if OSINTUtilities:
            self.utilities = OSINTUtilities(self.config.api_keys)
        else:
            self.utilities = None
            self.logger.warning("OSINTUtilities not available. Some features will be limited.")
    
    def setup(self) -> bool:
        """Setup the OSINT environment"""
        self.logger.info("Setting up OSINT environment...")
        
        # Setup tools
        tools_status = self.tool_manager.setup_tools()
        
        # Check if all tools are ready
        all_ready = all(tools_status.values())
        
        if all_ready:
            self.logger.success("All OSINT tools are ready!")
        else:
            failed_tools = [tool for tool, status in tools_status.items() if not status]
            self.logger.warning(f"Some tools failed to install: {', '.join(failed_tools)}")
        
        return all_ready
    
    def investigate_target(self, target: OSINTTarget) -> Dict:
        """Perform comprehensive OSINT investigation on target"""
        self.logger.info(f"Starting OSINT investigation for: {target.full_name}")
        
        investigation_results = {
            'target_info': {
                'full_name': target.full_name,
                'email': target.email,
                'social_handles': target.social_handles,
                'address': target.address,
                'coordinates': target.coordinates
            },
            'maigret_results': {},
            'recon_ng_results': {},
            'spiderfoot_results': {},
            'additional_intel': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Create target-specific output directory
        target_output_dir = self.config.output_dir / f"investigation_{target.full_name.replace(' ', '_')}_{int(time.time())}"
        target_output_dir.mkdir(exist_ok=True)
        
        # Run Maigret for username enumeration
        if target.username_variants:
            self.logger.info("Running username enumeration with Maigret...")
            for username in target.username_variants:
                maigret_result = self.maigret.search_username(username, target_output_dir)
                if maigret_result:
                    investigation_results['maigret_results'][username] = maigret_result
        
        # Run Recon-ng for domain reconnaissance
        if target.domain:
            self.logger.info("Running domain reconnaissance with Recon-ng...")
            workspace_name = f"investigation_{int(time.time())}"
            recon_result = self.recon_ng.run_domain_recon(target.domain, workspace_name)
            if recon_result:
                investigation_results['recon_ng_results'] = recon_result
        
        # Run SpiderFoot for comprehensive scanning
        scan_targets = []
        if target.email:
            scan_targets.append(target.email)
        if target.domain:
            scan_targets.append(target.domain)
        
        for scan_target in scan_targets:
            self.logger.info(f"Running comprehensive scan with SpiderFoot for: {scan_target}")
            spiderfoot_result = self.spiderfoot.run_scan(scan_target)
            if spiderfoot_result:
                investigation_results['spiderfoot_results'][scan_target] = spiderfoot_result
        
        # Additional intelligence gathering using FREE utilities
        additional_intel = {}
        
        if self.utilities:
            # Domain analysis
            if target.domain:
                self.logger.info(f"Performing comprehensive domain analysis for: {target.domain}")
                try:
                    additional_intel['domain_analysis'] = self.utilities.comprehensive_domain_analysis(target.domain)
                except Exception as e:
                    self.logger.error(f"Domain analysis failed: {str(e)}")
            
            # Email investigation
            if target.email:
                self.logger.info(f"Investigating email: {target.email}")
                try:
                    additional_intel['email_investigation'] = self.utilities.email_investigation(target.email)
                except Exception as e:
                    self.logger.error(f"Email investigation failed: {str(e)}")
            
            # Social media search for usernames
            if target.username_variants:
                self.logger.info("Performing social media search...")
                try:
                    additional_intel['social_media_search'] = {}
                    for username in target.username_variants[:3]:  # Limit to first 3 to avoid rate limiting
                        additional_intel['social_media_search'][username] = self.utilities.social_media_search(username)
                except Exception as e:
                    self.logger.error(f"Social media search failed: {str(e)}")
            
            # Location analysis
            if target.coordinates:
                self.logger.info(f"Analyzing location: {target.coordinates}")
                try:
                    lat, lon = target.coordinates
                    # Pass investigation results for interest-based filtering
                    additional_intel['location_analysis'] = self.utilities.location_analysis(lat, lon, investigation_results)
                except Exception as e:
                    self.logger.error(f"Location analysis failed: {str(e)}")
        else:
            self.logger.warning("Additional intelligence features not available. Install missing dependencies.")
        
        investigation_results['additional_intel'] = additional_intel
        
        # Save investigation results
        results_file = target_output_dir / "investigation_results.json"
        try:
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(investigation_results, f, indent=2, default=str, ensure_ascii=False)
            self.logger.success(f"Investigation completed. Results saved to: {results_file}")
        except Exception as e:
            self.logger.error(f"Failed to save results: {str(e)}")
        
        return investigation_results
    
    def generate_report(self, investigation_results: Dict) -> str:
        """Generate a human-readable report"""
        report = []
        report.append("="*80)
        report.append("OSINT INVESTIGATION REPORT")
        report.append("="*80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Target Information
        target_info = investigation_results.get('target_info', {})
        report.append("TARGET INFORMATION:")
        report.append("-" * 40)
        report.append(f"Full Name: {target_info.get('full_name', 'N/A')}")
        report.append(f"Email: {target_info.get('email', 'N/A')}")
        report.append(f"Social Handles: {', '.join(target_info.get('social_handles', []))}")
        report.append(f"Address: {target_info.get('address', 'N/A')}")
        report.append(f"Coordinates: {target_info.get('coordinates', 'N/A')}")
        report.append("")
        
        # Maigret Results
        maigret_results = investigation_results.get('maigret_results', {})
        if maigret_results:
            report.append("MAIGRET RESULTS (Username Enumeration):")
            report.append("-" * 40)
            for username, results in maigret_results.items():
                report.append(f"Username: {username}")
                if isinstance(results, dict):
                    found_profiles = 0
                    for platform, data in results.items():
                        if isinstance(data, dict) and data.get('status') == 'found':
                            report.append(f"  - {platform}: {data.get('url', 'Found')}")
                            found_profiles += 1
                    report.append(f"  Total profiles found: {found_profiles}")
                report.append("")
        
        # Recon-ng Results
        recon_results = investigation_results.get('recon_ng_results', {})
        if recon_results:
            report.append("RECON-NG RESULTS (Domain Reconnaissance):")
            report.append("-" * 40)
            report.append(recon_results.get('output', 'No output available'))
            report.append("")
        
        # SpiderFoot Results
        spiderfoot_results = investigation_results.get('spiderfoot_results', {})
        if spiderfoot_results:
            report.append("SPIDERFOOT RESULTS (Comprehensive Scan):")
            report.append("-" * 40)
            for target, results in spiderfoot_results.items():
                report.append(f"Target: {target}")
                # Summarize SpiderFoot results
                if isinstance(results, list):
                    report.append(f"Total findings: {len(results)}")
                    # Group by data type
                    data_types = {}
                    for item in results:
                        if isinstance(item, dict):
                            data_type = item.get('type', 'Unknown')
                            data_types[data_type] = data_types.get(data_type, 0) + 1
                    
                    for data_type, count in data_types.items():
                        report.append(f"  - {data_type}: {count}")
                report.append("")
        
        # Additional Intelligence
        additional_intel = investigation_results.get('additional_intel', {})
        if additional_intel:
            report.append("ADDITIONAL INTELLIGENCE:")
            report.append("-" * 40)
            
            # Domain Analysis
            domain_analysis = additional_intel.get('domain_analysis')
            if domain_analysis:
                report.append(f"Domain Analysis for: {domain_analysis.get('domain', 'N/A')}")
                
                # DNS Records
                dns_records = domain_analysis.get('dns_records', {})
                if dns_records:
                    report.append("  DNS Records:")
                    for record_type, records in dns_records.items():
                        if records:
                            report.append(f"    {record_type}: {', '.join(records[:3])}{'...' if len(records) > 3 else ''}")
                
                # Subdomains
                subdomains = domain_analysis.get('subdomains', [])
                if subdomains:
                    report.append(f"  Subdomains found: {len(subdomains)}")
                    for subdomain in subdomains[:5]:  # Show first 5
                        report.append(f"    - {subdomain}")
                    if len(subdomains) > 5:
                        report.append(f"    ... and {len(subdomains) - 5} more")
                
                # IP Analysis
                ip_analysis = domain_analysis.get('ip_analysis', {})
                if ip_analysis:
                    report.append("  IP Analysis:")
                    for ip, data in ip_analysis.items():
                        report.append(f"    IP: {ip}")
                        
                        # Geolocation
                        geo = data.get('geolocation', {})
                        if geo:
                            location = f"{geo.get('city', 'Unknown')}, {geo.get('country', 'Unknown')}"
                            report.append(f"      Location: {location}")
                            if geo.get('isp'):
                                report.append(f"      ISP: {geo.get('isp')}")
                        
                        # Port scan results
                        ports = data.get('port_scan', {})
                        if ports and ports.get('open_ports'):
                            report.append(f"      Open ports: {', '.join(map(str, ports['open_ports']))}")
                
                # WHOIS Information
                whois_info = domain_analysis.get('whois', {})
                if whois_info and not whois_info.get('error'):
                    report.append("  WHOIS Information:")
                    report.append(f"    Registrar: {whois_info.get('registrar', 'N/A')}")
                    report.append(f"    Creation Date: {whois_info.get('creation_date', 'N/A')}")
                    report.append(f"    Expiration Date: {whois_info.get('expiration_date', 'N/A')}")
                
                # SSL Information
                ssl_info = domain_analysis.get('ssl_info', {})
                if ssl_info and not ssl_info.get('error'):
                    report.append("  SSL Certificate:")
                    subject = ssl_info.get('subject', {})
                    if subject:
                        report.append(f"    Subject: {subject.get('commonName', 'N/A')}")
                    issuer = ssl_info.get('issuer', {})
                    if issuer:
                        report.append(f"    Issuer: {issuer.get('organizationName', 'N/A')}")
                    report.append(f"    Valid Until: {ssl_info.get('notAfter', 'N/A')}")
                
                report.append("")
            
            # Email Investigation
            email_investigation = additional_intel.get('email_investigation')
            if email_investigation:
                report.append(f"Email Investigation for: {email_investigation.get('email', 'N/A')}")
                
                # Format validation
                format_check = email_investigation.get('format_validation', {})
                if format_check:
                    report.append(f"  Email Format: {'Valid' if format_check.get('format_valid') else 'Invalid'}")
                    report.append(f"  Domain: {format_check.get('domain', 'N/A')}")
                
                # MX Record check
                mx_check = email_investigation.get('domain_mx_check', {})
                if mx_check:
                    report.append(f"  MX Records: {'Yes' if mx_check.get('has_mx') else 'No'}")
                
                # Basic breach check
                breach_check = email_investigation.get('breach_check', {})
                if breach_check:
                    if breach_check.get('domain_in_known_breaches'):
                        report.append("  ⚠️  Domain found in known breach lists")
                    else:
                        report.append("  ✅ Domain not in common breach lists")
                
                report.append("")
            
            # Social Media Search
            social_search = additional_intel.get('social_media_search')
            if social_search:
                report.append("SOCIAL MEDIA SEARCH:")
                report.append("-" * 30)
                for username, results in social_search.items():
                    report.append(f"Username: {username}")
                    verified = results.get('verified_profiles', [])
                    potential = results.get('potential_profiles', [])
                    
                    if verified:
                        report.append(f"  ✅ Verified profiles ({len(verified)}):")
                        for profile in verified:
                            report.append(f"    - {profile['platform']}: {profile['url']}")
                    
                    report.append(f"  🔍 Potential profiles to check: {len(potential)}")
                    for profile in potential[:5]:  # Show first 5
                        report.append(f"    - {profile['platform']}: {profile['url']}")
                    
                    if len(potential) > 5:
                        report.append(f"    ... and {len(potential) - 5} more")
                    
                    report.append("")
                
                report.append("")
            
            # Location Analysis
            location_analysis = additional_intel.get('location_analysis')
            if location_analysis:
                coordinates = location_analysis.get('coordinates', 'N/A')
                report.append(f"Location Analysis for: {coordinates}")
                
                # Reverse Geocoding
                geocoding = location_analysis.get('reverse_geocoding', {})
                if geocoding and 'display_name' in geocoding:
                    report.append(f"  Address: {geocoding['display_name']}")
                
                # Nearby Places
                nearby_places = location_analysis.get('nearby_places', [])
                if nearby_places:
                    report.append(f"  Nearby Places of Interest: {len(nearby_places)}")
                    # Group by type
                    place_types = {}
                    for place in nearby_places:
                        place_type = place.get('type', 'Unknown')
                        place_types[place_type] = place_types.get(place_type, 0) + 1
                    
                    for place_type, count in list(place_types.items())[:5]:  # Show top 5
                        report.append(f"    - {place_type}: {count}")
                
                # Norfolk Events (if location is in Norfolk, VA area)
                norfolk_events = location_analysis.get('norfolk_events')
                if norfolk_events and not norfolk_events.get('error'):
                    report.append("  🏛️ NORFOLK, VA LOCAL EVENTS:")
                    report.append("  " + "-" * 35)
                    
                    # Show filtering information if applied
                    if norfolk_events.get('filter_applied'):
                        user_interests = norfolk_events.get('user_interests', [])
                        report.append(f"  🎯 Filtered based on detected interests: {', '.join(user_interests[:5])}{'...' if len(user_interests) > 5 else ''}")
                        report.append(f"  📊 Showing {norfolk_events.get('events_found', 0)} relevant events (from {norfolk_events.get('original_events_count', 0)} total)")
                        report.append("")
                    
                    events = norfolk_events.get('events', [])
                    news_items = norfolk_events.get('news_items', [])
                    
                    if events:
                        report.append(f"  📅 Relevant Events ({len(events)} found):")
                        for event in events[:5]:  # Show first 5 events
                            report.append(f"    • {event.get('title', 'Untitled Event')}")
                            report.append(f"      Date: {event.get('date', 'TBD')}")
                            report.append(f"      Location: {event.get('location', 'Location TBD')}")
                            
                            # Show relevance information if available
                            if event.get('relevance_score'):
                                matched_interests = event.get('matched_interests', [])
                                report.append(f"      Relevance: {event.get('relevance_score')} matches ({', '.join(matched_interests[:3])})")
                            
                            if event.get('description') and len(event['description']) > 50:
                                desc = event['description'][:100] + '...' if len(event['description']) > 100 else event['description']
                                report.append(f"      Description: {desc}")
                            report.append("")
                        
                        if len(events) > 5:
                            report.append(f"    ... and {len(events) - 5} more relevant events")
                    else:
                        report.append("  📅 No events found matching your interests")
                    
                    if news_items:
                        report.append(f"  📰 Relevant Local News/Announcements ({len(news_items)} found):")
                        for news in news_items[:3]:  # Show first 3 news items
                            headline = news.get('headline', 'No headline')
                            report.append(f"    • {headline}")
                            
                            # Show relevance information if available
                            if news.get('relevance_score'):
                                matched_interests = news.get('matched_interests', [])
                                report.append(f"      Relevance: {news.get('relevance_score')} matches ({', '.join(matched_interests[:3])})")
                            
                            if news.get('context') and len(news['context']) > 50:
                                context = news['context'][:150] + '...' if len(news['context']) > 150 else news['context']
                                report.append(f"      {context}")
                            report.append("")
                    
                    report.append(f"  Source: NFK Currents (scraped on {norfolk_events.get('scrape_date', 'unknown date')})")
                
                elif norfolk_events and norfolk_events.get('error'):
                    report.append("  🏛️ Norfolk, VA area detected, but unable to fetch local events:")
                    report.append(f"  Error: {norfolk_events['error']}")
                
                report.append("")
        
        report.append("="*80)
        report.append("END OF REPORT")
        report.append("="*80)
        
        return '\n'.join(report)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Advanced OSINT Scraper")
    parser.add_argument("--setup", action="store_true", help="Setup OSINT tools")
    parser.add_argument("--name", help="Target's full name")
    parser.add_argument("--email", help="Target's email address")
    parser.add_argument("--social", nargs="*", help="Social media handles")
    parser.add_argument("--address", help="Target's address")
    parser.add_argument("--coordinates", nargs=2, type=float, help="Latitude and longitude")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = OSINTScraper()
    
    if args.setup:
        scraper.setup()
        return
    
    if args.interactive:
        # Interactive mode
        print(f"{Fore.CYAN}Welcome to Advanced OSINT Scraper{Style.RESET_ALL}")
        print("Please provide target information:")
        
        full_name = input("Full Name: ").strip()
        email = input("Email: ").strip()
        
        social_handles = []
        while True:
            handle = input("Social Media Handle (press Enter to skip): ").strip()
            if not handle:
                break
            social_handles.append(handle)
        
        address = input("Address: ").strip()
        
        coord_input = input("Coordinates (lat,lon): ").strip()
        coordinates = None
        if coord_input:
            try:
                lat, lon = map(float, coord_input.split(','))
                coordinates = (lat, lon)
            except ValueError:
                print("Invalid coordinates format. Skipping...")
        
        target = OSINTTarget(full_name, email, social_handles, address, coordinates)
    else:
        # Command line mode
        if not args.name and not args.email:
            print("Error: At least name or email must be provided")
            return
        
        coordinates = tuple(args.coordinates) if args.coordinates else None
        target = OSINTTarget(
            args.name or "",
            args.email or "",
            args.social or [],
            args.address or "",
            coordinates
        )
    
    # Setup tools if not already done
    if not scraper.setup():
        print("Warning: Some tools may not be available. Continuing with available tools...")
    
    # Run investigation
    results = scraper.investigate_target(target)
    
    # Generate and display report
    report = scraper.generate_report(results)
    print("\n" + report)
    
    # Save report
    report_file = scraper.config.output_dir / f"report_{target.full_name.replace(' ', '_').replace('/', '_')}_{int(time.time())}.txt"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n{Fore.GREEN}Report saved to: {report_file}{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Failed to save report: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
