
from robertcommonbasic.basic.data.conversion import convert_value, convert_bytes_to_values, convert_values_to_bytes, TypeFormat, DataFormat, reverse_bytes, get_bool, set_bool


def format_bytes(data: bytes) -> str:
    return ''.join(["%02X" % x for x in data]).strip()


def test_long_ver():
    values = [52501, 1883]       # CDAB
    bytes = convert_values_to_bytes(values, TypeFormat.UINT16)
    print(format_bytes(bytes))
    #bytes = reverse_bytes(bytes, len(bytes), 0, DataFormat.ABCD)
    print(reverse_bytes(bytes, len(bytes), 0, DataFormat.BADC))
    bytes = reverse_bytes(bytes, len(bytes), 0, DataFormat.ABCD)
    print(format_bytes(bytes))
    v = convert_bytes_to_values(bytes, TypeFormat.INT32, 0)
    print(v)


def test_bool():
    value = 0
    print(get_bool(value, 0))
    value = set_bool(value, 1, 1)
    print(value)
    print(get_bool(value, 0))
    print(get_bool(value, 1))


def test_convert():
    print(convert_value(1067282596, TypeFormat.INT64, TypeFormat.FLOAT, DataFormat.ABCD))


def test_float():
    print(convert_bytes_to_values(bytes.fromhex('23 E5 5E 41'), TypeFormat.FLOAT, 0))


def test_int():
    print(convert_bytes_to_values(bytes.fromhex('02 1B'), TypeFormat.INT16, 0))
    print(convert_bytes_to_values(bytes.fromhex('42 FF'), TypeFormat.INT16, 0))


def test_ints():
    datas = bytes.fromhex('16 16 87 FF 42 FA 12 FA 12 FF E5 FF 28 FF 26 02 87 01 21 00 90 00 5F 02 FE 00 00 00 00 00 75 FE 2F FE 2F FE 2F 0E D1 02 49 03 59 02 F2 FF 43 FF E3 FE 2F 01 D4 00 80 00 00 18 0B 11 00 00 00 00 22 01 48 04 02 07 00 05 00 00 00 00 00 05 01 01 00 18 00 00 00 00 00 FF E4 FF 24 FF 23 FF 4C FF 4C 00 4B 03 00 00 01 52 00 64 FF FC 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 E5 8B')
    for i in range(len(datas)):
        d = reverse_bytes(datas[i: i+2], 2, format=DataFormat.DCBA)
        print(f"{i} {convert_bytes_to_values(datas[i: i+2], TypeFormat.INT16, 0)} {convert_bytes_to_values(d, TypeFormat.INT16, 0)}")


def test_floats():
    datas = bytes.fromhex('1B 02 64 00 FE 7F 6A 00 70 00 70 01 93 02 FF 7F DE 00 FE 7F FE 7F FE 7F FE 7F FE 7F FE 7F D3 00')
    for i in range(len(datas)):
        d = reverse_bytes(datas[i: i+4], 4, format=DataFormat.DCBA)
        print(f"{i} {convert_bytes_to_values(datas[i: i+4], TypeFormat.FLOAT, 0)} {convert_bytes_to_values(d, TypeFormat.FLOAT, 0)}")


def test_tk():
    datas = bytes.fromhex('1B 02 64 00 FE 7F 6A 00 70 00 73 01 94 02 FF')
    for i in range(len(datas)):
        print(f"temp_set: {-99.8 + (datas[i+1] % 8) * 25.5 + datas[i+2]* 0.1}")


test_ints()
