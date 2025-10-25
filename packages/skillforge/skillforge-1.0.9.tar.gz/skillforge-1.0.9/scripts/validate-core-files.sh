#!/bin/bash

# Script to validate SkillForge Core Configuration Files
# Ensures all required files exist and meet minimum standards

set -e  # Exit on error

echo "🔍 Validating SkillForge Core Files..."
echo "======================================"
echo ""

# Base directory for core files
CORE_DIR="skillforge/data/skill_files/core"

# List of required core files
CORE_FILES=(
    "SKILLFORGE.md"
    "ORCHESTRATION.md"
    "GENERATOR.md"
    "PATTERNS.md"
    "RULES.md"
    "WORKFLOWS.md"
    "MCP_INTEGRATION.md"
)

# Track validation status
all_valid=true
total_lines=0

# Function to validate a file
validate_file() {
    local file_path="$1"
    local file_name=$(basename "$file_path")

    echo "Checking: $file_name"

    # Check if file exists
    if [ ! -f "$file_path" ]; then
        echo "  ❌ File missing: $file_path"
        all_valid=false
        return 1
    fi

    # Check file size (should be substantial, at least 100 lines)
    size=$(wc -l < "$file_path")
    total_lines=$((total_lines + size))

    if [ "$size" -lt 100 ]; then
        echo "  ⚠️  File too short: $size lines (expected >100)"
        all_valid=false
    else
        echo "  ✅ Length: $size lines"
    fi

    # Check for main heading
    if grep -q "^# " "$file_path"; then
        echo "  ✅ Has main heading"
    else
        echo "  ❌ Missing main heading"
        all_valid=false
    fi

    # Check for multiple sections
    section_count=$(grep -c "^## " "$file_path" || echo "0")
    if [ "$section_count" -lt 3 ]; then
        echo "  ⚠️  Few sections: $section_count (expected 3+)"
    else
        echo "  ✅ Sections: $section_count"
    fi

    # Check for code blocks (should have examples)
    code_block_count=$(grep -c '```' "$file_path" || echo "0")
    if [ "$code_block_count" -lt 2 ]; then
        echo "  ⚠️  Few code blocks: $code_block_count (expected 2+)"
    else
        echo "  ✅ Code blocks: $((code_block_count / 2))"
    fi

    echo ""
}

# Validate each core file
for file in "${CORE_FILES[@]}"; do
    file_path="$CORE_DIR/$file"
    validate_file "$file_path"
done

# Check for specific required sections in SKILLFORGE.md
echo "Validating specific sections..."
echo ""

SKILLFORGE_PATH="$CORE_DIR/SKILLFORGE.md"

required_sections=(
    "Core Philosophy"
    "Operational Modes"
    "Skill Discovery Algorithm"
    "Token Economics"
    "Pattern Learning System"
)

echo "Checking SKILLFORGE.md required sections:"
for section in "${required_sections[@]}"; do
    if grep -q "## [0-9]*\\. $section" "$SKILLFORGE_PATH" || grep -q "## $section" "$SKILLFORGE_PATH"; then
        echo "  ✅ $section"
    else
        echo "  ❌ Missing: $section"
        all_valid=false
    fi
done
echo ""

# Summary
echo "======================================"
echo "📊 Validation Summary"
echo "======================================"
echo ""
echo "Files checked: ${#CORE_FILES[@]}"
echo "Total lines: $total_lines"
echo ""

if [ "$all_valid" = true ]; then
    echo "✅ All core files validated successfully!"
    echo ""
    echo "Core files are ready for use."
    exit 0
else
    echo "❌ Validation failed. Please fix the issues above."
    echo ""
    echo "Some files are missing, too short, or missing required sections."
    exit 1
fi
