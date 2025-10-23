try:
    from .common_utils import safe_print
except ImportError:
    from omnipkg.common_utils import safe_print
"""
omnipkg_metadata_builder.py - v11 - The "Multi-Version Complete" Edition
A fully integrated, self-aware metadata gatherer with complete multi-version
support for robust, side-by-side package management.
"""
import os
import re
import json
import subprocess
import hashlib
import importlib.metadata
import zlib
import sys
import tempfile
import concurrent.futures
import requests as http_requests
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from packaging.utils import canonicalize_name
from omnipkg.loader import omnipkgLoader
import threading
import traceback
import sys
from functools import wraps
import tempfile
import subprocess
import json
import re

# Add this global recursion tracking code at module level (after imports, before class definition)
_security_scan_depth = threading.local()
_max_depth = 10  # Adjust as needed
_security_scan_lock = threading.RLock()
_security_scan_running = threading.local()
from omnipkg.i18n import _
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

def get_python_version():
    """Get current Python version in X.Y format"""
    return f'{sys.version_info.major}.{sys.version_info.minor}'

def get_site_packages_path():
    """Dynamically find the site-packages path"""
    import site
    site_packages_dirs = site.getsitepackages()
    if hasattr(site, 'getusersitepackages'):
        site_packages_dirs.append(site.getusersitepackages())
    if hasattr(sys, 'prefix') and sys.prefix != sys.base_prefix:
        venv_site_packages = Path(sys.prefix) / 'lib' / f'python{get_python_version()}' / 'site-packages'
        if venv_site_packages.exists():
            return str(venv_site_packages)
    for sp in site_packages_dirs:
        if Path(sp).exists():
            return sp
    return str(Path(sys.executable).parent.parent / 'lib' / f'python{get_python_version()}' / 'site-packages')

def get_bin_paths():
    """Get binary paths to index"""
    paths = [str(Path(sys.executable).parent)]
    if hasattr(sys, 'prefix') and sys.prefix != sys.base_prefix:
        venv_bin = str(Path(sys.prefix) / 'bin')
        if venv_bin not in paths and Path(venv_bin).exists():
            paths.append(venv_bin)
    return paths

class omnipkgMetadataGatherer:

    def __init__(self, config: Dict, env_id: str, force_refresh: bool=False, omnipkg_instance=None, target_context_version: Optional[str]=None):
        self.cache_client = None
        self.omnipkg_instance = omnipkg_instance
        self.cache_client = self.omnipkg_instance.cache_client if self.omnipkg_instance else None
        self.force_refresh = force_refresh
        self.security_report = {}
        self.target_context_version = target_context_version
        self.config = config
        self.env_id = os.environ.get('OMNIPKG_ENV_ID_OVERRIDE', env_id)
        self.package_path_registry = {}
        if self.force_refresh:
            safe_print(_('🟢 --force flag detected. Caching will be ignored.'))
        if not HAS_TQDM:
            safe_print(_("⚠️ Install 'tqdm' for a better progress bar."))

    @property
    def redis_env_prefix(self) -> str:
        """
        Delegates to the main omnipkg instance to get the correct,
        environment-specific key prefix.
        """
        if self.omnipkg_instance:
            return self.omnipkg_instance.redis_env_prefix
        # Fallback in case the main instance isn't available for some reason
        return self.redis_key_prefix.rsplit('pkg:', 1)[0]

    @property
    def redis_key_prefix(self) -> str:
        """
        (CORRECTED) This now DELEGATES to the main omnipkg instance to get the
        one, true, authoritative redis_key_prefix. This eliminates the mismatch bug.
        """
        if self.omnipkg_instance and hasattr(self.omnipkg_instance, 'redis_key_prefix'):
            # This is the primary, correct path.
            return self.omnipkg_instance.redis_key_prefix
        
        # The following is a fallback for rare cases (like direct script execution)
        # and is now corrected to match the logic in core.py exactly.
        python_exe_path = self.config.get('python_executable', sys.executable)
        py_ver_str = 'unknown'
        match = re.search('python(3\\.\\d+)', python_exe_path)
        if match:
            py_ver_str = f'py{match.group(1)}'
        else:
            try:
                result = subprocess.run([python_exe_path, '-c', "import sys; print(f'py{sys.version_info.major}.{sys.version_info.minor}')"], capture_output=True, text=True, check=True, timeout=2)
                py_ver_str = result.stdout.strip()
            except Exception:
                py_ver_str = f'py{sys.version_info.major}.{sys.version_info.minor}'
        
        return f'omnipkg:env_{self.env_id}:{py_ver_str}:pkg:'

    def _get_package_name_variants(self, name: str) -> List[str]:
        """
        Generates comprehensive package name variants to handle ALL Python packaging
        naming conventions including dots, hyphens, underscores.
        """
        variants = {name, canonicalize_name(name), name.replace('-', '_'), name.replace('_', '-'), name.replace('-', '.'), name.replace('.', '-'), name.replace('_', '.'), name.replace('.', '_'), name.lower(), name.upper()}
        clean_name = name.lower()
        if clean_name.startswith('python-'):
            base = clean_name[7:]
            variants.update({base, base.replace('-', '_'), base.replace('-', '.'), base.replace('_', '.'), base.replace('_', '-')})
        if clean_name.startswith('py-'):
            base = clean_name[3:]
            variants.update({base, base.replace('-', '_'), base.replace('-', '.'), base.replace('_', '.'), base.replace('_', '-')})
        if clean_name.endswith('-python'):
            base = clean_name[:-7]
            variants.update({base, base.replace('-', '_'), base.replace('-', '.'), base.replace('_', '.'), base.replace('_', '-')})
        return list(variants)

    def _is_known_subcomponent(self, dist_info_path: Path) -> bool:
        """Check if this dist-info belongs to a sub-component that shouldn't be treated independently."""
        name = dist_info_path.name
        subcomponent_patterns = ['tensorboard_data_server-', 'tensorboard_plugin_']
        for pattern in subcomponent_patterns:
            if name.startswith(pattern):
                return True
        return False
    
        # ADD THIS HELPER METHOD TO omnipkgMetadataGatherer IN package_meta_builder.py
    def _is_dist_compatible_with_context(self, dist: importlib.metadata.Distribution, python_version: str) -> bool:
        """Checks if a given distribution is compatible with the specified python_version context."""
        context_info = self._get_install_context(dist)
        install_type = context_info['install_type']

        if install_type in ['active', 'vendored', 'unknown']:
            return True

        if install_type in ['bubble', 'nested']:
            multiversion_base_path = Path(self.config.get('multiversion_base', '/dev/null'))
            try:
                relative_to_base = dist._path.relative_to(multiversion_base_path)
                bubble_root_name = relative_to_base.parts[0]
                bubble_root_path = multiversion_base_path / bubble_root_name
                manifest_file = bubble_root_path / '.omnipkg_manifest.json'
                
                if not manifest_file.exists():
                    return True # Assume compatible if no manifest (legacy)
                
                with open(manifest_file, 'r') as f:
                    manifest = json.load(f)
                
                return manifest.get('python_version') == python_version
            except (ValueError, IndexError, IOError, json.JSONDecodeError):
                return True # Be safe, assume compatible on error
        
        return False
    
    def _parse_distribution_worker(self, dist_info_path: Path) -> Optional[importlib.metadata.Distribution]:
            """Worker function for parallel discovery. Parses a single dist-info path."""
            try:
                # We must use PathDistribution directly for paths outside the standard sys.path
                from importlib.metadata import PathDistribution
                dist = PathDistribution(dist_info_path)
                # Basic validation: ensure it has a name.
                if dist.metadata.get('Name'):
                    return dist
            except Exception:
                # Silently ignore corrupted or unreadable metadata
                pass
            return None

    def _discover_distributions(self, targeted_packages: Optional[List[str]], verbose: bool=False) -> List[importlib.metadata.Distribution]:
        """
        ENHANCED DISCOVERY V10: Combines V9's authoritative file system scanning 
        with V7's comprehensive targeted search features and vendored package detection.
        
        This version completely ignores the running interpreter's sys.path and ONLY scans 
        the exact file paths provided by the configuration for the target context, 
        eliminating all context bleed while preserving all advanced search capabilities.
        
        Args:
            targeted_packages: Optional list of specific packages to find
            verbose: If True, shows detailed search progress. If False, only shows results.
        """
        # Get the ground-truth paths from the config (loaded by omnipkg core)
        site_packages_path = self.config.get('site_packages_path')
        multiversion_base_path = self.config.get('multiversion_base')
        search_paths = []
        
        if site_packages_path and Path(site_packages_path).is_dir():
            search_paths.append(Path(site_packages_path))
        if multiversion_base_path and Path(multiversion_base_path).is_dir():
            search_paths.append(Path(multiversion_base_path))
            
        if not search_paths:
            safe_print("   - ⚠️ No valid site-packages or multiversion paths found in config. Cannot discover packages.")
            return []

        if targeted_packages:
            if verbose:
                safe_print(f'🎯 Running AUTHORITATIVE targeted scan for {len(targeted_packages)} package(s).')
            discovered_dists = []
            
            for spec in targeted_packages:
                try:
                    if '==' in spec:
                        name, version = spec.split('==', 1)
                    else:
                        name = spec
                        version = None
                        
                    found_dist = None
                    name_variants = self._get_package_name_variants(name)
                    
                    if verbose:
                        safe_print(f"   🔍 Searching for '{spec}' with variants: {name_variants}")
                    
                    # Search each configured path using authoritative file system scanning
                    for base_path in search_paths:
                        if verbose:
                            safe_print(_('      -> Authoritative scan in: {}').format(base_path))
                        
                        # Strategy 1: Check for vendored packages (V7 feature)
                        if verbose:
                            safe_print(f'      -> Strategy 1: Checking for vendored packages...')
                        vendored_dist_infos = list(base_path.rglob('*/_vendor/*.dist-info'))
                        if verbose:
                            safe_print(_('         Found {} vendored dist-info directories').format(len(vendored_dist_infos)))
                        
                        for vendor_dist_info in vendored_dist_infos:
                            if not vendor_dist_info.is_dir():
                                continue
                            try:
                                dist = importlib.metadata.Distribution.at(vendor_dist_info)
                                dist_name = dist.metadata.get('Name', '')
                                name_matches = any((
                                    canonicalize_name(dist_name) == canonicalize_name(variant) or 
                                    dist_name.lower() == variant.lower() or 
                                    dist_name.replace('.', '-').lower() == variant.replace('.', '-').lower() or 
                                    dist_name.replace('-', '.').lower() == variant.replace('-', '.').lower() 
                                    for variant in name_variants
                                ))
                                if name_matches:
                                    if version is None or dist.version == version:
                                        vendor_parent = str(vendor_dist_info).split('/_vendor/')[0].split('/')[-1]
                                        found_dist = dist
                                        safe_print(_('✅ Found VENDORED {} v{} (inside {}) at {}').format(
                                            dist_name, dist.version, vendor_parent, vendor_dist_info))
                                        break
                                    elif verbose:
                                        vendor_parent = str(vendor_dist_info).split('/_vendor/')[0].split('/')[-1]
                                        safe_print(_('         ⚠️  Found VENDORED {} v{} (inside {}) but need v{}').format(
                                            dist_name, dist.version, vendor_parent, version))
                            except Exception as e:
                                if verbose:
                                    safe_print(_('         ❌ Error reading vendored {}: {}').format(vendor_dist_info, e))
                                continue
                        
                        if found_dist:
                            break
                        
                        # Strategy 2: Direct pattern matching (V7 feature)
                        if verbose:
                            safe_print(f'      -> Strategy 2: Direct pattern matching...')
                        for variant in name_variants:
                            if version:
                                patterns = [
                                    f'{variant}-{version}.dist-info', 
                                    f'{variant}-{version}-*.dist-info',
                                    f"{variant.replace('.', '_')}-{version}.dist-info", 
                                    f"{variant.replace('.', '_')}-{version}-*.dist-info"
                                ]
                            else:
                                patterns = [
                                    f'{variant}-*.dist-info', 
                                    f"{variant.replace('.', '_')}-*.dist-info"
                                ]
                                
                            for pattern in patterns:
                                matching_paths = list(base_path.glob(pattern))
                                if verbose:
                                    safe_print(_("         Pattern '{}' found: {} matches").format(pattern, len(matching_paths)))
                                
                                for dist_info_path in matching_paths:
                                    if not dist_info_path.is_dir():
                                        continue
                                    try:
                                        dist = importlib.metadata.Distribution.at(dist_info_path)
                                        dist_name = dist.metadata.get('Name', '')
                                        if (canonicalize_name(dist_name) == canonicalize_name(name) or 
                                            dist_name.lower() == name.lower() or 
                                            dist_name.replace('.', '-').lower() == name.replace('.', '-').lower() or 
                                            dist_name.replace('-', '.').lower() == name.replace('-', '.').lower()):
                                            if version is None or dist.version == version:
                                                found_dist = dist
                                                safe_print(_('✅ Found {} v{} at {}').format(dist_name, dist.version, dist_info_path))
                                                break
                                            elif verbose:
                                                safe_print(_('         ⚠️  Found {} v{} but need v{}').format(dist_name, dist.version, version))
                                        elif verbose:
                                            safe_print(f'         ❌ Name mismatch: found "{dist_name}", looking for "{name}"')
                                    except Exception as e:
                                        if verbose:
                                            safe_print(_('         ❌ Error reading {}: {}').format(dist_info_path, e))
                                        continue
                                if found_dist:
                                    break
                            if found_dist:
                                break
                        
                        if found_dist:
                            break
                        
                        # Strategy 3: Nested directory search (V7 feature)  
                        if verbose:
                            safe_print(f'      -> Strategy 3: Searching nested directories for dist-info...')
                        for variant in name_variants:
                            if version:
                                nested_dir_patterns = [
                                    f'{variant}-{version}', 
                                    f"{variant.replace('.', '_')}-{version}"
                                ]
                            else:
                                nested_dir_patterns = [
                                    f'{variant}-*', 
                                    f"{variant.replace('.', '_')}-*"
                                ]
                                
                            for pattern in nested_dir_patterns:
                                matching_dirs = list(base_path.glob(pattern))
                                if verbose:
                                    safe_print(_("         Nested dir pattern '{}' found: {} directories").format(pattern, len(matching_dirs)))
                                
                                for nested_dir in matching_dirs:
                                    if not nested_dir.is_dir():
                                        continue
                                        
                                    dist_info_pattern = '*.dist-info'
                                    dist_infos = list(nested_dir.glob(dist_info_pattern))
                                    
                                    for dist_info_path in dist_infos:
                                        if not dist_info_path.is_dir():
                                            continue
                                        try:
                                            dist = importlib.metadata.Distribution.at(dist_info_path)
                                            dist_name = dist.metadata.get('Name', '')
                                            name_matches = any((
                                                canonicalize_name(dist_name) == canonicalize_name(v) 
                                                for v in name_variants
                                            ))
                                            if name_matches:
                                                if version is None or dist.version == version:
                                                    found_dist = dist
                                                    safe_print(_('✅ Found nested {} v{} at {}').format(
                                                        dist_name, dist.version, dist_info_path))
                                                    break
                                                elif verbose:
                                                    safe_print(_('         ⚠️  Found nested {} v{} but need v{}').format(
                                                        dist_name, dist.version, version))
                                        except Exception as e:
                                            if verbose:
                                                safe_print(_('         ❌ Error reading nested {}: {}').format(dist_info_path, e))
                                            continue
                                    if found_dist:
                                        break
                                if found_dist:
                                    break
                            if found_dist:
                                break
                        
                        if found_dist:
                            break
                        
                        # Strategy 4: Comprehensive fallback scan (V7 feature)
                        if verbose:
                            safe_print(f'      -> Strategy 4: Fallback comprehensive scan...')
                        all_dist_infos = list(base_path.glob('*.dist-info'))
                        all_dist_infos.extend(list(base_path.glob('*/*.dist-info')))
                        # Add recursive search for deeper nesting
                        all_dist_infos.extend(list(base_path.rglob('*.dist-info')))
                        
                        # Remove duplicates while preserving order
                        seen = set()
                        unique_dist_infos = []
                        for path in all_dist_infos:
                            if path not in seen:
                                seen.add(path)
                                unique_dist_infos.append(path)
                        
                        if verbose:
                            safe_print(_('         Found {} unique dist-info directories to check').format(len(unique_dist_infos)))
                        
                        for dist_info_path in unique_dist_infos:
                            if not dist_info_path.is_dir():
                                continue
                            try:
                                dist = importlib.metadata.Distribution.at(dist_info_path)
                                dist_name = dist.metadata.get('Name', '')
                                name_matches = any((
                                    canonicalize_name(dist_name) == canonicalize_name(variant) 
                                    for variant in name_variants
                                ))
                                if name_matches:
                                    if version is None or dist.version == version:
                                        found_dist = dist
                                        safe_print(_('✅ Fallback found {} v{} at {}').format(
                                            dist_name, dist.version, dist_info_path))
                                        break
                                    elif verbose:
                                        safe_print(_('         ⚠️  Fallback found {} v{} but need v{}').format(
                                            dist_name, dist.version, version))
                            except Exception as e:
                                continue
                        
                        if found_dist:
                            break
                    
                    # Record results
                    if found_dist:
                        discovered_dists.append(found_dist)
                        if verbose:
                            if version:
                                safe_print(f'   -> Successfully found distribution for {name}=={version}')
                            else:
                                safe_print(f'   -> Successfully found distribution for {name} v{found_dist.version}')
                    elif version:
                        safe_print(_("❌ Could not find distribution matching '{}=={}'").format(name, version))
                        if verbose:
                            safe_print(_('   💡 Available variants tried: {}').format(name_variants))
                    else:
                        safe_print(_("❌ Could not find distribution matching '{}'").format(name))
                        
                except ValueError as e:
                    safe_print(_("❌ Could not parse spec '{}': {}").format(spec, e))
                    
            return discovered_dists
        
        # Full discovery mode using V9's authoritative approach with V7's comprehensive scanning
        if verbose:
            safe_print('🔍 Running AUTHORITATIVE full discovery scan (no context bleed)...')
        
        # Phase 1: Rapidly locate all potential package metadata files using authoritative paths
        safe_print("   - Phase 1: Rapidly locating all potential package metadata files...")
        all_dist_info_paths = []
        
        for path in search_paths:
            if verbose:
                safe_print(f"      -> Authoritative scan of: {path}")
            # Use rglob to find all .dist-info directories recursively (V9 approach)
            all_dist_info_paths.extend(path.rglob('*.dist-info'))
        
        safe_print(f"   - Phase 2: Parsing {len(all_dist_info_paths)} metadata files in parallel...")
        
        # Phase 2: Process these concrete paths in parallel (V9's efficient approach)
        discovered_dists = []
        max_workers = min(32, (os.cpu_count() or 4) + 4)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Filter out non-directories before submitting to avoid worker errors
            valid_paths = [path for path in all_dist_info_paths if path.is_dir()]
            future_to_path = {
                executor.submit(self._parse_distribution_worker, path): path 
                for path in valid_paths
            }
            
            iterator = concurrent.futures.as_completed(future_to_path)
            if HAS_TQDM:
                iterator = tqdm(iterator, total=len(future_to_path), desc="      Parsing", unit="pkg")
            
            for future in iterator:
                result = future.result()
                if result:
                    discovered_dists.append(result)
        
        if verbose:
            safe_print(_('✅ Authoritative discovery complete. Found {} total package versions.').format(len(discovered_dists)))
            
        return discovered_dists

    def _is_bubbled(self, dist: importlib.metadata.Distribution) -> bool:
        multiversion_base = self.config.get('multiversion_base', '/dev/null')
        return str(dist._path).startswith(multiversion_base)

    def discover_all_packages(self) -> List[Tuple[str, str]]:
        """
        Authoritatively discovers all active and bubbled packages from the file system,
        and cleans up any "ghost" entries from the Redis index that no longer exist.
        """
        safe_print(_('🔍 Discovering all packages from file system (ground truth)...'))
        from packaging.utils import canonicalize_name
        found_on_disk = {}
        active_packages = {}
        try:
            for dist in importlib.metadata.distributions():
                pkg_name = canonicalize_name(dist.metadata.get('Name', ''))
                if not pkg_name:
                    continue
                if pkg_name not in found_on_disk:
                    found_on_disk[pkg_name] = set()
                found_on_disk[pkg_name].add(dist.version)
                active_packages[pkg_name] = dist.version
        except Exception as e:
            safe_print(_('⚠️ Error discovering active packages: {}').format(e))
        multiversion_base_path = Path(self.config['multiversion_base'])
        if multiversion_base_path.is_dir():
            for bubble_dir in multiversion_base_path.iterdir():
                dist_info = next(bubble_dir.glob('*.dist-info'), None)
                if dist_info:
                    try:
                        from importlib.metadata import PathDistribution
                        dist = PathDistribution(dist_info)
                        pkg_name = canonicalize_name(dist.metadata.get('Name', ''))
                        if not pkg_name:
                            continue
                        if pkg_name not in found_on_disk:
                            found_on_disk[pkg_name] = set()
                        found_on_disk[pkg_name].add(dist.version)
                    except Exception:
                        continue
        safe_print(_('    -> Reconciling file system state with Redis knowledge base...'))
        self._store_active_versions(active_packages)
        result_list = []
        for pkg_name, versions_set in found_on_disk.items():
            for version_str in versions_set:
                result_list.append((pkg_name, version_str))
        safe_print(_('✅ Discovery complete. Found {} unique packages with {} total versions to process.').format(len(found_on_disk), len(result_list)))
        return sorted(result_list, key=lambda x: x[0])

    def _register_bubble_path(self, pkg_name: str, version: str, bubble_path: Path):
        """Register bubble paths in Redis for dedup across bubbles and main env."""
        redis_key = f'{self.redis_key_prefix}bubble:{pkg_name}:{version}:path'
        self.cache_client.set(redis_key, str(bubble_path))
        self.package_path_registry[pkg_name] = self.package_path_registry.get(pkg_name, {})
        self.package_path_registry[pkg_name][version] = str(bubble_path)

    def _store_active_versions(self, active_packages: Dict[str, str]):
        if not self.cache_client:
            return
        prefix = self.redis_key_prefix
        for pkg_name, version in active_packages.items():
            main_key = f'{prefix}{pkg_name}'
            try:
                self.cache_client.hset(main_key, 'active_version', version)
            except Exception as e:
                safe_print(_('⚠️ Failed to store active version for {}: {}').format(pkg_name, e))

    def _perform_security_scan(self, packages: Dict[str, str]):
        """
        Runs a security check using a dedicated, isolated 'safety' tool bubble,
        created on-demand by the bubble_manager to guarantee isolation.
        """
        safe_print(f'🛡️ Performing security scan for {len(packages)} active package(s) using isolated tool...')
        if not packages:
            safe_print(_(' - No active packages found to scan.'))
            self.security_report = {}
            return
        if not self.omnipkg_instance:
            safe_print(_(' ⚠️ Cannot run security scan: omnipkg_instance not available to builder.'))
            self.security_report = {}
            return
        TOOL_SPEC = 'safety==3.6.0'
        TOOL_NAME, TOOL_VERSION = TOOL_SPEC.split('==')
        try:
            bubble_path = self.omnipkg_instance.multiversion_base / f'{TOOL_NAME}-{TOOL_VERSION}'
            if not bubble_path.is_dir():
                safe_print(f" 💡 First-time setup: Creating isolated bubble for '{TOOL_SPEC}' tool...")
                success = self.omnipkg_instance.bubble_manager.create_isolated_bubble(
                    TOOL_NAME, TOOL_VERSION, python_context_version=self.target_context_version
                )
                if not success:
                    safe_print(f' ❌ Failed to create the tool bubble for {TOOL_SPEC}. Skipping scan.')
                    self.security_report = {}
                    return
                safe_print(_(' ✅ Successfully created tool bubble.'))
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as reqs_file:
                reqs_file_path = reqs_file.name
                for name, version in packages.items():
                    reqs_file.write(f'{name}=={version}\n')
            safe_print(_(" 🌀 Force-activating '{}' context to run scan...").format(TOOL_SPEC))
            with omnipkgLoader(TOOL_SPEC, config=self.omnipkg_instance.config, force_activation=True, quiet=True):
                python_exe = self.config.get('python_executable', sys.executable)
                cmd = [python_exe, '-m', 'safety', 'check', '-r', reqs_file_path, '--json']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            self.security_report = {}
            if result.stdout:
                try:
                    json_match = re.search('(\\[.*\\]|\\{.*\\})', result.stdout, re.DOTALL)
                    if json_match:
                        self.security_report = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    safe_print(_(' ⚠️ Could not parse safety JSON output.'))
            if result.stderr and 'error' in result.stderr.lower():
                safe_print(_(' ⚠️ Safety tool produced errors: {}').format(result.stderr.strip()))
        except Exception as e:
            safe_print(_(' ⚠️ An unexpected error occurred during the isolated security scan: {}').format(e))
            self.security_report = {}
        finally:
            if 'reqs_file_path' in locals() and os.path.exists(reqs_file_path):
                os.unlink(reqs_file_path)
        issue_count = 0
        if isinstance(self.security_report, list):
            issue_count = len(self.security_report)
        elif isinstance(self.security_report, dict) and 'vulnerabilities' in self.security_report:
            issue_count = len(self.security_report['vulnerabilities'])
        safe_print(_('✅ Security scan complete. Found {} potential issues.').format(issue_count))

    def run(self, targeted_packages: Optional[List[str]]=None, newly_active_packages: Optional[Dict[str, str]]=None):
        """
        (V5.3 - Robust Path Fix) The main execution loop. Now uses robust logic
        to locate the bubble root and correctly determine context compatibility.
        """
        if not self.cache_client:
            safe_print(_('❌ Cache client not available to the builder. Aborting.'))
            return

        all_discovered_dists = self._discover_distributions(targeted_packages)
        distributions_to_process = []
        safe_print(f"   -> Filtering {len(all_discovered_dists)} discovered packages for current Python {self.target_context_version} context...")

        for dist in all_discovered_dists:
            context_info = self._get_install_context(dist)
            install_type = context_info['install_type']

            if install_type in ['active', 'vendored', 'unknown']:
                distributions_to_process.append(dist)
                continue

            if install_type in ['bubble', 'nested']:
                is_compatible = False
                multiversion_base_path = Path(self.config.get('multiversion_base', '/dev/null'))
                
                # --- THIS IS THE ROBUST FIX ---
                try:
                    # Directly calculate the bubble root path instead of traversing.
                    relative_to_base = dist._path.relative_to(multiversion_base_path)
                    bubble_root_name = relative_to_base.parts[0]
                    bubble_root_path = multiversion_base_path / bubble_root_name
                    manifest_file = bubble_root_path / '.omnipkg_manifest.json'

                    if manifest_file.exists():
                        try:
                            with open(manifest_file, 'r') as f:
                                manifest = json.load(f)
                            bubble_py_ver = manifest.get('python_version')
                            if bubble_py_ver == self.target_context_version:
                                is_compatible = True
                        except Exception:
                            is_compatible = True # Assume compatible if manifest is corrupt
                    else:
                        is_compatible = True # Assume compatible if no manifest exists (legacy)
                except ValueError:
                    # Should not happen if type is bubble/nested, but a safeguard.
                    is_compatible = True
                # --- END FIX ---

                if is_compatible:
                    distributions_to_process.append(dist)
        
        safe_print(f"   -> Found {len(distributions_to_process)} packages belonging to this context.")

        if not distributions_to_process:
            safe_print(_('✅ No packages found for the current context to process.'))
            return []

        active_packages_to_scan = {
            canonicalize_name(dist.metadata['Name']): dist.version
            for dist in distributions_to_process if self._get_install_context(dist)['install_type'] == 'active'
        }
        self._perform_security_scan(active_packages_to_scan)

        import time
        start_time = time.perf_counter()

        updated_count = 0
        max_workers = (os.cpu_count() or 4) * 2
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix='omnipkg_builder') as executor:
            future_to_dist = {executor.submit(self._process_package, dist): dist for dist in distributions_to_process}
            iterator = concurrent.futures.as_completed(future_to_dist)
            if HAS_TQDM:
                iterator = tqdm(iterator, total=len(distributions_to_process), desc='Processing packages', unit='pkg')

            for future in iterator:
                try:
                    if future.result():
                        updated_count += 1
                except Exception as exc:
                    dist = future_to_dist[future]
                    safe_print(f'\n❌ Error processing {dist.metadata["Name"]}: {exc}')
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        total_packages = len(distributions_to_process)
        pkgs_per_sec = total_packages / total_time if total_time > 0 else float('inf')

        print("\n" + "="*60)
        print("🚀 KNOWLEDGE BASE BUILD - PERFORMANCE SUMMARY 🚀")
        print("="*60)
        print(f"   - Processed {total_packages} packages in {total_time:.2f} seconds.")
        print(f"   - 🔥 Average Throughput: {pkgs_per_sec:.2f} pkg/s")
        print("="*60 + "\n")
                
        safe_print(_('🎉 Metadata building complete! Updated {} package(s) for this context.').format(updated_count))
        return distributions_to_process
    
    def _get_install_context(self, dist: importlib.metadata.Distribution) -> Dict:
        """
        (V2 - CORRECTED) Determines the precise installation context (active, bubble, nested, vendored)
        by comparing the package's identity to its location on the filesystem.
        """
        dist_path = dist._path
        path_str = str(dist_path)
        multiversion_base = Path(self.config.get('multiversion_base', '/dev/null'))
        site_packages = Path(self.config.get('site_packages_path', '/dev/null'))

        # Vendored check (remains the same)
        if '_vendor/' in path_str or '.vendor/' in path_str:
            # ... (code for vendored packages is correct) ...
            try:
                parent_path = dist_path
                while parent_path != site_packages and parent_path != multiversion_base and parent_path.parent != parent_path:
                    parent_dist_info = next(parent_path.glob('*.dist-info'), None)
                    if parent_dist_info and ('_vendor' not in str(parent_dist_info)):
                        parent_dist = importlib.metadata.Distribution.at(parent_dist_info)
                        return {'install_type': 'vendored', 'owner_package': canonicalize_name(parent_dist.metadata['Name'])}
                    parent_path = parent_path.parent
            except Exception:
                pass
            return {'install_type': 'vendored', 'owner_package': 'Unknown'}

        # --- THIS IS THE FIX ---
        try:
            # Get the top-level directory within the multiversion_base
            relative_path = dist_path.relative_to(multiversion_base)
            bubble_dir_name = relative_path.parts[0]
            
            # Get the package's own canonical name and version
            pkg_name = canonicalize_name(dist.metadata['Name'])
            version = dist.version
            
            expected_bubble_name = f"{pkg_name}-{version}"
            
            # Compare the parent directory name to the package's own identity
            if bubble_dir_name == expected_bubble_name:
                # It's a true bubble
                return {'install_type': 'bubble', 'owner_package': None}
            else:
                # It's nested inside another package's bubble
                return {'install_type': 'nested', 'owner_package': bubble_dir_name}
        except ValueError:
            # Not in the multiversion_base, so it must be active or unknown
            pass
        # --- END FIX ---

        # Active check (remains the same)
        try:
            dist_path.relative_to(site_packages)
            return {'install_type': 'active', 'owner_package': None}
        except ValueError:
            pass
        
        return {'install_type': 'unknown', 'owner_package': None}

    def _process_package(self, dist: importlib.metadata.Distribution) -> bool:
        """
        (V3.1 - Vendored Fix) Processes a single distribution, now correctly
        including vendored packages instead of skipping them.
        """
        try:
            raw_name = dist.metadata.get('Name')
            if not raw_name:
                return False # Silently skip corrupted metadata

            # --- FIX: REMOVED THE LOGIC THAT SKIPPED VENDORED PACKAGES ---
            # All discovered and filtered packages should be processed.
            context_info = self._get_install_context(dist)
            
            metadata = self._build_comprehensive_metadata(dist)
            is_active = (context_info['install_type'] == 'active')
            
            return self._store_in_redis(dist, is_active=is_active, context_info=context_info)

        except Exception as e:
            safe_print(f'\n❌ Error processing {dist._path}: {e}')
            return False

    def _build_comprehensive_metadata(self, dist: importlib.metadata.Distribution) -> Dict:
        """
        FIXED: Builds metadata exclusively from the provided Distribution object
        and now includes the physical path of the package.
        """
        package_name = canonicalize_name(dist.metadata['Name'])
        metadata = {k: v for k, v in dist.metadata.items()}
        try:
            package_path = dist.locate_file('')
            metadata['path'] = str(package_path)
        except Exception:
            metadata['path'] = str(dist._path)
        metadata['last_indexed'] = datetime.now().isoformat()
        context_version = self.target_context_version if self.target_context_version else get_python_version()
        metadata['indexed_by_python'] = context_version
        metadata['dependencies'] = [str(req) for req in dist.requires] if dist.requires else []
        package_files = self._find_package_files(dist)
        if package_files.get('binaries'):
            metadata['help_text'] = self._get_help_output(package_files['binaries'][0]).get('help_text', 'No executable binary found.')
        else:
            metadata['help_text'] = 'No executable binary found.'
        metadata['cli_analysis'] = self._analyze_cli(metadata.get('help_text', ''))
        metadata['security'] = self._get_security_info(package_name)
        metadata['health'] = self._perform_health_checks(dist, package_files)
        metadata['checksum'] = self._generate_checksum(metadata)
        return metadata

    def _find_distribution_at_path(self, package_name: str, version: str, search_path: Path) -> Optional[importlib.metadata.Distribution]:
        normalized_name_dash = canonicalize_name(package_name)
        normalized_name_under = normalized_name_dash.replace('-', '_')
        for name_variant in {normalized_name_dash, normalized_name_under}:
            for dist_info in search_path.glob(f'{name_variant}-{version}*.dist-info'):
                if dist_info.is_dir():
                    try:
                        from importlib.metadata import PathDistribution
                        dist = PathDistribution(dist_info)
                        metadata_name = dist.metadata.get('Name', '')
                        if canonicalize_name(metadata_name) == normalized_name_dash and dist.metadata.get('Version') == version:
                            return dist
                    except Exception:
                        continue
        return None
        
    def _get_instance_key(self, dist: importlib.metadata.Distribution) -> str:
            """Generates a unique, deterministic Redis key for a specific package instance."""
            path_str = str(dist._path)
            # Use a short, stable hash of the unique path
            instance_hash = hashlib.sha256(path_str.encode()).hexdigest()[:12]
            
            pkg_name = canonicalize_name(dist.metadata['Name'])
            version = dist.version
            prefix = self.redis_key_prefix.replace(':pkg:', ':inst:') # Change namespace to 'inst'
            
            return f"{prefix}{pkg_name}:{version}:{instance_hash}"   

    def _parse_metadata_file(self, metadata_content: str) -> Dict:
        metadata = {}
        current_key = None
        current_value = []
        for line in metadata_content.splitlines():
            if ': ' in line and (not line.startswith(' ')):
                if current_key:
                    metadata[current_key] = '\n'.join(current_value).strip() if current_value else ''
                current_key, value = line.split(': ', 1)
                current_value = [value]
            elif line.startswith(' ') and current_key:
                current_value.append(line.strip())
        if current_key:
            metadata[current_key] = '\n'.join(current_value).strip() if current_value else ''
        return metadata

    def _store_in_redis(self, dist: importlib.metadata.Distribution, is_active: bool, context_info: Dict):
        """
        (V5.1 - The Absolute Path Fix) Stores metadata using a hash of the
        unambiguous, resolved, absolute dist._path, ensuring that two installations
        of the same package version at different locations get unique, deterministic instance keys.
        """
        try:
            metadata = self._build_comprehensive_metadata(dist)
            package_name = canonicalize_name(dist.metadata['Name'])
            version_str = dist.version

            # --- THE FIX ---
            # The hash MUST be based on the unique, resolved, absolute filesystem path.
            # Using .resolve() guarantees a canonical path string for the hash.
            resolved_path_str = str(dist._path.resolve())
            unique_instance_identifier = f"{resolved_path_str}::{version_str}"
            instance_hash = hashlib.sha256(unique_instance_identifier.encode()).hexdigest()[:12]
            # --- END FIX ---

            instance_key = f"{self.redis_key_prefix.replace(':pkg:', ':inst:')}{package_name}:{version_str}:{instance_hash}"

            data_to_store = metadata.copy()
            data_to_store.update(context_info)
            data_to_store['installation_hash'] = instance_hash
            
            flattened_data = self._flatten_dict(data_to_store)

            main_key = f'{self.redis_key_prefix}{package_name}'
            index_key = f"{self.redis_env_prefix}index"

            with self.cache_client.pipeline() as pipe:
                pipe.delete(instance_key)
                pipe.hset(instance_key, mapping=flattened_data)
                pipe.sadd(f"{main_key}:installed_versions", version_str)
                pipe.sadd(f"{main_key}:{version_str}:instances", instance_hash)
                pipe.sadd(index_key, package_name)
                pipe.hset(main_key, 'name', package_name) 

                if is_active:
                    pipe.hset(main_key, 'active_version_instance_hash', instance_hash)
                    pipe.hset(main_key, 'active_version', version_str)
                
                if context_info.get('install_type') == 'bubble':
                    pipe.hset(main_key, 'bubble_version:{version_str}', 'true')

                pipe.execute()
            return True

        except Exception as e:
            safe_print(f'\n❌ Error storing {dist.metadata.get("Name", "N/A")} in Redis: {e}')
            return False

    def _perform_health_checks(self, dist: importlib.metadata.Distribution, package_files: Dict) -> Dict:
        """
        FIXED: Passes the specific distribution to the verification function.
        """
        health_data = {'import_check': self._verify_installation(dist), 'binary_checks': {Path(bin_path).name: self._check_binary_integrity(bin_path) for bin_path in package_files.get('binaries', [])}}
        oversized = [name for name, check in health_data['binary_checks'].items() if check.get('size', 0) > 10000000]
        if oversized:
            health_data['size_warnings'] = oversized
        return health_data

    def _verify_installation(self, dist: importlib.metadata.Distribution) -> Dict:
        """
        SMART VERSION: Uses authoritative top_level.txt and fallback strategies
        to correctly verify importability of any package structure.
        """
        package_name = canonicalize_name(dist.metadata['Name'])
        is_bubbled = self._is_bubbled(dist)
        bubble_path = str(dist._path.parent) if is_bubbled else None
        import_candidates = self._get_import_candidates(dist, package_name)
        script_lines = ['import sys', 'import importlib', 'import traceback', 'results = []']
        if bubble_path:
            script_lines.append(f"sys.path.insert(0, r'{bubble_path}')")
        for candidate in import_candidates:
            script_lines.extend([_('# Testing import: {}').format(candidate), 'try:', _("    mod = importlib.import_module('{}')").format(candidate), _("    version = getattr(mod, '__version__', None)"), _("    results.append(('{}', True, version))").format(candidate), 'except Exception as e:', _("    results.append(('{}', False, str(e)))").format(candidate)])
        script_lines.extend(['import json', 'print(json.dumps(results))'])
        script = '\n'.join(script_lines)
        import json
        try:
            python_exe = self.config.get('python_executable', sys.executable)
            result = subprocess.run([python_exe, '-c', script], capture_output=True, text=True, check=True, timeout=10)
            import json
            test_results = json.loads(result.stdout.strip())
            successful_imports = [(name, version) for name, success, version in test_results if success]
            failed_imports = [(name, error) for name, success, error in test_results if not success]
            if successful_imports:
                import_version = None
                for name, version in successful_imports:
                    if version and version != 'None':
                        import_version = version
                        break
                if not import_version:
                    try:
                        import_version = dist.version
                    except:
                        import_version = 'unknown'
                return {'importable': True, 'version': import_version, 'successful_modules': [name for name, _ in successful_imports], 'failed_modules': [name for name, _ in failed_imports] if failed_imports else []}
            else:
                return {'importable': False, 'error': f'All import attempts failed: {dict(failed_imports)}', 'attempted_modules': import_candidates}
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            error_msg = e.stderr.strip() if hasattr(e, 'stderr') and e.stderr else str(e)
            return {'importable': False, 'error': _('Subprocess failed: {}').format(error_msg), 'attempted_modules': import_candidates}

    def _get_import_candidates(self, dist: importlib.metadata.Distribution, package_name: str) -> List[str]:
        """
        Get the authoritative list of import candidates for a package.
        Uses multiple strategies in order of reliability.
        """
        candidates = []
        try:
            if hasattr(dist, 'read_text'):
                top_level_content = dist.read_text('top_level.txt')
                if top_level_content:
                    candidates.extend([line.strip() for line in top_level_content.strip().split('\n') if line.strip()])
        except Exception:
            pass
        if not candidates:
            candidates.extend(self._parse_record_for_modules(dist))
        if not candidates:
            candidates.extend(self._generate_import_heuristics(package_name))
        if not candidates:
            candidates.append(package_name.replace('-', '_'))
        seen = set()
        unique_candidates = []
        for candidate in candidates:
            if candidate not in seen:
                seen.add(candidate)
                unique_candidates.append(candidate)
        return unique_candidates

    def _parse_record_for_modules(self, dist: importlib.metadata.Distribution) -> List[str]:
        """
        Parse the RECORD file to identify top-level modules.
        """
        candidates = []
        try:
            if hasattr(dist, 'read_text'):
                record_content = dist.read_text('RECORD')
                if record_content:
                    import os
                    top_level_dirs = set()
                    for line in record_content.strip().split('\n'):
                        if line.strip():
                            file_path = line.split(',')[0]
                            parts = file_path.split('/')
                            if parts and (not parts[0].endswith('.dist-info')):
                                top_part = parts[0]
                                if '.' not in top_part or top_part.endswith('.py'):
                                    module_name = top_part.replace('.py', '')
                                    if module_name and (not module_name.startswith('_')):
                                        top_level_dirs.add(module_name)
                    candidates.extend(sorted(top_level_dirs))
        except Exception:
            pass
        return candidates

    def _generate_import_heuristics(self, package_name: str) -> List[str]:
        """
        Generate smart import candidates based on package name patterns.
        """
        candidates = []
        if '.' in package_name:
            candidates.append(package_name)
            candidates.append(package_name.split('.')[0])
        underscore_name = package_name.replace('-', '_')
        if underscore_name != package_name:
            candidates.append(underscore_name)
        if package_name.startswith('python-'):
            candidates.append(package_name[7:])
            candidates.append(package_name[7:].replace('-', '_'))
        if package_name.endswith('-python'):
            candidates.append(package_name[:-7])
            candidates.append(package_name[:-7].replace('-', '_'))
        common_mappings = {'beautifulsoup4': ['bs4'], 'pillow': ['PIL'], 'pyyaml': ['yaml'], 'msgpack-python': ['msgpack'], 'protobuf': ['google.protobuf', 'google'], 'python-dateutil': ['dateutil'], 'setuptools-scm': ['setuptools_scm']}
        canonical = canonicalize_name(package_name)
        if canonical in common_mappings:
            candidates.extend(common_mappings[canonical])
        return candidates

    def _check_binary_integrity(self, bin_path: str) -> Dict:
        if not os.path.exists(bin_path):
            return {'exists': False}
        integrity_report = {'exists': True, 'size': os.path.getsize(bin_path), 'is_elf': False, 'valid_shebang': self._has_valid_shebang(bin_path)}
        try:
            with open(bin_path, 'rb') as f:
                if f.read(4) == b'\x7fELF':
                    integrity_report['is_elf'] = True
        except Exception:
            pass
        return integrity_report

    def _has_valid_shebang(self, path: str) -> bool:
        try:
            with open(path, 'r', errors='ignore') as f:
                return f.readline().startswith('#!')
        except Exception:
            return False

    def _find_package_files(self, dist: importlib.metadata.Distribution) -> Dict:
        """
        FIXED: Authoritatively finds files belonging to the specific distribution.
        """
        files = {'binaries': []}
        if not dist or not dist.files:
            return files
        for file_path in dist.files:
            try:
                abs_path = dist.locate_file(file_path)
                if 'bin' in file_path.parts or 'Scripts' in file_path.parts:
                    if abs_path and abs_path.exists() and os.access(abs_path, os.X_OK):
                        files['binaries'].append(str(abs_path))
            except (FileNotFoundError, NotADirectoryError):
                continue
        return files

    def _run_bulk_security_check(self, packages: Dict[str, str]):
        reqs_file_path = '/tmp/bulk_safety_reqs.txt'
        try:
            with open(reqs_file_path, 'w') as f:
                for name, version in packages.items():
                    f.write(f'{name}=={version}\n')
            python_exe = self.config.get('python_executable', sys.executable)
            result = subprocess.run([python_exe, '-m', 'safety', 'check', '-r', reqs_file_path, '--json'], capture_output=True, text=True, timeout=120)
            if result.stdout:
                self.security_report = json.loads(result.stdout)
        except Exception as e:
            safe_print(_('    ⚠️ Bulk security scan failed: {}').format(e))
        finally:
            if os.path.exists(reqs_file_path):
                os.remove(reqs_file_path)

    def _get_security_info(self, package_name: str) -> Dict:
        """
        FIXED: Parses the security report from `safety`, correctly handling both the
        legacy object format ({'pkg': [...]}) and the modern list format ([...]).
        """
        c_name = canonicalize_name(package_name)
        vulnerabilities = []
        if isinstance(self.security_report, dict):
            vulnerabilities = self.security_report.get(c_name, [])
        elif isinstance(self.security_report, list):
            vulnerabilities = [vuln for vuln in self.security_report if isinstance(vuln, dict) and canonicalize_name(vuln.get('package_name', '')) == c_name]
        return {'audit_status': 'checked_in_bulk', 'issues_found': len(vulnerabilities), 'report': vulnerabilities}

    def _generate_checksum(self, metadata: Dict) -> str:
        core_data = {'Version': metadata.get('Version'), 'dependencies': metadata.get('dependencies'), 'help_text': metadata.get('help_text')}
        data_string = json.dumps(core_data, sort_keys=True)
        return hashlib.sha256(data_string.encode('utf-8')).hexdigest()

    def _get_help_output(self, executable_path: str) -> Dict:
        if not os.path.exists(executable_path):
            return {'help_text': 'Executable not found.'}
        for flag in ['--help', '-h']:
            try:
                result = subprocess.run([executable_path, flag], capture_output=True, text=True, timeout=3, errors='ignore')
                output = (result.stdout or result.stderr).strip()
                if output and 'usage:' in output.lower():
                    return {'help_text': output[:5000]}
            except Exception:
                continue
        return {'help_text': 'No valid help output captured.'}

    def _analyze_cli(self, help_text: str) -> Dict:
        if not help_text or 'No valid help' in help_text:
            return {}
        analysis = {'common_flags': [], 'subcommands': []}
        lines = help_text.split('\n')
        command_regex = re.compile('^\\s*([a-zA-Z0-9_-]+)\\s{2,}(.*)')
        in_command_section = False
        for line in lines:
            if re.search('^(commands|available commands):', line, re.IGNORECASE):
                in_command_section = True
                continue
            if in_command_section and (not line.strip()):
                in_command_section = False
                continue
            if in_command_section:
                match = command_regex.match(line)
                if match:
                    command_name = match.group(1).strip()
                    if not command_name.startswith('-'):
                        analysis['subcommands'].append({'name': command_name, 'description': match.group(2).strip()})
        if not analysis['subcommands']:
            analysis['subcommands'] = [{'name': cmd, 'description': 'N/A'} for cmd in self._fallback_analyze_cli(lines)]
        analysis['common_flags'] = list(set(re.findall('--[a-zA-Z0-9][a-zA-Z0-9-]+', help_text)))
        return analysis

    def _fallback_analyze_cli(self, lines: list) -> list:
        subcommands = []
        in_command_section = False
        for line in lines:
            if re.search('commands:', line, re.IGNORECASE):
                in_command_section = True
                continue
            if in_command_section and line.strip():
                match = re.match('^\\s*([a-zA-Z0-9_-]+)', line)
                if match:
                    subcommands.append(match.group(1))
            elif in_command_section and (not line.strip()):
                in_command_section = False
        return list(set(subcommands))

    def _get_distribution(self, package_name: str, version: str=None):
        try:
            dist = importlib.metadata.distribution(package_name)
            if version is None or dist.version == version:
                return dist
        except importlib.metadata.PackageNotFoundError:
            pass
        if version:
            bubble_path = Path(self.config['multiversion_base']) / f'{package_name}-{version}'
            return self._find_distribution_at_path(package_name, version, bubble_path)
        return None

    def _enrich_from_site_packages(self, name: str, version: str=None) -> Dict:
        enriched_data = {}
        guesses = set([name, name.lower().replace('-', '_')])
        base_path = Path(get_site_packages_path())
        if version:
            base_path = Path(self.config['multiversion_base']) / f'{name}-{version}'
        for g in guesses:
            pkg_path = base_path / g
            if pkg_path.is_dir():
                readme_path = next((p for p in pkg_path.glob('[Rr][Ee][Aa][Dd][Mm][Ee].*') if p.is_file()), None)
                if readme_path:
                    enriched_data['readme_snippet'] = readme_path.read_text(encoding='utf-8', errors='ignore')[:500]
                license_path = next((p for p in pkg_path.glob('[Ll][Ii][Cc][Ee][Nn][Ss]*') if p.is_file()), None)
                if license_path:
                    enriched_data['license_text'] = license_path.read_text(encoding='utf-8', errors='ignore')[:500]
                return enriched_data
        return {}

    def _flatten_dict(self, d: Dict, parent_key: str='', sep: str='.') -> Dict:
        items = []
        for k, v in d.items():
            new_key = f'{parent_key}{sep}{k}' if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, str(v)))
        return dict(items)
if __name__ == '__main__':
    import json
    from pathlib import Path
    import hashlib
    from omnipkg.cache import SQLiteCacheClient
    safe_print(_('🚀 Starting omnipkg Metadata Builder v12 (SQLite/Redis Edition)...'))
    try:
        config_path = Path.home() / '.config' / 'omnipkg' / 'config.json'
        with open(config_path, 'r') as f:
            full_config = json.load(f)
        env_id_from_os = os.environ.get('OMNIPKG_ENV_ID_OVERRIDE')
        if env_id_from_os:
            env_id = env_id_from_os
            safe_print(_('   (Inherited environment ID: {})').format(env_id))
        else:
            current_dir = Path(sys.executable).resolve().parent
            venv_path = Path(sys.prefix)
            while current_dir != current_dir.parent:
                if (current_dir / 'pyvenv.cfg').exists():
                    venv_path = current_dir
                    break
                current_dir = current_dir.parent
            env_id = hashlib.md5(str(venv_path.resolve()).encode()).hexdigest()[:8]
            safe_print(_('   (Calculated environment ID: {})').format(env_id))
        config = full_config['environments'][env_id]
    except (FileNotFoundError, KeyError) as e:
        safe_print(f'❌ CRITICAL: Could not load omnipkg configuration for this environment (ID: {env_id}). Error: {e}. Aborting.')
        sys.exit(1)
    gatherer = omnipkgMetadataGatherer(config=config, env_id=env_id, force_refresh='--force' in sys.argv)
    try:
        cache_dir = Path(config.get('cache_dir', Path.home() / '.cache' / 'omnipkg'))
        db_path = cache_dir / f'omnipkg_cache_{env_id}.db'
        safe_print(_('   (Using SQLite cache at: {})').format(db_path))
        gatherer.cache_client = SQLiteCacheClient(db_path=db_path)
        if gatherer.cache_client and gatherer.cache_client.ping():
            targeted_packages = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
            if targeted_packages:
                gatherer.run(targeted_packages=targeted_packages)
            else:
                gatherer.run()
            safe_print(_('\n🎉 Metadata building complete!'))
        else:
            safe_print(_('❌ Failed to connect to SQLite cache. Aborting.'))
            sys.exit(1)
    except Exception as e:
        safe_print(_('\n❌ An unexpected error occurred during metadata build: {}').format(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)