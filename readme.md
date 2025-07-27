# ⚙️ gitnot
### 🚫 not git > should be self explanatory

gitnot is a snapshot-based changelog tool that lets you create lightweight version checkpoints of your code or notes. It tracks only what’s changed, bumps the version after each run, and logs your edits like a personal ledger — without the overhead of full version control.

## 🧠 why
gitnot is built on a simple idea: versioning doesn’t need to be complex. It’s a simplified version control system for individuals who prefer intuitive snapshots over branching and commit workflows — built for those who think in checkpoints, not merges.

## 📦 Installation

[get yanked](https://github.com/codinganovel/yanked)

## 🚀 Usage

### gitnot
The main command. Run this in any folder that has already been initialized with gitnot --init. It checks your files for changes, and if anything has been added, removed, or modified, it:

Saves a snapshot of the current state
Bumps the version number
Logs the changes in a human-readable changelog
Think of this like a personal "commit" — but simpler and without ceremony. If nothing has changed, it does nothing.

### gitnot --init
Bootstraps the current folder to start using gitnot. This sets up a .gitnot/ directory where all version data and history will be stored. Run this once per project — before your first gitnot command.

### gitnot --show
Displays the current version of the folder you're in — simple and clean. Run it anytime you want to know which version you're working on.

## 📁 What it creates

When you run gitnot --init, it creates a hidden .gitnot/ folder inside your current directory. This folder contains all the versioning and change-tracking data for the project. Here's what’s inside:
### how to read what gets Saved.
### 📂 `.gitnot/`

| File/Folder    | Purpose |
|----------------|---------|
| `version.txt`  | Tracks the current version number (e.g., `v0.2`) of the folder. |
| `hashes.json`  | Internal tracker that stores the hash of every file to detect changes. |
| `changelogs/`  | A folder containing markdown files of each version's changelog. Every time you run `gitnot`, a new changelog is created here. |
| `snapshot/`    | Stores the actual full snapshot of the folder at each version (used for diffing). |
| `deleted/`     | A folder where deleted files are moved and versioned, so you can always retrieve removed content if needed. |

This entire `.gitnot/` folder is **self-contained**, lightweight, and designed to be ignored by Git if you want to keep your version history personal.

You can safely add `.gitnot/` to your `.gitignore`.


## 🛠 Contributing

Pull requests welcome. Open an issue or suggest an idea.

## 📄 License

under ☕️, check out [the-coffee-license](https://github.com/codinganovel/The-Coffee-License)

I've included both licenses with the repo, do what you know is right. The licensing works by assuming you're operating under good faith.

> built by **Sam** with ☕️&❤️