class DeepInheritance1:
    def method1(self):
        pass

class DeepInheritance2(DeepInheritance1):
    def method2(self):
        pass

class DeepInheritance3(DeepInheritance2):
    def method3(self):
        pass

class DeepInheritance4(DeepInheritance3):
    def method4(self):
        pass

class DeepInheritance5(DeepInheritance4):
    def method5(self):
        pass

class HighCoupling:
    def __init__(self, dep1, dep2, dep3, dep4, dep5):
        self.dep1 = dep1
        self.dep2 = dep2
        self.dep3 = dep3
        self.dep4 = dep4
        self.dep5 = dep5

    def use_dependencies(self):
        self.dep1.method1()
        self.dep2.method2()
        self.dep3.method3()
        self.dep4.method4()
        self.dep5.method5()

class LargeMethod:
    def large_method(self):
        for i in range(100):
            print(i)