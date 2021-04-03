from detect_globals import get_globals_of

def common(source, results):
    for res1, res2 in zip(results, get_globals_of([source])):
        # Verify, for each result:
        #
        # - whethere it is global/static
        # - name of variable
        # - type of variable (global/static)
        assert res1 == res2[:3]
        # - ...and the reported filename
        assert res2[3].endswith(source)

def test1_nothing():
    assert get_globals_of(["tests/example1_empty.c"]) == []

def test2_simpletypes():
    source = "tests/example2_simpletypes.c"
    results = [
        ['global', 'i', 'int'],
        ['global', 'f', 'float'],
        ['global', 'd', 'double']
    ]
    common(source, results)

def test3_typedef():
    source = "tests/example3_typedef.c"
    results = [
        ['global', 'g_foo', 'Foo']
    ]
    common(source, results)

def test4_taste1():
    source = "tests/example4_taste1.c"
    results = [
        ['global', 'g1', 'FILE *'],
        ['global', 'g2', 'FILE *'],
        ['global', 'g3', 'FILE *'],
        ['global', 'g_count', 'int'],
        ['global', 'g_brave_fpga', 'int'],
        ['static', 's_someStatic', 'int']]
    common(source, results)

def test5_taste2():
    source = "tests/example5_taste2.c"
    results = [
        ['global', 'ads', 'FILE *'],
        ['global', 'adb', 'FILE *'],
        ['global', 'async_ads', 'FILE *'],
        ['global', 'async_adb', 'FILE *'],
        ['global', 'contains_sync_interface', 'int']]
    common(source, results)

def test6_taste3():
    source = "tests/example6_taste3.c"
    results = [
        ['global', 'adb', 'FILE *'],
        ['global', 'ads', 'FILE *']]
    common(source, results)

def test7_taste4():
    source = "tests/example7_taste4.c"
    results = [
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
    common(source, results)
