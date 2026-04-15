class TemporaryField:
    def __init__(self):
        self.temp = None

    def method1(self):
        self.temp = 1

    def method2(self):
        return self.temp

class RefusedBequestParent:
    def method1(self):
        pass

    def method2(self):
        pass

    def method3(self):
        pass

class RefusedBequestChild(RefusedBequestParent):
    def method1(self):
        pass

class AlternativeClass1:
    def method1(self):
        pass

    def method2(self):
        pass

class AlternativeClass2:
    def methodA(self):
        pass

    def methodB(self):
        pass

class DivergentChange:
    def save_to_db(self):
        pass

    def save_to_file(self):
        pass

    def load_from_db(self):
        pass

    def load_from_file(self):
        pass

def shotgun_surgery():
    print("shotgun")
    print("surgery")
    print("example")
    print("code")
    print("here")

class FeatureEnvy:
    def __init__(self, other):
        self.other = other

    def envy(self):
        return self.other.method1() + self.other.method2() + self.other.method3()

class DataClass:
    def __init__(self):
        self.field1 = None
        self.field2 = None

    def get_field1(self):
        return self.field1

    def set_field1(self, value):
        self.field1 = value

    def get_field2(self):
        return self.field2

    def set_field2(self, value):
        self.field2 = value

class LazyClass:
    def method1(self):
        pass

class MiddleMan:
    def __init__(self, delegate):
        self.delegate = delegate

    def method1(self):
        return self.delegate.method1()

    def method2(self):
        return self.delegate.method2()