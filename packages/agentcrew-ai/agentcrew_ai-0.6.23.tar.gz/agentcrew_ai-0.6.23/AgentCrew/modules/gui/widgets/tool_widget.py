import json
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QFrame,
)
from PySide6.QtCore import Qt
from AgentCrew.modules.gui.themes import StyleProvider


class ToolWidget(QWidget):
    """Modern widget to display tool use and results in the chat UI."""

    # Tool icons and colors are now managed by the StyleProvider and themes

    def __init__(
        self,
        tool_name: str,
        tool_data: Dict[str, Any],
        result_data: Optional[Any] = None,
        is_error: bool = False,
        parent=None,
    ):
        """
        Initialize a tool widget with tool use and optional result.

        Args:
            tool_name: The name of the tool
            tool_data: Dictionary containing tool use data
            result_data: Optional result data from tool execution
            is_error: Whether the result is an error
            parent: Parent widget
        """
        super().__init__(parent)

        # Store tool data
        self.tool_name = tool_name
        self.tool_data = tool_data
        self.result_data = result_data
        self.is_error = is_error
        self.is_expanded = False
        self.style_provider = StyleProvider()

        # Setup main layout - reduced margins and spacing for compactness
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.setSpacing(2)

        # Create card container with rounded corners and shadow - more compact
        self.card = QFrame(self)
        self.card.setObjectName("toolCard")
        self._apply_card_style()
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(6, 6, 6, 6)  # Reduced from 12px
        self.card_layout.setSpacing(4)  # Reduced from 8px

        # Create header section
        self._create_header()

        # Create single collapsible content section (input + result)
        self._create_content_section()

        # If we don't have result data yet, show progress
        if result_data is None:
            self._create_progress_section()

        # Add card to main layout
        self.main_layout.addWidget(self.card)
        self.content_container.setVisible(False)

    def _apply_card_style(self):
        """Apply the appropriate card style based on error state"""
        if self.is_error:
            self.card.setStyleSheet(self.style_provider.get_tool_card_error_style())
        else:
            self.card.setStyleSheet(self.style_provider.get_tool_card_style())

    def _get_tool_icon(self) -> str:
        """Get appropriate icon for the tool"""
        return self.style_provider.get_tool_icon(self.tool_name)

    def _create_header(self):
        """Create the header section with tool name and controls"""
        header_layout = QHBoxLayout()

        # Tool icon and name - reduced sizes for subtlety
        tool_icon = QLabel(self._get_tool_icon())
        tool_icon_font = tool_icon.font()
        tool_icon_font.setPixelSize(13)
        tool_icon.setFont(tool_icon_font)  # Reduced from 16px

        tool_name_label = QLabel(
            f"<b>{self.tool_name.replace('_', ' ').capitalize()}</b>"
        )
        tool_name_font = tool_name_label.font()
        tool_name_font.setPixelSize(13)
        tool_name_label.setFont(tool_name_font)
        tool_name_label.setStyleSheet(self.style_provider.get_tool_header_style())

        # Status indicator
        if self.is_error:
            status_text = "❌ Error"
            status_attr = "error"
        elif self.result_data is not None:
            status_text = "✅ Complete"
            status_attr = "complete"
        else:
            status_text = "⏳ Running"
            status_attr = "running"

        status_label = QLabel(status_text)
        status_label.setProperty("status", status_attr)
        status_label.setStyleSheet(self.style_provider.get_tool_status_style())

        # Single toggle button for content visibility - smaller and more subtle
        self.toggle_button = QPushButton("▼")  # Down triangle for collapsed
        self.toggle_button.setFlat(True)
        self.toggle_button.setStyleSheet(
            self.style_provider.get_tool_toggle_button_style()
        )
        self.toggle_button.clicked.connect(self.toggle_content_visibility)
        self.toggle_button.setFixedSize(16, 16)  # Reduced from 24x24

        # Add widgets to header
        header_layout.addWidget(tool_icon)
        header_layout.addWidget(tool_name_label)
        header_layout.addStretch(1)
        header_layout.addWidget(status_label)
        header_layout.addWidget(self.toggle_button)

        self.card_layout.addLayout(header_layout)

    def _create_content_section(self):
        """Create the single collapsible content section containing input and result"""
        # Container for all content (input + result) - more compact
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 2, 0, 0)  # Minimal margins
        self.content_layout.setSpacing(4)  # Reduced spacing

        # Add input section
        self._add_input_content()

        # Add result section if we have result data
        if self.result_data is not None:
            self._add_result_content()

        # Add to card layout
        self.card_layout.addWidget(self.content_container)

    def _add_input_content(self):
        """Add input parameters to the content section"""
        # Input title
        input_title = QLabel("Input Parameters:")
        input_title.setProperty("role", "title")
        input_title.setStyleSheet(self.style_provider.get_tool_content_style())
        self.content_layout.addWidget(input_title)

        # Format and display the tool input
        arg_key = "input" if "input" in self.tool_data else "arguments"
        try:
            # For dict input, show key-value pairs
            if isinstance(self.tool_data.get(arg_key, {}), dict):
                input_data = self.tool_data.get(arg_key, {})
                for key, value in input_data.items():
                    param_layout = QHBoxLayout()
                    key_label = QLabel(f"<b>{key}:</b>")
                    key_label.setProperty("role", "key")
                    key_label.setStyleSheet(
                        self.style_provider.get_tool_content_style()
                    )

                    # Format the value nicely
                    value_str = str(value)
                    if isinstance(value, dict) or isinstance(value, list):
                        value_str = json.dumps(value, indent=2)

                    value_label = QLabel(value_str)
                    value_label.setWordWrap(True)
                    value_label.setProperty("role", "value")
                    value_label.setStyleSheet(
                        self.style_provider.get_tool_content_style()
                    )

                    param_layout.addWidget(key_label)
                    param_layout.addWidget(value_label, 1)
                    self.content_layout.addLayout(param_layout)
            else:
                # For non-dict input, show as string
                input_text = QLabel(str(self.tool_data.get("input", "")))
                input_text.setWordWrap(True)
                input_text.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByMouse
                    | Qt.TextInteractionFlag.LinksAccessibleByMouse
                )
                input_text.setProperty("role", "value")
                input_text.setStyleSheet(self.style_provider.get_tool_content_style())
                self.content_layout.addWidget(input_text)

        except Exception as e:
            error_label = QLabel(f"Error displaying input: {str(e)}")
            error_label.setProperty("role", "error")
            error_label.setStyleSheet(self.style_provider.get_tool_content_style())
            self.content_layout.addWidget(error_label)

    def _add_result_content(self):
        """Add result content directly after input parameters"""
        # Add minimal spacing between input and result
        spacing_widget = QWidget()
        spacing_widget.setFixedHeight(4)  # Reduced from 8px
        self.content_layout.addWidget(spacing_widget)

        # Result title
        result_title = QLabel("Result:" if not self.is_error else "Error:")
        result_title.setProperty("role", "title")
        result_title.setProperty("status", "error" if self.is_error else "complete")
        result_title.setStyleSheet(self.style_provider.get_tool_content_style())
        self.content_layout.addWidget(result_title)

        # Format the result
        result_text = QLabel()
        result_text.setWordWrap(True)
        result_text.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )

        # Convert to string and render appropriately
        result_str = (
            str(self.result_data)[:2800] + "..." + str(self.result_data)[-200:]
            if len(str(self.result_data)) > 3000
            else str(self.result_data)
        )

        # Fallback to plain text if markdown rendering fails
        result_text.setTextFormat(Qt.TextFormat.PlainText)
        result_text.setText(result_str)

        result_text.setProperty("role", "error" if self.is_error else "value")
        result_text.setStyleSheet(self.style_provider.get_tool_content_style())
        self.content_layout.addWidget(result_text)

    def _create_progress_section(self):
        """Create a progress section for pending tool execution"""
        self.progress_container = QWidget()
        progress_layout = QVBoxLayout(self.progress_container)

        # Progress bar - more subtle height
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 0)  # Indeterminate progress
        progress_bar.setTextVisible(False)
        progress_bar.setFixedHeight(6)  # Reduced from 10px
        progress_bar.setStyleSheet(self.style_provider.get_tool_progress_style())

        progress_layout.addWidget(progress_bar)
        self.card_layout.addWidget(self.progress_container)

    def toggle_content_visibility(self):
        """Toggle the visibility of the entire content section (input + result)"""
        self.is_expanded = not self.is_expanded

        # Toggle visibility
        self.content_container.setVisible(self.is_expanded)

        # Update button text
        self.toggle_button.setText("▲" if self.is_expanded else "▼")

    def update_with_result(self, result_data: Any, is_error: bool = False):
        """Update the widget with tool result data"""
        self.result_data = result_data
        self.is_error = is_error

        # Update card style for new status
        self._apply_card_style()

        # Remove progress indicator if present
        if hasattr(self, "progress_container") and self.progress_container:
            self.card_layout.removeWidget(self.progress_container)
            self.progress_container.deleteLater()
            self.progress_container = None

        # Add result content to existing content section
        self._add_result_content()

        # Update header status
        self._update_header_status()

    def _update_header_status(self):
        """Update the header status indicator based on current state"""
        # Find and update the status label (which is the 2nd to last widget in header)
        header_layout = self.card_layout.itemAt(0).layout()
        for i in range(header_layout.count()):
            item = header_layout.itemAt(i)
            if not item:
                continue
            widget = item.widget()
            if isinstance(widget, QLabel) and widget.text() in [
                "⏳ Running",
                "✅ Complete",
                "❌ Error",
            ]:
                if self.is_error:
                    widget.setText("❌ Error")
                    widget.setProperty("status", "error")
                else:
                    widget.setText("✅ Complete")
                    widget.setProperty("status", "complete")
                widget.setStyleSheet(self.style_provider.get_tool_status_style())
                break
