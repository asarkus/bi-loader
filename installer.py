import subprocess
import sys
import zipfile
import re
import json
from pathlib import Path


def parse_version(v):
    """Parse version string to comparable tuple"""
    v = v.strip()
    parts = re.split(r'[.+_-]', v)
    try:
        return tuple(int(p) if p.isdigit() else p for p in parts if p)
    except:
        return (v,)


class WheelInstaller:
    def __init__(self):
        self.python_exe = sys.executable

    def validate_whl(self, whl_path):
        """
        Валидация WHL файла
        Возвращает: (valid: bool, errors: list, warnings: list)
        """
        whl_path = str(Path(whl_path))
        errors = []
        warnings = []
        
        path = Path(whl_path)
        
        if not path.exists():
            errors.append(f"File not found: {whl_path}")
            return False, errors, warnings
        
        if not whl_path.lower().endswith('.whl'):
            errors.append("File does not have .whl extension")
        
        filename = path.name
        
        whl_pattern = r'^[a-zA-Z0-9_\-]+\-[0-9a-zA-Z_\.\+\-]+\-cp[0-9]+\-abi[0-9]+\-win_[a-z0-9_]+\.whl$'
        if not re.match(whl_pattern, filename):
            warnings.append(f"Non-standard filename format: {filename}")
        
        try:
            with zipfile.ZipFile(whl_path, 'r') as z:
                has_metadata = False
                has_wheel = False
                
                for name in z.namelist():
                    if name.endswith('.dist-info/METADATA'):
                        has_metadata = True
                    if name.endswith('.dist-info/WHEEL'):
                        has_wheel = True
                
                if not has_metadata:
                    errors.append("METADATA file not found in archive")
                if not has_wheel:
                    warnings.append("WHEEL file not found in archive")
                
                if has_metadata:
                    for name in z.namelist():
                        if name.endswith('.dist-info/METADATA'):
                            with z.open(name) as f:
                                content = f.read().decode('utf-8', errors='ignore')
                                metadata = self._parse_metadata(content)
                                
                                if not metadata.get('name'):
                                    warnings.append("Package name not found in METADATA")
                                if not metadata.get('version'):
                                    warnings.append("Package version not found in METADATA")
                                
                                deps = metadata.get('dependencies', [])
                                if deps:
                                    warnings.append(f"Dependencies: {', '.join(deps[:3])}{'...' if len(deps) > 3 else ''}")
        
        except zipfile.BadZipFile:
            errors.append("Invalid ZIP archive")
        except Exception as e:
            errors.append(f"Error reading archive: {str(e)}")
        
        valid = len(errors) == 0
        return valid, errors, warnings

    def parse_requirements(self, file_path):
        """
        Парсит файл requirements.txt
        Поддержка: ==, >=, <=, >, <, ~=, !=
        Игнорирует комментарии и пустые строки
        """
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    if not line or line.startswith('#'):
                        continue
                    
                    line = re.sub(r'#.*', '', line).strip()
                    
                    if not line:
                        continue
                    
                    match = re.match(r'^([a-zA-Z0-9_\-]+)(.*)$', line)
                    if match:
                        pkg_name = match.group(1)
                        version_spec = match.group(2).strip()
                        
                        dependencies.append({
                            'name': pkg_name,
                            'spec': version_spec
                        })
        
        except Exception as e:
            return [], str(e)
        
        return dependencies, None

    def install_from_requirements(self, file_path, callback=None):
        """
        Устанавливает пакеты из requirements.txt по очереди
        """
        def log(msg):
            if callback:
                callback(msg)
            print(msg)
        
        log(f"Reading requirements from: {file_path}")
        
        dependencies, error = self.parse_requirements(file_path)
        
        if error:
            log(f"Error parsing requirements: {error}")
            return False, [error]
        
        if not dependencies:
            log("No dependencies found")
            return True, []
        
        log(f"Found {len(dependencies)} packages to install")
        
        errors = []
        for i, dep in enumerate(dependencies, 1):
            pkg_name = dep['name']
            spec = dep['spec']
            
            log(f"[{i}/{len(dependencies)}] Installing: {pkg_name}{spec}")
            
            try:
                cmd = [self.python_exe, '-m', 'pip', 'install', f"{pkg_name}{spec}"]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
                
                if result.returncode == 0:
                    log(f"  ✓ {pkg_name}{spec} installed")
                else:
                    error_msg = result.stderr or result.stdout
                    log(f"  ✗ Error: {error_msg[:100]}...")
                    errors.append(f"{pkg_name}: {error_msg[:50]}")
            
            except Exception as e:
                log(f"  ✗ Exception: {str(e)}")
                errors.append(f"{pkg_name}: {str(e)}")
        
        success = len(errors) == 0
        return success, errors

    def extract_metadata(self, whl_path):
        try:
            with zipfile.ZipFile(whl_path, 'r') as z:
                for name in z.namelist():
                    if name.endswith('.dist-info/METADATA'):
                        with z.open(name) as f:
                            content = f.read().decode('utf-8', errors='ignore')
                            return self._parse_metadata(content)
        except Exception as e:
            return {}
        return {}

    def _parse_metadata(self, content):
        deps = []
        name = version = ""
        for line in content.split('\n'):
            if line.startswith('Name:'):
                name = line.split('Name:')[1].strip()
            if line.startswith('Version:'):
                version = line.split('Version:')[1].strip()
            if line.startswith('Requires-Dist:'):
                dep = line.split('Requires-Dist:')[1].strip()
                dep = re.sub(r'\s*\[.*?\]', '', dep)
                dep = re.sub(r'\s*;.*', '', dep)
                dep = dep.split(',')[0].strip()
                if dep:
                    deps.append(dep)
        return {'name': name, 'version': version, 'dependencies': deps}

    def get_package_info_from_whl(self, whl_path):
        metadata = self.extract_metadata(whl_path)
        return metadata.get('name', ''), metadata.get('version', '')

    def install_whl(self, whl_path, callback=None):
        whl_path = str(Path(whl_path).resolve())
        
        def log(msg):
            if callback:
                callback(msg)
            print(msg)

        log(f"Installing: {Path(whl_path).name}")

        metadata = self.extract_metadata(whl_path)
        package_name = metadata.get('name', Path(whl_path).stem.split('-')[0])
        package_version = metadata.get('version', 'unknown')
        dependencies = metadata.get('dependencies', [])

        cmd = [self.python_exe, '-m', 'pip', 'install', '--force-reinstall', '--no-deps', whl_path]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode != 0:
                log(f"Error installing {Path(whl_path).name}:")
                log(result.stderr)
                return False, None
            
            log(f"✓ {Path(whl_path).name} installed")
            
        except Exception as e:
            log(f"Error: {e}")
            return False, None

        if dependencies:
            log(f"Installing dependencies for {Path(whl_path).name}...")
            for dep in dependencies:
                try:
                    log(f"  → {dep}")
                    result = subprocess.run(
                        [self.python_exe, '-m', 'pip', 'install', dep],
                        capture_output=True,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                    )
                    if result.returncode == 0:
                        log(f"    ✓ {dep}")
                    else:
                        log(f"    ⚠ {dep} (not found or error)")
                except Exception as e:
                    log(f"    Error installing {dep}: {e}")

        return True, {'name': package_name, 'version': package_version}

    def install_multiple(self, whl_paths, callback=None):
        results = []
        for whl_path in whl_paths:
            if whl_path.lower().endswith('.whl'):
                success, info = self.install_whl(whl_path, callback)
                results.append((whl_path, success, info))
        return results

    def list_installed_packages(self, callback=None):
        def log(msg):
            if callback:
                callback(msg)
        
        packages = []
        try:
            result = subprocess.run(
                [self.python_exe, '-m', 'pip', 'list', '--format=json'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode == 0:
                packages = json.loads(result.stdout)
        except Exception as e:
            log(f"Error listing packages: {e}")
        
        return packages

    def get_package_version(self, package_name, callback=None):
        def log(msg):
            if callback:
                callback(msg)
        
        try:
            result = subprocess.run(
                [self.python_exe, '-m', 'pip', 'show', package_name],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Version:'):
                        return line.split('Version:')[1].strip()
        except Exception as e:
            log(f"Error getting version: {e}")
        
        return None

    def uninstall_package(self, package_name, callback=None):
        def log(msg):
            if callback:
                callback(msg)
        
        log(f"Uninstalling: {package_name}")
        
        try:
            result = subprocess.run(
                [self.python_exe, '-m', 'pip', 'uninstall', '-y', package_name],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode == 0:
                log(f"✓ {package_name} uninstalled")
                return True
            else:
                log(f"✗ Error uninstalling {package_name}")
                log(result.stderr)
                return False
        except Exception as e:
            log(f"Error: {e}")
            return False

    def check_package_update(self, package_name, callback=None):
        def log(msg):
            if callback:
                callback(msg)
        
        current_version = self.get_package_version(package_name, callback)
        if not current_version:
            return None
        
        try:
            result = subprocess.run(
                [self.python_exe, '-m', 'pip', 'index', 'versions', package_name],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode == 0:
                output = result.stdout
                match = re.search(r'Available versions:\s*([\d.,\s]+)', output)
                if match:
                    versions_str = match.group(1)
                    versions = [v.strip() for v in versions_str.split(',') if v.strip()]
                    
                    if versions:
                        latest = max(versions, key=parse_version)
                        has_update = parse_version(latest) > parse_version(current_version)
                        
                        return {
                            'name': package_name,
                            'current': current_version,
                            'latest': latest,
                            'has_update': has_update
                        }
        except Exception as e:
            log(f"Error checking update: {e}")
        
        return {'name': package_name, 'current': current_version, 'latest': current_version, 'has_update': False}

    def update_package(self, package_name, callback=None):
        def log(msg):
            if callback:
                callback(msg)
        
        log(f"Updating: {package_name}")
        
        try:
            result = subprocess.run(
                [self.python_exe, '-m', 'pip', 'install', '--upgrade', package_name],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            if result.returncode == 0:
                log(f"✓ {package_name} updated")
                return True
            else:
                log(f"✗ Error updating {package_name}")
                log(result.stderr)
                return False
        except Exception as e:
            log(f"Error: {e}")
            return False

    def check_all_updates(self, callback=None):
        def log(msg):
            if callback:
                callback(msg)
        
        log("Checking for updates...")
        packages = self.list_installed_packages(callback)
        updates = []
        
        for pkg in packages:
            pkg_name = pkg['name']
            update_info = self.check_package_update(pkg_name, callback)
            if update_info and update_info.get('has_update'):
                updates.append(update_info)
        
        return updates
