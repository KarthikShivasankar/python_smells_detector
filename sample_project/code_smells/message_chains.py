class A:
    def b(self):
        return B()

class B:
    def c(self):
        return C()

class C:
    def d(self):
        return "result"

a = A()
result = a.b().c().d()