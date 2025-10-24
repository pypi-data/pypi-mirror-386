#!/usr/bin/env python3
"""
SecureChat Setup Script
Automated installation and configuration for SecureChat
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
import argparse
import platform
import urllib.request
import zipfile
import tarfile

class SecureChatSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.config_dir = Path.home() / ".securechat"
        self.config_file = self.config_dir / "config.json"
        self.cert_dir = self.config_dir / "certs"
        self.data_dir = self.config_dir / "data"
        self.log_dir = self.config_dir / "logs"

    def print_banner(self):
        print("""
╔══════════════════════════════════════════════════════════════╗
║                    🔐 SECURECHAT SETUP 🔐                    ║
║              Ultra-Secure Private Messaging Platform         ║
╚══════════════════════════════════════════════════════════════╝
""")

    def check_python_version(self):
        """Check if Python version is compatible"""
        if sys.version_info < (3, 8):
            print("❌ Error: Python 3.8 or higher is required")
            print(f"   Current version: {sys.version}")
            return False
        print(f"✅ Python {sys.version.split()[0]} - OK")
        return True

    def check_dependencies(self):
        """Check and install required dependencies"""
        required_packages = [
            "cryptography>=3.4.0",
            "setuptools>=61.0"
        ]

        print("\n📦 Checking dependencies...")

        # Check if pip is available
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "--version"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            print("❌ pip is not available. Please install pip first.")
            return False

        # Install required packages
        for package in required_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"✅ {package} - OK")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {package}")
                return False

        return True

    def create_directories(self):
        """Create necessary directories"""
        print("\n📁 Creating directories...")

        directories = [self.config_dir, self.cert_dir, self.data_dir, self.log_dir]

        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created {directory}")
            except Exception as e:
                print(f"❌ Failed to create {directory}: {e}")
                return False

        return True

    def generate_certificates(self):
        """Generate SSL certificates"""
        print("\n🔐 Generating SSL certificates...")

        # Import here to avoid issues if dependencies aren't installed yet
        try:
            from securechat.crypto import generate_self_signed_cert
        except ImportError:
            print("❌ Could not import SecureChat crypto module")
            return False

        cert_file = self.cert_dir / "server.crt"
        key_file = self.cert_dir / "server.key"

        try:
            generate_self_signed_cert(str(cert_file), str(key_file))
            print(f"✅ Certificates generated:")
            print(f"   Certificate: {cert_file}")
            print(f"   Private Key: {key_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to generate certificates: {e}")
            return False

    def create_config_file(self):
        """Create default configuration file"""
        print("\n⚙️  Creating configuration...")

        default_config = {
            "server": {
                "host": "0.0.0.0",
                "port": 12346,
                "max_clients": 1000,
                "max_message_size": 1048576,  # 1MB
                "federation_timeout": 30,
                "message_ttl_days": 7,
                "rate_limit_per_second": 10
            },
            "security": {
                "certificate_file": str(self.cert_dir / "server.crt"),
                "key_file": str(self.cert_dir / "server.key"),
                "require_certificate_validation": True,
                "certificate_check_interval_hours": 24
            },
            "storage": {
                "database_file": str(self.data_dir / "securechat.db"),
                "backup_directory": str(self.data_dir / "backups"),
                "max_backup_files": 10
            },
            "logging": {
                "log_directory": str(self.log_dir),
                "log_level": "INFO",
                "max_log_size_mb": 100,
                "max_log_files": 5
            },
            "features": {
                "federation_enabled": True,
                "file_sharing_enabled": True,
                "offline_messaging_enabled": True,
                "group_chat_enabled": True
            }
        }

        try:
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"✅ Configuration created: {self.config_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to create configuration: {e}")
            return False

    def create_startup_scripts(self):
        """Create convenient startup scripts"""
        print("\n🚀 Creating startup scripts...")

        # Create server startup script
        server_script = self.config_dir / "start-server.py"
        server_content = f'''#!/usr/bin/env python3
"""
SecureChat Server Startup Script
"""
import sys
import os
sys.path.insert(0, r"{self.project_root}")

from securechat.server import SecureChatServer
import json

def main():
    # Load configuration
    config_file = r"{self.config_file}"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        server_config = config.get('server', {{}})
        security_config = config.get('security', {{}})
        storage_config = config.get('storage', {{}})
    else:
        server_config = {{}}
        security_config = {{}}
        storage_config = {{}}

    # Start server with config
    server = SecureChatServer(
        host=server_config.get('host', '0.0.0.0'),
        port=server_config.get('port', 12346),
        cert_file=security_config.get('certificate_file', 'server.crt'),
        key_file=security_config.get('key_file', 'server.key'),
        db_path=storage_config.get('database_file', 'securechat.db')
    )
    server.start()

if __name__ == '__main__':
    main()
'''

        try:
            with open(server_script, 'w') as f:
                f.write(server_content)
            # Make executable on Unix-like systems
            if platform.system() != 'Windows':
                os.chmod(server_script, 0o755)
            print(f"✅ Server startup script: {server_script}")
        except Exception as e:
            print(f"❌ Failed to create server script: {e}")
            return False

        # Create client launcher script
        client_script = self.config_dir / "launch-client.py"
        client_content = f'''#!/usr/bin/env python3
"""
SecureChat Client Launcher
"""
import sys
import os
sys.path.insert(0, r"{self.project_root}")

from securechat.client import SecureChatClient
import argparse

def main():
    parser = argparse.ArgumentParser(description='SecureChat Client')
    parser.add_argument('server', help='Server address (host:port)')
    parser.add_argument('username', help='Your username')
    args = parser.parse_args()

    host, port = args.server.split(':')
    client = SecureChatClient(host, int(port), args.username)
    client.connect()

if __name__ == '__main__':
    main()
'''

        try:
            with open(client_script, 'w') as f:
                f.write(client_content)
            if platform.system() != 'Windows':
                os.chmod(client_script, 0o755)
            print(f"✅ Client launcher script: {client_script}")
        except Exception as e:
            print(f"❌ Failed to create client script: {e}")
            return False

        return True

    def create_desktop_shortcuts(self):
        """Create desktop shortcuts for easy access"""
        print("\n🖥️  Creating desktop shortcuts...")

        if platform.system() == 'Windows':
            # Create Windows shortcuts
            try:
                import winshell  # type: ignore
                from win32com.client import Dispatch  # type: ignore

                desktop = winshell.desktop()
                shell = Dispatch('WScript.Shell')

                # Server shortcut
                server_shortcut = shell.CreateShortCut(str(Path(desktop) / "SecureChat Server.lnk"))
                server_shortcut.Targetpath = sys.executable
                server_shortcut.Arguments = str(self.config_dir / "start-server.py")
                server_shortcut.WorkingDirectory = str(self.config_dir)
                server_shortcut.IconLocation = sys.executable
                server_shortcut.save()

                # Client shortcut
                client_shortcut = shell.CreateShortCut(str(Path(desktop) / "SecureChat Client.lnk"))
                client_shortcut.Targetpath = sys.executable
                client_shortcut.Arguments = str(self.config_dir / "launch-client.py")
                client_shortcut.WorkingDirectory = str(self.config_dir)
                client_shortcut.IconLocation = sys.executable
                client_shortcut.save()

                print("✅ Desktop shortcuts created")
                return True

            except ImportError:
                print("ℹ️  Desktop shortcuts require pywin32 (optional)")
                return True
            except Exception as e:
                print(f"⚠️  Could not create desktop shortcuts: {e}")
                return True

        elif platform.system() == 'Linux':
            # Create Linux desktop files
            desktop_dir = Path.home() / ".local" / "share" / "applications"
            desktop_dir.mkdir(parents=True, exist_ok=True)

            server_desktop = desktop_dir / "securechat-server.desktop"
            server_content = f"""[Desktop Entry]
Name=SecureChat Server
Comment=Start SecureChat Server
Exec={sys.executable} {self.config_dir / "start-server.py"}
Terminal=true
Type=Application
Categories=Network;
"""

            client_desktop = desktop_dir / "securechat-client.desktop"
            client_content = f"""[Desktop Entry]
Name=SecureChat Client
Comment=Launch SecureChat Client
Exec={sys.executable} {self.config_dir / "launch-client.py"}
Terminal=true
Type=Application
Categories=Network;
"""

            try:
                with open(server_desktop, 'w') as f:
                    f.write(server_content)
                with open(client_desktop, 'w') as f:
                    f.write(client_content)

                # Make executable
                os.chmod(server_desktop, 0o755)
                os.chmod(client_desktop, 0o755)

                print("✅ Desktop launchers created")
                return True
            except Exception as e:
                print(f"⚠️  Could not create desktop launchers: {e}")
                return True

        else:
            print("ℹ️  Desktop shortcuts not supported on this platform")
            return True

    def install_package(self):
        """Install the SecureChat package"""
        print("\n📦 Installing SecureChat package...")

        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", str(self.project_root)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("✅ SecureChat package installed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install package: {e}")
            return False

    def create_readme(self):
        """Create a quick start guide"""
        print("\n📖 Creating quick start guide...")

        readme_content = f"""# SecureChat - Quick Start Guide

## Installation Complete!

Your SecureChat installation is ready. Here's how to get started:

## Starting the Server

### Option 1: Use the startup script
python {self.config_dir / "start-server.py"}

### Option 2: Use the installed command
securechat server

## Connecting as a Client

### Option 1: Use the launcher script
python {self.config_dir / "launch-client.py"} localhost:12346 your_username

### Option 2: Use the installed command
securechat client localhost:12346 your_username

## Configuration

Your configuration file is located at:
{self.config_file}

You can edit this file to customize server settings, security options, and features.

## What's Next?

1. Start the server on your main machine
2. Connect clients from any device on your network
3. Try federation by connecting multiple servers together
4. Explore features like group chat, file sharing, and offline messaging

## Security Notes

- Your private keys are encrypted with your password
- All communication is end-to-end encrypted
- SSL/TLS protects transport layer security
- Certificates are automatically validated

## Need Help?

- Check the logs in: {self.log_dir}
- Configuration file: {self.config_file}
- Certificates: {self.cert_dir}

Happy secure chatting!

---
Generated by SecureChat Setup on {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        readme_file = self.config_dir / "QUICKSTART.md"
        try:
            with open(readme_file, 'w') as f:
                f.write(readme_content)
            print(f"✅ Quick start guide created: {readme_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to create quick start guide: {e}")
            return False

    def run_setup(self):
        """Run the complete setup process"""
        self.print_banner()

        print("🔧 Starting SecureChat setup...\n")

        # Run all setup steps
        steps = [
            ("Checking Python version", self.check_python_version),
            ("Checking dependencies", self.check_dependencies),
            ("Creating directories", self.create_directories),
            ("Installing package", self.install_package),
            ("Generating certificates", self.generate_certificates),
            ("Creating configuration", self.create_config_file),
            ("Creating startup scripts", self.create_startup_scripts),
            ("Creating desktop shortcuts", self.create_desktop_shortcuts),
            ("Creating quick start guide", self.create_readme),
        ]

        success_count = 0
        for step_name, step_func in steps:
            print(f"🔄 {step_name}...")
            if step_func():
                success_count += 1
            else:
                print(f"❌ Setup failed at: {step_name}")
                return False

        print(f"\n🎊 Setup completed successfully! ({success_count}/{len(steps)} steps)")
        print(f"\n📂 Configuration directory: {self.config_dir}")
        print(f"📖 Quick start guide: {self.config_dir / 'QUICKSTART.md'}")
        print("\n🚀 Ready to start chatting securely!")

        return True

def main():
    parser = argparse.ArgumentParser(description='SecureChat Setup')
    parser.add_argument('--config-dir', help='Custom configuration directory')
    parser.add_argument('--force', action='store_true', help='Force reinstallation')
    args = parser.parse_args()

    setup = SecureChatSetup()

    if args.config_dir:
        setup.config_dir = Path(args.config_dir)
        setup.config_file = setup.config_dir / "config.json"
        setup.cert_dir = setup.config_dir / "certs"
        setup.data_dir = setup.config_dir / "data"
        setup.log_dir = setup.config_dir / "logs"

    if args.force:
        print("🧹 Force reinstallation requested...")
        import shutil
        if setup.config_dir.exists():
            shutil.rmtree(setup.config_dir)
            print(f"✅ Removed existing configuration: {setup.config_dir}")

    success = setup.run_setup()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()