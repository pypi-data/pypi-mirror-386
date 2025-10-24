import re

def markdown_to_rich_markup(text: str) -> str:
    result = text
    result = re.sub(r'\*\*(.+?)\*\*', r'[bold]\1[/bold]', result)
    result = re.sub(r'\*(.+?)\*', r'[italic]\1[/italic]', result)
    result = re.sub(r'_(.+?)_', r'[italic]\1[/italic]', result)
    result = re.sub(r'`([^`]+)`', r'[cyan]\1[/cyan]', result)
    result = re.sub(r'~~(.+?)~~', r'[strike]\1[/strike]', result)
    return result

