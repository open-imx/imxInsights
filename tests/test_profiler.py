from imxInsights.utils.profiler import profile


@profile
def sample_function(x):
    """A simple function to test profiling"""
    total = 0
    for i in range(x):
        total += i
    return total


def test_profile_decorator(capfd):
    # we just need test coverage ....
    sample_function(1)
