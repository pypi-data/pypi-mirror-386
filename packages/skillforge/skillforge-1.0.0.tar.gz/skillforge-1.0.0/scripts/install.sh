#!/bin/bash
# SkillForge Installer Script
# Installs SkillForge package and sets up Claude Code skills directory

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "🔨 SkillForge Installer v1.0.0"
echo "=============================="
echo ""

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Step 1: Check prerequisites
echo "Step 1: Checking prerequisites..."
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found. Please install Python 3.11 or later."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    print_error "Python 3.11+ required. Found: $PYTHON_VERSION"
    exit 1
fi

print_success "Python $PYTHON_VERSION"

# Check pip
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    print_error "pip not found. Please install pip."
    exit 1
fi

print_success "pip found"

# Check Claude Code (optional)
if command -v claude &> /dev/null; then
    print_success "Claude Code found"
else
    print_warning "Claude Code not found in PATH (will be needed to use SkillForge)"
fi

echo ""

# Step 2: Install Python package
echo "Step 2: Installing SkillForge package..."
echo ""

# Check if installing from PyPI or local
if [ "$1" == "--local" ] || [ -f "pyproject.toml" ]; then
    print_info "Installing from local source..."
    pip3 install -e . || {
        print_error "Installation failed"
        exit 1
    }
else
    print_info "Installing from PyPI..."
    pip3 install skillforge || {
        print_error "Installation failed"
        print_info "Try: pip3 install --user skillforge"
        exit 1
    }
fi

print_success "Package installed"
echo ""

# Step 3: Verify installation
echo "Step 3: Verifying installation..."
echo ""

# Check skillforge command
if command -v skillforge &> /dev/null; then
    VERSION=$(skillforge --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' || echo "unknown")
    print_success "skillforge command available (v$VERSION)"
else
    print_warning "skillforge command not in PATH"
    print_info "You may need to add ~/.local/bin to your PATH"
fi

# Check Python import
if python3 -c "import skillforge; print(skillforge.__version__)" &> /dev/null; then
    print_success "Python package importable"
else
    print_error "Cannot import skillforge package"
    exit 1
fi

echo ""

# Step 4: Setup directories
echo "Step 4: Setting up directories..."
echo ""

SKILLFORGE_HOME="$HOME/.claude/skills/skillforge"
DATA_DIR="$SKILLFORGE_HOME/data"
CACHE_DIR="$DATA_DIR/cache/context7"

# Create directories
mkdir -p "$SKILLFORGE_HOME"
mkdir -p "$DATA_DIR"
mkdir -p "$CACHE_DIR"

print_success "Created: $SKILLFORGE_HOME"
print_success "Created: $DATA_DIR"
print_success "Created: $CACHE_DIR"

echo ""

# Step 5: Copy core skill files (if available)
echo "Step 5: Installing core skill files..."
echo ""

# Check if we're in the repo or if files are in package
if [ -d "skillforge/data/skill_files/core" ]; then
    # Local installation
    CORE_SOURCE="skillforge/data/skill_files/core"
elif python3 -c "import skillforge; import os; print(os.path.dirname(skillforge.__file__))" &> /dev/null; then
    # Package installation
    PACKAGE_DIR=$(python3 -c "import skillforge, os; print(os.path.dirname(skillforge.__file__))")
    CORE_SOURCE="$PACKAGE_DIR/data/skill_files/core"
else
    CORE_SOURCE=""
fi

if [ -n "$CORE_SOURCE" ] && [ -d "$CORE_SOURCE" ]; then
    cp -r "$CORE_SOURCE" "$SKILLFORGE_HOME/"
    print_success "Core skill files installed"
else
    print_warning "Core skill files not found (they will be generated on first use)"
fi

echo ""

# Step 6: Run initial setup test
echo "Step 6: Testing installation..."
echo ""

# Run status command
if skillforge status &> /dev/null; then
    print_success "Installation test passed"
else
    print_warning "Installation test had warnings (this may be normal)"
fi

echo ""

# Step 7: Success message
echo "=============================="
echo "✅ SkillForge installed successfully!"
echo "=============================="
echo ""
echo "📋 Installation Details:"
echo "   Package version: $(python3 -c 'import skillforge; print(skillforge.__version__)' 2>/dev/null || echo 'unknown')"
echo "   Skillforge home: $SKILLFORGE_HOME"
echo "   Data directory: $DATA_DIR"
echo ""
echo "🚀 Next Steps:"
echo ""
echo "   1. Check installation:"
echo "      $ skillforge status"
echo ""
echo "   2. Run setup wizard (in Claude Code):"
echo "      /sf:wizard"
echo ""
echo "   3. Or generate a specific skill:"
echo "      $ skillforge generate nextjs"
echo ""
echo "   4. Read the documentation:"
echo "      https://github.com/omarpioselli/SkillForge"
echo ""
echo "💡 Tips:"
echo "   - Restart Claude Code after installation"
echo "   - Run 'skillforge --help' to see all commands"
echo "   - Join the community for support and updates"
echo ""
echo "Happy coding! 🎉"
echo ""
