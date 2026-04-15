class HubLikeDependency:
    def __init__(self, dep1, dep2, dep3):
        self.dep1 = dep1
        self.dep2 = dep2
        self.dep3 = dep3

def scattered_functionality1():
    pass

def scattered_functionality2():
    pass

def redundant_abstraction1():
    pass

def redundant_abstraction2():
    pass

class GodObject:
    def method1(self):
        pass

    def method2(self):
        pass

    def method3(self):
        pass

    def method4(self):
        pass

    def method5(self):
        pass

    def method6(self):
        pass

    def method7(self):
        pass

    def method8(self):
        pass

    def method9(self):
        pass

    def method10(self):
        pass

    def method11(self):
        pass

    def method12(self):
        pass

    def method13(self):
        pass

    def method14(self):
        pass

    def method15(self):
        pass

    def method16(self):
        pass

    def method17(self):
        pass

    def method18(self):
        pass

    def method19(self):
        pass

    def method20(self):
        pass

    def method21(self):
        pass

def improper_api_usage():
    for _ in range(10):
        print("API call")

class OrphanModule:
    pass

class CyclicDependencyA:
    def __init__(self, b):
        self.b = b

class CyclicDependencyB:
    def __init__(self, a):
        self.a = a

class UnstableDependency:
    def __init__(self, dep):
        self.dep = dep