"""Parrot animation screen - displays dancing ASCII parrot"""

import math
from textual.app import ComposeResult
from textual.containers import Center, Middle
from textual.screen import Screen
from textual.widgets import Static
from textual.reactive import reactive


class ParrotScreen(Screen):
    """Screen that displays an animated dancing parrot"""

    BINDINGS = [
        ("escape", "dismiss", "Back"),
        ("q", "dismiss", "Back"),
    ]

    angle = reactive(0.0)

    def generate_spinner(self, angle: float) -> str:
        """Generate a spinning pattern programmatically"""
        center_x, center_y = 15, 6  # Center position
        width, height = 30, 13

        # Create a canvas
        canvas = [[' ' for _ in range(width)] for _ in range(height)]

        # Place center star
        canvas[center_y][center_x] = '*'

        # Draw 8 spokes radiating from center
        num_spokes = 8
        for i in range(num_spokes):
            spoke_angle = angle + (i * math.pi * 2 / num_spokes)

            # Draw spoke at different radii
            for radius in [1, 2, 3, 4, 5]:
                dx = radius * math.cos(spoke_angle)
                dy = radius * math.sin(spoke_angle) / 2  # Divide by 2 for terminal aspect ratio

                x = center_x + int(dx)
                y = center_y + int(dy)

                if 0 <= y < height and 0 <= x < width:
                    # Choose character based on direction
                    abs_angle = abs(spoke_angle % (math.pi * 2))
                    if radius == 1:
                        # Inner ring uses line characters
                        if abs_angle < math.pi / 8 or abs_angle > 15 * math.pi / 8:
                            char = '-'
                        elif abs_angle < 3 * math.pi / 8:
                            char = '/'
                        elif abs_angle < 5 * math.pi / 8:
                            char = '|'
                        elif abs_angle < 7 * math.pi / 8:
                            char = '\\'
                        elif abs_angle < 9 * math.pi / 8:
                            char = '-'
                        elif abs_angle < 11 * math.pi / 8:
                            char = '/'
                        elif abs_angle < 13 * math.pi / 8:
                            char = '|'
                        else:
                            char = '\\'
                    elif radius <= 3:
                        char = ':' if i % 2 == 0 else '.'
                    else:
                        char = '.'

                    if canvas[y][x] == ' ':
                        canvas[y][x] = char

        # Convert canvas to string
        return '\n' + '\n'.join(''.join(row) for row in canvas) + '\n'

    def compose(self) -> ComposeResult:
        """Layout for spinning animation"""
        with Middle():
            with Center():
                yield Static(self.generate_spinner(0), id="spinner")
                yield Static("✨ SPINNING STAR ✨", id="title")

    async def on_mount(self) -> None:
        """Start the animation"""
        self.set_interval(0.05, self.update_angle)

    def update_angle(self) -> None:
        """Update the rotation angle"""
        self.angle = (self.angle + math.pi / 16) % (math.pi * 2)

    def watch_angle(self, new_angle: float) -> None:
        """Update the displayed spinner when angle changes"""
        spinner_widget = self.query_one("#spinner", Static)
        spinner_widget.update(self.generate_spinner(new_angle))

    def action_dismiss(self) -> None:
        """Return to the previous screen"""
        self.app.pop_screen()
