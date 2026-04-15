class LowCohesion:
    def __init__(self):
        self.a = 1
        self.b = 2
        self.c = 3

    def method1(self):
        return self.a

    def method2(self):
        return self.b

    def method3(self):
        return self.c

    def method4(self):
        return self.a + self.b

    def method5(self):
        return self.b + self.c

    def unrelated_method(self):
        print("This method doesn't use any instance variables")
    
    # Low cohesion due to methods not sharing instance variables