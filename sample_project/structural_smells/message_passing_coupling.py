class HighMPC:
    def __init__(self):
        self.obj1 = SomeClass1()
        self.obj2 = SomeClass2()
        self.obj3 = SomeClass3()

    def method(self):
        self.obj1.method1()
        self.obj1.method2()
        self.obj2.method1()
        self.obj2.method2()
        self.obj3.method1()
        self.obj3.method2()
        self.obj3.method3()
        self.obj3.method4()
        # ... more method calls
        # Total method calls to other classes exceeds 10