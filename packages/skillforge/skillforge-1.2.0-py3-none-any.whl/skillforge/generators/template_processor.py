"""Template processor for SkillForge code generation.

This module provides a lightweight template engine with Handlebars/Mustache-like
syntax for processing code templates with variables, conditionals, loops, and
partial includes.

Supported syntax:
- Variables: {{variable_name}}
- Dot notation: {{user.name}}
- Default values: {{variable|default_value}}
- Conditionals: {{#if condition}}...{{/if}}
- Else blocks: {{#if x}}...{{else}}...{{/if}}
- Loops: {{#each items}}{{name}}{{/each}}
- Includes: {{> partial_name}}
- Raw output: {{{raw_html}}}
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class TemplateError(Exception):
    """Base exception for template processing errors."""
    pass


class TemplateSyntaxError(TemplateError):
    """Raised when template syntax is invalid."""
    pass


class TemplateVariableError(TemplateError):
    """Raised when required variables are missing."""
    pass


class TemplateProcessor:
    """Process templates with variables, conditionals, loops, and includes.

    This processor implements a simplified Handlebars/Mustache-like template
    engine with support for common templating operations.

    Attributes:
        template_dir: Base directory for loading partial templates
        partials: Cache of loaded partial templates
        strict_mode: If True, raise errors on missing variables
        track_usage: If True, track which variables are actually used
    """

    # Regular expression patterns for template syntax
    VAR_PATTERN = re.compile(r'\{\{([^{}#/>!]+?)\}\}')
    RAW_VAR_PATTERN = re.compile(r'\{\{\{([^{}]+?)\}\}\}')
    CONDITIONAL_PATTERN = re.compile(
        r'\{\{#if\s+([^}]+?)\}\}(.*?)(?:\{\{else\}\}(.*?))?\{\{/if\}\}',
        re.DOTALL
    )
    LOOP_PATTERN = re.compile(
        r'\{\{#each\s+([^}]+?)\}\}(.*?)\{\{/each\}\}',
        re.DOTALL
    )
    INCLUDE_PATTERN = re.compile(r'\{\{>\s*([^}]+?)\}\}')
    COMMENT_PATTERN = re.compile(r'\{\{!.*?\}\}', re.DOTALL)

    def __init__(
        self,
        template_dir: Optional[Union[str, Path]] = None,
        strict_mode: bool = True
    ):
        """Initialize the template processor.

        Args:
            template_dir: Base directory for loading templates and partials
            strict_mode: If True, raise errors on missing required variables
        """
        self.template_dir = Path(template_dir) if template_dir else None
        self.partials: Dict[str, str] = {}
        self.strict_mode = strict_mode
        self._used_variables: Set[str] = set()
        self._required_variables: Set[str] = set()

    def load_template(self, template_path: Union[str, Path]) -> str:
        """Load a template file from disk.

        Args:
            template_path: Path to template file (absolute or relative to template_dir)

        Returns:
            Template content as string

        Raises:
            FileNotFoundError: If template file doesn't exist
            TemplateError: If template cannot be read
        """
        path = Path(template_path)

        # Try absolute path first
        if not path.is_absolute() and self.template_dir:
            path = self.template_dir / path

        try:
            return path.read_text(encoding='utf-8')
        except FileNotFoundError:
            raise FileNotFoundError(f"Template not found: {path}")
        except Exception as e:
            raise TemplateError(f"Error reading template {path}: {e}")

    def process(
        self,
        template: str,
        variables: Dict[str, Any],
        validate: bool = True
    ) -> str:
        """Process a template with the given variables.

        This is the main entry point for template processing. It applies all
        transformations in the correct order.

        Args:
            template: Template string to process
            variables: Dictionary of variables to substitute
            validate: If True, validate variables before processing

        Returns:
            Processed template string

        Raises:
            TemplateVariableError: If required variables are missing (strict mode)
            TemplateSyntaxError: If template syntax is invalid
        """
        # Reset tracking
        self._used_variables = set()
        self._required_variables = set()

        # Remove comments first
        template = self._remove_comments(template)

        # Find all required variables
        if validate:
            self._extract_required_variables(template)
            self._validate_variables(variables)

        # Process in order: includes -> conditionals -> loops -> variables
        template = self.process_includes(template)
        template = self.process_conditionals(template, variables)
        template = self.process_loops(template, variables)
        template = self.substitute_variables(template, variables)

        # Warn about unused variables
        if validate:
            self._warn_unused_variables(variables)

        return template

    def process_conditionals(self, template: str, variables: Dict[str, Any]) -> str:
        """Process conditional blocks in template.

        Supports:
        - {{#if variable}}...{{/if}}
        - {{#if variable}}...{{else}}...{{/if}}

        Args:
            template: Template string with conditionals
            variables: Variables for evaluating conditions

        Returns:
            Template with conditionals resolved
        """
        def replace_conditional(match: re.Match) -> str:
            condition = match.group(1).strip()
            if_block = match.group(2)
            else_block = match.group(3) or ''

            # Evaluate condition
            is_truthy = self._evaluate_condition(condition, variables)

            # Return appropriate block
            if is_truthy:
                return if_block
            else:
                return else_block

        # Process nested conditionals from inside out
        prev_template = None
        while prev_template != template:
            prev_template = template
            template = self.CONDITIONAL_PATTERN.sub(replace_conditional, template)

        return template

    def process_loops(self, template: str, variables: Dict[str, Any]) -> str:
        """Process loop blocks in template.

        Supports:
        - {{#each items}}{{name}}{{/each}}
        - Access to {{@index}} and {{@first}}, {{@last}} special variables
        - Nested loops with proper tag balancing

        Args:
            template: Template string with loops
            variables: Variables containing iterable data

        Returns:
            Template with loops expanded
        """
        # Find and process loops with balanced tags (innermost first)
        while True:
            loop_info = self._find_innermost_loop(template)
            if loop_info is None:
                break

            start, end, iterator_name, loop_body = loop_info

            # Process this loop
            expanded = self._expand_loop(iterator_name, loop_body, variables)

            # Replace in template
            template = template[:start] + expanded + template[end:]

        return template

    def _find_innermost_loop(self, template: str) -> Optional[Tuple[int, int, str, str]]:
        """Find the first (outermost) loop block with balanced tags.

        Returns:
            Tuple of (start_pos, end_pos, iterator_name, loop_body) or None if no loop found
        """
        # Find first {{#each}} tag
        start_pattern = re.compile(r'\{\{#each\s+([^}]+?)\}\}')
        match = start_pattern.search(template)

        if not match:
            return None

        start_pos = match.start()
        iterator_name = match.group(1).strip()
        content_start = match.end()

        # Find matching {{/each}} by counting nesting level
        depth = 1
        pos = content_start

        while pos < len(template) and depth > 0:
            # Check for nested {{#each}}
            next_start = template.find('{{#each', pos)
            next_end = template.find('{{/each}}', pos)

            if next_end == -1:
                # No closing tag found
                raise TemplateSyntaxError(f"Unclosed loop: {{{{#each {iterator_name}}}}}")

            if next_start != -1 and next_start < next_end:
                # Found a nested opening tag
                depth += 1
                pos = next_start + 7  # len('{{#each')
            else:
                # Found a closing tag
                depth -= 1
                if depth == 0:
                    # This is our matching closing tag
                    loop_body = template[content_start:next_end]
                    end_pos = next_end + 9  # len('{{/each}}')
                    return (start_pos, end_pos, iterator_name, loop_body)
                pos = next_end + 9

        raise TemplateSyntaxError(f"Unclosed loop: {{{{#each {iterator_name}}}}}")

    def _expand_loop(self, iterator_name: str, loop_body: str, variables: Dict[str, Any]) -> str:
        """Expand a single loop block.

        Args:
            iterator_name: Name of the iterator variable
            loop_body: Template content inside the loop
            variables: Variables for substitution

        Returns:
            Expanded loop content
        """
        # Get the iterable
        items = self._get_nested_value(iterator_name, variables)

        if items is None:
            if self.strict_mode:
                raise TemplateVariableError(f"Loop variable not found: {iterator_name}")
            return ''

        if not isinstance(items, (list, tuple)):
            items = [items]

        # Expand loop
        result = []
        for index, item in enumerate(items):
            # Create loop context
            loop_vars = variables.copy()

            # Handle different item types
            if isinstance(item, dict):
                loop_vars.update(item)
            else:
                loop_vars['this'] = item

            # Add special loop variables
            loop_vars['@index'] = index
            loop_vars['@first'] = index == 0
            loop_vars['@last'] = index == len(items) - 1
            loop_vars['@length'] = len(items)

            # Process nested loops first, then substitute variables
            processed = self.process_loops(loop_body, loop_vars)
            processed = self.substitute_variables(processed, loop_vars)
            result.append(processed)

        return ''.join(result)

    def process_includes(self, template: str) -> str:
        """Process partial includes in template.

        Supports:
        - {{> partial_name}}

        Partials are loaded from template_dir if set, or from the partials cache.

        Args:
            template: Template string with includes

        Returns:
            Template with partials included

        Raises:
            TemplateError: If partial cannot be loaded
        """
        def replace_include(match: re.Match) -> str:
            partial_name = match.group(1).strip()

            # Check cache first
            if partial_name in self.partials:
                return self.partials[partial_name]

            # Try to load from file
            if self.template_dir:
                try:
                    partial_path = self.template_dir / f"{partial_name}.hbs"
                    if not partial_path.exists():
                        partial_path = self.template_dir / partial_name

                    partial_content = partial_path.read_text(encoding='utf-8')
                    self.partials[partial_name] = partial_content
                    return partial_content
                except Exception as e:
                    raise TemplateError(f"Error loading partial '{partial_name}': {e}")

            raise TemplateError(f"Partial not found: {partial_name}")

        # Process includes (may be nested)
        prev_template = None
        while prev_template != template:
            prev_template = template
            template = self.INCLUDE_PATTERN.sub(replace_include, template)

        return template

    def substitute_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in template.

        Supports:
        - {{variable}}
        - {{user.name}} (dot notation)
        - {{variable|default}} (default values)
        - {{{raw_html}}} (unescaped output)

        Args:
            template: Template string with variables
            variables: Dictionary of variable values

        Returns:
            Template with variables substituted
        """
        # Process raw variables first (no escaping)
        def replace_raw_var(match: re.Match) -> str:
            var_expr = match.group(1).strip()
            value = self._resolve_variable(var_expr, variables, escape=False)
            return str(value) if value is not None else ''

        template = self.RAW_VAR_PATTERN.sub(replace_raw_var, template)

        # Process regular variables (with escaping)
        def replace_var(match: re.Match) -> str:
            var_expr = match.group(1).strip()

            # Skip special syntax (already processed)
            if var_expr.startswith(('#', '/', '>', '!')):
                return match.group(0)

            value = self._resolve_variable(var_expr, variables, escape=True)
            return str(value) if value is not None else ''

        template = self.VAR_PATTERN.sub(replace_var, template)

        return template

    def register_partial(self, name: str, content: str) -> None:
        """Register a partial template for later use.

        Args:
            name: Name to register the partial under
            content: Partial template content
        """
        self.partials[name] = content

    def _resolve_variable(
        self,
        var_expr: str,
        variables: Dict[str, Any],
        escape: bool = True
    ) -> Any:
        """Resolve a variable expression with support for defaults and dot notation.

        Args:
            var_expr: Variable expression (e.g., 'user.name' or 'var|default')
            variables: Variable dictionary
            escape: Whether to HTML-escape the result

        Returns:
            Resolved variable value
        """
        # Handle default values
        parts = var_expr.split('|', 1)
        var_name = parts[0].strip()
        default = parts[1].strip() if len(parts) > 1 else None

        # Get value with dot notation support
        value = self._get_nested_value(var_name, variables)

        # Track usage
        self._used_variables.add(var_name.split('.')[0])

        # Handle missing variables
        if value is None:
            if default is not None:
                return default
            if self.strict_mode:
                raise TemplateVariableError(f"Variable not found: {var_name}")
            return ''

        # Escape HTML if needed
        if escape and isinstance(value, str):
            value = self._escape_html(value)

        return value

    def _get_nested_value(self, path: str, variables: Dict[str, Any]) -> Any:
        """Get a value from variables using dot notation.

        Args:
            path: Dot-separated path (e.g., 'user.address.city')
            variables: Variable dictionary

        Returns:
            Value at the path, or None if not found
        """
        parts = path.split('.')
        value = variables

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None

        return value

    def _evaluate_condition(self, condition: str, variables: Dict[str, Any]) -> bool:
        """Evaluate a conditional expression.

        Args:
            condition: Condition to evaluate
            variables: Variable dictionary

        Returns:
            True if condition is truthy
        """
        value = self._get_nested_value(condition, variables)

        # Track usage
        self._used_variables.add(condition.split('.')[0])

        # Evaluate truthiness
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (list, dict, str)):
            return len(value) > 0
        if isinstance(value, (int, float)):
            return value != 0

        return bool(value)

    def _extract_required_variables(self, template: str) -> None:
        """Extract all variables referenced in template.

        Args:
            template: Template string to analyze
        """
        # Find all variable references
        for pattern in [self.VAR_PATTERN, self.RAW_VAR_PATTERN]:
            for match in pattern.finditer(template):
                var_expr = match.group(1).strip()
                if not var_expr.startswith(('#', '/', '>', '!', '@')):
                    # Extract root variable name (before dot or pipe)
                    root_var = var_expr.split('.')[0].split('|')[0].strip()
                    if root_var and root_var != 'this':
                        self._required_variables.add(root_var)

        # Find variables in conditionals
        for match in self.CONDITIONAL_PATTERN.finditer(template):
            condition = match.group(1).strip()
            root_var = condition.split('.')[0].strip()
            if root_var:
                self._required_variables.add(root_var)

        # Find variables in loops
        for match in self.LOOP_PATTERN.finditer(template):
            iterator = match.group(1).strip()
            root_var = iterator.split('.')[0].strip()
            if root_var:
                self._required_variables.add(root_var)

    def _validate_variables(self, variables: Dict[str, Any]) -> None:
        """Validate that all required variables are provided.

        Args:
            variables: Variable dictionary to validate

        Raises:
            TemplateVariableError: If required variables are missing
        """
        if not self.strict_mode:
            return

        missing = self._required_variables - set(variables.keys())
        if missing:
            raise TemplateVariableError(
                f"Missing required variables: {', '.join(sorted(missing))}"
            )

    def _warn_unused_variables(self, variables: Dict[str, Any]) -> None:
        """Warn about variables that were provided but not used.

        Args:
            variables: Variable dictionary
        """
        unused = set(variables.keys()) - self._used_variables
        if unused:
            import warnings
            warnings.warn(
                f"Unused variables: {', '.join(sorted(unused))}",
                UserWarning
            )

    def _remove_comments(self, template: str) -> str:
        """Remove template comments.

        Args:
            template: Template string

        Returns:
            Template with comments removed
        """
        return self.COMMENT_PATTERN.sub('', template)

    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters.

        Args:
            text: Text to escape

        Returns:
            Escaped text
        """
        return (
            text.replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#x27;')
        )
