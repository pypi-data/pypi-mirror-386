"""Rich formatting utilities for enhanced text display with syntax highlighting."""

import re
from typing import List, Tuple

from rich.console import Console
from rich.syntax import Syntax


def format_explanation_with_syntax(explanation: str, console: Console) -> None:
    """Format and display explanation text with syntax-highlighted code blocks.

    Args:
        explanation: The explanation text that may contain code blocks
        console: Rich console instance for output
    """
    # Split the text into parts: regular text and code blocks
    parts = _split_text_and_code_blocks(explanation)

    for i, (part_type, content) in enumerate(parts):
        if part_type == "text":
            # Convert markdown to Rich formatting and print
            formatted_text = _convert_markdown_to_rich(content.strip())
            console.print(formatted_text)
        elif part_type == "sql":
            # Add empty line before code block (unless it's the first part)
            if i > 0:
                console.print()
            # Print SQL code block with syntax highlighting
            if content.strip():
                syntax = Syntax(
                    content.strip(), "sql", theme="monokai", line_numbers=False
                )
                console.print(syntax)
            # Add empty line after code block (unless it's the last part)
            if i < len(parts) - 1:
                console.print()
        elif part_type == "bash":
            # Add empty line before code block (unless it's the first part)
            if i > 0:
                console.print()
            # Print bash code block with syntax highlighting
            if content.strip():
                syntax = Syntax(
                    content.strip(), "bash", theme="monokai", line_numbers=False
                )
                console.print(syntax)
            # Add empty line after code block (unless it's the last part)
            if i < len(parts) - 1:
                console.print()


def _convert_markdown_to_rich(text: str) -> str:
    """Convert markdown formatting to Rich markup for CLI display.

    Args:
        text: Text with markdown formatting (**bold**, *italic*)

    Returns:
        Text with Rich markup tags
    """
    # Convert **bold** to Rich bold (bright cyan)
    text = re.sub(r"\*\*([^*]+)\*\*", r"[bold bright_cyan]\1[/bold bright_cyan]", text)

    # Convert *italic* to Rich dim (slightly dimmed)
    text = re.sub(r"\*([^*]+)\*", r"[dim]\1[/dim]", text)

    # Wrap everything in blue to maintain consistency
    return f"[blue]{text}[/blue]"


def _split_text_and_code_blocks(text: str) -> List[Tuple[str, str]]:
    """Split text into alternating text and code block parts.

    Args:
        text: Input text with potential code blocks

    Returns:
        List of tuples (part_type, content) where part_type is 'text', 'sql', or 'bash'
    """
    parts = []

    # Pattern to match code blocks with language specification (only properly tagged ones)
    code_block_pattern = r"```(sql|bash|shell|postgresql)\s*\n(.*?)\n```"

    last_end = 0

    for match in re.finditer(code_block_pattern, text, re.DOTALL | re.IGNORECASE):
        # Add text before the code block
        if match.start() > last_end:
            text_before = text[last_end : match.start()].strip()
            if text_before:
                parts.append(("text", text_before))

        # Determine code block type based on language tag
        language = match.group(1).lower()
        code_content = match.group(2).strip()

        if language in ["sql", "postgresql"]:
            parts.append(("sql", code_content))
        elif language in ["bash", "shell"]:
            parts.append(("bash", code_content))

        last_end = match.end()

    # Add remaining text after the last code block
    if last_end < len(text):
        remaining_text = text[last_end:].strip()
        if remaining_text:
            parts.append(("text", remaining_text))

    return parts


def clean_and_format_explanation(text: str) -> str:
    """Clean explanation text but preserve code blocks for later syntax highlighting.

    Args:
        text: Raw explanation text from LLM

    Returns:
        Cleaned text with preserved code blocks
    """
    # Remove common prefixes that shouldn't be there
    text = re.sub(r"^--\s*", "", text, flags=re.MULTILINE)

    # Don't remove code block markers here - we need them for syntax highlighting

    # Fix spacing around bold/italic markdown
    text = re.sub(r"\*\*([^*]+)\*\*", r"**\1**", text)
    text = re.sub(r"\*([^*]+)\*", r"*\1*", text)

    # Add proper line breaks before numbered lists (but not if already properly formatted)
    text = re.sub(r"(?<!\n)(\d+\.\s+\*\*)", r"\n\n\1", text)
    text = re.sub(r"(?<!\n)(\d+\.\s+[A-Z])", r"\n\n\1", text)

    # Add line breaks before bullet points with proper markdown
    text = re.sub(r"(?<!\n)\s*-\s+([A-Z*])", r"\n\n- \1", text)

    # Ensure proper spacing after periods before new sentences
    text = re.sub(r"\.(?!\n)\s*([A-Z][a-z])", r".\n\n\1", text)

    # Fix spacing around colons followed by lists
    text = re.sub(r":(?!\n)\s*([A-Z*-])", r":\n\n\1", text)

    # Clean up excessive whitespaces within lines
    text = re.sub(r"[ \t]+", " ", text)

    # Clean up multiple newlines (max 2 consecutive)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

    # Ensure code blocks are properly separated from text
    text = re.sub(r"([.:])\s*(```)", r"\1\n\n\2", text)
    text = re.sub(r"(```[^`]*```)\s*([A-Z*])", r"\1\n\n\2", text)

    return text.strip()
