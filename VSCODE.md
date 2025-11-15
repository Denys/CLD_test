# PSFB Loss Analyzer - VS Code Integration Guide

Complete guide for using VS Code with PSFB Loss Analyzer on Windows 11 + WSL2.

## Table of Contents

1. [Initial Setup](#initial-setup)
2. [Workspace Configuration](#workspace-configuration)
3. [Debugging](#debugging)
4. [IntelliSense and Autocomplete](#intellisense-and-autocomplete)
5. [Running and Testing](#running-and-testing)
6. [Useful Extensions](#useful-extensions)
7. [Keyboard Shortcuts](#keyboard-shortcuts)
8. [Troubleshooting](#troubleshooting)

---

## Initial Setup

### 1. Install VS Code Extensions in WSL

**Required extensions** (install in WSL, not Windows):

1. **WSL** by Microsoft
2. **Python** by Microsoft
3. **Pylance** by Microsoft
4. **Python Debugger** by Microsoft

**How to install in WSL:**
- Click Extensions icon (Ctrl+Shift+X)
- Search for extension
- Click "Install in WSL: Ubuntu-22.04"

**Optional but recommended:**
- **GitLens** - Git supercharged
- **Jupyter** - Notebook support
- **Error Lens** - Inline error messages
- **Better Comments** - Color-coded comments

### 2. Open Project in WSL

**Method A - From WSL Terminal:**
```bash
cd ~/projects/CLD_test
code .
```

**Method B - From VS Code:**
1. Press F1
2. Type: `WSL: Connect to WSL`
3. Select "Ubuntu-22.04"
4. File → Open Folder → Navigate to `~/projects/CLD_test`

**Verify WSL connection:**
- Bottom-left corner shows: `WSL: Ubuntu-22.04`
- Terminal shows Ubuntu prompt

---

## Workspace Configuration

### 1. Python Interpreter Selection

**Select the virtual environment:**

1. Press `Ctrl+Shift+P`
2. Type: `Python: Select Interpreter`
3. Choose: `./venv/bin/python` (Python 3.10.x)

**Verify:**
- Bottom-right shows: `Python 3.10.x ('venv')`
- Terminal shows `(venv)` prefix when opening new terminal

### 2. Create VS Code Settings

Create `.vscode/settings.json` in project root:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.analysis.typeCheckingMode": "basic",
    "python.analysis.autoImportCompletions": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true,
    "editor.rulers": [88, 120],
    "[python]": {
        "editor.tabSize": 4,
        "editor.insertSpaces": true
    }
}
```

**What this does:**
- Sets default Python interpreter to venv
- Enables automatic venv activation
- Configures Pylance type checking
- Enables pytest for testing
- Auto-formats code with black on save
- Sets line length rulers at 88 and 120 characters

### 3. Create Launch Configuration

Create `.vscode/launch.json`:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "debugpy",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal",
            "justMyCode": true,
            "env": {
                "PYTHONPATH": "${workspaceFolder}"
            }
        },
        {
            "name": "Python: Test Suite",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/tests/test_suite.py",
            "console": "integratedTerminal",
            "justMyCode": false
        },
        {
            "name": "Python: MOSFET Loss Example",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/psfb_loss_analyzer/examples/example_6p6kw_complete_analysis.py",
            "console": "integratedTerminal",
            "justMyCode": true
        },
        {
            "name": "Python: Optimizer",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/psfb_loss_analyzer/examples/example_auto_design.py",
            "console": "integratedTerminal",
            "justMyCode": true
        }
    ]
}
```

**What this provides:**
- Debug current file (F5)
- Debug test suite
- Debug examples directly
- Pre-configured Python debugger settings

---

## Debugging

### Basic Debugging

**1. Set Breakpoints:**
- Click left of line number (red dot appears)
- Or press F9 on line

**2. Start Debugging:**
- Press F5
- Or: Run → Start Debugging
- Or: Click green play button in Run panel

**3. Debug Controls:**
- **Continue:** F5
- **Step Over:** F10
- **Step Into:** F11
- **Step Out:** Shift+F11
- **Restart:** Ctrl+Shift+F5
- **Stop:** Shift+F5

### Debug Example: MOSFET Loss Calculation

```python
from psfb_loss_analyzer import (
    MOSFETParameters,
    CapacitanceVsVoltage,
    calculate_mosfet_conduction_loss,
)

mosfet = MOSFETParameters(
    part_number="TEST",
    v_dss=650.0,
    i_d_continuous=90.0,
    r_dson_25c=20e-3,
    r_dson_150c=28e-3,
    capacitances=CapacitanceVsVoltage(
        c_iss_constant=7200e-12,
        c_oss_constant=520e-12,
        c_rss_constant=15e-12,
    ),
    q_g=142e-9,
)

# Set breakpoint here (click left margin or press F9)
i_rms = 20.0
temp = 100.0

# Step through calculation
loss = calculate_mosfet_conduction_loss(
    mosfet, i_rms, duty_cycle=0.45, t_junction=temp
)

print(f"Loss: {loss:.2f}W")
```

**Debug workflow:**
1. Set breakpoint at `i_rms = 20.0`
2. Press F5 to start debugging
3. Press F10 to step over each line
4. Hover over variables to see values
5. Use Debug Console to evaluate expressions

### Advanced Debugging Features

**1. Watch Expressions:**
- In Debug panel, click "+" under "Watch"
- Add: `mosfet.r_dson_25c * 1000` (see R_DS(on) in mΩ)
- Add: `loss / i_rms**2` (see effective resistance)

**2. Debug Console:**
While debugging, use console at bottom:
```python
>>> mosfet.r_dson_25c * 1000
20.0
>>> i_rms ** 2 * mosfet.r_dson_25c
8.0
```

**3. Conditional Breakpoints:**
- Right-click breakpoint
- Select "Edit Breakpoint"
- Add condition: `loss > 10.0`
- Breakpoint only triggers when condition true

**4. Logpoints:**
- Right-click line number
- Select "Add Logpoint"
- Enter: `Loss = {loss:.2f}W`
- Logs message without stopping execution

---

## IntelliSense and Autocomplete

### Enabling Full IntelliSense

**1. Verify Pylance is active:**
- Bottom-right: Should show "Pylance"
- If not: Ctrl+Shift+P → "Python: Select Language Server" → Pylance

**2. Configure type checking:**

In `.vscode/settings.json`:
```json
{
    "python.analysis.typeCheckingMode": "basic",  // or "strict"
    "python.analysis.diagnosticMode": "workspace",
    "python.analysis.autoImportCompletions": true
}
```

### Using IntelliSense

**1. Autocomplete (Ctrl+Space):**
```python
from psfb_loss_analyzer import MOSF  # Press Ctrl+Space
# Shows: MOSFETParameters, MOSFET_LIBRARY_SIC, etc.
```

**2. Parameter hints (Ctrl+Shift+Space):**
```python
calculate_mosfet_conduction_loss(  # Cursor here, press Ctrl+Shift+Space
# Shows: (mosfet: MOSFETParameters, i_rms: float, duty_cycle: float, t_junction: float) -> float
```

**3. Quick info (hover):**
- Hover over function/variable to see documentation
- Shows type hints and docstrings

**4. Go to definition (F12):**
- Place cursor on function name
- Press F12 to jump to definition

**5. Find all references (Shift+F12):**
- Place cursor on function/variable
- Press Shift+F12 to see all usages

---

## Running and Testing

### Run Python Files

**Method 1: Debug mode (F5)**
- Opens in debug mode
- Can set breakpoints

**Method 2: Run without debugging (Ctrl+F5)**
- Faster execution
- No debug overhead

**Method 3: Right-click**
- Right-click in editor
- Select "Run Python File in Terminal"

**Method 4: Terminal**
```bash
python my_script.py
```

### Run Tests

**Method 1: Test Explorer**
1. Click Testing icon (beaker) in left sidebar
2. Click "Configure Python Tests"
3. Select "pytest"
4. Select "tests" directory
5. Click play button next to test to run

**Method 2: Terminal**
```bash
# Run all tests
python tests/test_suite.py

# Run specific test file
python tests/unit/test_mosfet_loss.py

# Run with pytest (if installed)
pytest tests/
```

**Method 3: Debug Tests**
1. Set breakpoint in test file
2. Right-click test name in Test Explorer
3. Select "Debug Test"

---

## Useful Extensions

### Recommended Extensions

**1. Python Docstring Generator**
- Auto-generates docstrings
- Press `Ctrl+Shift+2` after function definition

**2. autoDocstring**
- Generates detailed docstrings
- Supports multiple formats (Google, NumPy, Sphinx)

**3. Error Lens**
- Shows errors inline in editor
- Very helpful for catching issues early

**4. GitLens**
- Git blame annotations
- View commit history
- Compare revisions

**5. Jupyter**
- Run notebooks in VS Code
- Useful for interactive exploration

**6. Bracket Pair Colorizer**
- Colors matching brackets
- Helpful for nested structures

### Installing Extensions

```bash
# From terminal (if extension is on WSL marketplace)
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
```

---

## Keyboard Shortcuts

### Essential Shortcuts

| Action | Shortcut |
|--------|----------|
| **Navigation** |
| Quick Open | Ctrl+P |
| Go to Symbol | Ctrl+Shift+O |
| Go to Line | Ctrl+G |
| Go to Definition | F12 |
| Go Back | Alt+← |
| Go Forward | Alt+→ |
| **Editing** |
| Format Document | Shift+Alt+F |
| Comment Line | Ctrl+/ |
| Duplicate Line | Shift+Alt+↓ |
| Delete Line | Ctrl+Shift+K |
| Move Line Up/Down | Alt+↑/↓ |
| **Multi-cursor** |
| Add Cursor Above/Below | Ctrl+Alt+↑/↓ |
| Add Cursor at Selection | Ctrl+D |
| Select All Occurrences | Ctrl+Shift+L |
| **Search** |
| Find | Ctrl+F |
| Replace | Ctrl+H |
| Find in Files | Ctrl+Shift+F |
| **Terminal** |
| Toggle Terminal | Ctrl+` |
| New Terminal | Ctrl+Shift+` |
| **Debugging** |
| Start Debugging | F5 |
| Step Over | F10 |
| Step Into | F11 |
| Toggle Breakpoint | F9 |
| **Python Specific** |
| Run Python File | Ctrl+F5 |
| Run Selection | Shift+Enter |
| Select Interpreter | Ctrl+Shift+P → Python: Select Interpreter |

### Custom Keybindings

Create custom shortcuts in `Ctrl+K Ctrl+S` (Keyboard Shortcuts).

Example: Bind "Run Tests" to Ctrl+T:
1. Open Keyboard Shortcuts (Ctrl+K Ctrl+S)
2. Search: "Python: Run All Tests"
3. Double-click, press Ctrl+T

---

## Troubleshooting

### Issue 1: IntelliSense Not Working

**Symptoms:**
- No autocomplete
- No type hints
- Red squiggles everywhere

**Solutions:**

1. **Reload window:**
   - Ctrl+Shift+P → "Developer: Reload Window"

2. **Verify interpreter:**
   - Bottom-right should show correct Python version
   - Ctrl+Shift+P → "Python: Select Interpreter"

3. **Rebuild index:**
   - Ctrl+Shift+P → "Python: Clear Cache and Reload Window"

4. **Check Pylance:**
   - Bottom-right should show "Pylance"
   - If not, reinstall Python extension

### Issue 2: Imports Not Resolved

**Symptoms:**
```python
import psfb_loss_analyzer  # Shows error
```

**Solutions:**

1. **Set PYTHONPATH:**
   In `.vscode/settings.json`:
   ```json
   {
       "terminal.integrated.env.linux": {
           "PYTHONPATH": "${workspaceFolder}"
       }
   }
   ```

2. **Reinstall package:**
   ```bash
   pip install -e .
   ```

3. **Add to workspace settings:**
   ```json
   {
       "python.analysis.extraPaths": [
           "${workspaceFolder}"
       ]
   }
   ```

### Issue 3: Debugger Not Stopping at Breakpoints

**Symptoms:**
- Breakpoints shown as gray (not red)
- Debugger doesn't stop

**Solutions:**

1. **Check justMyCode:**
   In `launch.json`:
   ```json
   {
       "justMyCode": false  // Change to false to debug library code
   }
   ```

2. **Verify Python file is saved:**
   - Unsaved changes may cause issues
   - Save file (Ctrl+S)

3. **Use print debugging:**
   ```python
   import sys
   print(f"DEBUG: Value = {value}", file=sys.stderr)
   ```

### Issue 4: Terminal Shows Windows Path

**Symptoms:**
- Terminal shows `C:\Users\...` instead of `/home/user/...`

**Solution:**
- Ensure VS Code connected to WSL
- Bottom-left should show "WSL: Ubuntu-22.04"
- If not: F1 → "WSL: Connect to WSL"

### Issue 5: Extensions Not Working in WSL

**Solution:**
- Extensions must be installed specifically in WSL
- Look for "Install in WSL: Ubuntu-22.04" button
- Don't install in Windows, won't work in WSL

---

## Tips and Tricks

### Tip 1: Use Workspace Folders

Add multiple projects to workspace:
```
File → Add Folder to Workspace
```

Save workspace:
```
File → Save Workspace As → psfb.code-workspace
```

### Tip 2: Zen Mode

Focus on code without distractions:
```
View → Appearance → Zen Mode (Ctrl+K Z)
```

### Tip 3: Split Editor

Work on multiple files side-by-side:
- Drag tab to right
- Or: Right-click tab → "Split Right"

### Tip 4: Integrated Git

- View changes: Ctrl+Shift+G
- Stage files: Click "+"
- Commit: Type message, press Ctrl+Enter
- Push: Click "..." → Push

### Tip 5: Snippets

Create custom snippets for common code patterns:

File → Preferences → User Snippets → python.json

```json
{
    "MOSFET Parameters": {
        "prefix": "mosfet",
        "body": [
            "MOSFETParameters(",
            "    part_number=\"$1\",",
            "    v_dss=$2,",
            "    i_d_continuous=$3,",
            "    r_dson_25c=$4e-3,",
            "    r_dson_150c=$5e-3,",
            "    capacitances=CapacitanceVsVoltage(",
            "        c_iss_constant=$6e-12,",
            "        c_oss_constant=$7e-12,",
            "        c_rss_constant=$8e-12,",
            "    ),",
            "    q_g=$9e-9,",
            ")"
        ]
    }
}
```

Type `mosfet` and press Tab to expand.

---

## Next Steps

1. ✅ Configure VS Code settings
2. ✅ Set up launch configurations
3. ✅ Try debugging an example
4. ✅ Run tests from Test Explorer
5. ✅ Install useful extensions

**Happy coding in VS Code!** 🎉

For more information:
- [VS Code Python Documentation](https://code.visualstudio.com/docs/python/python-tutorial)
- [VS Code WSL Documentation](https://code.visualstudio.com/docs/remote/wsl)
- [INSTALL.md](INSTALL.md) - Installation guide
- [TESTING.md](TESTING.md) - Testing guide
