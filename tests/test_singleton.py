from imxInsights.utils.singleton import SingletonMeta


class SingletonTestClass(metaclass=SingletonMeta):
    def __init__(self, value):
        self.value = value


def test_singleton_instance():
    instance1 = SingletonTestClass(10)
    instance2 = SingletonTestClass(20)

    assert instance1 is instance2, "Singleton instances are not the same"


def test_singleton_value_persistence():
    instance1 = SingletonTestClass(30)
    assert instance1.value == 30, "Singleton instance value did not persist correctly"

    # should not update.
    instance2 = SingletonTestClass(40)
    assert instance2.value == 40, "Singleton instance value did not update correctly"

    assert instance1 is instance2, "Singleton instances are not the same"
    assert instance1.value == 40, "Singleton instance value did not update correctly"
    assert instance2.value == 40, "Singleton instance value did not update correctly"


def test_singleton_different_classes():
    class AnotherSingletonClass(metaclass=SingletonMeta):
        def __init__(self, value):
            self.value = value

    instance1 = SingletonTestClass(50)
    instance2 = AnotherSingletonClass(60)

    assert (
        instance1 is not instance2
    ), "Different singleton classes share the same instance"
    assert instance1.value == 50, "Singleton instance value did not persist correctly"
    assert (
        instance2.value == 60
    ), "Another singleton instance value did not persist correctly"
