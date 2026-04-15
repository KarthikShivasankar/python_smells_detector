class HighResponseForClass:
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    
    def complex_method(self):
        self.method1()
        self.method2()
        self.method3()
        self.method4()
        external_obj1.method5()
        external_obj2.method6()
        external_obj3.method7()
        # RFC exceeds 10 (4 own methods + 7 external method calls)