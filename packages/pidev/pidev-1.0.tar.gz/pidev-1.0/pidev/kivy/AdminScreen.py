import os
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

ADMIN_SCREEN_NAME  = "admin"
MAIN_SCREEN_NAME = "main"

class AdminScreen(Screen):
    """
    Class to handle the AdminScreen and its functionality
    """

    def __init__(self, **kwargs):
        """
        Load the AdminScreen.kv file. Set the necessary names of the screens for the PassCodeScreen to transition to.
        Lastly super Screen's __init__
        :param kwargs: Normal kivy.uix.screenmanager.Screen attributes
        """
        admin_screen_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "", "AdminScreen.kv")
        Builder.load_file(admin_screen_path)

        super(AdminScreen, self).__init__(**kwargs)

    def transition_back(self):
        """
        Transition back to the main screen
        :return: None
        """
        self.parent.current = MAIN_SCREEN_NAME

    def set_main_screen_name(self, main_screen_name):
        """
        Set the main screen name
        :param main_screen_name: Main screen name
        :return: None
        """
        global MAIN_SCREEN_NAME
        MAIN_SCREEN_NAME = main_screen_name

    @staticmethod
    def shutdown():
        """
        Shutdown the system. This should free all steppers and do any cleanup necessary
        :return: None
        """
        os.system("sudo shutdown now")

    @staticmethod
    def exit_program():
        """
        Quit the program. This should free all steppers and do any cleanup necessary
        :return: None
        """
        quit()
