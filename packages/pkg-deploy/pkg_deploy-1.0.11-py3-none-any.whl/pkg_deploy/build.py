import os
import sys
import copy
import logging
import textwrap
import subprocess
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
from tomlkit.toml_document import TOMLDocument

from .utils import save_config, is_uv_venv, ensure_uv_installed


logger = logging.getLogger(__name__)


@dataclass
class DeployConfig:
    package_name: str
    project_dir: Path
    package_dir: Path
    package_entry: str
    pyproject_path: Path
    version_type: str
    new_version: str
    use_cython: bool
    use_cibuildwheel: bool
    is_uv_venv: bool
    repository_name: str
    repository_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    dry_run: bool = False


class BuildStrategy(ABC):

    @staticmethod
    def build_cmd(config: DeployConfig):
        if config.use_cibuildwheel:
            cmd = ['cibuildwheel', '--output-dir', 'dist']
        elif is_uv_venv():
            ensure_uv_installed()
            cmd = ["uv", "build", "--wheel"]
        else:
            cmd = [sys.executable, "-m", "build", "--wheel"]
        return cmd

    @abstractmethod
    def build(self, config: DeployConfig, toml_config: TOMLDocument) -> bool:
        pass


class StandardBuildStrategy(BuildStrategy):

    def build(self, config: DeployConfig, toml_config: TOMLDocument) -> bool:
        cmd = self.build_cmd(config=config)
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=config.project_dir
        )
        if result.returncode != 0:
           raise ValueError(f"Build failed, \nstdout: {result.stdout}\nstderr: {result.stderr}")
        logger.info("Standard build completed successfully")
        return True

class CythonBuildStrategy(BuildStrategy):

    def build(self, config: DeployConfig, toml_config: TOMLDocument) -> bool:
        try:
            self.prepare_pyproject_for_cython_build(config.project_dir, toml_config)
            self.create_setup_py_for_cython(config, toml_config)
            cmd = self.build_cmd(config=config)
            logger.info(f"Running Cython build: {' '.join(cmd)}")
            env = os.environ.copy()
            env['CYTHONIZE'] = '1'
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            env["CIBW_BUILD_VERBOSITY"] = "1"
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                env=env,
                cwd=config.project_dir
            )
            if result.returncode != 0:
                raise ValueError(f"Cython build failed, \nstdout: {result.stdout}\nstderr: {result.stderr}")
            logger.info("Cython build completed successfully")
            return True
        except Exception as e:
            logger.error(f"Cython build error: {e}")
            return False
        finally:
            if not config.dry_run:
                self.restore_pyproject_toml(project_dir=config.project_dir, original_toml_config=toml_config)

    @staticmethod
    def prepare_pyproject_for_cython_build(project_dir: Path, toml_config: TOMLDocument):
        pyproject_path = project_dir / "pyproject.toml"
        if pyproject_path.exists():
            new_config = copy.deepcopy(toml_config)

            # Add Cython build dependency
            if 'build-system' not in new_config:
                new_config['build-system'] = {}

            if 'requires' not in new_config['build-system']:
                new_config['build-system']['requires'] = []

            cython_deps = ['setuptools', 'Cython']
            requires = new_config['build-system']['requires']
            for dep in cython_deps:
                if not any(req.startswith(dep) for req in requires):
                    new_config['build-system']['requires'].append(dep)

            if 'build-backend' not in new_config['build-system'] or new_config['build-system'][
                'build-backend'] != 'setuptools.build_meta':
                new_config['build-system']['build-backend'] = 'setuptools.build_meta'
            save_config(new_config, pyproject_path)

    @staticmethod
    def restore_pyproject_toml(project_dir: Path, original_toml_config: TOMLDocument):
        pyproject_path = project_dir / "pyproject.toml"
        if original_toml_config:
            save_config(original_toml_config, pyproject_path)
            logger.info("Restored original pyproject.toml")

    @staticmethod
    def create_setup_py_for_cython(config: DeployConfig, toml_config: TOMLDocument):
        setup_py_path = config.project_dir / "setup.py"
        if setup_py_path.exists():
            raise FileExistsError(
                f"Cannot build Cython code: setup.py already exists at {setup_py_path}\n"
                f"\n"
                f"In Cython build mode, this tool generates its own setup.py file optimized for "
                f"Cython compilation. An existing setup.py would be overwritten, potentially "
                f"causing build errors or losing your custom configuration.\n"
                f"\n"
                f"To proceed with Cython build:\n"
                f"  1. Migrate your setup.py settings to pyproject.toml:\n"
                f"     - Move dependencies to [project.dependencies]\n"
                f"     - Move metadata (name, version, description) to [project]\n"
                f"     - Move entry points to [project.scripts]\n"
                f"     - Move build configuration to [build-system] or [tool] sections\n"
                f"  2. Back up your current setup.py: mv setup.py setup.py.backup\n"
                f"  3. Then retry the Cython build\n"
                f"\n"
                f"Alternative (quick start):\n"
                f"  - Just backup setup.py now: mv setup.py setup.py.backup\n"
                f"  - Retry the build, then migrate settings later by comparing\n"
                f"    setup.py.backup with the generated pyproject.toml\n"
                f"\n"
                f"Note: Modern Python projects use pyproject.toml (PEP 518/621) for "
                f"configuration instead of setup.py. This approach provides better "
                f"tooling integration and is the recommended standard."
            )

        if "authors" in toml_config["project"]:
            author_names = ", ".join(p["name"] for p in toml_config["project"]["authors"] if "name" in p)
            author_emails = ", ".join(p["email"] for p in toml_config["project"]["authors"] if "email" in p)
        else:
            author_names = ""
            author_emails = ""
        if "scripts" in toml_config["project"]:
            entry_points = [f"{k}={v}" for k, v in toml_config["project"]["scripts"].items()]
        else:
            entry_points = []
        setup_py_content = textwrap.dedent(f'''
        import glob
        from Cython.Build import cythonize
        from setuptools import setup, find_packages
        from setuptools.dist import Distribution
        from setuptools.command.build_py import build_py as _build_py
    
        py_files = glob.glob("{config.package_entry}/**/*.py", recursive=True)
        py_files = [f for f in py_files if not f.endswith("__init__.py")]
    
        class build_py(_build_py):
            def find_package_modules(self, package, package_dir):
                modules = super().find_package_modules(package, package_dir)
                if self.distribution.ext_modules:
                    # Get the list of compiled module names
                    compiled_modules = {{ext.name for ext in self.distribution.ext_modules}}
                    # Filter out the modules that are compiled
                    modules = [
                        (pkg, mod, file) for (pkg, mod, file) in modules
                        if f"{{pkg}}.{{mod}}" not in compiled_modules
                    ]
                return modules
    
        class BinaryDistribution(Distribution):
            def has_ext_modules(self):
                return True
    
        setup(
            name="{toml_config["project"]["name"]}",
            version="{toml_config["project"]["version"]}",
            {f"author='{author_names}'," if author_names else ""}
            {f"author_email='{author_emails}'," if author_emails else ""}
            {f"description='{toml_config['project']['description']}'," if toml_config["project"].get("description", "") else ""}
            {f"python_requires='{toml_config['project']['requires-python']}'," if toml_config["project"].get("requires-python") else ""}
            {f"install_requires={toml_config['project']['dependencies']}," if toml_config["project"].get("dependencies") and len(toml_config["project"]["dependencies"]) > 0 else ""}
            entry_points={{
                'console_scripts': {entry_points}
            }},
            packages=find_packages(where="{config.package_entry}"),
            package_dir={{"": "{config.package_entry}"}},
            include_package_data=True,
            ext_modules=cythonize(
                py_files,
                compiler_directives={{'language_level': "3"}},
            ),
            distclass=BinaryDistribution,
            setup_requires=["cython>=3.1"],
            cmdclass={{'build_py': build_py}},
            zip_safe=False
        )
        ''').strip()

        with open(config.project_dir / "setup.py", 'w', encoding='utf-8') as f:
            f.write(setup_py_content)
