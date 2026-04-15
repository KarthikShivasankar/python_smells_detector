class FeatureEnvy:
    def __init__(self, other):
        self.other = other

    def method(self):
        return self.other.get_value() + self.other.get_value()