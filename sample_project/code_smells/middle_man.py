class MiddleMan:
    def __init__(self, delegate):
        self.delegate = delegate

    def method1(self):
        return self.delegate.method1()

    def method2(self):
        return self.delegate.method2()