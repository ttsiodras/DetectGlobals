from detect_globals import get_globals_of

def test1_nothing():
    assert get_globals_of(["tests/example1_empty.c"]) == []

def test2_simpletypes():
    assert get_globals_of(["tests/example2_simpletypes.c"]) == [
        ['global', 'i', 'int'],
        ['global', 'f', 'float'],
        ['global', 'd', 'double']
    ]

def test3_typedef():
    assert get_globals_of(["tests/example3_typedef.c"]) == [
        ['global', 'g_foo', 'Foo']
    ]

def test4_taste1():
    res = get_globals_of(["tests/example4_taste1.c"])
    assert res == [
        ['global', 'g1', 'FILE *'],
        ['global', 'g2', 'FILE *'],
        ['global', 'g3', 'FILE *'],
        ['global', 'g_count', 'int'],
        ['global', 'g_brave_fpga', 'int'],
        ['static', 's_someStatic', 'int']]

def test5_taste2():
    res = get_globals_of(["tests/example5_taste2.c"])
    assert res == [
        ['global', 'ads', 'FILE *'],
        ['global', 'adb', 'FILE *'],
        ['global', 'async_ads', 'FILE *'],
        ['global', 'async_adb', 'FILE *'],
        ['global', 'contains_sync_interface', 'int']]

def test6_taste3():
    res = get_globals_of(["tests/example6_taste3.c"])
    assert res == [
        ['global', 'adb', 'FILE *'],
        ['global', 'ads', 'FILE *']]

def test7_taste4():
    res = get_globals_of(["tests/example7_taste4.c"])
    assert res == [
        ['global', 'thread', 'FILE *'],
        ['global', 'process', 'FILE *'],
        ['global', 'nodes', 'FILE *'],
        ['global', 'period', 'long long'],
        ['global', 'cyclic_name', 'char *'],
        ['global', 'op_kind', 'int'],
        ['global', 'first_interface', 'int'],
        ['global', 'system_root_node', 'char *'],
        ['global', 'features_declared', 'int'],
        ['global', 'system_connections_declared', 'unsigned int']]
