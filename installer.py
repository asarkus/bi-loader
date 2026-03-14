import subprocess
import sys
import os
import zipfile
import tempfile
import re
from pathlib import Path


class WheelInstaller:
    def __init__(self):
        self.python_exe = sys.executable

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
        in_requires = False
        for line in content.split('\n'):
            if line.startswith('Requires-Dist:'):
                dep = line.split('Requires-Dist:')[1].strip()
                dep = re.sub(r'\s*\[.*?\]', '', dep)
                dep = re.sub(r'\s*;.*', '', dep)
                dep = dep.split(',')[0].strip()
                if dep:
                    deps.append(dep)
        return {'dependencies': deps}

    def install_whl(self, whl_path, callback=None):
        whl_path = str(Path(whl_path).resolve())
        
        def log(msg):
            if callback:
                callback(msg)
            print(msg)

        log(f"Установка: {Path(whl_path).name}")

        metadata = self.extract_metadata(whl_path)
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
                log(f"Ошибка установки {Path(whl_path).name}:")
                log(result.stderr)
                return False
            
            log(f"✓ {Path(whl_path).name} установлен")
            
        except Exception as e:
            log(f"Ошибка: {e}")
            return False

        if dependencies:
            log(f"Установка зависимостей для {Path(whl_path).name}...")
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
                        log(f"    ⚠ {dep} (не найден или ошибка)")
                except Exception as e:
                    log(f"    Ошибка установки {dep}: {e}")

        return True

    def install_multiple(self, whl_paths, callback=None):
        results = []
        for whl_path in whl_paths:
            if whl_path.lower().endswith('.whl'):
                success = self.install_whl(whl_path, callback)
                results.append((whl_path, success))
        return results
