#!/usr/bin/env python3
import os
import shutil
import hashlib
import json
import difflib
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Constants
GITNOT_DIR = ".gitnot"
SNAPSHOT_DIR = os.path.join(GITNOT_DIR, "snapshot")
CHANGELOG_DIR = os.path.join(GITNOT_DIR, "changelogs")
DELETED_DIR = os.path.join(GITNOT_DIR, "deleted")
HASHES_FILE = os.path.join(GITNOT_DIR, "hashes.json")
VERSION_FILE = os.path.join(GITNOT_DIR, "version.txt")
CONFIG_FILE = os.path.join(GITNOT_DIR, "config.json")

# Default configuration
DEFAULT_CONFIG = {
    "extensions": [".txt", ".md", ".csv", ".log", ".py", ".js", ".sh", 
                   ".html", ".css", ".c", ".java", ".json", ".yaml", 
                   ".yml", ".ini", ".toml", ".xml", ".rtf"],
    "ignore_patterns": ["*.tmp", "*.bak"]
}

def load_config():
    """Load configuration from config file or return defaults"""
    if Path(CONFIG_FILE).exists():
        try:
            return load_json(CONFIG_FILE)
        except:
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG

def safe_makedirs(path):
    """Create directories safely, handling empty paths"""
    dirname = os.path.dirname(path)
    if dirname and dirname != '.' and dirname != '':
        os.makedirs(dirname, exist_ok=True)

def should_ignore_file(file_path, ignore_patterns):
    """Check if file should be ignored based on patterns"""
    file_path = Path(file_path)
    
    for pattern in ignore_patterns:
        # Handle directory patterns like "node_modules/*" or "__pycache__/*"
        if pattern.endswith('/*'):
            dir_pattern = pattern[:-2]  # Remove /*
            if any(part == dir_pattern for part in file_path.parts):
                return True
        # Handle glob patterns like "*.tmp", "*.bak", "test_*"
        elif '*' in pattern or '?' in pattern:
            if file_path.match(pattern):
                return True
        # Handle exact filename matches like ".DS_Store", "Thumbs.db"
        else:
            if file_path.name == pattern:
                return True
    return False

def get_all_text_files(folder):
    """Get all text files based on configuration"""
    config = load_config()
    text_extensions = set(config["extensions"])
    ignore_patterns = config.get("ignore_patterns", [])
    
    files = []
    for f in Path(folder).rglob('*'):
        if (f.suffix.lower() in text_extensions and 
            f.is_file() and 
            not str(f).startswith(GITNOT_DIR) and
            not should_ignore_file(f, ignore_patterns)):
            files.append(f)
    return files

def hash_file(file_path):
    """Hash file in chunks - handles large files gracefully"""
    hasher = hashlib.sha1()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (OSError, IOError):
        # Return a consistent hash for unreadable files
        return f"unreadable-{os.path.basename(file_path)}"

def load_json(path):
    """Load JSON file with error handling"""
    if Path(path).exists():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}
    return {}

def save_json(path, data):
    """Save JSON file with error handling"""
    try:
        safe_makedirs(path)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except (OSError, UnicodeEncodeError) as e:
        print(f"⚠️  Warning: Could not save {path}: {e}")

def read_version():
    """Read version number from file"""
    if Path(VERSION_FILE).exists():
        try:
            with open(VERSION_FILE, 'r', encoding='utf-8') as f:
                return float(f.read().strip())
        except (ValueError, UnicodeDecodeError):
            return 0.0
    return 0.0

def write_version(version):
    """Write version number to file"""
    try:
        os.makedirs(GITNOT_DIR, exist_ok=True)
        with open(VERSION_FILE, 'w', encoding='utf-8') as f:
            f.write(f"{version:.1f}")
    except OSError as e:
        print(f"⚠️  Warning: Could not write version: {e}")

def bump_version():
    """Increment version number"""
    version = read_version() + 0.1
    write_version(version)
    return version

def format_diff_as_markdown(diff_lines):
    """
    Convert unified-diff output into a human-friendly
    Markdown section. Identical -/+ pairs (typical of
    newline-only changes) are ignored so they don't show
    up in both Added and Removed lists.
    """
    output, add, remove = [], [], []
    old_ln = new_ln = 0
    i = 0
    while i < len(diff_lines):
        line = diff_lines[i]

        # New hunk header  --- @@ -a,b +c,d @@
        if line.startswith('@@'):
            parts = line.split()
            if len(parts) >= 3:
                try:
                    old_ln = int(parts[1].split(',')[0][1:])
                    new_ln = int(parts[2].split(',')[0][1:])
                except (ValueError, IndexError):
                    old_ln = new_ln = 0
            i += 1
            continue

        # Look-ahead for identical -/+ pair (newline / whitespace change)
        if (line.startswith('-') and i + 1 < len(diff_lines)
                and diff_lines[i + 1].startswith('+')
                and line[1:].rstrip() == diff_lines[i + 1][1:].rstrip()):
            # Skip both lines, just advance counters
            old_ln += 1
            new_ln += 1
            i += 2
            continue

        if line.startswith('-') and not line.startswith('---'):
            remove.append(f"L{old_ln}: {line[1:].rstrip()}")
            old_ln += 1
        elif line.startswith('+') and not line.startswith('+++'):
            add.append(f"L{new_ln}: {line[1:].rstrip()}")
            new_ln += 1
        else:
            # Context line or \ No newline at end of file
            if not line.startswith('\\'):
                old_ln += 1
                new_ln += 1
        i += 1

    if add:
        output.append("### ➕ Added")
        output.extend(add)
        output.append("")
    if remove:
        output.append("### ➖ Removed")
        output.extend(remove)
        output.append("")

    return "\n".join(output)

def init_gitnot():
    """Initialize gitnot in current directory"""
    try:
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)
        os.makedirs(CHANGELOG_DIR, exist_ok=True)
        os.makedirs(DELETED_DIR, exist_ok=True)
        
        # Save default configuration
        save_json(CONFIG_FILE, DEFAULT_CONFIG)
        
        files = get_all_text_files(".")
        hashes = {}
        
        for file in files:
            rel_path = str(file)
            snapshot_path = os.path.join(SNAPSHOT_DIR, rel_path)
            safe_makedirs(snapshot_path)
            
            try:
                shutil.copy2(file, snapshot_path)
                hashes[rel_path] = hash_file(file)
                
                changelog_path = os.path.join(CHANGELOG_DIR, rel_path + ".log")
                safe_makedirs(changelog_path)
                with open(changelog_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {rel_path} — original v0.1\n")
            except (OSError, shutil.Error) as e:
                print(f"⚠️  Warning: Could not process {rel_path}: {e}")
                continue
        
        save_json(HASHES_FILE, hashes)
        write_version(0.1)
        print(f"✨ Initialized gitnot at version 0.1")
        print(f"📁 Tracking {len(hashes)} files")
        
    except Exception as e:
        print(f"❌ Failed to initialize gitnot: {e}")

def update_gitnot():
    """Update gitnot with current changes"""
    try:
        if not Path(GITNOT_DIR).exists():
            print("❌ gitnot not initialized in this folder. Run 'gitnot --init'")
            return

        old_hashes = load_json(HASHES_FILE)
        current_files = get_all_text_files(".")
        current_hashes = {str(f): hash_file(f) for f in current_files}
        
        changes_made = False
        version = bump_version()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Check for new and modified files
        for rel_path, new_hash in current_hashes.items():
            if rel_path not in old_hashes:
                # New file
                changes_made = True
                changelog_path = os.path.join(CHANGELOG_DIR, rel_path + ".log")
                safe_makedirs(changelog_path)
                try:
                    with open(changelog_path, 'a', encoding='utf-8') as f:
                        f.write(f"\n## v{version:.1f} – {timestamp}\n")
                        f.write("📄 New file added.\n")
                except OSError as e:
                    print(f"⚠️  Warning: Could not update changelog for {rel_path}: {e}")
                    
            elif old_hashes[rel_path] != new_hash:
                # Modified file
                changes_made = True
                old_file = os.path.join(SNAPSHOT_DIR, rel_path)
                new_file = rel_path
                
                if Path(old_file).exists():
                    try:
                        with open(old_file, 'r', encoding='utf-8', errors='ignore') as f1, \
                             open(new_file, 'r', encoding='utf-8', errors='ignore') as f2:
                            diff = list(difflib.unified_diff(
                                f1.readlines(), f2.readlines(),
                                fromfile='before', tofile='after', lineterm=''))
                        
                        changelog_path = os.path.join(CHANGELOG_DIR, rel_path + ".log")
                        safe_makedirs(changelog_path)
                        with open(changelog_path, 'a', encoding='utf-8') as f:
                            f.write(f"\n## v{version:.1f} – {timestamp}\n")
                            if diff:
                                f.write(format_diff_as_markdown(diff) + "\n")
                            else:
                                f.write("📄 File changed (no readable diff)\n")
                                
                    except (UnicodeDecodeError, OSError) as e:
                        # Handle encoding issues gracefully
                        changelog_path = os.path.join(CHANGELOG_DIR, rel_path + ".log")
                        safe_makedirs(changelog_path)
                        try:
                            with open(changelog_path, 'a', encoding='utf-8') as f:
                                f.write(f"\n## v{version:.1f} – {timestamp}\n")
                                f.write("📄 File changed (encoding issues, diff skipped)\n")
                        except OSError:
                            print(f"⚠️  Warning: Could not update changelog for {rel_path}")

        # Check for deleted files
        for rel_path in old_hashes:
            if rel_path not in current_hashes:
                changes_made = True
                deleted_file_path = os.path.join(SNAPSHOT_DIR, rel_path)
                if Path(deleted_file_path).exists():
                    target = os.path.join(DELETED_DIR, rel_path)
                    safe_makedirs(target)
                    try:
                        shutil.move(deleted_file_path, target)
                    except (OSError, shutil.Error) as e:
                        print(f"⚠️  Warning: Could not move deleted file {rel_path}: {e}")
                
                changelog_path = os.path.join(CHANGELOG_DIR, rel_path + ".log")
                safe_makedirs(changelog_path)
                try:
                    with open(changelog_path, 'a', encoding='utf-8') as f:
                        f.write(f"\n## v{version:.1f} – {timestamp}\n")
                        f.write("🔻 File was deleted.\n")
                except OSError as e:
                    print(f"⚠️  Warning: Could not update changelog for deleted {rel_path}: {e}")

        if not changes_made:
            # Revert version bump if no changes
            write_version(version - 0.1)
            print("✅ No changes detected")
            return

        # Safely replace snapshot directory
        if Path(SNAPSHOT_DIR).exists():
            temp_snapshot = tempfile.mkdtemp(prefix="gitnot_snapshot_")
            try:
                # Copy current files to temp location
                for file in current_files:
                    rel_path = str(file)
                    target_path = os.path.join(temp_snapshot, rel_path)
                    safe_makedirs(target_path)
                    shutil.copy2(file, target_path)
                
                # Atomic replacement
                shutil.rmtree(SNAPSHOT_DIR)
                shutil.move(temp_snapshot, SNAPSHOT_DIR)
            except (OSError, shutil.Error) as e:
                print(f"⚠️  Warning: Could not update snapshot: {e}")
                # Clean up temp directory if it still exists
                if Path(temp_snapshot).exists():
                    shutil.rmtree(temp_snapshot)
        else:
            print("⚠️  Snapshot folder missing. Please reinitialize with 'gitnot --init'")
            return

        save_json(HASHES_FILE, current_hashes)
        print(f"⬆ Version bumped → v{version:.1f}")
        print(f"📝 {len(current_files)} files tracked")
        
    except PermissionError:
        print("❌ Permission denied. Check file/folder permissions.")
    except OSError as e:
        print(f"❌ System error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print("💡 Try 'gitnot --init' to reset if needed.")

def show_version():
    """Display current version"""
    version = read_version()
    print(f"📌 Current version: v{version:.1f}")

def show_status():
    """Show what would change if update was run"""
    if not Path(GITNOT_DIR).exists():
        print("❌ gitnot not initialized")
        return
    
    try:
        old_hashes = load_json(HASHES_FILE)
        current_files = get_all_text_files(".")
        current_hashes = {str(f): hash_file(f) for f in current_files}
        
        new_files = [f for f in current_hashes if f not in old_hashes]
        changed_files = [f for f in current_hashes if f in old_hashes and old_hashes[f] != current_hashes[f]]
        deleted_files = [f for f in old_hashes if f not in current_hashes]
        
        if not (new_files or changed_files or deleted_files):
            print("✅ No changes detected")
            return
        
        if new_files:
            print(f"📄 New files ({len(new_files)}): {', '.join(new_files[:3])}")
            if len(new_files) > 3:
                print(f"    ... and {len(new_files) - 3} more")
        if changed_files:
            print(f"📝 Modified ({len(changed_files)}): {', '.join(changed_files[:3])}")
            if len(changed_files) > 3:
                print(f"    ... and {len(changed_files) - 3} more")
        if deleted_files:
            print(f"🗑️  Deleted ({len(deleted_files)}): {', '.join(deleted_files[:3])}")
            if len(deleted_files) > 3:
                print(f"    ... and {len(deleted_files) - 3} more")
                
    except Exception as e:
        print(f"❌ Error checking status: {e}")

def show_help():
    """Display help information"""
    print("""
🔧 gitnot - Simple version control for personal projects

Usage:
  gitnot          Track changes and bump version
  gitnot --init   Initialize gitnot in current folder  
  gitnot --show   Display current version
  gitnot --status Show pending changes (without committing)
  gitnot --help   Show this help message

Examples:
  gitnot --init   # Start tracking this folder
  gitnot          # Save current state as new version
  gitnot --status # See what's changed since last version

Configuration:
  Edit .gitnot/config.json to customize file extensions and ignore patterns
  
Features:
  • Lightweight snapshots without git complexity
  • Automatic change detection and version bumping
  • Human-readable markdown changelogs
  • Safe handling of file encoding issues
  • Personal project focused (not for large codebases)
""")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        update_gitnot()
    elif sys.argv[1] == "--init":
        init_gitnot()
    elif sys.argv[1] == "--show":
        show_version()
    elif sys.argv[1] == "--status":
        show_status()
    elif sys.argv[1] in ["--help", "-h"]:
        show_help()
    else:
        print("❓ Unknown command. Use '--help' to see available options")