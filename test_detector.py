from detect_globals import get_globals_of

def test1_nothing():
    assert get_globals_of(["tests/example1_empty.c"]) == []

def test2_simpletypes():
    assert get_globals_of(["tests/example2_simpletypes.c"]) == [
        ['int', 'i'],
        ['float', 'f'],
        ['double', 'd']
    ]

def test3_typedef():
    assert get_globals_of(["tests/example3_typedef.c"]) == [
        ['Foo', 'g_foo']
    ]
