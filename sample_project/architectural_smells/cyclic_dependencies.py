from module2 import Module2

class Module1:
    def __init__(self):
        self.module2 = Module2()

# module2.py
from module1 import Module1

class Module2:
    def __init__(self):
        self.module1 = Module1()