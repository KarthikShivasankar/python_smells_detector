class GrandParent:
    pass

class Parent(GrandParent):
    pass

class Child(Parent):
    pass

class GrandChild(Child):
    pass  # Depth of 4, exceeding the default threshold of 3