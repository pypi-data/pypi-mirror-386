import os
from kivy.lang import Builder
from kivy.properties import ObjectProperty, ColorProperty
from kivy.uix.button import Button
from kivy.core.window import Window

dpea_button_kv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "", "DPEAButton.kv")
Builder.load_file(dpea_button_kv_path)

class DPEAButton(Button):
    current_button_id = 0 # static variable to keep track of all buttons
    button_id = 0 # the individual button id
    type = "DPEAButton"
    # The thickness and radii are in pixels
    border_thickness = ObjectProperty(5)
    border_radius = ObjectProperty(10)
    fill_radius = ObjectProperty(10)
    # text_color is a clearer name for the text's color property. Using 'color: rgba' to change the color of the text still works, however text_color takes precedent
    text_color = ColorProperty([0, 0, 0, 1])
    border_color = ColorProperty([0, 0, 0, 1])
    fill_color = ColorProperty([1, 1, 1, 1])
    # determines what color to change the fill_color to when hovered over
    hover_color = ColorProperty([0.875, 0.875, 0.875, 1.0])
    # controls whether the hover_color is multiplied or just set
    multiply_hover_color = True
    # can be set to True to add mouseover capabilities
    mouseover_activated = False

    # Read only variables:
    # hovered_over tells whether the button is currently being hovered over or not
    hovered_over = False
    # Shouldn't be set, the mouseover methods will handle it
    original_color = (0.0, 0.0, 0.0, 0.0)
    # already_hovered handles the one time variable setting
    already_hovered = False


    def __init__(self, **kwargs):
        """
        Constructor for the DPEAButton
        :param kwargs: Arguments supplied to super
        """
        super(DPEAButton, self).__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouseover)
        # handles the button_id, each button will have a unique number
        self.button_id = DPEAButton.current_button_id
        DPEAButton.current_button_id += 1

    # appends the button_id to the end of what self returns to allow for a complete individual reference to each button (the base self return is based off of position, meaning that two buttons could be mixed up)
    def __repr__(self):
        return super(DPEAButton, self).__repr__() + str(self.button_id)

    # multiplies the two colors together by their individual rgba values
    def multiply_colors(self, color1, color2):
        return (color1[0] * color2[0], color1[1] * color2[1], color1[2] * color2[2], color1[3] * color2[3])

    # runs on everytime mouse is with in the window
    def on_mouseover(self, window, pos):
        if not self.mouseover_activated:
            return
        if not self.already_hovered:
            self.already_hovered = True
            self.original_color = self.fill_color
        # runs when the button is being hovered over
        # it runs once, as soon as the cursor is OVER the button
        if not self.hovered_over and self.collide_point(*pos):
            self.hovered_over = True
            # multiplies the color (or just sets the color) to hover_color
            if self.multiply_hover_color:
                self.fill_color = self.multiply_colors(self.hover_color, self.fill_color)
            else:
                self.fill_color = self.hover_color
        # runs when not hovering over the button
        # it runs once, as soon as the cursor is OFF the button
        elif not self.collide_point(*pos) and self.hovered_over:
            self.hovered_over = False
            self.fill_color = self.original_color
