from module1 import Class1
from module2 import Class2
from module3 import Class3
from module4 import Class4
from module5 import Class5
from module6 import Class6

class HighCoupling:
    def __init__(self):
        self.obj1 = Class1()
        self.obj2 = Class2()
        self.obj3 = Class3()
        self.obj4 = Class4()
        self.obj5 = Class5()
        self.obj6 = Class6()  # Coupled to 6 classes, exceeding the default threshold of 5