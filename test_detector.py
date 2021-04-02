from detect_globals import get_globals_of

def test1_nothing():
    assert get_globals_of(["tests/example1_empty.c"]) == []

def test2_simpletypes():
    assert get_globals_of(["tests/example2_simpletypes.c"]) == [
        ['i', 'int'],
        ['f', 'float'],
        ['d', 'double']
    ]

def test3_typedef():
    assert get_globals_of(["tests/example3_typedef.c"]) == [
        ['g_foo', 'Foo']
    ]

def test4_taste1():
    res = get_globals_of(["tests/example4_taste1.c"])
    assert res == [
        ['g1', 'FILE *'], ['g2', 'FILE *'], ['g3', 'FILE *'],
        ['g_count', 'int'], ['g_brave_fpga', 'int']]

def test5_taste2():
    res = get_globals_of(["tests/example5_taste2.c"])
    assert res == [
        ['ads', 'FILE *'], ['adb', 'FILE *'], ['async_ads', 'FILE *'],
        ['async_adb', 'FILE *'], ['contains_sync_interface', 'int']]

def test6_taste3():
    res = get_globals_of(["tests/example6_taste3.c"])
    assert res == [
        ['adb', 'FILE *'], ['ads', 'FILE *']]

def test7_taste4():
    res = get_globals_of(["tests/example7_taste4.c"])
    assert res == [
        ['thread', 'FILE *'], ['process', 'FILE *'],
        ['nodes', 'FILE *'], ['period', 'long long'],
        ['cyclic_name', 'char *'], ['op_kind', 'int'],
        ['first_interface', 'int'],
        ['system_root_node', 'char *'],
        ['features_declared', 'int'],
        ['system_connections_declared', 'unsigned int']]
