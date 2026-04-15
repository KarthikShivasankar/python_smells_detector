class HighCouplingClass:
    def __init__(self, dep1, dep2, dep3, dep4, dep5, dep6, dep7, dep8, dep9, dep10):
        self.dep1 = dep1
        self.dep2 = dep2
        self.dep3 = dep3
        self.dep4 = dep4
        self.dep5 = dep5
        self.dep6 = dep6
        self.dep7 = dep7
        self.dep8 = dep8
        self.dep9 = dep9
        self.dep10 = dep10

    def use_dependencies(self):
        self.dep1.method1()
        self.dep2.method2()
        self.dep3.method3()
        self.dep4.method4()
        self.dep5.method5()
        self.dep6.method6()
        self.dep7.method7()
        self.dep8.method8()
        self.dep9.method9()
        self.dep10.method10()

class HighFanIn:
    def __init__(self):
        self.value = 0

    def increment(self):
        self.value += 1

    def decrement(self):
        self.value -= 1

    def multiply(self, factor):
        self.value *= factor

    def divide(self, divisor):
        self.value /= divisor

    def reset(self):
        self.value = 0