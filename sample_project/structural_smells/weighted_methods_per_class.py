class HighWMC:
    def complex_method1(self, x):
        if x > 0:
            if x < 10:
                return x * 2
            else:
                return x * 3
        else:
            return 0

    def complex_method2(self, y):
        for i in range(y):
            if i % 2 == 0:
                print(i)
            else:
                print(i * 2)

    # More complex methods...
    # The sum of cyclomatic complexities exceeds 10