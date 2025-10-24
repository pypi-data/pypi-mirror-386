#!/bin/bash
# SkillForge Installer Script
# Installs SkillForge package and sets up Claude Code skills directory

set -e

# ============================================================================
# COLORS & STYLES
# ============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# Background colors
BG_GREEN='\033[42m'
BG_BLUE='\033[44m'
BG_RED='\033[41m'

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

# Print colored messages
print_success() {
    echo -e "${GREEN}✅ $1${RESET}"
}

print_error() {
    echo -e "${RED}❌ $1${RESET}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${RESET}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${RESET}"
}

print_step() {
    echo -e "\n${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo -e "${BOLD}${BLUE}▶  $1${RESET}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
}

print_box() {
    local text="$1"
    local color="${2:-$CYAN}"
    local width=60

    echo -e "${color}╔$(printf '═%.0s' $(seq 1 $width))╗${RESET}"
    printf "${color}║${RESET} ${BOLD}%-${width}s${RESET} ${color}║${RESET}\n" "$text"
    echo -e "${color}╚$(printf '═%.0s' $(seq 1 $width))╝${RESET}"
}

# Spinner animation
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    while ps -p $pid > /dev/null 2>&1; do
        local temp=${spinstr#?}
        printf " ${CYAN}[%c]${RESET} " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# Progress bar
progress_bar() {
    local current=$1
    local total=$2
    local width=40
    local percentage=$((current * 100 / total))
    local filled=$((width * current / total))
    local empty=$((width - filled))

    printf "\r${CYAN}["
    printf "${GREEN}%0.s█" $(seq 1 $filled)
    printf "${DIM}%0.s░" $(seq 1 $empty)
    printf "${CYAN}]${RESET} ${BOLD}${percentage}%%${RESET} ${DIM}($current/$total)${RESET}"
}

# Animated checkmark
animated_check() {
    echo -n "  "
    for i in {1..3}; do
        echo -ne "${GREEN}●${RESET}"
        sleep 0.1
    done
    echo -ne "\r"
    echo -e "  ${GREEN}✅${RESET}"
}

# Count files in directory
count_files() {
    local dir="$1"
    if [ -d "$dir" ]; then
        find "$dir" -type f | wc -l | tr -d ' '
    else
        echo "0"
    fi
}

# Get directory size
get_dir_size() {
    local dir="$1"
    if [ -d "$dir" ]; then
        du -sh "$dir" 2>/dev/null | cut -f1
    else
        echo "0B"
    fi
}

# ============================================================================
# ASCII ART BANNER
# ============================================================================

print_banner() {
    clear
    echo -e "${CYAN}"
    cat << "EOF"
    ███████╗██╗  ██╗██╗██╗     ██╗     ███████╗ ██████╗ ██████╗  ██████╗ ███████╗
    ██╔════╝██║ ██╔╝██║██║     ██║     ██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
    ███████╗█████╔╝ ██║██║     ██║     █████╗  ██║   ██║██████╔╝██║  ███╗█████╗
    ╚════██║██╔═██╗ ██║██║     ██║     ██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝
    ███████║██║  ██╗██║███████╗███████╗██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
    ╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
EOF
    echo -e "${RESET}"
    echo -e "${BOLD}${WHITE}              Meta-Programming Framework for Claude Code${RESET}"
    echo -e "${DIM}              Transform Claude into YOUR expert developer${RESET}"
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
}

# ============================================================================
# MAIN INSTALLATION
# ============================================================================

# Start timer
START_TIME=$(date +%s)

print_banner

# ============================================================================
# STEP 1: Prerequisites Check
# ============================================================================
print_step "Step 1/7: Checking Prerequisites"

echo -e "${DIM}Verifying system requirements...${RESET}\n"

# Check Python
echo -ne "  ${DIM}Python 3.11+${RESET} "
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗${RESET}"
    print_error "Python 3 not found. Please install Python 3.11 or later."
    echo -e "\n${CYAN}Download: ${BOLD}https://www.python.org/downloads/${RESET}\n"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo -e "${RED}✗${RESET}"
    print_error "Python 3.11+ required. Found: $PYTHON_VERSION"
    exit 1
fi

echo -e "${GREEN}✓${RESET} ${DIM}v$PYTHON_VERSION${RESET}"

# Check pip
echo -ne "  ${DIM}pip package manager${RESET} "
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo -e "${RED}✗${RESET}"
    print_error "pip not found. Please install pip."
    exit 1
fi
echo -e "${GREEN}✓${RESET}"

# Check Claude Code
echo -ne "  ${DIM}Claude Code${RESET} "
if command -v claude &> /dev/null; then
    CLAUDE_VERSION=$(claude --version 2>&1 | head -1 || echo "unknown")
    echo -e "${GREEN}✓${RESET} ${DIM}$CLAUDE_VERSION${RESET}"
else
    echo -e "${YELLOW}!${RESET} ${DIM}Not found (optional)${RESET}"
    print_warning "Claude Code not detected. You'll need it to use SkillForge."
fi

echo ""
animated_check
sleep 0.3

# ============================================================================
# STEP 2: Install Python Package
# ============================================================================
print_step "Step 2/7: Installing SkillForge Package"

# Check if installing from PyPI or local
if [ "$1" == "--local" ] || [ -f "pyproject.toml" ]; then
    print_info "Installing from local source..."
    echo ""

    pip3 install -e . 2>&1 | while IFS= read -r line; do
        echo -e "  ${DIM}$line${RESET}"
    done || {
        print_error "Installation failed"
        exit 1
    }
else
    print_info "Installing from PyPI..."
    echo ""

    pip3 install skillforge 2>&1 | while IFS= read -r line; do
        echo -e "  ${DIM}$line${RESET}"
    done || {
        print_error "Installation failed"
        print_info "Try: pip3 install --user skillforge"
        exit 1
    }
fi

echo ""
animated_check
sleep 0.3

# ============================================================================
# STEP 3: Verify Installation
# ============================================================================
print_step "Step 3/7: Verifying Installation"

# Check skillforge command
echo -ne "  ${DIM}CLI command${RESET} "
if command -v skillforge &> /dev/null; then
    VERSION=$(skillforge --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' || echo "unknown")
    echo -e "${GREEN}✓${RESET} ${DIM}v$VERSION${RESET}"
else
    echo -e "${YELLOW}!${RESET} ${DIM}Not in PATH${RESET}"
    print_warning "skillforge command not in PATH. Add ~/.local/bin to your PATH."
fi

# Check Python import
echo -ne "  ${DIM}Python module${RESET} "
if python3 -c "import skillforge; print(skillforge.__version__)" &> /dev/null; then
    echo -e "${GREEN}✓${RESET}"
else
    echo -e "${RED}✗${RESET}"
    print_error "Cannot import skillforge package"
    exit 1
fi

echo ""
animated_check
sleep 0.3

# ============================================================================
# STEP 4: Setup Directories
# ============================================================================
print_step "Step 4/7: Creating Directory Structure"

SKILLFORGE_HOME="$HOME/.claude/skills/skillforge"
DATA_DIR="$SKILLFORGE_HOME/data"
CACHE_DIR="$DATA_DIR/cache/context7"
COMMANDS_DIR="$HOME/.claude/commands/sf"

echo -e "${DIM}Setting up directories...${RESET}\n"

# Create directories with animation
dirs=("$SKILLFORGE_HOME" "$DATA_DIR" "$CACHE_DIR" "$COMMANDS_DIR")
for i in "${!dirs[@]}"; do
    dir="${dirs[$i]}"
    progress_bar $((i + 1)) ${#dirs[@]}
    mkdir -p "$dir"
    sleep 0.2
done

echo -e "\n"

print_success "Created: ${DIM}$SKILLFORGE_HOME${RESET}"
print_success "Created: ${DIM}$DATA_DIR${RESET}"
print_success "Created: ${DIM}$CACHE_DIR${RESET}"
print_success "Created: ${DIM}$COMMANDS_DIR${RESET}"

echo ""
animated_check
sleep 0.3

# ============================================================================
# STEP 5: Install Core Skill Files
# ============================================================================
print_step "Step 5/7: Installing Core Skill Files"

# Determine source directory
if [ -d "skillforge/data/skill_files" ]; then
    # Local installation
    SKILL_FILES_SOURCE="skillforge/data/skill_files"
elif python3 -c "import skillforge; import os; print(os.path.dirname(skillforge.__file__))" &> /dev/null; then
    # Package installation
    PACKAGE_DIR=$(python3 -c "import skillforge, os; print(os.path.dirname(skillforge.__file__))")
    SKILL_FILES_SOURCE="$PACKAGE_DIR/data/skill_files"
else
    SKILL_FILES_SOURCE=""
fi

if [ -z "$SKILL_FILES_SOURCE" ] || [ ! -d "$SKILL_FILES_SOURCE" ]; then
    print_error "Skill files not found in package"
    exit 1
fi

echo -e "${DIM}Copying skill files from package...${RESET}\n"

# Copy SKILL.md (main entry point)
if [ -f "$SKILL_FILES_SOURCE/SKILL.md" ]; then
    echo -ne "  ${DIM}SKILL.md (entry point)${RESET} "
    cp "$SKILL_FILES_SOURCE/SKILL.md" "$SKILLFORGE_HOME/SKILL.md"
    SIZE=$(du -h "$SKILLFORGE_HOME/SKILL.md" | cut -f1)
    echo -e "${GREEN}✓${RESET} ${DIM}$SIZE${RESET}"
else
    print_error "SKILL.md not found"
    exit 1
fi

# Copy core/ directory (behavioral files)
if [ -d "$SKILL_FILES_SOURCE/core" ]; then
    echo -ne "  ${DIM}core/ (behavioral files)${RESET} "
    cp -r "$SKILL_FILES_SOURCE/core" "$SKILLFORGE_HOME/"
    CORE_FILES=$(count_files "$SKILLFORGE_HOME/core")
    CORE_SIZE=$(get_dir_size "$SKILLFORGE_HOME/core")
    echo -e "${GREEN}✓${RESET} ${DIM}$CORE_FILES files, $CORE_SIZE${RESET}"
else
    print_warning "core/ directory not found"
fi

echo ""
animated_check
sleep 0.3

# ============================================================================
# STEP 6: Install Slash Commands
# ============================================================================
print_step "Step 6/7: Installing Slash Commands"

echo -e "${DIM}Copying slash commands...${RESET}\n"

if [ -d "$SKILL_FILES_SOURCE/commands/sf" ]; then
    # Copy all command files
    CMD_FILES=$(find "$SKILL_FILES_SOURCE/commands/sf" -type f -name "*.md")
    CMD_COUNT=$(echo "$CMD_FILES" | wc -l | tr -d ' ')

    current=0
    for cmd_file in $CMD_FILES; do
        current=$((current + 1))
        cmd_name=$(basename "$cmd_file")
        progress_bar $current $CMD_COUNT
        cp "$cmd_file" "$COMMANDS_DIR/"
        sleep 0.1
    done

    echo -e "\n"
    CMD_SIZE=$(get_dir_size "$COMMANDS_DIR")
    print_success "Installed $CMD_COUNT commands (${CMD_SIZE})"
    echo ""

    # List installed commands
    echo -e "${DIM}Available commands:${RESET}"
    for cmd_file in $(ls "$COMMANDS_DIR"/*.md 2>/dev/null | sort); do
        cmd_name=$(basename "$cmd_file" .md)
        echo -e "  ${CYAN}/sf:${cmd_name}${RESET}"
    done
else
    print_warning "Slash commands not found in package"
fi

echo ""
animated_check
sleep 0.3

# ============================================================================
# STEP 7: Final Verification
# ============================================================================
print_step "Step 7/7: Final Verification"

echo -e "${DIM}Running installation tests...${RESET}\n"

# Test skillforge status
echo -ne "  ${DIM}Testing CLI command${RESET} "
if skillforge status &> /dev/null; then
    echo -e "${GREEN}✓${RESET}"
else
    echo -e "${YELLOW}!${RESET} ${DIM}Warnings (may be normal)${RESET}"
fi

# Verify file structure
echo -ne "  ${DIM}Checking file structure${RESET} "
required_files=(
    "$SKILLFORGE_HOME/SKILL.md"
    "$SKILLFORGE_HOME/core"
    "$SKILLFORGE_HOME/data"
    "$COMMANDS_DIR"
)

all_good=true
for file in "${required_files[@]}"; do
    if [ ! -e "$file" ]; then
        all_good=false
        break
    fi
done

if [ "$all_good" = true ]; then
    echo -e "${GREEN}✓${RESET}"
else
    echo -e "${RED}✗${RESET}"
    print_error "Some required files are missing"
fi

echo ""
animated_check
sleep 0.3

# ============================================================================
# SUCCESS SCREEN
# ============================================================================

# Calculate elapsed time
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

clear
echo -e "${GREEN}"
cat << "EOF"
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                                                                       ║
    ║         ████████╗  ██╗  ██╗  ██████╗  ███╗   ██╗ ███████╗         ║
    ║         ██╔══██║  ██║  ██║ ██╔═══██╗ ████╗  ██║ ██╔════╝         ║
    ║         ██║  ██║  ██║  ██║ ██║   ██║ ██╔██╗ ██║ █████╗           ║
    ║         ██║  ██║  ██║  ██║ ██║   ██║ ██║╚██╗██║ ██╔══╝           ║
    ║         ██████╔╝  ╚═╝  ╚═╝ ╚██████╔╝ ██║ ╚████║ ███████╗         ║
    ║         ╚═════╝               ╚═════╝  ╚═╝  ╚═══╝ ╚══════╝         ║
    ║                                                                       ║
    ║               🎉  Installation Complete!  🎉                         ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${RESET}"

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"

# Installation summary
print_box "📊 INSTALLATION SUMMARY" "$BOLD$CYAN"
echo ""

echo -e "  ${BOLD}Package Version:${RESET}    ${GREEN}$(python3 -c 'import skillforge; print(skillforge.__version__)' 2>/dev/null || echo 'unknown')${RESET}"
echo -e "  ${BOLD}Installation Time:${RESET}  ${GREEN}${ELAPSED}s${RESET}"
echo -e "  ${BOLD}SkillForge Home:${RESET}    ${DIM}$SKILLFORGE_HOME${RESET}"

echo -e "\n  ${BOLD}Installed Files:${RESET}"
echo -e "    ${GREEN}✓${RESET} SKILL.md (entry point)"
echo -e "    ${GREEN}✓${RESET} $(count_files "$SKILLFORGE_HOME/core") core behavioral files"
echo -e "    ${GREEN}✓${RESET} $(ls "$COMMANDS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ') slash commands"

TOTAL_SIZE=$(du -sh "$SKILLFORGE_HOME" 2>/dev/null | cut -f1)
echo -e "\n  ${BOLD}Total Size:${RESET}         ${GREEN}$TOTAL_SIZE${RESET}"

echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"

# Next steps
print_box "🚀 NEXT STEPS" "$BOLD$BLUE"
echo ""

echo -e "  ${BOLD}${WHITE}1.${RESET} ${BOLD}Restart Claude Code${RESET}"
echo -e "     ${DIM}Close and reopen Claude to load SkillForge${RESET}"
echo ""

echo -e "  ${BOLD}${WHITE}2.${RESET} ${BOLD}Run the Setup Wizard${RESET}"
echo -e "     ${CYAN}claude${RESET} ${DIM}(in any project)${RESET}"
echo -e "     ${CYAN}/sf:wizard${RESET}"
echo ""

echo -e "  ${BOLD}${WHITE}3.${RESET} ${BOLD}Generate Your First Skill${RESET}"
echo -e "     ${DIM}Answer a few questions about your preferences${RESET}"
echo -e "     ${DIM}SkillForge will generate personalized skills for your stack${RESET}"
echo ""

echo -e "  ${BOLD}${WHITE}4.${RESET} ${BOLD}Start Coding!${RESET}"
echo -e "     ${DIM}SkillForge will automatically orchestrate skills${RESET}"
echo -e "     ${DIM}Claude will code exactly the way YOU do${RESET}"

echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"

# Quick reference
print_box "📚 QUICK REFERENCE" "$BOLD$MAGENTA"
echo ""

echo -e "  ${BOLD}Check Status:${RESET}"
echo -e "    ${CYAN}skillforge status${RESET}"
echo ""

echo -e "  ${BOLD}Available Commands:${RESET}"
echo -e "    ${CYAN}/sf:wizard${RESET}      ${DIM}Interactive setup wizard${RESET}"
echo -e "    ${CYAN}/sf:generate${RESET}    ${DIM}Generate specific skill${RESET}"
echo -e "    ${CYAN}/sf:list${RESET}        ${DIM}List installed skills${RESET}"
echo -e "    ${CYAN}/sf:analyze${RESET}     ${DIM}Analyze usage patterns${RESET}"
echo -e "    ${CYAN}/sf:optimize${RESET}    ${DIM}Optimize skills${RESET}"
echo ""

echo -e "  ${BOLD}Documentation:${RESET}"
echo -e "    ${CYAN}https://github.com/omarpiosedev/SkillForge${RESET}"

echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"

# Final message
echo -e "${BOLD}${WHITE}Welcome to SkillForge!${RESET} 🎨"
echo -e "${DIM}Transform Claude Code into YOUR expert developer.${RESET}\n"

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
