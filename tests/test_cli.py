import os
import json
import unittest
import tempfile
from pathlib import Path

# Core imports
from pym.venv import find_venv_root, get_venv_bin_dir, get_venv_python
from pym.project import load_pyckage_json, save_pyckage_json, update_pyckage_dependencies
from pym.runner import load_dotenv
from pym.engine import caret_to_pep440, sanitize_version_specifiers

class TestPyCkCore(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for file operations
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_path = Path(self.test_dir.name).resolve()

    def tearDown(self):
        # Clean up temp directory
        self.test_dir.cleanup()

    def test_find_venv_root_fallback(self):
        """
        Verify find_venv_root defaults to local folder candidate if none found in parents.
        """
        root = find_venv_root(self.test_path)
        self.assertEqual(root, self.test_path / ".venv")

    def test_get_venv_bin_dir(self):
        """
        Verify venv bin path resolves correctly depending on OS platform.
        """
        venv_path = self.test_path / ".venv"
        bin_dir = get_venv_bin_dir(venv_path)
        if os.name == "nt":
            self.assertEqual(bin_dir, venv_path / "Scripts")
        else:
            self.assertEqual(bin_dir, venv_path / "bin")

    def test_pyckage_json_load_and_save(self):
        """
        Verify pyckage.json schema load, save, and field order formatting.
        """
        json_file = self.test_path / "pyckage.json"
        
        # Test Default
        data = load_pyckage_json(json_file)
        self.assertEqual(data["name"], "my-project")
        self.assertEqual(data["version"], "0.1.0")
        
        # Test Custom Save
        custom_data = {
            "name": "custom-app",
            "version": "1.0.0",
            "scripts": {"dev": "python api.py"},
            "dependencies": {"fastapi": "^0.110.0"}
        }
        save_pyckage_json(custom_data, json_file)
        
        loaded = load_pyckage_json(json_file)
        self.assertEqual(loaded["name"], "custom-app")
        self.assertEqual(loaded["version"], "1.0.0")
        self.assertEqual(loaded["dependencies"]["fastapi"], "^0.110.0")
        self.assertEqual(loaded["scripts"]["dev"], "python api.py")

    def test_dotenv_parser(self):
        """
        Verify load_dotenv correctly parses environment variables, removes trailing comments,
        and handles single/double quotes.
        """
        env_file = self.test_path / ".env"
        env_content = """
# Mock Env Config
PORT=8080
ENVIRONMENT="development"
DB_URL='postgres://user:pass@host:5432/db'
DEBUG=True # Toggle debug flag
"""
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(env_content)
            
        env_vars = load_dotenv(env_file)
        
        self.assertEqual(env_vars.get("PORT"), "8080")
        self.assertEqual(env_vars.get("ENVIRONMENT"), "development")
        self.assertEqual(env_vars.get("DB_URL"), "postgres://user:pass@host:5432/db")
        self.assertEqual(env_vars.get("DEBUG"), "True")
        self.assertNotIn("Toggle debug flag", env_vars.get("DEBUG"))

    def test_caret_version_translation(self):
        """
        Verify that NPM caret specifiers (^3.0.0, ^0.3.0, ^0.0.3) mathematical conversions
        translate correctly into PEP 440 constraints.
        """
        # Major version > 0
        self.assertEqual(caret_to_pep440("flask", "^3.0.0"), "flask>=3.0.0,<4.0.0")
        self.assertEqual(caret_to_pep440("requests", "^2.31.0"), "requests>=2.31.0,<3.0.0")
        
        # Major version = 0, minor > 0
        self.assertEqual(caret_to_pep440("ruff", "^0.3.0"), "ruff>=0.3.0,<0.4.0")
        self.assertEqual(caret_to_pep440("click", "^0.8.2"), "click>=0.8.2,<0.9.0")
        
        # Major version = 0, minor = 0
        self.assertEqual(caret_to_pep440("secret", "^0.0.3"), "secret==0.0.4")
        
        # Non-caret or wildcard
        self.assertEqual(caret_to_pep440("numpy", ">=1.20"), "numpy>=1.20")
        
        # Bulk sanitization
        packages = ["flask^3.0.0", "ruff^0.3.0", "requests"]
        sanitized = sanitize_version_specifiers(packages)
        self.assertEqual(sanitized, ["flask>=3.0.0,<4.0.0", "ruff>=0.3.0,<0.4.0", "requests"])

if __name__ == "__main__":
    unittest.main()
