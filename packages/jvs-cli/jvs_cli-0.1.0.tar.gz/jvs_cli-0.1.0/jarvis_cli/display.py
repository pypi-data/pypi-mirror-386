from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.live import Live
from typing import Optional, Dict, Any
from datetime import datetime
import re
from .models import JarvisStep, ChatCompletionChunk
from .config import DisplayConfig
from .themes import get_theme, ColorTheme
from .animations import typewriter_effect_chunks


class DisplayManager:
    def __init__(self, config: Optional[DisplayConfig] = None):
        self.console = Console()
        self.config = config or DisplayConfig()
        self._current_content = ""
        self._live: Optional[Live] = None
        self._spinner_tasks: Dict[str, Any] = {}

    def print_user_message(self, content: str) -> None:
        # Display user message with styling
        text = Text()
        text.append("You: ", style="bold cyan")
        text.append(content, style="cyan")
        self.console.print(text)
        self.console.print()

    def print_assistant_message(self, content: str) -> None:
        # Display assistant message with markdown rendering
        self.console.print(Text("Jarvis:", style="bold green"))

        if self.config.markdown:
            md = Markdown(content)
            self.console.print(md)
        else:
            self.console.print(content, style="green")

        self.console.print()

    def print_error(self, message: str) -> None:
        # Display error message
        self.console.print(f"[bold red]Error:[/bold red] {message}")
        self.console.print()

    def print_info(self, message: str) -> None:
        # Display info message
        self.console.print(f"[dim]{message}[/dim]")

    def print_step(self, step: JarvisStep) -> None:
        # Display Jarvis step based on type
        if not self.config.show_thinking and step.type == "thinking":
            return

        if not self.config.show_tools and step.type.startswith("mcp_tool"):
            return

        step_type = step.type
        data = step.data

        # Conversation start
        if step_type == "conversation_start":
            self.print_info(f"Starting conversation: {data.conversation_id}")

        # Senser phase
        elif step_type == "senser_start":
            self.print_info("· Analyzing your request...")

        elif step_type == "senser_complete":
            intention = data.intention or "unknown"
            language = data.language or "unknown"
            self.print_info(f"· Intent: {intention} | Language: {language}")

        # Thinking
        elif step_type == "thinking":
            if self.config.show_thinking:
                panel = Panel(
                    data.content or "",
                    title="Thinking",
                    border_style="yellow dim",
                    expand=False,
                )
                self.console.print(panel)

        # Tool execution
        elif step_type == "mcp_tool_start":
            if self.config.show_tools:
                tool_name = data.tools.get("tool_name") if data.tools else "unknown"
                self.print_info(f"· Calling tool: {tool_name}")

        elif step_type == "mcp_tool_executing":
            if self.config.show_tools:
                tool_name = data.tool_name or "unknown"
                self.print_info(f"· Executing: {tool_name}...")

        elif step_type == "mcp_tool_complete":
            if self.config.show_tools:
                tool_name = data.tools.get("tool_name") if data.tools else "unknown"
                success = data.success
                style = "green" if success else "red"
                self.console.print(f"[{style}]· Tool completed: {tool_name}[/{style}]")

        # Knowledge search
        elif step_type == "knowledge_search_start":
            queries = data.queries or []
            self.print_info(f"· Searching knowledge base: {len(queries)} queries")

        elif step_type == "knowledge_search_complete":
            doc_links = data.doc_links or []
            doc_count = len(doc_links)
            self.print_info(f"· Found {doc_count} relevant documents")

            if doc_links and self.config.show_knowledge_sources:
                for doc in doc_links[:5]:
                    title = doc.get("title", "Unknown")
                    url = doc.get("url", "")
                    count = doc.get("count", 0)
                    self.console.print(f"  [{self.theme.knowledge_text}]• {title}[/{self.theme.knowledge_text}] [{self.theme.system_text}](refs: {count})[/{self.theme.system_text}]")
                    if url:
                        self.console.print(f"    [dim {self.theme.system_text}]{url}[/dim {self.theme.system_text}]")

        # Document reading
        elif step_type == "document_reading_start":
            doc_count = data.total_documents or 0
            self.print_info(f"· Reading {doc_count} documents...")

        elif step_type == "document_reading_complete":
            self.print_info("· Document reading completed")

        # Agent execution
        elif step_type == "agent_start":
            agent_type = data.agent_type or "unknown"
            self.print_info(f"· Starting agent: {agent_type}")

        elif step_type == "agent_complete":
            agent_type = data.agent_type or "unknown"
            success = data.success
            self.print_info(f"· Agent completed: {agent_type}")

        # Conversation complete
        elif step_type == "conversation_complete":
            if data.total_time_seconds:
                self.print_info(f"· Total time: {data.total_time_seconds:.2f}s")

        # Error
        elif step_type == "error":
            self.print_error(data.error_message or "Unknown error")

    def start_streaming(self) -> None:
        # Start streaming display (accumulates content)
        self._current_content = ""
        self.console.print(Text("Jarvis:", style="bold green"))

    def update_streaming_content(self, delta_content: str) -> None:
        # Update streaming content (incremental)
        self._current_content += delta_content
        self.console.print(delta_content, end="", style="green")
        self.console.file.flush()

    def end_streaming(self) -> None:
        # End streaming display
        self.console.print("\n")
        self._current_content = ""

    def process_chunk(self, chunk: ChatCompletionChunk) -> Optional[str]:
        # Process a single chunk and return content delta if any
        if not chunk.choices:
            return None

        choice = chunk.choices[0]
        delta = choice.delta

        if not delta:
            return None

        # Handle Jarvis step events
        if delta.jarvis_step:
            self.print_step(delta.jarvis_step)

        # Handle content delta
        if delta.content:
            return delta.content

        # Handle finish reason
        if choice.finish_reason == "stop":
            return None

        if choice.finish_reason == "error":
            self.print_error("An error occurred during processing")

        return None

    def print_conversation_info(self, conversation_id: str) -> None:
        # Print conversation ID info
        self.print_info(f"Conversation ID: {conversation_id}")

    def print_help(self) -> None:
        # Print help message with available commands
        help_text = """
[bold cyan]Available Commands:[/bold cyan]

[yellow]/new[/yellow]       - Start a new conversation
[yellow]/history[/yellow]   - Show conversation history
[yellow]/config[/yellow]    - Show current configuration
[yellow]/help[/yellow]      - Show this help message
[yellow]/exit[/yellow]      - Exit the CLI (or Ctrl+D)

[bold cyan]Keyboard Shortcuts:[/bold cyan]

[yellow]Ctrl+C[/yellow]    - Cancel current request
[yellow]Ctrl+D[/yellow]    - Exit the CLI
        """
        self.console.print(help_text)

    def print_welcome(self) -> None:
        # Print welcome message
        welcome = Panel(
            "[bold cyan]Jarvis CLI[/bold cyan]\n\n"
            "Type your message or use /help for commands",
            border_style="cyan",
            expand=False,
        )
        self.console.print(welcome)
        self.console.print()

    def clear_screen(self) -> None:
        # Clear terminal screen
        self.console.clear()


class LiveWorkflowDisplay:
    """Serial event stream display inspired by Claude Code"""

    def __init__(self, config: Optional[DisplayConfig] = None, theme_name: str = "claude_dark"):
        self.console = Console()
        self.config = config or DisplayConfig()
        self.theme: ColorTheme = get_theme(theme_name)

        # State tracking
        self.conversation_id: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self._current_content: str = ""

        # Track active tool for completion timing
        self._active_tool_start: Optional[float] = None
        self._active_tool_name: Optional[str] = None
        self._tool_status_line: Optional[int] = None
        
        # XML tag patterns for filtering - state machine
        # Tags that are completely hidden (no output)
        self._hidden_tags = {
            'use_mcp_tool', 'goal', 'context', 'tool_name', 'arguments',
            'use_agent', 'agent_name',
            'knowledge_search', 'query',
            'document_reading', 'urls',
            'ask_followup_question', 'question', 'default_value'
        }
        # Tags that need special formatting (collect content then format)
        self._formatted_tags = {
            'update_todo_list', 'update_todo'  # Format with status icons
        }
        # Tags that preserve content (remove tags only)
        self._content_only_tags = {
            'attempt_completion', 'result', 'result_summary'
        }
        # Tags that apply style in real-time (streaming)
        self._styled_tags = {
            'thinking'  # Apply dimmed style while streaming
        }
        self._current_hidden_tag: Optional[str] = None
        self._current_formatted_tag: Optional[str] = None
        self._current_styled_tag: Optional[str] = None
        self._formatted_content: str = ""
        self._buffer: str = ""  # Buffer for incomplete tags


    def _format_thinking(self, content: str) -> str:
        """Format thinking content with dimmed style"""
        if not content.strip():
            return ""
        lines = content.strip().split('\n')
        formatted = [f"[{self.theme.thinking_text}]{line}[/{self.theme.thinking_text}]" for line in lines]
        return '\n' + '\n'.join(formatted) + '\n'
    
    def _format_todo_list(self, content: str) -> str:
        """Format todo list with status icons"""
        if not content.strip():
            return ""
        
        # Extract content from <todos> tag if present
        import re
        todos_match = re.search(r'<todos>(.*?)</todos>', content, re.DOTALL)
        if todos_match:
            content = todos_match.group(1)
        
        lines = content.strip().split('\n')
        formatted = []
        for line in lines:
            line = line.strip()
            if line.startswith('[x]'):
                formatted.append(f"[{self.theme.status_complete}]✓[/{self.theme.status_complete}] ~~{line[3:].strip()}~~")
            elif line.startswith('[-]'):
                formatted.append(f"[{self.theme.status_running}]•[/{self.theme.status_running}] {line[3:].strip()}")
            elif line.startswith('[ ]'):
                formatted.append(f"[{self.theme.system_text}]○[/{self.theme.system_text}] {line[3:].strip()}")
            elif line:
                formatted.append(line)
        return '\n' + '\n'.join(formatted) + '\n' if formatted else ""

    def _parse_xml_tags(self, content: str) -> str:
        """Parse XML tags with state machine for streaming content"""
        if not content:
            return content
        
        # Add to buffer
        self._buffer += content
        result = []
        i = 0
        
        while i < len(self._buffer):
            # Check if we're in a hidden block
            if self._current_hidden_tag:
                closing_tag = f'</{self._current_hidden_tag}>'
                closing_pos = self._buffer.find(closing_tag, i)
                
                if closing_pos != -1:
                    i = closing_pos + len(closing_tag)
                    self._current_hidden_tag = None
                    continue
                else:
                    self._buffer = self._buffer[i:]
                    return ''.join(result)
            
            # Check if we're in a formatted block (collect then format)
            if self._current_formatted_tag:
                closing_tag = f'</{self._current_formatted_tag}>'
                closing_pos = self._buffer.find(closing_tag, i)
                
                if closing_pos != -1:
                    # Collect content
                    self._formatted_content += self._buffer[i:closing_pos]
                    
                    # Recursively parse content for nested tags
                    parsed_content = self._parse_nested_tags(self._formatted_content)
                    
                    # Format based on tag type
                    if self._current_formatted_tag in ('todos', 'update_todo', 'update_todo_list'):
                        formatted = self._format_todo_list(parsed_content)
                        result.append(formatted)
                    
                    # Reset state
                    i = closing_pos + len(closing_tag)
                    self._current_formatted_tag = None
                    self._formatted_content = ""
                    continue
                else:
                    # Keep accumulating content
                    self._formatted_content += self._buffer[i:]
                    self._buffer = ""
                    return ''.join(result)
            
            # Check if we're in a styled block (stream with style marker)
            if self._current_styled_tag:
                closing_tag = f'</{self._current_styled_tag}>'
                closing_pos = self._buffer.find(closing_tag, i)
                
                if closing_pos != -1:
                    # Output remaining content with style marker
                    content_chunk = self._buffer[i:closing_pos]
                    if content_chunk:
                        result.append(f"__STYLED__{self._current_styled_tag}__{content_chunk}")
                    result.append(f"__END_STYLED__{self._current_styled_tag}__")
                    
                    i = closing_pos + len(closing_tag)
                    self._current_styled_tag = None
                    continue
                else:
                    # Output content with style marker and keep buffering
                    content_chunk = self._buffer[i:]
                    if content_chunk:
                        result.append(f"__STYLED__{self._current_styled_tag}__{content_chunk}")
                    self._buffer = ""
                    return ''.join(result)
            
            # Bounds check
            if i >= len(self._buffer):
                break
            
            # Check for opening tags
            if self._buffer[i] == '<':
                tag_end = self._buffer.find('>', i)
                if tag_end == -1:
                    self._buffer = self._buffer[i:]
                    return ''.join(result)
                
                tag_content = self._buffer[i+1:tag_end]
                
                # Check if it's a closing tag
                if tag_content.startswith('/'):
                    tag_name = tag_content[1:].strip()
                    # Skip closing tags for content_only_tags and styled_tags
                    if tag_name in self._content_only_tags or tag_name in self._styled_tags:
                        i = tag_end + 1
                        continue
                    i = tag_end + 1
                    continue
                
                # It's an opening tag
                tag_name = tag_content.split()[0] if ' ' in tag_content else tag_content
                
                # Check if it's a hidden tag
                if tag_name in self._hidden_tags:
                    self._current_hidden_tag = tag_name
                    i = tag_end + 1
                    continue
                
                # Check if it's a formatted tag
                if tag_name in self._formatted_tags:
                    self._current_formatted_tag = tag_name
                    self._formatted_content = ""
                    i = tag_end + 1
                    continue
                
                # Check if it's a styled tag (stream with style)
                if tag_name in self._styled_tags:
                    self._current_styled_tag = tag_name
                    result.append(f"__START_STYLED__{tag_name}__")
                    i = tag_end + 1
                    continue
                
                # Check if it's a content_only tag (remove tag, keep content)
                if tag_name in self._content_only_tags:
                    i = tag_end + 1
                    continue
                
                # Not a special tag, keep it
                result.append(self._buffer[i])
                i += 1
            else:
                # Regular content
                result.append(self._buffer[i])
                i += 1
        
        # Clear buffer if we've processed everything
        self._buffer = ""
        return ''.join(result)
    
    def _parse_nested_tags(self, content: str) -> str:
        """Parse nested tags within formatted content"""
        result = []
        i = 0
        
        while i < len(content):
            if content[i] == '<':
                tag_end = content.find('>', i)
                if tag_end == -1:
                    result.append(content[i])
                    i += 1
                    continue
                
                tag_content = content[i+1:tag_end]
                
                # Check if it's a closing tag
                if tag_content.startswith('/'):
                    tag_name = tag_content[1:].strip()
                    if tag_name in self._content_only_tags:
                        i = tag_end + 1
                        continue
                
                # It's an opening tag
                tag_name = tag_content.split()[0] if ' ' in tag_content else tag_content
                
                # Remove content_only tags
                if tag_name in self._content_only_tags:
                    i = tag_end + 1
                    continue
                
                result.append(content[i])
                i += 1
            else:
                result.append(content[i])
                i += 1
        
        return ''.join(result)

    def process_step(self, step: JarvisStep) -> None:
        """Process a Jarvis step with serial event stream display"""
        step_type = step.type
        data = step.data

        # Conversation start - track start time
        if step_type == "conversation_start":
            self.conversation_id = data.conversation_id
            self.start_time = datetime.now()

        # Senser phase
        elif step_type == "senser_start":
            self.console.print(f"[{self.theme.status_running}]·[/{self.theme.status_running}] [{self.theme.phase_senser}]Analyzing...[/{self.theme.phase_senser}]")

        elif step_type == "senser_complete":
            intention = data.intention or "unknown"
            language = data.language or "unknown"
            self.console.print(
                f"[{self.theme.status_complete}]·[/{self.theme.status_complete}] "
                f"Intent: [{self.theme.accent_primary}]{intention}[/{self.theme.accent_primary}] | "
                f"Language: [{self.theme.accent_primary}]{language}[/{self.theme.accent_primary}]"
            )

        # Planner phase
        elif step_type == "planner_start":
            self.console.print(f"[{self.theme.status_running}]·[/{self.theme.status_running}] [{self.theme.phase_planner}]Planning...[/{self.theme.phase_planner}]")

        elif step_type == "planner_complete":
            self.console.print(f"[{self.theme.status_complete}]·[/{self.theme.status_complete}] Plan created")

        # Actor phase
        elif step_type == "actor_start":
            self.console.print(f"[{self.theme.status_running}]·[/{self.theme.status_running}] [{self.theme.phase_actor}]Executing...[/{self.theme.phase_actor}]")

        elif step_type == "actor_complete":
            self.console.print(f"[{self.theme.status_complete}]·[/{self.theme.status_complete}] Execution complete")

        # Thinking
        elif step_type == "thinking":
            if self.config.show_thinking:
                # Only show status indicator, full thinking content will be shown in streaming
                pass

        # Tool execution
        elif step_type == "mcp_tool_start":
            if self.config.show_tools:
                tool_name = data.tools.get("tool_name") if data.tools else "unknown"
                self._active_tool_name = tool_name
                self._active_tool_start = datetime.now().timestamp()
                
                # Print tool line without newline for in-place update
                self.console.print(
                    f"[{self.theme.status_running}]·[/{self.theme.status_running}] [{self.theme.tool_text}]Tool: {tool_name}[/{self.theme.tool_text}] ",
                    end=""
                )
                self.console.file.flush()

        elif step_type == "mcp_tool_executing":
            if self.config.show_tools:
                # Update on the same line
                self.console.print(f"[{self.theme.status_running}](executing...)[/{self.theme.status_running}]", end="")
                self.console.file.flush()

        elif step_type == "mcp_tool_complete":
            if self.config.show_tools:
                success = data.success
                elapsed = ""
                if self._active_tool_start:
                    duration = datetime.now().timestamp() - self._active_tool_start
                    elapsed = f" [{self.theme.system_text}]({duration:.1f}s)[/{self.theme.system_text}]"
                    self._active_tool_start = None

                # Complete the line with status
                if success:
                    self.console.print(
                        f" [{self.theme.status_complete}]✓ completed[/{self.theme.status_complete}]{elapsed}"
                    )
                else:
                    self.console.print(
                        f" [{self.theme.status_error}]✗ failed[/{self.theme.status_error}]{elapsed}"
                    )
                
                self._active_tool_name = None

        # Knowledge search
        elif step_type == "knowledge_search_start":
            queries = data.queries or []
            self.console.print(
                f"[{self.theme.status_running}]·[/{self.theme.status_running}] [{self.theme.knowledge_text}]Searching knowledge base ({len(queries)} queries)...[/{self.theme.knowledge_text}]"
            )

        elif step_type == "knowledge_search_complete":
            doc_links = data.doc_links or []
            doc_count = len(doc_links)
            self.console.print(
                f"[{self.theme.status_complete}]·[/{self.theme.status_complete}] Found {doc_count} documents"
            )

            if doc_links and self.config.show_knowledge_sources:
                for doc in doc_links[:5]:
                    title = doc.get("title", "Unknown")
                    url = doc.get("url", "")
                    count = doc.get("count", 0)
                    self.console.print(f"  [{self.theme.knowledge_text}]• {title}[/{self.theme.knowledge_text}] [{self.theme.system_text}](refs: {count})[/{self.theme.system_text}]")
                    if url:
                        self.console.print(f"    [dim {self.theme.system_text}]{url}[/dim {self.theme.system_text}]")

        # Document reading
        elif step_type == "document_reading_start":
            doc_count = data.total_documents or 0
            self.console.print(
                f"[{self.theme.status_running}]·[/{self.theme.status_running}] [{self.theme.knowledge_text}]Reading {doc_count} documents...[/{self.theme.knowledge_text}]"
            )

        elif step_type == "document_reading_complete":
            self.console.print(f"[{self.theme.status_complete}]·[/{self.theme.status_complete}] Documents read")

        # Agent execution
        elif step_type == "agent_start":
            agent_type = data.agent_type or "unknown"
            self.console.print(f"[{self.theme.status_running}]·[/{self.theme.status_running}] [{self.theme.phase_actor}]Agent: {agent_type}[/{self.theme.phase_actor}]")

        elif step_type == "agent_complete":
            success = data.success
            if success:
                self.console.print(f"[{self.theme.status_complete}]·[/{self.theme.status_complete}] Agent completed")
            else:
                self.console.print(f"[{self.theme.status_error}]·[/{self.theme.status_error}] Agent failed")

        # Conversation complete
        elif step_type == "conversation_complete":
            if data.total_time_seconds:
                self.console.print(
                    f"\n[{self.theme.system_text}]· Total: {data.total_time_seconds:.1f}s[/{self.theme.system_text}]"
                )

        # Error
        elif step_type == "error":
            error_msg = data.error_message or "Unknown error"
            self.console.print(
                f"[{self.theme.status_error}]· Error: {error_msg}[/{self.theme.status_error}]"
            )

    def print_user_message(self, content: str) -> None:
        """Display user message"""
        self.console.print()
        text = Text()
        text.append("You: ", style=f"{self.theme.user_text} bold")
        text.append(content, style=self.theme.user_text)
        self.console.print(text)
        self.console.print()

    def print_assistant_message(self, content: str, typewriter: bool = False) -> None:
        """Display assistant message with optional typewriter effect"""
        import time

        self.console.print()
        self.console.print(Text("Jarvis:", style=f"{self.theme.assistant_text} bold"))

        if typewriter and len(content) > 100 and not self.config.markdown:
            # Typewriter effect only works well without markdown
            chunks = typewriter_effect_chunks(content, chunk_size=5)
            for chunk in chunks:
                self.console.print(chunk, end="", style=self.theme.assistant_text)
                time.sleep(0.02)  # Small delay for typewriter effect
            self.console.print()
        else:
            # Regular display
            if self.config.markdown:
                md = Markdown(content)
                self.console.print(md)
            else:
                self.console.print(content, style=self.theme.assistant_text)

        self.console.print()

    def start_streaming(self) -> None:
        """Start streaming content display"""
        self._current_content = ""
        self.console.print()
        self.console.print(Text("Jarvis:", style=f"{self.theme.assistant_text} bold"))

    def update_streaming_content(self, delta_content: str) -> None:
        """Update streaming content - print immediately for real-time streaming"""
        self._current_content += delta_content
        
        # Parse and filter XML tags
        filtered_content = self._parse_xml_tags(delta_content)
        
        # Only print if there's actual content after filtering
        if filtered_content:
            # Process style markers
            import re
            
            # Split by style markers
            parts = re.split(r'(__START_STYLED__\w+__|__STYLED__\w+__|__END_STYLED__\w+__)', filtered_content)
            
            for part in parts:
                if not part:
                    continue
                
                # Check for style markers
                if part.startswith('__START_STYLED__'):
                    continue  # Just marks the start, no output
                elif part.startswith('__END_STYLED__'):
                    continue  # Just marks the end, no output
                elif part.startswith('__STYLED__'):
                    # Extract tag name and content
                    match = re.match(r'__STYLED__(\w+)__(.*)', part, re.DOTALL)
                    if match:
                        tag_name = match.group(1)
                        content = match.group(2)
                        if content:
                            # Apply style based on tag
                            if tag_name == 'thinking':
                                self.console.print(content, end="", style=self.theme.thinking_text)
                            else:
                                self.console.print(content, end="", style=self.theme.assistant_text)
                else:
                    # Regular content
                    # Check if content has Rich markup (formatted tags)
                    if '[' in part and ']' in part and '/' in part:
                        # Already formatted, print without additional style
                        self.console.print(part, end="")
                    elif part.strip() or part == '\n':
                        # Regular content, apply assistant style
                        self.console.print(part, end="", style=self.theme.assistant_text)
            
        self.console.file.flush()

    def end_streaming(self) -> None:
        """End streaming content display"""
        self.console.print("\n")

    def process_chunk(self, chunk: ChatCompletionChunk) -> Optional[str]:
        """Process a chunk and return content delta"""
        if not chunk.choices:
            return None

        choice = chunk.choices[0]
        delta = choice.delta

        if not delta:
            return None

        # Handle Jarvis step events
        if delta.jarvis_step:
            self.process_step(delta.jarvis_step)
            # Return None to avoid processing content in the same chunk as step
            # This ensures proper separation between step events and content
            return None

        # Handle content delta
        if delta.content:
            return delta.content

        # Handle finish reason
        if choice.finish_reason == "stop":
            return None

        if choice.finish_reason == "error":
            self.console.print(
                f"[{self.theme.status_error}]Error occurred during processing[/{self.theme.status_error}]"
            )

        return None

    def print_error(self, message: str) -> None:
        """Display error message"""
        self.console.print(
            f"[{self.theme.accent_error} bold]Error:[/{self.theme.accent_error} bold] "
            f"[{self.theme.status_error}]{message}[/{self.theme.status_error}]"
        )
        self.console.print()

    def print_info(self, message: str) -> None:
        """Display info message"""
        self.console.print(f"[{self.theme.system_text}]{message}[/{self.theme.system_text}]")

    def print_success(self, message: str) -> None:
        """Display success message"""
        self.console.print(
            f"[{self.theme.accent_success}]· {message}[/{self.theme.accent_success}]"
        )

    def print_welcome(self) -> None:
        """Print welcome message with theme"""
        welcome = Panel(
            f"[{self.theme.accent_primary} bold]Jarvis CLI[/{self.theme.accent_primary} bold]\n\n"
            f"[{self.theme.assistant_text}]Type your message or use /help for commands[/{self.theme.assistant_text}]",
            border_style=self.theme.border_main,
            expand=False,
        )
        self.console.print(welcome)
        self.console.print()

    def clear_screen(self) -> None:
        """Clear terminal screen"""
        self.console.clear()

    def print_help(self) -> None:
        """Print help message with available commands"""
        help_text = f"""
[{self.theme.accent_primary} bold]Available Commands:[/{self.theme.accent_primary} bold]

[{self.theme.accent_secondary}]/new[/{self.theme.accent_secondary}]       - Start a new conversation
[{self.theme.accent_secondary}]/history[/{self.theme.accent_secondary}]   - Show conversation history
[{self.theme.accent_secondary}]/config[/{self.theme.accent_secondary}]    - Show current configuration
[{self.theme.accent_secondary}]/help[/{self.theme.accent_secondary}]      - Show this help message
[{self.theme.accent_secondary}]/exit[/{self.theme.accent_secondary}]      - Exit the CLI (or Ctrl+D)

[{self.theme.accent_primary} bold]Keyboard Shortcuts:[/{self.theme.accent_primary} bold]

[{self.theme.accent_secondary}]Ctrl+C[/{self.theme.accent_secondary}]    - Cancel current request
[{self.theme.accent_secondary}]Ctrl+D[/{self.theme.accent_secondary}]    - Exit the CLI
        """
        self.console.print(help_text)
