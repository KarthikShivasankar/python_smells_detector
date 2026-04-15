class ComplexClass:
    def __init__(self):
        self.value = 0

    def complex_method(self):
        for i in range(10):
            if i % 2 == 0:
                self.value += i
            else:
                self.value -= i

    def another_complex_method(self):
        for i in range(5):
            if i % 2 == 0:
                self.value *= i
            else:
                self.value /= (i + 1)

class InconsistentNaming:
    def __init__(self):
        self.value = 0

    def add_value(self, val):
        self.value += val

    def subtractValue(self, val):
        self.value -= val

    def multiply_value(self, val):
        self.value *= val

    def divideValue(self, val):
        self.value /= val

def long_chain_of_calls():
    return (ComplexClass()
            .complex_method()
            .another_complex_method()
            .complex_method()
            .another_complex_method())

class UnusedClass:
    def unused_method(self):
        pass