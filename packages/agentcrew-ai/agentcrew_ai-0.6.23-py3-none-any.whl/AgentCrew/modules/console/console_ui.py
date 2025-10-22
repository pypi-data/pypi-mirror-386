"""
Main console UI class that orchestrates all console functionality.
Refactored to use separate modules for different responsibilities.
"""

import asyncio
import sys
import time
from typing import Any
from rich.console import Console
from rich.text import Text

try:
    import pyperclip
except ImportError:
    pyperclip = None

import AgentCrew
from AgentCrew.modules.chat.message_handler import MessageHandler, Observer
from loguru import logger
from .utils import agent_evaluation_remove

from .constants import (
    RICH_STYLE_GREEN,
    RICH_STYLE_YELLOW,
    RICH_STYLE_GREEN_BOLD,
    RICH_STYLE_YELLOW_BOLD,
)

from .display_handlers import DisplayHandlers
from .tool_display import ToolDisplayHandlers
from .input_handler import InputHandler
from .ui_effects import UIEffects
from .confirmation_handler import ConfirmationHandler
from .conversation_handler import ConversationHandler
from .command_handlers import CommandHandlers


class ConsoleUI(Observer):
    """
    A console-based UI for the interactive chat that implements the Observer interface
    to receive updates from the MessageHandler.
    """

    def __init__(self, message_handler: MessageHandler):
        """
        Initialize the ConsoleUI.

        Args:
            message_handler: The MessageHandler instance that this UI will observe.
        """
        self.message_handler = message_handler
        self.voice_recording = False
        self.message_handler.attach(self)

        self.console = Console()
        self._last_ctrl_c_time = 0
        self.latest_assistant_response = ""
        self.session_cost = 0.0

        # Initialize component handlers
        self.display_handlers = DisplayHandlers(self.console)
        self.tool_display = ToolDisplayHandlers(self.console)
        self.input_handler = InputHandler(
            self.console, self.message_handler, self.display_handlers
        )
        self.ui_effects = UIEffects(self.console, self.message_handler)
        self.confirmation_handler = ConfirmationHandler(
            self.console, self.input_handler
        )
        self.conversation_handler = ConversationHandler(
            self.console, self.display_handlers
        )
        self.command_handlers = CommandHandlers(self.console, self.message_handler)

    def listen(self, event: str, data: Any = None):
        """
        Update method required by the Observer interface. Handles events from the MessageHandler.

        Args:
            event: The type of event that occurred.
            data: The data associated with the event.
        """

        if event == "thinking_started":
            self.ui_effects.stop_loading_animation()  # Stop loading on first chunk
            self.display_handlers.display_thinking_started(data)  # data is agent_name
        elif event == "thinking_chunk":
            self.display_handlers.display_thinking_chunk(
                data
            )  # data is the thinking chunk
        elif event == "user_message_created":
            self.console.print("\n")
        elif event == "response_chunk":
            _, assistant_response = data
            if (
                "<agent_evaluation>" in assistant_response
                and "</agent_evaluation>" not in assistant_response
            ):
                # Skip incomplete evaluation tags
                return
            if "<agent_evaluation>" in assistant_response:
                assistant_response = (
                    assistant_response[: assistant_response.find("<agent_evaluation>")]
                    + assistant_response[
                        assistant_response.find("</agent_evaluation>") + 19 :
                    ]
                )

            self.ui_effects.stop_loading_animation()  # Stop loading on first chunk
            self.ui_effects.update_live_display(
                assistant_response
            )  # data is the response chunk
        elif event == "tool_use":
            self.ui_effects.stop_loading_animation()  # Stop loading on first chunk
            self.tool_display.display_tool_use(data)  # data is the tool use object
        elif event == "tool_result":
            pass
            # self.tool_display.display_tool_result(data)  # data is dict with tool_use and tool_result
        elif event == "tool_error":
            self.tool_display.display_tool_error(
                data
            )  # data is dict with tool_use and error
        elif event == "tool_confirmation_required":
            self.ui_effects.stop_loading_animation()  # Stop loading on first chunk
            self.confirmation_handler.display_tool_confirmation_request(
                data, self.message_handler
            )  # data is the tool use with confirmation ID
        elif event == "tool_denied":
            self.tool_display.display_tool_denied(
                data
            )  # data is the tool use that was denied
        elif event == "response_completed" or event == "assistant_message_added":
            data = agent_evaluation_remove(data)
            self.ui_effects.finish_response(data)  # data is the complete response
            self.latest_assistant_response = data
        elif event == "error":
            self.display_handlers.display_error(
                data
            )  # data is the error message or dict
            self.ui_effects.cleanup()
        elif event == "clear_requested":
            self.display_handlers.display_message(
                Text("🎮 Chat history cleared.", style=RICH_STYLE_YELLOW_BOLD)
            )
            self.display_handlers.clear_files()
        elif event == "exit_requested":
            self.display_handlers.display_message(
                Text("🎮 Ending chat session. Goodbye!", style=RICH_STYLE_YELLOW_BOLD)
            )
            sys.exit(0)
        elif event == "copy_requested":
            self.copy_to_clipboard(data)  # data is the text to copy
        elif event == "debug_requested":
            self.display_handlers.display_debug_info(
                data
            )  # data is the debug information
        elif event == "think_budget_set":
            thinking_text = Text("Thinking budget set to ", style=RICH_STYLE_YELLOW)
            thinking_text.append(f"{data} tokens.")
            self.display_handlers.display_message(thinking_text)
        elif event == "models_listed":
            self.display_handlers.display_models(
                data
            )  # data is dict of models by provider
        elif event == "model_changed":
            model_text = Text("Switched to ", style=RICH_STYLE_YELLOW)
            model_text.append(f"{data['name']} ({data['id']})")
            self.display_handlers.display_message(model_text)
        elif event == "agents_listed":
            self.display_handlers.display_agents(data)  # data is dict of agent info
        elif event == "agent_changed":
            agent_text = Text("Switched to ", style=RICH_STYLE_YELLOW)
            agent_text.append(f"{data} agent")
            self.display_handlers.display_message(agent_text)
        elif event == "system_message":
            self.display_handlers.display_message(data)
        elif event == "mcp_prompt":
            self.confirmation_handler.display_mcp_prompt_confirmation(
                data, self.input_handler._input_queue
            )
        elif event == "agent_changed_by_transfer":
            transfer_text = Text("Transfered to ", style=RICH_STYLE_YELLOW)
            transfer_text.append(
                f"{data['agent_name'] if 'agent_name' in data else 'other'} agent"
            )
            self.display_handlers.display_message(transfer_text)
        elif event == "agent_continue":
            self.display_handlers.display_message(
                Text(f"\n🤖 {data.upper()}:", style=RICH_STYLE_GREEN_BOLD)
            )
        elif event == "jump_performed":
            jump_text = Text(
                f"🕰️ Jumping to turn {data['turn_number']}...\n",
                style=RICH_STYLE_YELLOW_BOLD,
            )
            preview_text = Text("Conversation rewound to: ", style=RICH_STYLE_YELLOW)
            preview_text.append(data["preview"])

            self.display_handlers.display_message(jump_text)
            self.display_handlers.display_message(preview_text)
        elif event == "thinking_completed":
            self.display_handlers.display_divider()
        elif event == "file_processing":
            self.ui_effects.stop_loading_animation()  # Stop loading on first chunk
            self.display_handlers.add_file(data["file_path"])
        elif event == "file_dropped":
            self.display_handlers._added_files.remove(data["file_path"])
        elif event == "consolidation_completed":
            self.display_handlers.display_consolidation_result(data)
            self.display_handlers.display_loaded_conversation(
                self.message_handler.streamline_messages, self.message_handler
            )

        elif event == "unconsolidation_completed":
            self.display_handlers.display_loaded_conversation(
                self.message_handler.streamline_messages, self.message_handler
            )
        elif event == "conversations_listed":
            self.display_handlers.display_conversations(
                data
            )  # data is list of conversation metadata
            self.conversation_handler.update_cached_conversations(data)
        elif event == "conversation_loaded":
            loaded_text = Text("Loaded conversation: ", style=RICH_STYLE_YELLOW)
            loaded_text.append(data.get("id", "N/A"))
            self.display_handlers.display_message(loaded_text)
        elif event == "conversation_saved":
            logger.info(f"Conversation saved: {data.get('id', 'N/A')}")
        elif event == "clear_requested":
            self.session_cost = 0.0
        elif event == "update_token_usage":
            self._calculate_token_usage(data["input_tokens"], data["output_tokens"])
        elif event == "voice_recording_started":
            self.display_handlers.display_message(
                Text("Start recording press Enter to stop...", style="bold yellow")
            )
        elif event == "voice_activate":
            if data:
                asyncio.run(self.message_handler.process_user_input(data))
                self.input_handler.is_message_processing = True
                # Get assistant response
                assistant_response, input_tokens, output_tokens = asyncio.run(
                    self.message_handler.get_assistant_response()
                )
                self.input_handler.is_message_processing = False

                total_cost = self._calculate_token_usage(input_tokens, output_tokens)

                if assistant_response:
                    # Calculate and display token usage
                    self.display_token_usage(
                        input_tokens, output_tokens, total_cost, self.session_cost
                    )

        elif event == "voice_recording_stopping":
            self.display_handlers.display_message(
                Text("⏹️  Stopping recording...", style="bold yellow")
            )
        elif event == "voice_recording_completed":
            self.voice_recording = False
            # Re-enable normal input
            if hasattr(self, "input_handler"):
                self.input_handler._start_input_thread()

    def copy_to_clipboard(self, text: str):
        """Copy text to clipboard and show confirmation."""
        if text:
            if pyperclip:
                pyperclip.copy(text)
                self.console.print(
                    Text("\n✓ Text copied to clipboard!", style=RICH_STYLE_YELLOW)
                )
            else:
                self.console.print(
                    Text(
                        "\n! Clipboard functionality not available (pyperclip not installed)",
                        style=RICH_STYLE_YELLOW,
                    )
                )
        else:
            self.console.print(Text("\n! No text to copy.", style=RICH_STYLE_YELLOW))

    def start_streaming_response(self, agent_name: str):
        """Start streaming the assistant's response."""
        self.ui_effects.start_streaming_response(agent_name)

    def update_live_display(self, chunk: str):
        """Update the live display with a new chunk of the response."""
        if not self.ui_effects.live:
            self.start_streaming_response(self.message_handler.agent.name)
        self.ui_effects.update_live_display(chunk)

    def finish_live_update(self):
        """Stop the live update display."""
        self.ui_effects.finish_live_update()

    def start_loading_animation(self):
        """Start the loading animation."""
        self.ui_effects.start_loading_animation()

    def stop_loading_animation(self):
        """Stop the loading animation."""
        self.ui_effects.stop_loading_animation()

    def get_user_input(self):
        """Get user input using the input handler."""
        return self.input_handler.get_user_input()

    def _handle_keyboard_interrupt(self):
        """Handle Ctrl+C pressed during streaming or other operations."""
        self.ui_effects.stop_loading_animation()
        self.message_handler.stop_streaming = True

        current_time = time.time()
        if (
            hasattr(self, "_last_ctrl_c_time")
            and current_time - self._last_ctrl_c_time < 2
        ):
            self.console.print(
                Text(
                    "\n🎮 Confirmed exit. Goodbye!",
                    style=RICH_STYLE_YELLOW_BOLD,
                )
            )
            self.input_handler.stop()
            sys.exit(0)
        else:
            self._last_ctrl_c_time = current_time
            self.console.print(
                Text(
                    "\n🎮 Chat interrupted. Press Ctrl+C again within 2 seconds to exit.",
                    style=RICH_STYLE_YELLOW_BOLD,
                )
            )

    def print_welcome_message(self):
        """Print the welcome message for the chat."""
        version = getattr(AgentCrew, "__version__", "Unknown")
        self.display_handlers.print_welcome_message(version)

    def print_logo(self):
        self.console.print(
            Text(
                """
  █████╗   ██████╗  ███████╗ ███╗   ██╗ ████████╗  ██████╗ ██████╗  ███████╗ ██╗    ██╗
 ██╔══██╗ ██╔════╝  ██╔════╝ ████╗  ██║ ╚══██╔══╝ ██╔════╝ ██╔══██╗ ██╔════╝ ██║    ██║
 ███████║ ██║  ███╗ █████╗   ██╔██╗ ██║    ██║    ██║      ██████╔╝ █████╗   ██║ █╗ ██║
 ██╔══██║ ██║   ██║ ██╔══╝   ██║╚██╗██║    ██║    ██║      ██╔══██╗ ██╔══╝   ██║███╗██║
 ██║  ██║ ╚██████╔╝ ███████╗ ██║ ╚████║    ██║    ╚██████╗ ██║  ██║ ███████╗ ╚███╔███╔╝
 ╚═╝  ╚═╝  ╚═════╝  ╚══════╝ ╚═╝  ╚═══╝    ╚═╝     ╚═════╝ ╚═╝  ╚═╝ ╚══════╝  ╚══╝╚══╝ 
        """,
                RICH_STYLE_GREEN,
            )
        )

    def display_token_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        total_cost: float,
        session_cost: float,
    ):
        """Display token usage and cost information."""
        self.display_handlers.display_token_usage(
            input_tokens, output_tokens, total_cost, session_cost
        )

    def _calculate_token_usage(self, input_tokens: int, output_tokens: int):
        """Calculate token usage and update session cost."""
        total_cost = self.message_handler.agent.calculate_usage_cost(
            input_tokens, output_tokens
        )
        self.session_cost += total_cost
        return total_cost

    def start(self):
        """Start the console UI main loop."""
        self.print_logo()
        self.print_welcome_message()

        self.session_cost = 0.0

        try:
            while True:
                try:
                    # Get user input (now in separate thread)
                    self.stop_loading_animation()  # Stop if any
                    user_input = self.get_user_input()

                    # Handle list command directly
                    if user_input.strip() == "/list":
                        conversations = self.message_handler.list_conversations()
                        self.conversation_handler.update_cached_conversations(
                            conversations
                        )
                        self.display_handlers.display_conversations(conversations)
                        continue

                    # Handle load command directly
                    elif user_input.strip().startswith("/load "):
                        load_arg = user_input.strip()[
                            6:
                        ].strip()  # Extract argument after "/load "
                        if load_arg:
                            self.conversation_handler.handle_load_conversation(
                                load_arg, self.message_handler
                            )
                        else:
                            self.console.print(
                                Text(
                                    "Usage: /load <conversation_id> or /load <number>",
                                    style=RICH_STYLE_YELLOW,
                                )
                            )
                        continue

                    elif user_input.strip() == "/help":
                        self.console.print("\n")
                        self.print_welcome_message()
                        continue

                    elif user_input.strip().startswith("/export_agent "):
                        # Extract arguments after "/export_agent "
                        args = user_input.strip()[14:].strip()
                        if args:
                            # Split into agent names and output file
                            # Expected format: /export_agent <agent1,agent2,...> <output_file>
                            parts = args.rsplit(maxsplit=1)
                            if len(parts) == 2:
                                agent_names, output_file = parts
                                self.command_handlers.handle_export_agent_command(
                                    agent_names, output_file
                                )
                            else:
                                self.console.print(
                                    Text(
                                        "Usage: /export_agent <agent_names> <output_file>\n"
                                        "Export selected agents to a TOML file.\n"
                                        "Agent names should be comma-separated.\n"
                                        "Example: /export_agent Agent1,Agent2 ./my_agents.toml",
                                        style=RICH_STYLE_YELLOW,
                                    )
                                )
                        else:
                            self.console.print(
                                Text(
                                    "Usage: /export_agent <agent_names> <output_file>\n"
                                    "Export selected agents to a TOML file.\n"
                                    "Agent names should be comma-separated.\n"
                                    "Example: /export_agent Agent1,Agent2 ./my_agents.toml",
                                    style=RICH_STYLE_YELLOW,
                                )
                            )
                        continue

                    elif user_input.strip().startswith("/import_agent "):
                        file_or_url = user_input.strip()[
                            14:
                        ].strip()  # Extract argument after "/import_agent "
                        if file_or_url:
                            self.command_handlers.handle_import_agent_command(
                                file_or_url
                            )
                        else:
                            self.console.print(
                                Text(
                                    "Usage: /import_agent <file_path_or_url>\nImport/replace agents from file or URL.\nExample: /import_agent ./agents.toml or /import_agent https://example.com/agents.toml",
                                    style=RICH_STYLE_YELLOW,
                                )
                            )
                        continue

                    # Handle edit_agent command directly
                    elif user_input.strip() == "/edit_agent":
                        self.command_handlers.handle_edit_agent_command()
                        continue

                    # Handle edit_mcp command directly
                    elif user_input.strip() == "/edit_mcp":
                        self.command_handlers.handle_edit_mcp_command()
                        continue

                    # Handle edit_config command directly
                    elif user_input.strip() == "/edit_config":
                        self.command_handlers.handle_edit_config_command()
                        continue

                    # Start loading animation while waiting for response
                    if (
                        not user_input.startswith("/")
                        or user_input.startswith("/file ")
                        or user_input.startswith("/consolidate ")
                        or user_input.startswith("/agent ")
                        or user_input.startswith("/model ")
                    ):
                        self.start_loading_animation()

                    if user_input.startswith("/voice"):
                        self.input_handler._stop_input_thread()
                        self.voice_recording = True

                    # Process user input and commands
                    should_exit, was_cleared = asyncio.run(
                        self.message_handler.process_user_input(user_input)
                    )

                    if self.voice_recording:
                        input()
                        should_exit, was_cleared = asyncio.run(
                            self.message_handler.process_user_input("/end_voice")
                        )
                    # Exit if requested
                    if should_exit:
                        break

                    # Skip to next iteration if messages were cleared
                    if was_cleared:
                        continue

                    # Skip to next iteration if no messages to process
                    if not self.message_handler.agent.history:
                        continue

                    self.input_handler.is_message_processing = True
                    # Get assistant response
                    assistant_response, input_tokens, output_tokens = asyncio.run(
                        self.message_handler.get_assistant_response()
                    )

                    self.input_handler.is_message_processing = False

                    # Ensure loading animation is stopped
                    self.stop_loading_animation()

                    total_cost = self._calculate_token_usage(
                        input_tokens, output_tokens
                    )

                    if assistant_response:
                        # Calculate and display token usage
                        self.display_token_usage(
                            input_tokens, output_tokens, total_cost, self.session_cost
                        )
                except KeyboardInterrupt:
                    self._handle_keyboard_interrupt()
                    self.input_handler.is_message_processing = False
                    continue  # Continue the loop instead of breaking
        finally:
            # Clean up input thread when exiting
            self.input_handler.stop()
            self.ui_effects.cleanup()
