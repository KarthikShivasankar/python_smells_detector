class TemporaryField:
    def __init__(self):
        self.temp = None

    def method1(self):
        self.temp = 1
        return self.temp

    def method2(self):
        return 2