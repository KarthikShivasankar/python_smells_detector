class Hub:
    def __init__(self):
        self.dependency1 = Dependency1()
        self.dependency2 = Dependency2()
        self.dependency3 = Dependency3()

class Dependency1: pass
class Dependency2: pass
class Dependency3: pass