#!/bin/bash
# SkillForge Installer Script
# Cinematic installation experience with beautiful ASCII art

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

# Gradient colors (from cyan to purple to pink)
C1='\033[38;5;51m'   # Cyan
C2='\033[38;5;45m'   # Light cyan
C3='\033[38;5;39m'   # Blue
C4='\033[38;5;33m'   # Deep blue
C5='\033[38;5;69m'   # Purple
C6='\033[38;5;105m'  # Light purple
C7='\033[38;5;141m'  # Pink purple
C8='\033[38;5;177m'  # Pink

# Animation speed
SLOW_DELAY=0.03
MEDIUM_DELAY=0.02
FAST_DELAY=0.01

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

# Slow print - character by character
slow_print() {
    local text="$1"
    local delay="${2:-$SLOW_DELAY}"

    for ((i=0; i<${#text}; i++)); do
        echo -n "${text:$i:1}"
        sleep "$delay"
    done
    echo ""
}

# Print line with delay
print_line_slow() {
    echo -e "$1"
    sleep "${2:-0.1}"
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

# Progress bar with animation
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
    sleep 0.15
}

# Animated checkmark with sparkle effect
animated_check() {
    echo -n "  "
    for i in {1..3}; do
        echo -ne "${GREEN}●${RESET}"
        sleep 0.15
    done
    echo -ne "\r"
    echo -e "  ${GREEN}✨ ✅ ✨${RESET}"
    sleep 0.3
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
# ASCII ART BANNER WITH GRADIENT
# ============================================================================

print_banner() {
    clear
    echo ""

    # Line by line with gradient colors
    print_line_slow "${C1}    ███████╗██╗  ██╗██╗██╗     ██╗     ███████╗ ██████╗ ██████╗  ██████╗ ███████╗${RESET}" $SLOW_DELAY
    print_line_slow "${C2}    ██╔════╝██║ ██╔╝██║██║     ██║     ██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝${RESET}" $SLOW_DELAY
    print_line_slow "${C3}    ███████╗█████╔╝ ██║██║     ██║     █████╗  ██║   ██║██████╔╝██║  ███╗█████╗  ${RESET}" $SLOW_DELAY
    print_line_slow "${C5}    ╚════██║██╔═██╗ ██║██║     ██║     ██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝  ${RESET}" $SLOW_DELAY
    print_line_slow "${C6}    ███████║██║  ██╗██║███████╗███████╗██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗${RESET}" $SLOW_DELAY
    print_line_slow "${C8}    ╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝${RESET}" $SLOW_DELAY

    echo ""
    sleep 0.3
    echo -e "              ${BOLD}${WHITE}Meta-Programming Framework for Claude Code${RESET}"
    sleep 0.2
    echo -e "              ${DIM}Transform Claude into YOUR expert developer${RESET}"
    sleep 0.2
    echo ""
    echo -e "${C3}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo ""
    sleep 0.5
}

# ============================================================================
# DONE ANIMATION
# ============================================================================

print_done_animation() {
    echo ""
    echo -e "${C1}    ██████╗  ██████╗ ███╗   ██╗███████╗${RESET}"
    sleep 0.08
    echo -e "${C2}    ██╔══██╗██╔═══██╗████╗  ██║██╔════╝${RESET}"
    sleep 0.08
    echo -e "${C3}    ██║  ██║██║   ██║██╔██╗ ██║█████╗  ${RESET}"
    sleep 0.08
    echo -e "${C5}    ██║  ██║██║   ██║██║╚██╗██║██╔══╝  ${RESET}"
    sleep 0.08
    echo -e "${C6}    ██████╔╝╚██████╔╝██║ ╚████║███████╗${RESET}"
    sleep 0.08
    echo -e "${C8}    ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝╚══════╝${RESET}"
    echo ""
}

# ============================================================================
# WELCOME FINALE
# ============================================================================

print_welcome_finale() {
    clear
    echo ""
    echo ""

    # Beautiful gradient welcome message
    print_line_slow "${C1}    ╔════════════════════════════════════════════════════════════════════════════╗${RESET}" 0.05
    print_line_slow "${C1}    ║                                                                            ║${RESET}" 0.05
    print_line_slow "${C2}    ║        ██╗    ██╗███████╗██╗      ██████╗ ██████╗ ███╗   ███╗███████╗.     ║${RESET}" 0.05
    print_line_slow "${C3}    ║        ██║    ██║██╔════╝██║     ██╔════╝██╔═══██╗████╗ ████║██╔════╝.     ║${RESET}" 0.05
    print_line_slow "${C4}    ║        ██║ █╗ ██║█████╗  ██║     ██║     ██║   ██║██╔████╔██║█████╗        ║${RESET}" 0.05
    print_line_slow "${C5}    ║        ██║███╗██║██╔══╝  ██║     ██║     ██║   ██║██║╚██╔╝██║██╔══╝        ║${RESET}" 0.05
    print_line_slow "${C6}    ║        ╚███╔███╔╝███████╗███████╗╚██████╗╚██████╔╝██║ ╚═╝ ██║███████╗.     ║${RESET}" 0.05
    print_line_slow "${C7}    ║         ╚══╝╚══╝ ╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝.     ║${RESET}" 0.05
    print_line_slow "${C8}    ║                                                                            ║${RESET}" 0.05
    print_line_slow "${C8}    ║                              ${BOLD}${WHITE}  TO  SKILLFORGE  ${RESET}${C8}                            ║${RESET}" 0.05
    print_line_slow "${C8}    ║                                                                            ║${RESET}" 0.05
    print_line_slow "${C8}    ╚════════════════════════════════════════════════════════════════════════════╝${RESET}" 0.05

    echo ""
    sleep 0.3

    # Animated sparkles
    echo -e "                     ${GREEN}✨${RESET} ${YELLOW}✨${RESET} ${CYAN}✨${RESET} ${MAGENTA}✨${RESET} ${BLUE}✨${RESET} ${GREEN}✨${RESET} ${YELLOW}✨${RESET}"
    sleep 0.3
    echo ""
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
print_step "Step 1/8: Checking Prerequisites"

echo -e "${DIM}Verifying system requirements...${RESET}"
sleep 0.2
echo ""

# Check Python
echo -ne "  ${DIM}Python 3.11+${RESET} "
sleep 0.3
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
sleep 0.2

# Check pip
echo -ne "  ${DIM}pip package manager${RESET} "
sleep 0.3
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo -e "${RED}✗${RESET}"
    print_error "pip not found. Please install pip."
    exit 1
fi
echo -e "${GREEN}✓${RESET}"
sleep 0.2

# Check Claude Code
echo -ne "  ${DIM}Claude Code${RESET} "
sleep 0.3
if command -v claude &> /dev/null; then
    CLAUDE_VERSION=$(claude --version 2>&1 | head -1 || echo "unknown")
    echo -e "${GREEN}✓${RESET} ${DIM}$CLAUDE_VERSION${RESET}"
else
    echo -e "${YELLOW}!${RESET} ${DIM}Not found (optional)${RESET}"
    print_warning "Claude Code not detected. You'll need it to use SkillForge."
fi

echo ""
animated_check
sleep 0.5

# ============================================================================
# STEP 2: Install Python Package
# ============================================================================
print_step "Step 2/8: Installing SkillForge Package"

# Check if installing from PyPI or local
if [ "$1" == "--local" ] || [ -f "pyproject.toml" ]; then
    echo -e "${CYAN}Installing from local source...${RESET}"
    sleep 0.2
    echo ""

    pip3 install -e . 2>&1 | while IFS= read -r line; do
        echo -e "  ${DIM}$line${RESET}"
        sleep 0.05
    done || {
        print_error "Installation failed"
        exit 1
    }
else
    echo -e "${CYAN}Installing from PyPI...${RESET}"
    sleep 0.2
    echo ""

    pip3 install skillforge 2>&1 | while IFS= read -r line; do
        echo -e "  ${DIM}$line${RESET}"
        sleep 0.05
    done || {
        print_error "Installation failed"
        print_info "Try: pip3 install --user skillforge"
        exit 1
    }
fi

echo ""
animated_check
sleep 0.5

# ============================================================================
# STEP 3: Verify Installation
# ============================================================================
print_step "Step 3/8: Verifying Installation"

sleep 0.3

# Check skillforge command
echo -ne "  ${DIM}CLI command${RESET} "
sleep 0.4
if command -v skillforge &> /dev/null; then
    VERSION=$(skillforge --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' || echo "unknown")
    echo -e "${GREEN}✓${RESET} ${DIM}v$VERSION${RESET}"
else
    echo -e "${YELLOW}!${RESET} ${DIM}Not in PATH${RESET}"
    print_warning "skillforge command not in PATH. Add ~/.local/bin to your PATH."
fi
sleep 0.2

# Check Python import
echo -ne "  ${DIM}Python module${RESET} "
sleep 0.4
if python3 -c "import skillforge; print(skillforge.__version__)" &> /dev/null; then
    echo -e "${GREEN}✓${RESET}"
else
    echo -e "${RED}✗${RESET}"
    print_error "Cannot import skillforge package"
    exit 1
fi

echo ""
animated_check
sleep 0.5

# ============================================================================
# STEP 4: Setup Directories
# ============================================================================
print_step "Step 4/8: Creating Directory Structure"

CLAUDE_HOME="$HOME/.claude"
SKILLFORGE_HOME="$CLAUDE_HOME/skills/skillforge"
DATA_DIR="$SKILLFORGE_HOME/data"
CACHE_DIR="$DATA_DIR/cache/context7"
COMMANDS_DIR="$CLAUDE_HOME/commands/sf"

echo -e "${DIM}Setting up directories...${RESET}"
sleep 0.2
echo ""

# Create directories with animation
dirs=("$CLAUDE_HOME" "$SKILLFORGE_HOME" "$DATA_DIR" "$CACHE_DIR" "$COMMANDS_DIR")
for i in "${!dirs[@]}"; do
    dir="${dirs[$i]}"
    progress_bar $((i + 1)) ${#dirs[@]}
    mkdir -p "$dir"
done

echo -e "\n"

print_success "Created: ${DIM}$CLAUDE_HOME${RESET}"
sleep 0.15
print_success "Created: ${DIM}$SKILLFORGE_HOME${RESET}"
sleep 0.15
print_success "Created: ${DIM}$DATA_DIR${RESET}"
sleep 0.15
print_success "Created: ${DIM}$CACHE_DIR${RESET}"
sleep 0.15
print_success "Created: ${DIM}$COMMANDS_DIR${RESET}"

echo ""
animated_check
sleep 0.5

# ============================================================================
# STEP 5: Install Global Entry Point
# ============================================================================
print_step "Step 5/7: Installing Global Entry Point"

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

echo -e "${DIM}Installing global SkillForge entry point...${RESET}"
sleep 0.2
echo ""

# Copy CLAUDE.md to root ~/.claude/ (CRITICAL - always loaded)
if [ -f "$SKILL_FILES_SOURCE/CLAUDE.md" ]; then
    echo -ne "  ${DIM}CLAUDE.md → ~/.claude/${RESET} "
    sleep 0.3
    cp "$SKILL_FILES_SOURCE/CLAUDE.md" "$CLAUDE_HOME/CLAUDE.md"
    SIZE=$(du -h "$CLAUDE_HOME/CLAUDE.md" | cut -f1)
    echo -e "${GREEN}✓${RESET} ${DIM}$SIZE${RESET}"
    sleep 0.2
    print_success "${BOLD}SkillForge will be active on every Claude Code session${RESET}"
    sleep 0.3
else
    print_warning "CLAUDE.md not found - will use legacy skill-based activation"
fi

echo ""
animated_check
sleep 0.5

# ============================================================================
# STEP 6: Install Core Skill Files
# ============================================================================
print_step "Step 6/7: Installing Core Skill Files"

echo -e "${DIM}Copying skill files from package...${RESET}"
sleep 0.2
echo ""

# Copy SKILL.md (skill entry point)
if [ -f "$SKILL_FILES_SOURCE/SKILL.md" ]; then
    echo -ne "  ${DIM}SKILL.md (skill entry point)${RESET} "
    sleep 0.3
    cp "$SKILL_FILES_SOURCE/SKILL.md" "$SKILLFORGE_HOME/SKILL.md"
    SIZE=$(du -h "$SKILLFORGE_HOME/SKILL.md" | cut -f1)
    echo -e "${GREEN}✓${RESET} ${DIM}$SIZE${RESET}"
    sleep 0.2
else
    print_error "SKILL.md not found"
    exit 1
fi

# Copy core/ directory (behavioral files)
if [ -d "$SKILL_FILES_SOURCE/core" ]; then
    echo -ne "  ${DIM}core/ (behavioral files)${RESET} "
    sleep 0.3
    cp -r "$SKILL_FILES_SOURCE/core" "$SKILLFORGE_HOME/"
    CORE_FILES=$(count_files "$SKILLFORGE_HOME/core")
    CORE_SIZE=$(get_dir_size "$SKILLFORGE_HOME/core")
    echo -e "${GREEN}✓${RESET} ${DIM}$CORE_FILES files, $CORE_SIZE${RESET}"
    sleep 0.2
else
    print_warning "core/ directory not found"
fi

echo ""
animated_check
sleep 0.5

# ============================================================================
# STEP 7: Install Slash Commands
# ============================================================================
print_step "Step 7/8: Installing Slash Commands"

echo -e "${DIM}Copying slash commands...${RESET}"
sleep 0.2
echo ""

if [ -d "$SKILL_FILES_SOURCE/commands/sf" ]; then
    # Copy all command files
    CMD_FILES=$(find "$SKILL_FILES_SOURCE/commands/sf" -type f -name "*.md")
    CMD_COUNT=$(echo "$CMD_FILES" | wc -l | tr -d ' ')

    current=0
    for cmd_file in $CMD_FILES; do
        current=$((current + 1))
        progress_bar $current $CMD_COUNT
        cp "$cmd_file" "$COMMANDS_DIR/"
    done

    echo -e "\n"
    CMD_SIZE=$(get_dir_size "$COMMANDS_DIR")
    print_success "Installed $CMD_COUNT commands (${CMD_SIZE})"
    sleep 0.3
    echo ""

    # List installed commands
    echo -e "${DIM}Available commands:${RESET}"
    sleep 0.2
    for cmd_file in $(ls "$COMMANDS_DIR"/*.md 2>/dev/null | sort); do
        cmd_name=$(basename "$cmd_file" .md)
        echo -e "  ${CYAN}/sf:${cmd_name}${RESET}"
        sleep 0.1
    done
else
    print_warning "Slash commands not found in package"
fi

echo ""
animated_check
sleep 0.5

# ============================================================================
# STEP 8: Final Verification
# ============================================================================
print_step "Step 8/8: Final Verification"

echo -e "${DIM}Running installation tests...${RESET}"
sleep 0.2
echo ""

# Test skillforge status
echo -ne "  ${DIM}Testing CLI command${RESET} "
sleep 0.4
if skillforge status &> /dev/null; then
    echo -e "${GREEN}✓${RESET}"
else
    echo -e "${YELLOW}!${RESET} ${DIM}Warnings (may be normal)${RESET}"
fi
sleep 0.2

# Verify file structure
echo -ne "  ${DIM}Checking file structure${RESET} "
sleep 0.4
required_files=(
    "$CLAUDE_HOME/CLAUDE.md"
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
sleep 0.5

# ============================================================================
# DONE ANIMATION
# ============================================================================
print_done_animation
sleep 0.8

# ============================================================================
# SUCCESS SCREEN
# ============================================================================

# Calculate elapsed time
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

print_welcome_finale

echo -e "${C3}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
sleep 0.3

# Installation summary
print_box "📊 INSTALLATION SUMMARY" "$BOLD$CYAN"
echo ""
sleep 0.2

echo -e "  ${BOLD}Package Version:${RESET}    ${GREEN}$(python3 -c 'import skillforge; print(skillforge.__version__)' 2>/dev/null || echo 'unknown')${RESET}"
sleep 0.15
echo -e "  ${BOLD}Installation Time:${RESET}  ${GREEN}${ELAPSED}s${RESET}"
sleep 0.15
echo -e "  ${BOLD}SkillForge Home:${RESET}    ${DIM}$SKILLFORGE_HOME${RESET}"
sleep 0.15

echo -e "\n  ${BOLD}Installed Files:${RESET}"
sleep 0.15
echo -e "    ${GREEN}✓${RESET} SKILL.md (entry point)"
sleep 0.1
echo -e "    ${GREEN}✓${RESET} $(count_files "$SKILLFORGE_HOME/core") core behavioral files"
sleep 0.1
echo -e "    ${GREEN}✓${RESET} $(ls "$COMMANDS_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ') slash commands"
sleep 0.1

TOTAL_SIZE=$(du -sh "$SKILLFORGE_HOME" 2>/dev/null | cut -f1)
echo -e "\n  ${BOLD}Total Size:${RESET}         ${GREEN}$TOTAL_SIZE${RESET}"
sleep 0.2

echo -e "\n${C3}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
sleep 0.3

# Next steps
print_box "🚀 NEXT STEPS" "$BOLD$BLUE"
echo ""
sleep 0.2

echo -e "  ${BOLD}${WHITE}1.${RESET} ${BOLD}Restart Claude Code${RESET}"
sleep 0.15
echo -e "     ${DIM}Close and reopen Claude to load SkillForge${RESET}"
sleep 0.15
echo ""

echo -e "  ${BOLD}${WHITE}2.${RESET} ${BOLD}Run the Setup Wizard${RESET}"
sleep 0.15
echo -e "     ${CYAN}claude${RESET} ${DIM}(in any project)${RESET}"
sleep 0.15
echo -e "     ${CYAN}/sf:wizard${RESET}"
sleep 0.15
echo ""

echo -e "  ${BOLD}${WHITE}3.${RESET} ${BOLD}Generate Your First Skill${RESET}"
sleep 0.15
echo -e "     ${DIM}Answer a few questions about your preferences${RESET}"
sleep 0.15
echo -e "     ${DIM}SkillForge will generate personalized skills for your stack${RESET}"
sleep 0.15
echo ""

echo -e "  ${BOLD}${WHITE}4.${RESET} ${BOLD}Start Coding!${RESET}"
sleep 0.15
echo -e "     ${DIM}SkillForge will automatically orchestrate skills${RESET}"
sleep 0.15
echo -e "     ${DIM}Claude will code exactly the way YOU do${RESET}"
sleep 0.15

echo -e "\n${C3}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
sleep 0.3

# Quick reference
print_box "📚 QUICK REFERENCE" "$BOLD$MAGENTA"
echo ""
sleep 0.2

echo -e "  ${BOLD}Commands in Claude Code:${RESET} ${DIM}(use these inside Claude)${RESET}"
sleep 0.1
echo -e "    ${CYAN}/sf:wizard${RESET}      ${DIM}Interactive setup wizard${RESET}"
sleep 0.08
echo -e "    ${CYAN}/sf:generate${RESET}    ${DIM}Generate specific skill with AI${RESET}"
sleep 0.08
echo -e "    ${CYAN}/sf:list${RESET}        ${DIM}List installed skills${RESET}"
sleep 0.08
echo -e "    ${CYAN}/sf:analyze${RESET}     ${DIM}Analyze usage patterns${RESET}"
sleep 0.08
echo -e "    ${CYAN}/sf:optimize${RESET}    ${DIM}Optimize skills${RESET}"
sleep 0.08
echo -e "    ${CYAN}/sf:update${RESET}      ${DIM}Update skill documentation${RESET}"
sleep 0.08
echo -e "    ${CYAN}/sf:introspect${RESET}  ${DIM}Analyze current project${RESET}"
sleep 0.08
echo -e "    ${CYAN}/sf:config${RESET}      ${DIM}View/edit configuration${RESET}"
sleep 0.08
echo -e "    ${CYAN}/sf:status${RESET}      ${DIM}Show SkillForge status${RESET}"
sleep 0.08
echo -e "    ${CYAN}/sf:reset${RESET}       ${DIM}Reset configuration${RESET}"
sleep 0.15
echo ""

echo -e "  ${BOLD}Commands in Terminal:${RESET} ${DIM}(use these in your shell)${RESET}"
sleep 0.1
echo -e "    ${CYAN}skillforge install${RESET}  ${DIM}Install skill files to Claude${RESET}"
sleep 0.08
echo -e "    ${CYAN}skillforge status${RESET}   ${DIM}Check installation status${RESET}"
sleep 0.08
echo -e "    ${CYAN}skillforge version${RESET}  ${DIM}Show version info${RESET}"
sleep 0.08
echo -e "    ${CYAN}skillforge --help${RESET}   ${DIM}Show all available commands${RESET}"
sleep 0.15
echo ""

echo -e "  ${BOLD}Documentation:${RESET}"
echo -e "    ${CYAN}https://github.com/omarpioselli/SkillForge${RESET}"

echo -e "\n${C3}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
sleep 0.3

# Final message
echo -e "${BOLD}${WHITE}Welcome to SkillForge!${RESET} 🎨"
sleep 0.2
echo -e "${DIM}Transform Claude Code into YOUR expert developer.${RESET}"
sleep 0.2
echo ""

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
sleep 0.5

# Wait for user input before closing
echo -e "${DIM}Press any key to exit...${RESET}"
read -n 1 -s -r
