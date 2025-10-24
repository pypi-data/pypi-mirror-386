from setuptools import setup, Command
from distutils.command.clean import clean
import shutil
import glob
import os

class clean_pycache(Command):
    """Command to remove all '__pycache__' directories.
    """
    
    # This command has no user options.
    user_options = []
    
    def run(self):
        # All "__pycache__" directories under ".".
        list_of_directories = glob.glob("**/__pycache__", recursive=True)
        for directory in list_of_directories:
            shutil.rmtree(directory)
    
    def initialize_options(self):
        pass
    
    def finalize_options(self):
        pass

class custom_clean_command(clean):
    """Custom 'clean' command.
    
    This version of the 'clean' command also removes the following directories: "./build", "./dist", "./medtext.egg-info", "./src/build", "./src/dist" and "./src/medtext.egg-info".
    """
    
    def run(self):
        super().run()
        self.run_command("clean_pycache")
        if os.path.isdir("build"):
            shutil.rmtree("build")
        if os.path.isdir("dist"):
            shutil.rmtree("dist")
        if os.path.isdir("medtext.egg-info"):
            shutil.rmtree("medtext.egg-info")
        if os.path.isdir("src/build"):
            shutil.rmtree("src/build")
        if os.path.isdir("src/dist"):
            shutil.rmtree("src/dist")
        if os.path.isdir("src/medtext.egg-info"):
            shutil.rmtree("src/medtext.egg-info")

if __name__ == "__main__":
    # Setup function.
    setup(
        cmdclass = {
            "clean_pycache" : clean_pycache,
            "clean" : custom_clean_command
        },
    )