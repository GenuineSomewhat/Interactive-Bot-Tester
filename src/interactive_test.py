"""
Generic interactive bot tester - manually test any bot's responses in real-time.
Works with any bot module that has a Flask app instance.
Auto-discovers Flask bots in the current directory.
"""

import os
import sys
import importlib.util
from urllib.parse import urlparse
from unittest.mock import patch, MagicMock
from pathlib import Path
from contextlib import ExitStack

try:
    from PIL import Image
except Exception:
    Image = None


def discover_bots(search_dir=None):
    """
    Scan directory for potential bot files (Flask-based or polling-based).
    Excludes this script itself and test files.
    
    Returns:
        List of tuples: [(file_path, file_name, bot_type), ...]
        where bot_type is 'flask' or 'polling'
    """
    if search_dir is None:
        search_dir = os.getcwd()
    
    if not os.path.isdir(search_dir):
        return []
    
    # Get this script's name to exclude it
    this_script = os.path.basename(__file__)
    exclude_patterns = ['test_', 'interactive_test', 'demo_', '__pycache__']
    
    bots = []
    for filename in sorted(os.listdir(search_dir)):
        # Skip test files, this script, and special files
        if any(pattern in filename.lower() for pattern in exclude_patterns):
            continue
        
        if filename.startswith('_') or not filename.endswith('.py'):
            continue
        
        filepath = os.path.join(search_dir, filename)
        
        # Quick heuristic check without loading
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()  # Read entire file for better detection
                
                # Strong polling indicators
                has_watch_for_messages = 'watch_for_messages' in content or ('while True:' in content and 'groupme_api' in content)
                has_groupme_api = content.count('groupme_api(') > 1
                
                # Strong Flask indicators (actual Flask app instantiation)
                has_flask_app = 'app = Flask(' in content or 'app=Flask(' in content
                has_flask_routes = '@app.route(' in content or '@app.post(' in content
                
                # Score-based detection
                polling_score = 0
                flask_score = 0
                
                if has_watch_for_messages:
                    polling_score += 10
                if has_groupme_api:
                    polling_score += 5
                
                if has_flask_app:
                    flask_score += 10
                if has_flask_routes:
                    flask_score += 5
                
                # Determine bot type
                if polling_score > 0 or flask_score > 0:
                    bot_type = 'polling' if polling_score > flask_score else 'flask'
                    bots.append((filepath, filename, bot_type))
        except Exception:
            continue
    
    return bots


def get_bot_path_startup():
    """
    Show startup menu to choose between auto-discovery and custom bot path entry.
    
    Returns:
        Path to bot module, or None if cancelled
    """
    print("\n" + "="*70)
    print("INTERACTIVE BOT TESTER")
    print("="*70)
    print("\nHow would you like to load a bot?\n")
    print("  1. Auto-discover bots in current directory")
    print("  2. Enter a custom bot path/folder")
    print("  q. Quit\n")
    
    while True:
        choice = input("Select option (1, 2, or 'q'): ").strip().lower()
        
        if choice == 'q':
            return None
        elif choice == '1':
            # Auto-discovery
            bots = discover_bots()
            if len(bots) == 0:
                print("\n[ERROR] No bot files found in current directory")
                print("Try option 2 to manually enter a bot path.\n")
                continue
            elif len(bots) == 1:
                bot_type = bots[0][2]
                type_label = "Flask" if bot_type == 'flask' else "Polling"
                print(f"\n[AUTO] Found {type_label} bot: {bots[0][1]}")
                return bots[0][0]
            else:
                # Show menu for multiple bots
                return select_bot_interactive()
        elif choice == '2':
            # Custom path entry
            return get_custom_bot_path()
        else:
            print("Invalid choice. Enter 1, 2, or 'q'")


def select_bot_interactive():
    """
    Present interactive menu to select a bot to test.
    
    Returns:
        Path to selected bot file, or None if cancelled
    """
    bots = discover_bots()
    
    if not bots:
        return None
    
    print("\n" + "="*70)
    print("AVAILABLE BOTS FOUND")
    print("="*70)
    
    for i, (path, filename, bot_type) in enumerate(bots, 1):
        size = os.path.getsize(path)
        type_label = "[Flask]" if bot_type == 'flask' else "[Polling]"
        print(f"  {i}. {filename:30} {type_label:12} ({size:,} bytes)")
    
    while True:
        try:
            choice = input("\nSelect bot to test (number or 'q' to cancel): ").strip()
            if choice.lower() == 'q':
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(bots):
                return bots[idx][0]
            print(f"Invalid choice. Enter 1-{len(bots)}")
        except ValueError:
            print("Please enter a valid number")


def get_custom_bot_path():
    """
    Prompt user to enter a custom bot folder or file path.
    
    Returns:
        Path to bot module, or None if cancelled
    """
    print("\n" + "="*70)
    print("ENTER BOT PATH")
    print("="*70)
    print("\nEnter the path to your bot folder or bot file:")
    print("Examples:")
    print("  ../lkh-sigma")
    print("  C:\\path\\to\\bot-test")
    print("  ./mybot.py")
    print("  /absolute/path/to/bot\n")
    
    while True:
        user_input = input("Bot path (or 'q' to cancel): ").strip()
        
        if user_input.lower() == 'q':
            return None
        
        if not user_input:
            print("Path cannot be empty. Try again.")
            continue
        
        # Expand user paths and environment variables
        bot_path = os.path.expanduser(os.path.expandvars(user_input))
        
        # If it's a directory, look for app.py or similar bot file
        if os.path.isdir(bot_path):
            print(f"\n[INFO] Scanning directory: {bot_path}")
            potential_bots = discover_bots(bot_path)
            
            if len(potential_bots) == 0:
                print(f"[ERROR] No bots found in {bot_path}")
                print("Looking for .py files with Flask or polling patterns...")
                print("Try entering the full path to a bot file instead.\n")
                continue
            elif len(potential_bots) == 1:
                bot_file = potential_bots[0][0]
                bot_type = potential_bots[0][2]
                type_label = "Flask" if bot_type == 'flask' else "Polling"
                print(f"[AUTO] Found {type_label} bot: {potential_bots[0][1]}")
                return bot_file
            else:
                # Multiple bots in folder - show menu
                print(f"\n[INFO] Found {len(potential_bots)} potential bots in {bot_path}\n")
                print("="*70)
                print("BOTS IN DIRECTORY")
                print("="*70)
                
                for i, (path, filename, bot_type) in enumerate(potential_bots, 1):
                    size = os.path.getsize(path)
                    type_label = "[Flask]" if bot_type == 'flask' else "[Polling]"
                    print(f"  {i}. {filename:30} {type_label:12} ({size:,} bytes)")
                
                while True:
                    try:
                        choice = input("\nSelect bot (number or 'q' to re-enter): ").strip()
                        if choice.lower() == 'q':
                            break
                        idx = int(choice) - 1
                        if 0 <= idx < len(potential_bots):
                            return potential_bots[idx][0]
                        print(f"Invalid choice. Enter 1-{len(potential_bots)}")
                    except ValueError:
                        print("Please enter a valid number")
                
                continue  # Go back to path entry
        
        # If it's a file
        elif os.path.isfile(bot_path):
            if not bot_path.endswith('.py'):
                print(f"[ERROR] File must be a Python file (.py)\n")
                continue
            print(f"\n[INFO] Using bot file: {os.path.basename(bot_path)}")
            return bot_path
        
        else:
            print(f"[ERROR] Path not found: {bot_path}")
            print("Please check the path and try again.\n")
            continue


def load_bot_module(bot_module_path):
    """
    Dynamically load a bot module from a file path.
    
    Args:
        bot_module_path: Path to the bot module (e.g., 'app.py' or '/path/to/mybot.py')
    
    Returns:
        Tuple of (module, flask_app, bot_mutable_state_dict)
    """
    # Convert to absolute path
    if not os.path.isabs(bot_module_path):
        bot_module_path = os.path.abspath(bot_module_path)
    
    if not os.path.exists(bot_module_path):
        raise FileNotFoundError(f"Bot module not found: {bot_module_path}")
    
    # Get the directory containing the bot file
    bot_dir = os.path.dirname(bot_module_path)
    
    # Save current working directory and sys.path
    original_cwd = os.getcwd()
    original_sys_path = sys.path.copy()
    try:
        os.chdir(bot_dir)
        
        # Add bot directory to sys.path so it can import its own modules (like config.py)
        if bot_dir not in sys.path:
            sys.path.insert(0, bot_dir)
        
        # Clear any previously cached module with the same name
        module_name = Path(bot_module_path).stem
        for mod_key in list(sys.modules.keys()):
            if module_name in mod_key:
                del sys.modules[mod_key]
        
        # Mock environment variables if not already set
        os.environ.setdefault("GROUPME_USER_ACCESS_TOKEN", "test_token_12345")
        os.environ.setdefault("GROUPME_GROUP_ID", "test_group_123")
        os.environ.setdefault("GROUPME_BOT_ID", "test_bot_123")
        
        # Load the module
        spec = importlib.util.spec_from_file_location(module_name, bot_module_path)
        bot_module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = bot_module
        spec.loader.exec_module(bot_module)
        
        # Find the Flask app instance
        flask_app = None
        for attr_name in dir(bot_module):
            if attr_name.startswith('_'):
                continue
            attr = getattr(bot_module, attr_name)
            # Check if it's a Flask app instance (not the Flask class itself)
            if hasattr(attr, 'test_client') and hasattr(attr, 'route'):
                try:
                    # Try to call test_client() - if it works, it's a Flask app instance
                    attr.test_client()
                    flask_app = attr
                    break
                except TypeError:
                    # If it fails with TypeError, it's likely the Flask class, not an instance
                    pass
        
        if not flask_app:
            raise RuntimeError(f"No Flask app instance found in {bot_module_path}")
        
        # Collect mutable state attributes (typically uppercase, dict/set-like)
        bot_state = {}
        for attr_name in dir(bot_module):
            if attr_name.isupper():
                attr = getattr(bot_module, attr_name)
                if isinstance(attr, (dict, set, list)):
                    bot_state[attr_name] = attr
        
        if not bot_state:
            print("[WARNING] No mutable state dicts found in bot module")
        
        return bot_module, flask_app, bot_state
    finally:
        # Always restore the original working directory and sys.path
        os.chdir(original_cwd)
        sys.path = original_sys_path


class InteractiveTester:
    def __init__(self, bot_module_path=None):
        """
        Initialize the interactive tester with a bot module.
        
        Args:
            bot_module_path: Optional path to bot module. If None, shows startup menu.
        """
        # Show startup menu if no path provided
        if bot_module_path is None:
            bot_module_path = get_bot_path_startup()
            if bot_module_path is None:
                print("\nCancelled.")
                sys.exit(0)
        
        self.bot_module_path = bot_module_path
        self.bot_name = os.path.basename(bot_module_path).replace('.py', '')
        self.bot_module = None
        self.app = None
        self.bot_state = {}
        self.webhook_route = "/"  # Will be updated by _load_bot
        self.bot_type = None  # 'flask' or 'polling'
        self._load_bot()
        
        self.sent_messages = []
        self.deleted_messages = []
        self.banned_members = []
        self.dummies = {
            "TestUser": "123"
        }
        self.active_user = "TestUser"
        self._next_dummy_id = 200
        self._next_message_id = 1
        self._message_store = {}
        self._original_requests_get = None

    def _load_bot(self):
        """Load the bot module."""
        try:
            # Auto-detect bot type by analyzing the code
            with open(self.bot_module_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()  # Read entire file for better detection
                
                # Strong polling indicators
                has_watch_for_messages = 'watch_for_messages' in content or 'while True:' in content and 'groupme_api' in content
                has_groupme_api = content.count('groupme_api(') > 1  # Multiple API calls
                has_send_message_func = 'def send_message(' in content or 'send_message(' in content
                
                # Strong Flask indicators (actual Flask app instantiation, not just imports)
                has_flask_app = 'app = Flask(' in content or 'app=Flask(' in content
                has_flask_routes = '@app.route(' in content or '@app.post(' in content
                
                # Score-based detection
                polling_score = 0
                flask_score = 0
                
                if has_watch_for_messages:
                    polling_score += 10  # Very strong indicator
                if has_groupme_api:
                    polling_score += 5
                if has_send_message_func:
                    polling_score += 3
                
                if has_flask_app:
                    flask_score += 10  # Very strong indicator
                if has_flask_routes:
                    flask_score += 5
                
                # Determine bot type based on scores
                is_polling = polling_score > flask_score
            
            if is_polling:
                # Polling bot
                self.bot_type = 'polling'
                self.bot_module = self._load_polling_bot()
                print("\n" + "="*70)
                print(f"BOT LOADED: {self.bot_name}")
                print("="*70)
                print(f"[INFO] Type: Polling Bot")
                print(f"[INFO] Path: {self.bot_module_path}")
                # For polling bots, collect state variables
                self._collect_bot_state_polling()
                print("="*70 + "\n")
            else:
                # Flask bot
                self.bot_type = 'flask'
                self.bot_module, self.app, self.bot_state = load_bot_module(self.bot_module_path)
                print("\n" + "="*70)
                print(f"BOT LOADED: {self.bot_name}")
                print("="*70)
                print(f"[INFO] Type: Flask Bot")
                print(f"[INFO] Path: {self.bot_module_path}")
                if self.bot_state:
                    print(f"[INFO] Found state attributes: {', '.join(self.bot_state.keys())}")
                print("="*70 + "\n")

                if hasattr(self.bot_module, "requests"):
                    self._original_requests_get = self.bot_module.requests.get
                
                # Auto-detect the webhook route
                self._detect_webhook_route()
        except Exception as e:
            print(f"[ERROR] Failed to load bot: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _load_polling_bot(self):
        """Load a polling bot module."""
        bot_module_path = self.bot_module_path
        
        # Convert to absolute path
        if not os.path.isabs(bot_module_path):
            bot_module_path = os.path.abspath(bot_module_path)
        
        # Get the directory containing the bot file
        bot_dir = os.path.dirname(bot_module_path)
        
        # Save current working directory and sys.path
        original_cwd = os.getcwd()
        original_sys_path = sys.path.copy()
        try:
            os.chdir(bot_dir)
            
            # Add bot directory to sys.path so it can import its own modules (like config.py)
            if bot_dir not in sys.path:
                sys.path.insert(0, bot_dir)
            
            # Create mock config module if config.py exists but might need defaults
            config_path = os.path.join(bot_dir, "config.py")
            if os.path.exists(config_path):
                # Load config module and inject test values if needed
                try:
                    import config
                    # Inject test values for any missing attributes
                    if not hasattr(config, 'TOKEN'):
                        config.TOKEN = "test_token_12345"
                    if not hasattr(config, 'GROUP_ID'):
                        config.GROUP_ID = "test_group_123"
                    if not hasattr(config, 'MAIN_GROUP_ID'):
                        config.MAIN_GROUP_ID = "test_group_123"
                    if not hasattr(config, 'YOUR_USER_ID'):
                        config.YOUR_USER_ID = "test_user_123"
                    if not hasattr(config, 'BASE_URL'):
                        config.BASE_URL = "https://api.groupme.com/v3"
                except:
                    pass
            
            # Mock environment variables if not already set
            os.environ.setdefault("GROUPME_USER_ACCESS_TOKEN", "test_token_12345")
            os.environ.setdefault("GROUPME_GROUP_ID", "test_group_123")
            os.environ.setdefault("GROUPME_BOT_ID", "test_bot_123")
            os.environ.setdefault("GROUP_ID", "test_group_123")
            os.environ.setdefault("BOT_ID", "test_bot_123")
            os.environ.setdefault("ACCESS_TOKEN", "test_token_12345")
            
            # Set flag to prevent bot from starting its main loop
            os.environ["TESTING_MODE"] = "1"
            
            # Clear any previously cached module with the same name
            module_name = Path(bot_module_path).stem
            for mod_key in list(sys.modules.keys()):
                if module_name in mod_key:
                    del sys.modules[mod_key]
            
            # Load the module
            spec = importlib.util.spec_from_file_location(module_name, bot_module_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            
            # Mock requests module to prevent actual API calls
            mock_response = MagicMock()
            mock_response.json.return_value = {"response": {"messages": []}}
            
            with ExitStack() as stack:
                # Suppress print statements during load
                stack.enter_context(patch('builtins.print'))
                # Mock requests to prevent API calls during init
                try:
                    import requests as req_mod
                    stack.enter_context(patch.object(req_mod, 'get', return_value=mock_response))
                    stack.enter_context(patch.object(req_mod, 'post', return_value=mock_response))
                except:
                    pass
                
                # Execute the module
                spec.loader.exec_module(module)
            
            return module
        finally:
            os.chdir(original_cwd)
            sys.path = original_sys_path
    
    def _collect_bot_state_polling(self):
        """Collect mutable state from polling bot."""
        # Common state variable names in polling bots
        state_names = ['MUTED', 'VIOLATION_COUNTS', 'settings', 'active_games', 
                       'timeouts', 'leaderboard', 'triggers']
        
        for name in state_names:
            if hasattr(self.bot_module, name):
                attr = getattr(self.bot_module, name)
                if isinstance(attr, (dict, list, set)):
                    self.bot_state[name] = attr
        
        if self.bot_state:
            print(f"[INFO] Found state attributes: {', '.join(self.bot_state.keys())}")
    
    def _detect_webhook_route(self):
        """Detect the webhook route for this bot."""
        if not self.app:
            self.webhook_route = "(polling bot - no webhook)"
            return
            
        # Default to root
        webhook_route = "/"
        
        # Check all routes for POST handlers
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
            # If no root route but other POST routes exist, use the first one
            webhook_route = routes[0]
        
        self.webhook_route = webhook_route
        print(f"[INFO] Using webhook route: {self.webhook_route} (POST routes: {', '.join(routes)})")


    def _get_muted_dict(self):
        """Get the MUTED or equivalent dict from the bot."""
        return self.bot_state.get('MUTED', {})
    
    def _get_violation_counts_dict(self):
        """Get the VIOLATION_COUNTS or equivalent dict from the bot."""
        return self.bot_state.get('VIOLATION_COUNTS', {})
    
    def _get_commands_dict(self):
        """Get the COMMANDS or equivalent dict from the bot."""
        # Try different possible names
        for name in ['COMMANDS', 'commands', 'COMMAND_MAP']:
            if name in self.bot_state:
                return getattr(self.bot_module, name)
        # If not in state dict, try direct attribute access
        for name in ['COMMANDS', 'commands', 'COMMAND_MAP']:
            if hasattr(self.bot_module, name):
                return getattr(self.bot_module, name)
        return {}


    def _get_active_user(self):
        user_id = self.dummies.get(self.active_user)
        if not user_id:
            user_id = "123"
        return self.active_user, user_id

    def _capture_delete(self, message_id):
        self.deleted_messages.append(message_id)
        return True

    def _capture_ban(self, membership_id):
        self.banned_members.append(membership_id)
        return True, ""

    def _get_image_dimensions(self, image_path):
        if not Image:
            return None
        try:
            with Image.open(image_path) as img:
                return img.size
        except Exception:
            return None

    def _build_message_response(self, message_id):
        record = self._message_store.get(message_id)
        attachments = []
        if record:
            for att in record.get("attachments", []):
                if att.get("type") == "image" and att.get("local_path"):
                    dims = self._get_image_dimensions(att.get("local_path"))
                    width = dims[0] if dims else None
                    height = dims[1] if dims else None
                    attachments.append({
                        "type": "image",
                        "url": f"local://{message_id}",
                        "original_width": width,
                        "original_height": height,
                        "width": width,
                        "height": height
                    })
                else:
                    attachments.append(att)

        return {
            "response": {
                "message": {
                    "attachments": attachments
                }
            }
        }

    def _mock_requests_get(self, url, *args, **kwargs):
        class _FakeResponse:
            def __init__(self, status_code, payload=None, content=b"", text=""):
                self.status_code = status_code
                self._payload = payload or {}
                self.content = content
                self.text = text

            def json(self):
                return self._payload

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise RuntimeError(f"HTTP {self.status_code}")

        parsed = urlparse(url)
        if parsed.scheme == "local":
            message_id = parsed.netloc or parsed.path.lstrip("/")
            record = self._message_store.get(message_id)
            local_path = None
            if record:
                for att in record.get("attachments", []):
                    if att.get("type") == "image" and att.get("local_path"):
                        local_path = att.get("local_path")
                        break
            if local_path and os.path.isfile(local_path):
                try:
                    with open(local_path, "rb") as f:
                        content = f.read()
                    return _FakeResponse(200, content=content)
                except Exception:
                    return _FakeResponse(500, text="Failed to read local image")
            return _FakeResponse(404, text="Local image not found")

        path_parts = parsed.path.strip("/").split("/")
        if "groups" in path_parts and "messages" in path_parts:
            try:
                msg_index = path_parts.index("messages")
                message_id = path_parts[msg_index + 1]
            except Exception:
                message_id = None

            if message_id and message_id in self._message_store:
                payload = self._build_message_response(message_id)
                return _FakeResponse(200, payload=payload)

        if self._original_requests_get:
            return self._original_requests_get(url, *args, **kwargs)
        return _FakeResponse(404, text="No handler for URL")

    def test_message(self, text, user_name=None, attachments=None, image_path=None):
        """Send a message and capture the response."""
        self.sent_messages = []  # Clear previous messages
        self.deleted_messages = []
        self.banned_members = []

        if self.bot_type == 'polling':
            return self._test_message_polling(text, user_name, attachments, image_path)
        else:
            return self._test_message_flask(text, user_name, attachments, image_path)
    
    def _test_message_polling(self, text, user_name=None, attachments=None, image_path=None):
        """Test a message for a polling bot."""
        text = self._rewrite_dummy_targets(text)
        
        def capture_message(msg_text, **kwargs):
            """Capture messages sent by the bot, ignoring extra kwargs like group_id, reply_to"""
            print(f"[DEBUG] Bot sent message: {msg_text}")
            self.sent_messages.append(msg_text)
        
        if user_name:
            user_id = self.dummies.get(user_name, "123")
        else:
            user_name, user_id = self._get_active_user()
        
        message_id = f"test_msg_{self._next_message_id}"
        self._next_message_id += 1

        if attachments is None:
            attachments = []
        if image_path:
            attachments = list(attachments) + [
                {
                    "type": "image",
                    "url": f"file://{image_path}"
                }
            ]

        # Create GroupMe-style message object
        import time
        msg = {
            "id": message_id,
            "user_id": user_id,
            "sender_id": user_id,
            "sender_type": "user",
            "name": user_name,
            "text": text,
            "created_at": int(time.time()),
            "attachments": attachments,
            "system": False
        }
        
        # Patch send_message everywhere (main module and all command modules)
        with ExitStack() as stack:
            # Patch in main module
            if hasattr(self.bot_module, 'send_message'):
                print(f"[DEBUG] Patching bot_module.send_message")
                stack.enter_context(patch.object(self.bot_module, 'send_message', capture_message))
            
            # Patch in all imported command/game modules that might have imported send_message
            for attr_name in dir(self.bot_module):
                attr = getattr(self.bot_module, attr_name)
                # Check if it's a module (command modules, game modules)
                if hasattr(attr, '__name__') and hasattr(attr, 'send_message'):
                    print(f"[DEBUG] Patching {attr.__name__}.send_message")
                    stack.enter_context(patch.object(attr, 'send_message', capture_message))
            
            # Also try patching in sys.modules for any Commands.* or Games.* modules
            for mod_name, mod in list(sys.modules.items()):
                if ('Commands.' in mod_name or 'Games.' in mod_name or 'Meme.' in mod_name) and hasattr(mod, 'send_message'):
                    print(f"[DEBUG] Patching {mod_name}.send_message")
                    stack.enter_context(patch.object(mod, 'send_message', capture_message))
            
            if hasattr(self.bot_module, 'delete_message'):
                stack.enter_context(patch.object(self.bot_module, 'delete_message', self._capture_delete))
            
            # Process message through bot's handlers
            self._process_polling_message(msg)
        
        print(f"[DEBUG] Captured {len(self.sent_messages)} messages")
        return self.sent_messages
    
    def _process_polling_message(self, msg):
        """Process a message through polling bot's handlers."""
        text = (msg.get("text") or "").strip().lower()
        raw_text = msg.get("text") or ""
        
        print(f"[DEBUG] Processing message: '{raw_text}'")
        print(f"[DEBUG] Bot module has these message handlers:")
        handlers = [attr for attr in dir(self.bot_module) if 'handle' in attr.lower() or attr in ['send_message', 'list_memes']]
        print(f"[DEBUG]   {', '.join(handlers)}")
        
        # Mimic the actual bot's message processing flow
        # Most handlers are called for EVERY message (they filter internally)
        
        # MEME COMMANDS (bot filters these)
        if hasattr(self.bot_module, 'handle_meme_command'):
            if text.startswith("!meme"):
                print(f"[DEBUG] Calling handle_meme_command")
                self.bot_module.handle_meme_command(msg)
        
        if hasattr(self.bot_module, 'list_memes'):
            if text == "!list":
                print(f"[DEBUG] Calling list_memes")
                memes = self.bot_module.list_memes()
                if hasattr(self.bot_module, 'send_message'):
                    if memes:
                        self.bot_module.send_message("Available meme templates:\\n" + "\\n".join(memes))
                    else:
                        self.bot_module.send_message("No meme templates found.")
        
        # GAME HANDLERS (called for every message, filter internally)
        if hasattr(self.bot_module, 'handle_tictactoe'):
            print(f"[DEBUG] Calling handle_tictactoe")
            self.bot_module.handle_tictactoe(msg)
        
        if hasattr(self.bot_module, 'handle_connect_four'):
            print(f"[DEBUG] Calling handle_connect_four")
            self.bot_module.handle_connect_four(msg)
        
        if hasattr(self.bot_module, 'handle_connectfour'):
            print(f"[DEBUG] Calling handle_connectfour")
            self.bot_module.handle_connectfour(msg)
        
        if hasattr(self.bot_module, 'handle_2048'):
            print(f"[DEBUG] Calling handle_2048")
            self.bot_module.handle_2048(msg)
        
        # 8BALL (called for every message, filters internally)
        if hasattr(self.bot_module, 'handle_eightball'):
            print(f"[DEBUG] Calling handle_eightball")
            self.bot_module.handle_eightball(msg)
        
        # HELP (called for every message, filters internally)
        if hasattr(self.bot_module, 'handle_help_command'):
            print(f"[DEBUG] Calling handle_help_command")
            self.bot_module.handle_help_command(msg)
        
        if hasattr(self.bot_module, 'handle_listtimeouts'):
            print(f"[DEBUG] Calling handle_listtimeouts")
            self.bot_module.handle_listtimeouts(msg)
        
        # RESTART
        if hasattr(self.bot_module, 'handle_restart'):
            print(f"[DEBUG] Calling handle_restart")
            self.bot_module.handle_restart(msg)
        
        # TRIGGERS (called for every message, filter internally)
        if hasattr(self.bot_module, 'handle_triggers'):
            print(f"[DEBUG] Calling handle_triggers")
            self.bot_module.handle_triggers(msg)
        
        if hasattr(self.bot_module, 'handle_addtrigger'):
            print(f"[DEBUG] Calling handle_addtrigger")
            self.bot_module.handle_addtrigger(msg)
        
        if hasattr(self.bot_module, 'handle_listtriggers'):
            print(f"[DEBUG] Calling handle_listtriggers")
            self.bot_module.handle_listtriggers(msg)
        
        if hasattr(self.bot_module, 'handle_rmtrigger'):
            print(f"[DEBUG] Calling handle_rmtrigger")
            self.bot_module.handle_rmtrigger(msg)
        
        # LEADERBOARD COMMANDS (called for every message, filter internally)
        if hasattr(self.bot_module, 'handle_leaderboard_command'):
            print(f"[DEBUG] Calling handle_leaderboard_command")
            self.bot_module.handle_leaderboard_command(msg)
        
        # Admin commands
        if text == "!admins" and hasattr(self.bot_module, 'get_admin_list_text'):
            admin_text = self.bot_module.get_admin_list_text()
            if hasattr(self.bot_module, 'send_message'):
                self.bot_module.send_message(admin_text)
    
    def _test_message_flask(self, text, user_name=None, attachments=None, image_path=None):
        """Test a message for a Flask bot."""
        text = self._rewrite_dummy_targets(text)
        
        def capture_message(msg_text):
            self.sent_messages.append(msg_text)
        
        if user_name:
            user_id = self.dummies.get(user_name, "123")
        else:
            user_name, user_id = self._get_active_user()
        message_id = f"test_msg_{self._next_message_id}"
        self._next_message_id += 1

        if attachments is None:
            attachments = []
        if image_path:
            attachments = list(attachments) + [
                {
                    "type": "image",
                    "local_path": image_path
                }
            ]

        self._message_store[message_id] = {
            "attachments": attachments
        }

        event = {
            "id": message_id,
            "sender_id": user_id,
            "sender_type": "user",
            "name": user_name,
            "text": text,
            "created_at": 123,
            "attachments": attachments
        }
        
        client = self.app.test_client()
        
        # Dynamically patch bot methods using ExitStack for clean multiple patches
        with ExitStack() as stack:
            if hasattr(self.bot_module, 'send_message'):
                stack.enter_context(patch.object(self.bot_module, 'send_message', capture_message))
            if hasattr(self.bot_module, 'delete_message'):
                stack.enter_context(patch.object(self.bot_module, 'delete_message', self._capture_delete))
            if hasattr(self.bot_module, 'ban_member'):
                stack.enter_context(patch.object(self.bot_module, 'ban_member', self._capture_ban))
            if hasattr(self.bot_module, 'api_delete'):
                stack.enter_context(patch.object(self.bot_module, 'api_delete', return_value=MagicMock()))
            if hasattr(self.bot_module, 'requests'):
                stack.enter_context(patch.object(self.bot_module.requests, 'get', self._mock_requests_get))
            
            client.post(self.webhook_route, json=event)
        
        return self.sent_messages


    def _rewrite_dummy_targets(self, text):
        lower_text = (text or "").strip().lower()
        if lower_text.startswith("sigma mute") or lower_text.startswith("/mute"):
            parts = text.split()
            if len(parts) >= 3:
                target = parts[2] if parts[0].lower() == "sigma" else parts[1]
                if not target.isdigit() and target in self.dummies:
                    parts[2 if parts[0].lower() == "sigma" else 1] = self.dummies[target]
                    return " ".join(parts)
        if lower_text.startswith("sigma unmute") or lower_text.startswith("/unmute"):
            parts = text.split()
            if len(parts) >= 2:
                target = parts[2] if parts[0].lower() == "sigma" and len(parts) >= 3 else parts[1]
                if not target.isdigit() and target in self.dummies:
                    parts[2 if parts[0].lower() == "sigma" and len(parts) >= 3 else 1] = self.dummies[target]
                    return " ".join(parts)
        return text

    def show_commands(self):
        """Show all available commands."""
        print("\n" + "="*70)
        print("AVAILABLE COMMANDS")
        print("="*70)
        commands = self._get_commands_dict()
        if not commands:
            print("  (no commands found)")
        else:
            for i, cmd in enumerate(commands.keys(), 1):
                response = commands[cmd].get("response", "")
                action = commands[cmd].get("action", "")
                always = commands[cmd].get("always", False)
                
                if response:
                    desc = f"-> {response[:55]}"
                elif action:
                    desc = f"-> [ACTION: {action}]"
                else:
                    desc = "-> ???"
                
                if always:
                    desc += " (ALWAYS ON)"
                
                print(f"  {i:2}. {cmd:20} {desc}")
        print("="*70)

    def show_state(self):
        """Display current bot state."""
        print("\n" + "-"*70)
        print("BOT STATE")
        print("-"*70)
        muted = self._get_muted_dict()
        violations = self._get_violation_counts_dict()
        print(f"  Muted users: {dict(muted) if muted else 'None'}")
        print(f"  Violation counts: {dict(violations) if violations else 'None'}")
        print(f"  Deleted messages: {self.deleted_messages if self.deleted_messages else 'None'}")
        print(f"  Banned members: {self.banned_members if self.banned_members else 'None'}")
        print("-"*70)

    def run(self):
        """Run interactive test mode."""
        print("\n" + "="*70)
        print(f"BOT INTERACTIVE TESTER - {os.path.basename(self.bot_module_path)}".center(70))
        print("="*70)
        print("\nCommands:")
        print("  <message>    - Send a message to the bot")
        print("  user:NAME    - Change user (default: TestUser)")
        print("  dummy add NAME [ID] - Add a dummy user")
        print("  dummy use NAME     - Switch active dummy user")
        print("  dummy list         - List dummy users")
        print("  dummy del NAME     - Remove a dummy user")
        print("  dummy clear        - Remove all dummy users")
        print("  say NAME:MESSAGE   - Send a message as a dummy user")
        print("  cmds         - List all available commands")
        print("  state        - Show bot memory (mutes, violations)")
        print("  reset        - Clear bot memory")
        print("  help         - Show this help")
        print("  quit/exit    - Exit the tester")
        print("="*70)

        while True:
            try:
                user_input = input(f"\n[{self.active_user}]> ").strip()

                if not user_input:
                    continue
                elif user_input.lower() in ["quit", "exit"]:
                    print("\nGoodbye!")
                    break
                elif user_input.lower() == "help":
                    print("\nCommands:")
                    print("  <message>    - Send a message to the bot")
                    print("  user:NAME    - Change user")
                    print("  dummy add NAME [ID] - Add a dummy user")
                    print("  dummy use NAME     - Switch active dummy user")
                    print("  dummy list         - List dummy users")
                    print("  dummy del NAME     - Remove a dummy user")
                    print("  dummy clear        - Remove all dummy users")
                    print("  say NAME:MESSAGE   - Send a message as a dummy user")
                    print("  cmds         - List all commands")
                    print("  state        - Show bot memory")
                    print("  reset        - Clear bot memory")
                    print("  quit/exit    - Exit")
                elif user_input.lower() == "state":
                    self.show_state()
                elif user_input.lower() == "cmds":
                    self.show_commands()
                elif user_input.lower() == "reset":
                    # Clear all state dicts
                    for state_dict in self.bot_state.values():
                        if isinstance(state_dict, dict):
                            state_dict.clear()
                    print("Bot memory cleared")
                elif user_input.lower().startswith("user:"):
                    new_user = user_input[5:].strip()
                    if new_user:
                        self.active_user = new_user
                        if new_user not in self.dummies:
                            self.dummies[new_user] = "123"
                        print(f"User changed to: {new_user}")
                    else:
                        print("Usage: user:NAME")
                elif user_input.lower().startswith("dummy "):
                    parts = user_input.split()
                    if len(parts) >= 2 and parts[1] == "add":
                        if len(parts) < 3:
                            print("Usage: dummy add NAME [ID]")
                        else:
                            if parts[-1].isdigit() and len(parts) >= 4:
                                user_id = parts[-1]
                                name = " ".join(parts[2:-1]).strip()
                            elif parts[-1].isdigit() and len(parts) == 3:
                                name = parts[2]
                                user_id = parts[-1]
                            else:
                                name = " ".join(parts[2:]).strip()
                                user_id = str(self._next_dummy_id)
                                self._next_dummy_id += 1

                            if not name:
                                print("Usage: dummy add NAME [ID]")
                            else:
                                self.dummies[name] = user_id
                                self.active_user = name
                                print(f"Dummy added: {name} ({user_id})")
                    elif len(parts) >= 2 and parts[1] == "use":
                        if len(parts) < 3:
                            print("Usage: dummy use NAME")
                        else:
                            name = parts[2]
                            if name in self.dummies:
                                self.active_user = name
                                print(f"Active dummy: {name} ({self.dummies[name]})")
                            else:
                                print("Dummy not found. Use 'dummy list'.")
                    elif len(parts) >= 2 and parts[1] == "list":
                        print("Dummies:")
                        for name, user_id in self.dummies.items():
                            marker = "*" if name == self.active_user else " "
                            print(f" {marker} {name}: {user_id}")
                    elif len(parts) >= 2 and parts[1] == "del":
                        if len(parts) < 3:
                            print("Usage: dummy del NAME")
                        else:
                            name = parts[2]
                            if name in self.dummies:
                                del self.dummies[name]
                                if self.active_user == name:
                                    self.active_user = "TestUser"
                                    self.dummies.setdefault("TestUser", "123")
                                print(f"Dummy removed: {name}")
                            else:
                                print("Dummy not found. Use 'dummy list'.")
                    elif len(parts) >= 2 and parts[1] == "clear":
                        self.dummies = {"TestUser": "123"}
                        self.active_user = "TestUser"
                        print("All dummies cleared")
                    else:
                        print("Usage: dummy add/use/list/del/clear")
                elif user_input.lower().startswith("say "):
                    payload = user_input[4:].strip()
                    if ":" not in payload:
                        print("Usage: say NAME:MESSAGE")
                    else:
                        name, message = payload.split(":", 1)
                        name = name.strip()
                        message = message.strip()
                        if not name or not message:
                            print("Usage: say NAME:MESSAGE")
                        elif name not in self.dummies:
                            print("Dummy not found. Use 'dummy list'.")
                        else:
                            responses = self.test_message(message, name)
                            if responses:
                                print("\nBot responses:")
                                for i, response in enumerate(responses, 1):
                                    print(f"  [{i}] {response}")
                            else:
                                print("(no response)")
                            if self.deleted_messages:
                                print(f"Deleted messages: {self.deleted_messages}")
                            if self.banned_members:
                                print(f"Banned members: {self.banned_members}")
                else:
                    # Send message to bot
                    responses = self.test_message(user_input)
                    if responses:
                        print("\nBot responses:")
                        for i, response in enumerate(responses, 1):
                            print(f"  [{i}] {response}")
                    else:
                        print("(no response)")
                    if self.deleted_messages:
                        print(f"Deleted messages: {self.deleted_messages}")
                    if self.banned_members:
                        print(f"Banned members: {self.banned_members}")

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    # Auto-discover bot, or accept optional path as argument
    bot_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        tester = InteractiveTester(bot_module_path=bot_path)
        tester.run()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)

