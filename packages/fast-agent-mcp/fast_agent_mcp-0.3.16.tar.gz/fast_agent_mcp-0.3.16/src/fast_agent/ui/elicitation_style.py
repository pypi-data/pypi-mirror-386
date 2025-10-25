"""Shared styling configuration for elicitation UIs (prompt_toolkit)."""

from prompt_toolkit.styles import Style

# Define consistent elicitation style - inspired by usage display and interactive prompt
ELICITATION_STYLE = Style.from_dict(
    {
        # Dialog structure - use ansidefault for true black, remove problematic shadow
        "dialog": "bg:ansidefault",  # True black dialog using ansidefault
        "dialog.body": "bg:ansidefault fg:ansidefault",  # True black dialog body with default text color
        "dialog shadow": "bg:ansidefault",  # Set shadow background to match application
        "dialog.border": "bg:ansidefault",  # True black border background
        # Set application background to true black
        "application": "bg:ansidefault",  # True black application background
        # Title styling with better contrast
        "title": "fg:ansidefault bold",  # Default color title for terminal compatibility
        # Buttons - only define focused state to preserve focus highlighting
        "button.focused": "bg:ansibrightgreen fg:ansiblack bold",  # Bright green with black text for contrast
        "button.arrow": "fg:ansidefault bold",  # Default color arrows for terminal compatibility
        # Form elements with consistent green/yellow theme
        # Checkboxes - green when checked, yellow when focused
        "checkbox": "fg:ansidefault",  # Default color unchecked checkbox (dimmer)
        "checkbox-checked": "fg:ansibrightgreen bold",  # Green when checked (matches buttons)
        "checkbox-selected": "bg:ansidefault fg:ansibrightyellow bold",  # Yellow when focused
        # Radio list styling - consistent with checkbox colors
        "radio-list": "bg:ansidefault",  # True black background for radio list
        "radio": "fg:ansidefault",  # Default color for unselected items (dimmer)
        "radio-selected": "bg:ansidefault fg:ansibrightyellow bold",  # Yellow when focused
        "radio-checked": "fg:ansibrightgreen bold",  # Green when selected (matches buttons)
        # Text input areas - use ansidefault for non-focused (dimmer effect)
        "input-field": "fg:ansidefault bold",  # Default color (inactive) - should be dimmer than white
        "input-field.focused": "fg:ansibrightyellow bold",  # Bright yellow (active)
        "input-field.error": "fg:ansired bold",  # Red text (validation error)
        # Frame styling with ANSI colors - make borders visible
        "frame.border": "fg:ansibrightblack",  # Bright black borders for subtlety
        "frame.label": "fg:ansigray",  # Gray frame labels (less prominent)
        # Labels and text - use default color for terminal compatibility
        "label": "fg:ansidefault",  # Default color labels for terminal compatibility
        "message": "fg:ansibrightcyan",  # Bright cyan messages (no bold)
        # Agent and server names - make them match
        "agent-name": "fg:ansibrightblue bold",
        "server-name": "fg:ansibrightblue bold",  # Same color as agent
        # Validation errors - better contrast
        "validation-toolbar": "bg:ansibrightred fg:ansidefault bold",
        "validation-toolbar.text": "bg:ansibrightred fg:ansidefault",
        "validation.border": "fg:ansibrightred",
        "validation-error": "fg:ansibrightred bold",  # For status line errors
        # Separator styling
        "separator": "fg:ansibrightblue bold",
        # Completion menu - exactly matching enhanced_prompt.py
        "completion-menu.completion": "bg:ansiblack fg:ansigreen",
        "completion-menu.completion.current": "bg:ansiblack fg:ansigreen bold",
        "completion-menu.meta.completion": "bg:ansiblack fg:ansiblue",
        "completion-menu.meta.completion.current": "bg:ansibrightblack fg:ansiblue",
        # Toolbar - matching enhanced_prompt.py exactly
        "bottom-toolbar": "fg:#ansiblack bg:#ansigray",
        "bottom-toolbar.text": "fg:#ansiblack bg:#ansigray",
    }
)
