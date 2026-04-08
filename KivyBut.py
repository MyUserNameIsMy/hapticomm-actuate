from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.button import Button


class HandMapApp(App):
    def build(self):
        layout = FloatLayout()

        # Add the hand image as the background
        hand_image = Image(source='image.jpg', allow_stretch=True, keep_ratio=False)
        layout.add_widget(hand_image)

        # Button positions (approximated for now)
        button_positions = {
            "T1": {"x": 0.12, "y": 0.15},
            "T2": {"x": 0.18, "y": 0.25},
            "FF1": {"x": 0.3, "y": 0.5},
            "FF2": {"x": 0.32, "y": 0.6},
            "FF3": {"x": 0.34, "y": 0.7},
            "MF1": {"x": 0.45, "y": 0.55},
            "MF2": {"x": 0.47, "y": 0.65},
            "MF3": {"x": 0.49, "y": 0.75},
            "RF1": {"x": 0.6, "y": 0.5},
            "RF2": {"x": 0.62, "y": 0.6},
            "P1": {"x": 0.68, "y": 0.2},
            "P2": {"x": 0.7, "y": 0.3},
            "Palm 11": {"x": 0.35, "y": 0.3},
            "Palm 12": {"x": 0.45, "y": 0.3},
            "Palm 13": {"x": 0.55, "y": 0.3},
            "Palm 21": {"x": 0.35, "y": 0.4},
            "Palm 22": {"x": 0.45, "y": 0.4},
            "Palm 23": {"x": 0.55, "y": 0.4},
            "Palm 31": {"x": 0.35, "y": 0.2},
            "Palm 32": {"x": 0.45, "y": 0.2},
        }

        # Create buttons for each label
        for label, pos in button_positions.items():
            button = Button(
                text=label,
                size_hint=(0.08, 0.08),  # Adjust size to better fit circles
                pos_hint={"x": pos["x"], "y": pos["y"]},
                background_color=(1, 1, 1, 1),  # White button
                color=(0, 0, 0, 1),  # Black text
                font_size='12sp',
            )
            button.bind(on_press=lambda instance, lbl=label: self.on_button_click(lbl))
            layout.add_widget(button)

        return layout

    def on_button_click(self, label):
        print(f"{label} clicked!")


# Run the app
if __name__ == "__main__":
    HandMapApp().run()
