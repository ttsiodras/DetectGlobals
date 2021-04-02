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

def test4_taste1():
    assert get_globals_of(["tests/example4_taste1.c"]) == [
        ['Foo', 'g_foo']
    ]

def test5_taste2():
    assert get_globals_of(["tests/example5_taste2.c"]) == [
        ['Foo', 'g_foo']
    ]

def test6_taste3():
    assert get_globals_of(["tests/example6_taste3.c"]) == [
        ['Foo', 'g_foo']
    ]

def test7_taste4():
    assert get_globals_of(["tests/example7_taste4.c"]) == [
        ['Foo', 'g_foo']
    ]
