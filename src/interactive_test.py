"""
Simple, clean interactive bot tester for Flask bots.
Loads the bot module, captures sent messages, and provides a test interface.
"""

import os
import sys
import importlib.util
import time
import threading
import uuid
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

# Setup logging - only use file handler when frozen to avoid GUI conflicts
import logging

# Create a simple logger that uses print() when frozen (PyInstaller)
class SimpleLogger:
    def info(self, msg):
        print(f"[INFO] {msg}")
    def warning(self, msg):
        print(f"[WARNING] {msg}")
    def error(self, msg, exc_info=False):
        print(f"[ERROR] {msg}")
        if exc_info:
            import traceback
            traceback.print_exc()
    def debug(self, msg):
        print(f"[DEBUG] {msg}")

if getattr(sys, 'frozen', False):
    # Running from PyInstaller - use simple print-based logging
    _logger = SimpleLogger()
else:
    # Running from source - use file logging
    _log_file = Path.home() / "tester_debug.log"
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler(_log_file),
            logging.StreamHandler()
        ]
    )
    _logger = logging.getLogger(__name__)

_logger.info("Interactive Tester starting")

# Patch subprocess to log calls (skip if frozen to reduce overhead)
if not getattr(sys, 'frozen', False):
    import subprocess as _subprocess_module
    _original_popen = _subprocess_module.Popen
    _original_run = _subprocess_module.run
    _original_check_output = _subprocess_module.check_output

    def _logged_popen(*args, **kwargs):
        _logger.warning(f"SUBPROCESS POPEN CALLED: args={args}, kwargs={kwargs}")
        import traceback
        _logger.warning("Traceback:\n" + "".join(traceback.format_stack()))
        return _original_popen(*args, **kwargs)

    def _logged_run(*args, **kwargs):
        _logger.warning(f"SUBPROCESS RUN CALLED: args={args}, kwargs={kwargs}")
        import traceback
        _logger.warning("Traceback:\n" + "".join(traceback.format_stack()))
        return _original_run(*args, **kwargs)

    def _logged_check_output(*args, **kwargs):
        _logger.warning(f"SUBPROCESS CHECK_OUTPUT CALLED: args={args}, kwargs={kwargs}")
        import traceback
        _logger.warning("Traceback:\n" + "".join(traceback.format_stack()))
        return _original_check_output(*args, **kwargs)

    _subprocess_module.Popen = _logged_popen
    _subprocess_module.run = _logged_run
    _subprocess_module.check_output = _logged_check_output

    # Also patch os.startfile on Windows
    if hasattr(os, 'startfile'):
        _original_startfile = os.startfile
        def _logged_startfile(path, *args, **kwargs):
            _logger.warning(f"OS.STARTFILE CALLED: path={path}, args={args}, kwargs={kwargs}")
            import traceback
            _logger.warning("Traceback:\n" + "".join(traceback.format_stack()))
            return _original_startfile(path, *args, **kwargs)
        os.startfile = _logged_startfile
else:
    print("[STARTUP] Running from frozen executable - subprocess logging disabled")

try:
    from PIL import Image
except Exception:
    Image = None


def _find_flask_app_in_folder(folder_path):
    """
    Find Flask app file in a folder (looks for app.py, main.py, bot.py, etc.).
    
    Args:
        folder_path: Path to folder to search
    
    Returns:
        Path to Flask app file, or None if not found
    """
    candidates = ['app.py', 'main.py', 'bot.py', '__main__.py']
    
    for candidate in candidates:
        app_path = os.path.join(folder_path, candidate)
        if os.path.exists(app_path):
            return app_path
    
    # If no candidates found, try any .py file that has Flask app
    for filename in os.listdir(folder_path):
        if filename.endswith('.py') and not filename.startswith('_'):
            filepath = os.path.join(folder_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'Flask' in content or 'app = ' in content:
                        return filepath
            except:
                pass
    
    return None


def _install_requirements(bot_dir):
    """
    Install requirements.txt from bot directory to current venv.
    
    Args:
        bot_dir: Directory containing the bot (to find requirements.txt)
    
    Returns:
        List of installed packages (from requirements.txt)
    """
    import subprocess
    
    requirements_file = os.path.join(bot_dir, "requirements.txt")
    installed = []
    
    if not os.path.exists(requirements_file):
        print(f"[INFO] No requirements.txt found in {bot_dir}")
        return installed
    
    print(f"[INFO] Installing requirements from {requirements_file}...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", requirements_file],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print(f"[INFO] Requirements installed successfully")
            # Parse requirements file to get package names
            try:
                with open(requirements_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            pkg = line.split('==')[0].split('>=')[0].split('<=')[0].strip()
                            if pkg:
                                installed.append(pkg)
            except:
                pass
        else:
            print(f"[WARNING] pip install returned code {result.returncode}")
            if result.stderr:
                print(f"[WARNING] pip stderr: {result.stderr[:500]}")
    except subprocess.TimeoutExpired:
        print(f"[WARNING] Requirements installation timed out")
    except Exception as e:
        print(f"[WARNING] Failed to install requirements: {e}")
    
    return installed


def _get_addon_requirements(bot_dir):
    """
    Scan addon files for ADDON_REQUIRES declarations WITHOUT importing them.
    Parse the files using AST to extract requirements safely.
    
    Args:
        bot_dir: Bot directory (to find addons folder)
    
    Returns:
        List of addon requirement package names
    """
    import ast
    
    addon_requirements = set()
    
    try:
        addons_dir = os.path.join(bot_dir, "addons")
        if not os.path.isdir(addons_dir):
            return []
        
        # Scan addon files WITHOUT importing them
        for filename in os.listdir(addons_dir):
            if filename.startswith('addon_') and filename.endswith('.py'):
                try:
                    addon_path = os.path.join(addons_dir, filename)
                    with open(addon_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse the file using AST
                    tree = ast.parse(content)
                    
                    # Look for ADDON_REQUIRES = [...]
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Assign):
                            for target in node.targets:
                                if isinstance(target, ast.Name) and target.id == 'ADDON_REQUIRES':
                                    if isinstance(node.value, ast.List):
                                        for elt in node.value.elts:
                                            if isinstance(elt, ast.Constant):
                                                req = elt.value
                                                if isinstance(req, str):
                                                    # Normalize package name (strip version specs)
                                                    pkg = req.split('==')[0].split('>=')[0].split('<=')[0].strip()
                                                    if pkg:
                                                        addon_requirements.add(pkg)
                                                        print(f"[INFO] Found addon requirement from {filename}: {pkg}")
                except Exception as e:
                    print(f"[DEBUG] Could not parse {filename} for ADDON_REQUIRES: {e}")
        
        return sorted(list(addon_requirements))
    except Exception as e:
        print(f"[DEBUG] Error scanning addon requirements: {e}")
        return []


def _get_python_executable():
    """
    Get the real Python executable.
    When running from PyInstaller, sys.executable points to the .exe, so we need to find the real Python.
    """
    python_exe = sys.executable
    
    # If we're running from PyInstaller, find the real Python
    if getattr(sys, 'frozen', False):
        _logger.info(f"Running from PyInstaller (sys.frozen={sys.frozen}), looking for real Python interpreter")
        # Try to find python.exe in common locations
        possible_pythons = [
            os.path.join(os.path.dirname(__file__), '..', '.venv', 'Scripts', 'python.exe'),
            os.path.join(Path.home(), 'AppData', 'Local', 'Programs', 'Python', 'Python314', 'python.exe'),
            os.path.join(Path.home(), 'AppData', 'Local', 'Programs', 'Python', 'Python313', 'python.exe'),
            os.path.join(Path.home(), 'AppData', 'Local', 'Programs', 'Python', 'Python312', 'python.exe'),
        ]
        for py_path in possible_pythons:
            if os.path.exists(py_path):
                python_exe = py_path
                _logger.info(f"Found Python at: {python_exe}")
                return python_exe
        
        _logger.warning(f"Could not find real Python interpreter, trying 'python' from PATH")
        python_exe = "python"
    
    return python_exe


def _install_addon_requirements(addon_requirements):
    """
    Install addon requirements to current venv.
    
    Args:
        addon_requirements: List of package names to install
    """
    if not addon_requirements:
        return
    
    # Check if packages are already installed
    installed_all = True
    for pkg in addon_requirements:
        try:
            # Map package names to import names (e.g., python-Levenshtein -> Levenshtein)
            import_name = pkg.replace('-', '_').split('[')[0].split('==')[0]
            __import__(import_name)
        except ImportError:
            installed_all = False
            break
    
    if installed_all:
        print(f"[INFO] Addon requirements already installed: {', '.join(addon_requirements)}")
        return
    
    import subprocess
    
    print(f"[INFO] Installing addon requirements: {', '.join(addon_requirements)}")
    
    python_exe = _get_python_executable()
    print(f"[INFO] Using Python: {python_exe}")
    
    # Suppress console window on Windows
    kwargs = {
        'capture_output': True,
        'text': True,
        'timeout': 120
    }
    if sys.platform == 'win32':
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
    
    try:
        result = subprocess.run(
            [python_exe, "-m", "pip", "install"] + addon_requirements,
            **kwargs
        )
        
        if result.returncode == 0:
            print(f"[INFO] Addon requirements installed successfully")
        else:
            print(f"[WARNING] pip install returned code {result.returncode}")
            if result.stderr:
                print(f"[WARNING] pip stderr: {result.stderr[:500]}")
    except subprocess.TimeoutExpired:
        print(f"[WARNING] Addon requirements installation timed out")
    except Exception as e:
        print(f"[WARNING] Failed to install addon requirements: {e}")


def _install_requirements(bot_dir):
    """
    Install requirements.txt from bot directory to current venv.
    
    Args:
        bot_dir: Directory containing the bot (to find requirements.txt)
    
    Returns:
        List of installed packages (from requirements.txt)
    """
    import subprocess
    
    # Skip pip install if running from frozen executable (PyInstaller)
    # All dependencies are already bundled in the .exe
    if getattr(sys, 'frozen', False):
        print(f"[INFO] Running from frozen executable - skipping pip install (all dependencies bundled)")
        return
    
    # Also skip if in TESTING_MODE
    if os.environ.get("TESTING_MODE") == "1":
        print(f"[INFO] TESTING_MODE enabled - skipping pip install")
        return
    
    requirements_file = os.path.join(bot_dir, "requirements.txt")
    
    if not os.path.exists(requirements_file):
        print(f"[INFO] No requirements.txt found in {bot_dir}")
        return
    
    print(f"[INFO] Installing requirements from {requirements_file}...")
    
    python_exe = _get_python_executable()
    print(f"[INFO] Using Python: {python_exe}")
    
    # Suppress console window on Windows
    kwargs = {
        'capture_output': True,
        'text': True,
        'timeout': 120
    }
    if sys.platform == 'win32':
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
    
    try:
        result = subprocess.run(
            [python_exe, "-m", "pip", "install", "-r", requirements_file],
            **kwargs
        )
        
        if result.returncode == 0:
            print(f"[INFO] Requirements installed successfully")
        else:
            print(f"[WARNING] pip install returned code {result.returncode}")
            if result.stderr:
                print(f"[WARNING] pip stderr: {result.stderr[:500]}")
    except subprocess.TimeoutExpired:
        print(f"[WARNING] Requirements installation timed out")
    except Exception as e:
        print(f"[WARNING] Failed to install requirements: {e}")


def load_bot_module(bot_path):
    """
    Load a Flask bot module from a file or folder path.
    
    Args:
        bot_path: Path to bot module file (e.g., 'app.py') or folder containing bot
    
    Returns:
        Tuple of (module, flask_app)
    """
    _logger.info(f"=== LOAD_BOT_MODULE STARTING ===")
    _logger.info(f"bot_path: {bot_path}")
    _logger.info(f"Current sys.modules has {len(sys.modules)} modules")
    if not os.path.isabs(bot_path):
        bot_path = os.path.abspath(bot_path)
    
    if not os.path.exists(bot_path):
        raise FileNotFoundError(f"Bot module not found: {bot_path}")
    
    # If it's a folder, find the app file
    if os.path.isdir(bot_path):
        app_file = _find_flask_app_in_folder(bot_path)
        if not app_file:
            raise FileNotFoundError(f"No Flask app found in folder: {bot_path}")
        bot_path = app_file
    
    bot_dir = os.path.dirname(bot_path)
    original_cwd = os.getcwd()
    original_sys_path = sys.path.copy()
    
    try:
        # Change to bot directory and add it to path
        os.chdir(bot_dir)
        if bot_dir not in sys.path:
            sys.path.insert(0, bot_dir)
        
        # Set environment variables for testing
        os.environ["TESTING_MODE"] = "1"  # Signal bot to disable background threads
        os.environ.setdefault("ACCESS_TOKEN", "test_token_12345")
        os.environ.setdefault("GROUP_ID", "test_group_123")
        os.environ.setdefault("BOT_ID", "test_bot_123")
        
        _logger.info(f"About to import bot module: {bot_path}")
        _logger.info(f"TESTING_MODE set to: {os.environ.get('TESTING_MODE')}")
        
        # Clear cached module if it exists
        module_name = Path(bot_path).stem
        for mod_key in list(sys.modules.keys()):
            if module_name in mod_key:
                del sys.modules[mod_key]
        
        # Load the module
        spec = importlib.util.spec_from_file_location(module_name, bot_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        _logger.info("About to call spec.loader.exec_module()")
        _logger.info(f"sys.modules count before: {len(sys.modules)}")
        
        import sys as sys_before
        threads_before = threading.enumerate()
        _logger.info(f"Threads before exec_module: {[t.name for t in threads_before]}")
        
        try:
            _logger.info(">>> CALLING spec.loader.exec_module() <<<")
            spec.loader.exec_module(module)
            _logger.info(">>> spec.loader.exec_module() RETURNED <<<")
        except Exception as e:
            _logger.error(f"Error during exec_module: {e}", exc_info=True)
            raise
        
        _logger.info(f"sys.modules count after: {len(sys.modules)}")
        _logger.info(f"Module loaded successfully: {module_name}")
        threads_after = threading.enumerate()
        new_threads = [t for t in threads_after if t not in threads_before]
        if new_threads:
            _logger.warning(f"New threads created during exec_module: {[t.name for t in new_threads]}")
        
        # Find Flask app instance
        flask_app = None
        for attr_name in dir(module):
            if attr_name.startswith('_'):
                continue
            attr = getattr(module, attr_name)
            if hasattr(attr, 'test_client') and hasattr(attr, 'route'):
                try:
                    attr.test_client()
                    flask_app = attr
                    break
                except TypeError:
                    pass
        
        if not flask_app:
            raise RuntimeError(f"No Flask app instance found in {bot_path}")
        
        return module, flask_app
    
    finally:
        os.chdir(original_cwd)
        sys.path = original_sys_path


class InteractiveTester:
    """Simple tester for Flask bots with message capture."""
    
    def __init__(self, bot_path):
        """Initialize tester with bot module path."""
        print("[TESTER INIT] Starting InteractiveTester.__init__")
        self.bot_path = bot_path
        # Determine bot directory
        if os.path.isdir(bot_path):
            self.bot_dir = os.path.abspath(bot_path)
        else:
            self.bot_dir = os.path.dirname(os.path.abspath(bot_path))
        
        self.bot_module = None
        self.app = None
        self.sent_messages = []
        self.message_responses = []
        self.startup_message = None  # Capture startup message from bot
        self.webhook_route = "/"
        self._message_id_counter = 1000000  # Start with realistic numeric IDs
        self._source_guid_counter = 0
        self.groupme_token = "test_token_" + str(uuid.uuid4())[:8]  # Simulate API token
        
        # Track user roles for testing
        self.test_users = {
            "admin": {"user_id": "admin_test_123", "name": "TestAdmin", "avatar": "https://i.groupme.com/admin.jpg"},
            "user": {"user_id": "user_test_456", "name": "TestUser", "avatar": "https://i.groupme.com/user.jpg"},
            "system": {"user_id": "system", "name": "GroupMe", "avatar": "https://i.groupme.com/system.jpg"}
        }
        
        print("[TESTER INIT] About to call _load_bot()")
        self._load_bot()
        print("[TESTER INIT] _load_bot() completed successfully")

    
    def _load_bot(self):
        """Load bot module and apply message capture patches."""
        print("[TESTER _LOAD_BOT] Starting _load_bot()")
        _logger.info(f"Loading bot from {self.bot_path}")
        
        # Install requirements from bot directory
        bot_dir = self.bot_path if os.path.isdir(self.bot_path) else os.path.dirname(self.bot_path)
        print("[TESTER _LOAD_BOT] About to install requirements")
        _install_requirements(bot_dir)
        print("[TESTER _LOAD_BOT] Requirements installed")
        
        # Scan and install addon requirements BEFORE loading bot
        print("[TESTER _LOAD_BOT] Scanning addon requirements")
        addon_reqs = _get_addon_requirements(bot_dir)
        if addon_reqs:
            print(f"[TESTER _LOAD_BOT] Installing addon requirements: {addon_reqs}")
            _logger.info(f"Installing addon requirements: {', '.join(addon_reqs)}")
            _install_addon_requirements(addon_reqs)
        print("[TESTER _LOAD_BOT] About to load bot module...")
        
        _logger.info("About to call load_bot_module()")
        print("[TESTER _LOAD_BOT] Calling load_bot_module()...")
        self.bot_module, self.app = load_bot_module(self.bot_path)
        print("[TESTER _LOAD_BOT] load_bot_module() completed!")
        _logger.info("load_bot_module() completed")
        
        # Detect webhook route
        print("[TESTER _LOAD_BOT] Detecting webhook route")
        self._detect_webhook_route()
        
        # Apply persistent patches to capture messages
        print("[TESTER _LOAD_BOT] Applying patches")
        self._apply_patches()
        
        # Wait for startup message if bot sends one
        print("[TESTER _LOAD_BOT] Waiting for startup message")
        _logger.info("Waiting for startup message...")
        time.sleep(3)
        
        _logger.info("Bot loaded successfully")
        _logger.info(f"Webhook route: {self.webhook_route}")
        if self.startup_message:
            print(f"[INFO] Startup message: {self.startup_message}")
    
    def _detect_webhook_route(self):
        """Auto-detect the webhook route for POST requests."""
        webhook_route = "/"
        
        routes = []
        for rule in self.app.url_map.iter_rules():
            if 'POST' in rule.methods:
                routes.append(rule.rule)
        
        # Prefer common webhook routes
        for candidate in ['/webhook', '/webhooks', '/message', '/', '/api/webhook']:
            if candidate in routes:
                webhook_route = candidate
                break
        
        if routes and webhook_route == "/" and "/" not in routes:
            webhook_route = routes[0]
        
        self.webhook_route = webhook_route
    
    def _patch_admin_checks(self):
        """Patch admin checking to allow test users to behave as admins."""
        test_user_id = "admin_test_123"
        
        # Add test user ID to ADMIN_IDS list if it exists
        if hasattr(self.bot_module, 'ADMIN_IDS'):
            admin_ids = getattr(self.bot_module, 'ADMIN_IDS')
            if isinstance(admin_ids, list) and test_user_id not in admin_ids:
                admin_ids.append(test_user_id)
        
        # Look for common admin check functions and patch them
        functions_to_patch = [
            'is_admin', 'check_admin', 'get_is_admin', 
            'is_user_admin', 'user_is_admin', 'validate_admin'
        ]
        
        for func_name in functions_to_patch:
            if hasattr(self.bot_module, func_name):
                setattr(self.bot_module, func_name, lambda *args, **kwargs: True)
        
        # Also patch if functions are stored in dict-like structures
        for attr_name in dir(self.bot_module):
            if attr_name.startswith('_') or attr_name.startswith('__'):
                continue
            try:
                attr = getattr(self.bot_module, attr_name)
                # Skip module-level imports and classes
                if callable(attr) and 'admin' in attr_name.lower() and not isinstance(attr, type):
                    setattr(self.bot_module, attr_name, lambda *args, **kwargs: True)
            except:
                pass
    
    def _apply_patches(self):
        """Apply persistent patches to capture messages and enable admin mode for testing."""
        import requests
        tester = self  # Closure capture
        original_post = requests.post  # Save original for non-GroupMe calls
        
        def capture_message(msg_text, **kwargs):
            """Capture text messages."""
            try:
                tester.sent_messages.append(msg_text)
                response = {"text": msg_text}
                if 'image_url' in kwargs:
                    response["attachments"] = [{"type": "image", "url": kwargs['image_url']}]
                tester.message_responses.append(response)
                return True  # Return True to indicate success
            except Exception as e:
                print("[CAPTURE ERROR]:", str(e))
                return False
        
        def capture_image_message(msg_text, image_url=None, **kwargs):
            """
            Intercept image sends BEFORE any GroupMe upload.
            Handles both local file paths and URLs.
            Prevents the bot from running any upload code.
            """
            try:
                # Simple logging that handles unicode by just noting the call
                tester.sent_messages.append(msg_text)
                response = {"text": msg_text}
                # Store the image - could be local file path or URL
                if image_url:
                    # Check if it's a local file path (doesn't start with http)
                    is_local = not image_url.startswith(('http://', 'https://', 'mock://'))
                    
                    # Resolve relative paths against bot directory
                    resolved_url = image_url
                    if is_local and not os.path.isabs(image_url):
                        resolved_url = os.path.join(tester.bot_dir, image_url)
                    
                    response["attachments"] = [{
                        "type": "image",
                        "url": resolved_url,
                        "is_local_file": is_local   # Flag for GUI to load directly vs download
                    }]
                    print(f"[CAPTURE DEBUG] Image message captured: url_len={len(resolved_url)}, is_local={is_local}")
                else:
                    print(f"[CAPTURE DEBUG] Message captured (no image)")
                tester.message_responses.append(response)
                print(f"[CAPTURE DEBUG] Total responses: {len(tester.message_responses)}")
                # Return True immediately - prevents rest of bot code from running
                return True
            except Exception as e:
                print(f"[CAPTURE ERROR] send_message_with_image: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        def fake_requests_post(url, *args, **kwargs):
            """Intercept GroupMe API calls (as fallback if they somehow get through)."""
            # Intercept GroupMe bot message sends
            if "api.groupme.com/v3/bots/post" in url:
                # Capture startup message if it hasn't been captured yet
                if kwargs.get('json') and kwargs['json'].get('text'):
                    msg_text = kwargs['json']['text']
                    # Check if this looks like a startup message (not from user input)
                    if not tester.sent_messages and tester.startup_message is None:
                        # This is likely the startup message sent during initialization
                        tester.startup_message = msg_text
                
                class FakeResponse:
                    status_code = 202
                    text = '{"response": {}}'
                    def json(self):
                        return {"response": {}}
                    def raise_for_status(self):
                        pass
                return FakeResponse()
            
            # Intercept GroupMe image uploads - return dummy success
            if "image.groupme.com/pictures" in url:
                class FakeImageResponse:
                    status_code = 200
                    text = '{"payload": {"url": "https://i.groupme.com/test.jpg"}}'
                    def json(self):
                        return {"payload": {"url": "https://i.groupme.com/test.jpg"}}
                    def raise_for_status(self):
                        pass
                return FakeImageResponse()
            
            # For all other requests, use the original
            return original_post(url, *args, **kwargs)
        
        def fake_upload_image_to_groupme(image_bytes, content_type="image/jpeg"):
            """Fake image upload - return dummy URL for testing."""
            # In test mode, just return a dummy URL without actually uploading
            return "https://i.groupme.com/test.jpg"
        
        # Patch send functions - these intercept BEFORE any GroupMe processing
        if hasattr(self.bot_module, 'send_message'):
            self.bot_module.send_message = capture_message
            print(f"[PATCH DEBUG] Patched send_message in {self.bot_module.__name__}")
        
        if hasattr(self.bot_module, 'send_message_with_image'):
            # This intercepts before ensure_groupme_image_url is called
            self.bot_module.send_message_with_image = capture_image_message
            print(f"[PATCH DEBUG] Patched send_message_with_image in {self.bot_module.__name__}")
        else:
            print(f"[PATCH DEBUG] send_message_with_image NOT FOUND in {self.bot_module.__name__}")
        
        if hasattr(self.bot_module, 'send_message_with_ping'):
            self.bot_module.send_message_with_ping = lambda msg_text, name=None, user_id=None, **kw: capture_message(msg_text, **kw)
        
        # IMPORTANT: Also patch addon system's send callbacks
        # The addon system has already captured references, so we need to update those
        try:
            from addons import get_translator
            from addons.core import Addon
            translator = get_translator()
            if translator.context:
                # Create wrapper that logs when send_message is called
                original_addon_send = translator.context.send_message
                def addon_send_wrapper(msg_text, **kwargs):
                    print(f"[ADDON SEND INTERCEPTED] '{msg_text[:60]}...'")
                    return capture_message(msg_text, **kwargs)
                
                translator.context.send_message = addon_send_wrapper
                translator.context.send_message_with_image = capture_image_message
                print("[PATCH DEBUG] Patched addon system context send_message")
                print(f"[PATCH DEBUG] Translator context object: {id(translator.context)}")
                
                # Also patch Addon.send() method itself to log calls
                original_addon_send_method = Addon.send
                def addon_send_method_wrapper(self, text):
                    print(f"[ADDON.SEND() CALLED] '{text[:60]}...', has_context={self.context is not None}")
                    if self.context:
                        print(f"[ADDON.SEND() DEBUG] context_id={id(self.context)}, has_send_message={hasattr(self.context, 'send_message')}, send_message={self.context.send_message}")
                        if self.context.send_message:
                            print(f"[ADDON.SEND() DEBUG] Calling context.send_message...")
                    else:
                        print(f"[ADDON.SEND() ERROR] No context set on addon!")
                    return original_addon_send_method(self, text)
                
                Addon.send = addon_send_method_wrapper
                print("[PATCH DEBUG] Patched Addon.send() method")
                
                # Also patch Addon.handle_message to log calls
                original_handle_message = Addon.handle_message
                def handle_message_wrapper(self, text):
                    print(f"[ADDON.HANDLE_MESSAGE() CALLED] text='{text[:60]}...'")
                    return original_handle_message(self, text)
                
                Addon.handle_message = handle_message_wrapper
                print("[PATCH DEBUG] Patched Addon.handle_message() method")
        except Exception as e:
            print(f"[DEBUG] Could not patch addon context: {e}")
            import traceback
            traceback.print_exc()
        
        # IMPORTANT: Also patch game modules (plane_game, gun_game) send functions
        # so background threads can use them
        try:
            import plane_game
            plane_game.send_message = capture_message
            plane_game.send_message_with_image = capture_image_message
            print("[INFO] Patched plane_game send functions")
        except Exception as e:
            print(f"[DEBUG] Could not patch plane_game (root): {e}")
        
        try:
            from lib import plane_game as lib_plane_game
            lib_plane_game.send_message = capture_message
            lib_plane_game.send_message_with_image = capture_image_message
            print("[INFO] Patched lib.plane_game send functions")
        except Exception as e:
            print(f"[DEBUG] Could not patch lib.plane_game: {e}")
        
        try:
            import gun_game
            gun_game.send_message = capture_message
            gun_game.send_message_with_image = capture_image_message
            print("[INFO] Patched gun_game send functions")
        except Exception as e:
            print(f"[DEBUG] Could not patch gun_game (root): {e}")
        
        try:
            from lib import gun_game as lib_gun_game
            lib_gun_game.send_message = capture_message
            lib_gun_game.send_message_with_image = capture_image_message
            print("[INFO] Patched lib.gun_game send functions")
        except Exception as e:
            print(f"[DEBUG] Could not patch lib.gun_game: {e}")
        
        # Patch image upload to skip uploading in test mode
        if hasattr(self.bot_module, 'upload_image_to_groupme'):
            self.bot_module.upload_image_to_groupme = fake_upload_image_to_groupme
        
        # Patch _fetch_reaction_meme to return local file path instead of uploading
        if hasattr(self.bot_module, '_fetch_reaction_meme'):
            original_fetch_reaction_meme = self.bot_module._fetch_reaction_meme
            
            def fake_fetch_reaction_meme(name):
                """Return local file path instead of uploading to GroupMe."""
                import os as os_module
                # Check common extensions
                extensions = ['.jpg', '.jpeg', '.png', '.gif']
                memes_dir = os_module.path.join(tester.bot_dir, 'reactionMemes')
                
                for ext in extensions:
                    path = os_module.path.join(memes_dir, name + ext)
                    if os_module.path.isfile(path):
                        # Return the local file path - the interceptor will handle it
                        return path
                
                # If not found, return None (like original)
                return None
            
            self.bot_module._fetch_reaction_meme = fake_fetch_reaction_meme
        
        # Patch _fetch_audio_clip to return local file path instead of uploading
        if hasattr(self.bot_module, '_fetch_audio_clip'):
            def fake_fetch_audio_clip(name):
                """Return local audio file path instead of uploading to GroupMe."""
                import os as os_module
                # Check common audio extensions
                extensions = ['.mp3', '.m4a', '.wav', '.ogg']
                audio_dir = os_module.path.join(tester.bot_dir, 'Audio')
                
                for ext in extensions:
                    path = os_module.path.join(audio_dir, name + ext)
                    if os_module.path.isfile(path):
                        # Return the local file path
                        return path
                
                # If not found, return None (like original)
                return None
            
            self.bot_module._fetch_audio_clip = fake_fetch_audio_clip
        
        # Patch send_audio_attachment to capture audio before upload
        if hasattr(self.bot_module, 'send_audio_attachment'):
            original_send_audio = self.bot_module.send_audio_attachment
            
            def capture_audio_attachment(audio_url, text="", duration=7, peaks=None, **kwargs):
                """
                Intercept audio sends BEFORE any GroupMe upload.
                Captures the audio file path directly.
                """
                try:
                    if audio_url:
                        # Determine if local file or URL
                        is_local = not audio_url.startswith(('http://', 'https://', 'mock://'))
                        
                        # Resolve relative paths against bot directory
                        resolved_url = audio_url
                        if is_local and not os.path.isabs(audio_url):
                            resolved_url = os.path.join(tester.bot_dir, audio_url)
                        
                        # Create message response
                        response = {}
                        if text:
                            response["text"] = text
                            tester.sent_messages.append(text)
                        
                        response["attachments"] = [{
                            "type": "audio",
                            "url": resolved_url,
                            "is_local_file": is_local,
                            "duration": duration,
                            "peaks": peaks
                        }]
                        tester.message_responses.append(response)
                    
                    # Return True to indicate success
                    return True
                except Exception as e:
                    print(f"[CAPTURE ERROR] send_audio_attachment: {e}")
                    return False
            
            self.bot_module.send_audio_attachment = capture_audio_attachment
        
        # Patch requests.post as fallback (shouldn't be needed since we intercept earlier)
        requests.post = fake_requests_post
        self.bot_module.requests.post = fake_requests_post
        
        # Patch admin checks to allow testing
        self._patch_admin_checks()
    
    def _generate_source_guid(self):
        """Generate unique source_guid for de-duplication (like real GroupMe)."""
        self._source_guid_counter += 1
        return f"test_{self._source_guid_counter}_{int(time.time() * 1000)}"
    
    def _get_next_message_id(self):
        """Get next realistic message ID (numeric string like GroupMe)."""
        self._message_id_counter += 1
        return str(self._message_id_counter)
    
    def _validate_attachment(self, attachment):
        """Validate attachment format matches GroupMe API."""
        if not isinstance(attachment, dict):
            raise ValueError("Attachment must be a dict")
        
        if "type" not in attachment:
            raise ValueError("Attachment must have 'type' field")
        
        att_type = attachment["type"]
        
        if att_type == "image":
            if "url" not in attachment:
                raise ValueError("Image attachment must have 'url'")
            # Validate URL format (should be i.groupme.com or mock:// for testing)
            if not attachment["url"].startswith(('http://', 'https://', 'mock://', 'file://')):
                raise ValueError("Image URL must be absolute URL (http://, https://, mock://, or file://)")
            return True
        
        elif att_type == "location":
            required = ["name", "lat", "lng"]
            for field in required:
                if field not in attachment:
                    raise ValueError(f"Location attachment must have '{field}'")
            return True
        
        elif att_type == "emoji":
            required = ["placeholder", "charmap"]
            for field in required:
                if field not in attachment:
                    raise ValueError(f"Emoji attachment must have '{field}'")
            return True
        
        elif att_type == "split":
            if "token" not in attachment:
                raise ValueError("Split attachment must have 'token'")
            return True
        
        else:
            raise ValueError(f"Unknown attachment type: {att_type}")
    
    def build_groupme_message(self, text, user_id, user_name, attachments=None, system=False):
        """
        Build a message event that exactly matches GroupMe API format.
        
        Args:
            text: Message text
            user_id: User ID
            user_name: User name
            attachments: List of attachment dicts
            system: Whether this is a system message
        
        Returns:
            GroupMe-formatted message dict
        """
        if attachments is None:
            attachments = []
        
        # Validate all attachments
        for att in attachments:
            self._validate_attachment(att)
        
        message_id = self._get_next_message_id()
        source_guid = self._generate_source_guid()
        
        # Get user avatar
        user_info = self.test_users.get(user_id.split('_')[0])
        avatar_url = user_info["avatar"] if user_info else "https://i.groupme.com/user.jpg"
        
        message = {
            # Required fields
            "id": message_id,
            "source_guid": source_guid,
            "created_at": int(time.time()),
            "user_id": user_id,
            "group_id": "123456789",  # Consistent test group ID
            "name": user_name,
            "avatar_url": avatar_url,
            "text": text,
            
            # Optional but commonly used fields
            "system": system,
            "sender_id": user_id,  # Some bots check this instead of user_id
            "sender_type": "system" if system else "user",
            "favorited_by": [],  # Will be populated if message is liked
            "attachments": attachments
        }
        
        return message
    
    def build_webhook_headers(self):
        """Build realistic HTTP headers that GroupMe sends."""
        return {
            "X-Access-Token": self.groupme_token,
            "Content-Type": "application/json",
            "X-Groupme-Signature": self._generate_groupme_signature(),
            "User-Agent": "GroupMe-Webhook/1.0"
        }
    
    def _generate_groupme_signature(self):
        """Generate a valid-looking GroupMe signature (HMAC)."""
        # In real GroupMe, this is HMAC-SHA-256 of message content
        # For testing, we'll generate a dummy signature
        return hashlib.sha256(str(time.time()).encode()).hexdigest()
    
    def test_message_batch(self, messages, user_role="admin"):
        """
        Send multiple messages in sequence (for conversation testing).
        
        Args:
            messages: List of message strings to send
            user_role: "admin" or "user" role for all messages
        
        Returns:
            List of all bot responses
        """
        all_responses = []
        user_info = self.test_users[user_role]
        
        for msg in messages:
            responses = self.test_message(msg, user_name=user_info["name"], user_id=user_info["user_id"])
            all_responses.extend(responses)
            time.sleep(0.2)  # Small delay between messages
        
        return all_responses
    
    def test_message_error(self, text, error_code=409, error_msg="Conflict", user_role="admin"):
        """
        Test how bot handles error responses from GroupMe.
        
        Args:
            text: Message text
            error_code: HTTP error code (409, 404, 429, 503, etc)
            error_msg: Error message
            user_role: "admin" or "user"
        
        Returns:
            List of bot responses (or error handling responses)
        """
        print(f"\n[ERROR TEST] Simulating {error_code} {error_msg} error")
        
        # Use local list for this specific message, don't clear global
        local_responses = []
        old_message_responses = self.message_responses
        self.message_responses = local_responses
        self.sent_messages = []
        
        user_info = self.test_users[user_role]
        
        # Build realistic error response
        error_response = {
            "meta": {
                "code": error_code,
                "errors": [error_msg]
            },
            "response": None
        }
        
        # Send message normally, but simulate error on response
        event = self.build_groupme_message(text, user_info["user_id"], user_info["name"])
        client = self.app.test_client()
        
        try:
            response = client.post(self.webhook_route, json=event)
            time.sleep(1)  # Wait longer for error handling
        except Exception as e:
            print(f"[ERROR TEST] Exception during webhook post: {e}")
        
        # Get responses and restore
        responses = list(local_responses)
        self.message_responses = old_message_responses
        
        return responses
    
    def test_duplicate_message(self, text, user_role="admin"):
        """
        Test duplicate message handling (same source_guid sent twice).
        GroupMe should reject the second message with 409 Conflict.
        
        Args:
            text: Message text
            user_role: "admin" or "user"
        
        Returns:
            (first_responses, second_responses)
        """
        print(f"\n[DUPLICATE TEST] Sending message twice (should trigger 409 Conflict on second)")
        
        user_info = self.test_users[user_role]
        
        # Send first message
        first_responses = self.test_message(text, user_name=user_info["name"], user_id=user_info["user_id"])
        time.sleep(0.5)
        
        # Try to send same message immediately (with same guid)
        # In real GroupMe, this triggers 409 Conflict
        second_responses = self.test_message_error(text, error_code=409, error_msg="Conflict", user_role=user_role)
        
        return (first_responses, second_responses)
    
    def test_timeout(self, text, timeout_seconds=30, user_role="admin"):
        """
        Test bot behavior when webhook takes too long to respond.
        
        Args:
            text: Message text
            timeout_seconds: How long to wait before timeout
            user_role: "admin" or "user"
        
        Returns:
            Responses (if any before timeout)
        """
        print(f"\n[TIMEOUT TEST] Simulating {timeout_seconds}s webhook timeout")
        
        user_info = self.test_users[user_role]
        
        # In real scenario, GroupMe times out after ~3 seconds
        # For testing, we'll just send the message and see what bot does
        self.sent_messages = []
        self.message_responses = []
        
        event = self.build_groupme_message(text, user_info["user_id"], user_info["name"])
        client = self.app.test_client()
        
        # Set a timeout on the request
        try:
            response = client.post(self.webhook_route, json=event, timeout=min(timeout_seconds, 3))
            time.sleep(2)
        except Exception as e:
            print(f"[TIMEOUT TEST] Request timed out (expected): {e}")
        
        return self.sent_messages
    
    def test_system_message(self, text, user_role="system"):
        """
        Test system messages (e.g., user joined/left group).
        
        Args:
            text: System message text
            user_role: Always "system" for these
        
        Returns:
            Bot responses
        """
        print(f"\n[SYSTEM MESSAGE TEST] Sending system message")
        
        self.sent_messages = []
        self.message_responses = []
        
        user_info = self.test_users["system"]
        event = self.build_groupme_message(text, user_info["user_id"], user_info["name"], system=True)
        
        client = self.app.test_client()
        
        try:
            response = client.post(self.webhook_route, json=event)
            time.sleep(0.5)
        except Exception as e:
            print(f"[SYSTEM MESSAGE TEST] Error: {e}")
        
        return self.sent_messages
    
    def test_message_with_attachments(self, text, attachments, user_role="admin"):
        """
        Test message with attachments (images, locations, etc).
        
        Args:
            text: Message text
            attachments: List of attachment dicts (must be validated format)
            user_role: "admin" or "user"
        
        Returns:
            Bot responses
        """
        print(f"\n[ATTACHMENT TEST] Testing message with {len(attachments)} attachment(s)")
        
        self.sent_messages = []
        self.message_responses = []
        
        user_info = self.test_users[user_role]
        
        try:
            event = self.build_groupme_message(text, user_info["user_id"], user_info["name"], attachments=attachments)
        except ValueError as e:
            print(f"[ATTACHMENT TEST] Validation error: {e}")
            return []
        
        client = self.app.test_client()
        
        try:
            # Include realistic headers
            headers = self.build_webhook_headers()
            response = client.post(self.webhook_route, json=event, headers=headers)
            time.sleep(0.5)
        except Exception as e:
            print(f"[ATTACHMENT TEST] Error: {e}")
        
        return self.sent_messages
    
    def test_high_volume(self, base_message, count=100, interval=0.1, user_role="admin"):
        """
        Test bot behavior under high message volume (like a busy group).
        
        Args:
            base_message: Base message text (will append count)
            count: Number of messages to send
            interval: Delay between messages (seconds)
            user_role: "admin" or "user"
        
        Returns:
            List of all bot responses
        """
        print(f"\n[HIGH VOLUME TEST] Sending {count} messages")
        
        user_info = self.test_users[user_role]
        all_responses = []
        
        for i in range(count):
            self.sent_messages = []
            msg = f"{base_message} [{i+1}/{count}]"
            
            try:
                responses = self.test_message(msg, user_name=user_info["name"], user_id=user_info["user_id"])
                all_responses.extend(responses)
                time.sleep(interval)
            except Exception as e:
                print(f"[HIGH VOLUME TEST] Error on message {i+1}: {e}")
        
        return all_responses
    
    def test_message(self, text, user_name="TestAdmin", user_id="admin_test_123", attachments=None, user_role=None):
        """
        Send a message to the bot and capture responses.
        NOW matches real GroupMe API format exactly!
        
        Args:
            text: Message text to send
            user_name: Name of the user sending message (default "TestAdmin" for admin mode)
            user_id: ID of the user (default "admin_test_123" for admin mode)
            attachments: List of attachment dicts (validated GroupMe format)
            user_role: "admin" or "user" (overrides user_name/user_id if set)
        
        Returns:
            List of response dicts with 'text' and optionally 'attachments'
        """
        # Use a local list for this specific message, don't clear the global one
        # This prevents race conditions with async addon calls
        local_responses = []
        old_message_responses = self.message_responses
        self.message_responses = local_responses  # Temporarily use local list
        self.sent_messages = []
        
        # If user_role specified, use that instead
        if user_role and user_role in self.test_users:
            user_info = self.test_users[user_role]
            user_id = user_info["user_id"]
            user_name = user_info["name"]
        
        if attachments is None:
            attachments = []
        
        # Build realistic GroupMe message using new method
        try:
            event = self.build_groupme_message(text, user_id, user_name, attachments=attachments)
        except ValueError as e:
            print(f"[ERROR] Invalid message format: {e}")
            self.message_responses = old_message_responses  # Restore before returning
            return []
        
        # Post to webhook WITH realistic headers
        client = self.app.test_client()
        headers = self.build_webhook_headers()
        
        try:
            response = client.post(self.webhook_route, json=event, headers=headers)
            
            # Wait for background threads
            # In TESTING_MODE, game initialization is skipped so only need short wait for REPLY
            # In production, would need much longer (45s) to fetch from Wikipedia
            if any(game_cmd in text.lower() for game_cmd in ['!planegame', '!gungame', 'game', 'hard mode', 'refresh']):
                wait_time = 1.0  # TESTING_MODE skips real initialization
            else:
                wait_time = 0.5  # Regular commands are faster
            
            time.sleep(wait_time)
        except Exception as e:
            print(f"[ERROR] Webhook post failed: {e}")
        
        # Get responses and restore the old list
        responses = list(local_responses)  # Make a copy
        self.message_responses = old_message_responses  # Restore
        
        print(f"[TEST DEBUG FINAL] Returning {len(responses)} responses for message: {text[:50]}...")
        return responses
    
    def get_active_skin_pfp(self):
        """
        Get the active skin's PFP if available.
        
        Returns:
            Path to skin's pfp.png if active and exists, None if skin active but no pfp,
            or default bot PFP path if no skin active.
        """
        import json
        
        # Try to load active_skin.json
        active_skin_path = os.path.join(self.bot_dir, 'active_skin.json')
        
        try:
            if os.path.isfile(active_skin_path):
                with open(active_skin_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    active_skin = data.get('skin')
                    
                    if active_skin:
                        # Check if skin folder has pfp.png
                        skin_pfp_path = os.path.join(self.bot_dir, 'addons', active_skin, 'pfp.png')
                        if os.path.isfile(skin_pfp_path):
                            return skin_pfp_path
                        else:
                            # Skin active but no PFP
                            return None
        except Exception as e:
            _logger.debug(f"Error reading active_skin.json: {e}")
        
        # No skin active - return default PFP path
        default_pfp = os.path.join(self.bot_dir, 'ClankerPFP.png')
        if os.path.isfile(default_pfp):
            return default_pfp
        
        return None


def run_interactive():
    """Run interactive testing mode with user input."""
    # Get bot path from argument or current directory
    if len(sys.argv) > 1:
        bot_path = sys.argv[1]
    else:
        # Try to find bot folder in parent directories
        bot_dir = Path(__file__).parent.parent.parent / "bot"
        if bot_dir.exists():
            bot_path = str(bot_dir)
        else:
            print(f"[ERROR] Bot folder not found at {bot_dir}")
            print("Usage: python interactive_test.py /path/to/bot [or /path/to/app.py]")
            sys.exit(1)
    
    try:
        tester = InteractiveTester(str(bot_path))
    except Exception as e:
        print(f"[ERROR] Failed to load bot: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "="*70)
    print("INTERACTIVE BOT TESTER")
    print("="*70)
    print(f"Bot: {Path(bot_path).name}")
    print(f"Webhook route: {tester.webhook_route}")
    
    if tester.startup_message:
        print(f"\n📨 Startup Message: {tester.startup_message}")
    
    print("\nType messages to send to the bot.")
    print("Type 'quit' to exit.")
    print("="*70 + "\n")
    
    while True:
        try:
            msg = input("> ").strip()
            
            if not msg:
                continue
            
            if msg.lower() in ['quit', 'exit']:
                print("Goodbye!")
                break
            
            responses = tester.test_message(msg)
            
            if responses:
                print("\nBot responses:")
                for i, resp in enumerate(responses, 1):
                    print(f"  [{i}] {resp[:100]}" + ("..." if len(resp) > 100 else ""))
            else:
                print("(no response)")
            print()
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    run_interactive()
