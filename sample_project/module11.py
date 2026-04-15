class CyclicDependencyX:
    def __init__(self, y):
        self.y = y

class CyclicDependencyY:
    def __init__(self, x):
        self.x = x

class UnstableDependencyClass:
    def __init__(self, dep):
        self.dep = dep

    def use_dependency(self):
        return self.dep.method()