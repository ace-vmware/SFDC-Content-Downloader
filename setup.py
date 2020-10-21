import cx_Freeze
from cx_Freeze import setup, Executable

setup(name="sfcd_app" ,
      version = "0.1" ,
      description = "" ,
      executables = [Executable("sfcd_app.py")])