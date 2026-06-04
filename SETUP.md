# Setup Instructions (Mac only)

This guide is written for non-technical users on macOS. Windows is not supported.

## Requirements

- A Mac running macOS
- Python 3 installed. To check, open Terminal (press Cmd + Space, type "Terminal", press Enter) and run:
  ```
  python3 --version
  ```
  If you see a version number, you're good. If not, download Python 3 from [python.org](https://www.python.org/downloads/).

## First time setup

### Option A: If you received a folder by email

1. Unzip the folder and move it to your Desktop
2. Open Terminal (press Cmd + Space, type "Terminal", press Enter)
3. Copy and paste this command, then press Enter:
   ```
   chmod +x ~/Desktop/order-parser/run_me.command
   ```
   You only need to do this once. It gives the script permission to run on your computer. If you skip it, you may see an "access privileges" error when you double-click.

### Option B: If you are setting it up from GitHub

1. You will need a free GitHub account — sign up at [github.com](https://github.com)
2. Open Terminal (press Cmd + Space, type "Terminal", press Enter)
3. Copy and paste this command, then press Enter:
   ```
   cd ~/Desktop && git clone https://github.com/yourusername/order-parser.git
   ```
4. Copy and paste this command, then press Enter:
   ```
   chmod +x ~/Desktop/order-parser/run_me.command
   ```
   You only need to do this once. It gives the script permission to run on your computer. If you skip it, you may see an "access privileges" error when you double-click.

## Using the tool

1. Drop your PDF files into the `input` folder inside `order-parser`
2. Double-click `run_me.command`
3. A Terminal window will open, process your files, and close when done
4. Find your CSV files in the `output` folder

Processed PDFs are automatically moved to `input/processed/` so they won't be converted twice.

## Getting updates

To get the latest version, open Terminal and run:
```
cd ~/Desktop/order-parser && git pull
```
