import alternative


@alternative.reference
def f():
    return 1


@f.add
def alt1():
    return 1


@f.add
def alt2():
    return 1


@f.pytest_parametrize_pairs
def test_f(reference, implementation):
    # FIXME: check the use of parameters is correct + decorator use
    assert reference() == implementation()
