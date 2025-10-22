from robertcommonbasic.basic.re.utils import format_name, find_match, contain_match, search_match, re
from robertcommonbasic.basic.dt.utils import parse_time


def test():
    name = 'Bldg3_Area1_hourly_SiteId_08-14-2021-23_00_00_PM_EDT.zip'
    time = format_name(name, r'[^0-9]+', '')
    tm = parse_time(time)
    print(tm)


def get_expression_points(expression: str, pattern: str = r'<%(.*?)%>') -> list:
    return find_match(expression, pattern)


log_content = f"""[2025-02-05 10:58:42] level: [ERROR] module: [syn_hggc_ctn.py] func: [loop_func] lineno: [146] msg: [CTN fail ((pymysql.err.IntegrityError) (1062, "Duplicate entry '2501010425' for key 'PRIMARY'")
[SQL:  Insert into T_CNTR (`CNTR_ID`, `CNTR_NO`, `CNTR_TYPE`, `CNTR_SIZE`, `CNTR_CLASS`, `CNTR_UN_NO`, `CNTR_DATE_IN`, `CNTR_DATE_OUT`, `CNTR_WEIGHT`, `CNTR_CARGO`, `CNTR_FE`, `CNTR_VESSEL`, `CNTR_VOY`, `ALARM`, `UPDATE_TIME`) Values ('2501010425', 'BMOU6368202', 'HC', '40', '3', 1993, '2025-01-23 08:51:20', '2025-01-24 09:40:24', 0.0, '桉叶油', 'F', 'UN9882205', '2413S', '0', '2025-02-05 10:58:24');]
(Background on this error at: https://sqlalche.me/e/14/gkpj))]"""

result = re.search(r'\[(?P<asctime>.*?)] level: \[(?P<level>.*?)] module: \[(?P<module>.*?)] func: \[(?P<func>.*?)] lineno: \[(?P<lineno>.*?)] msg: \[(?P<msg>.*)]', log_content)
print(result.groupdict())


#points = get_expression_points('if <%Bucket Brigade.Real4%> and <%Bucket@Brigade_Real5%>')
#points = get_expression_points('<%Bucket Brigade.Real4%>')
import re

value = '''$GNIMU,G,6,31995,1002,W,0,0,0,H,64713,60869,59410,R,359752,P,359577,Y,183482,Q,1969,3,1997,999,p,100518,h,6877,t,3856,*151
$GNGGA,,0000.0000000,N,00000.0000000,E,0,00,0.000,0.000,M,0.000,M,,*6D'''
vs = value.split('\n')
for v in value.split('\n'):
    if v.startswith('$GNIMU'):
        _v = v.split(',')
        if len(_v) >= 30:
            info = {
                        '加速度': {'X': int(_v[2]), 'Y': int(_v[3]), 'Z': int(_v[4])},
                '角速度': {'X': int(_v[6]), 'Y': int(_v[7]), 'Z': int(_v[8])},
                '磁场': {'X': int(_v[10]), 'Y': int(_v[11]), 'Z': int(_v[12])},
                '滚转角': int(_v[14]),
                '俯仰角': int(_v[16]),
                '偏航角': int(_v[18]),
                '四元数数据': {'Q0': int(_v[20]), 'Q1': int(_v[21]), 'Q2': int(_v[22]), 'Q3': int(_v[23])},
                '气压': int(_v[25]),
                '高度': int(_v[27]),
                '温度': int(_v[29]),
                    }
            print(info)


print(search_match(value, r'(?P<G1>.*?)'))

print(re.search('(?P<asctime>.*?)\((?P<lineno>.*?)\)', 'iot_base.py(101)').groupdict())
print(find_match(' power(W)', r'.*?\(.*?\)'))
print(re.sub(r'\(.*?[^)]\)', '', ' power(Wh)'))

print(re.sub(r'\([^)]\)', '', ' power'))
print(find_match(' power(W)', r'.*?\(.*?\)'))
print(find_match(' power', r'.*?\(.*?\)'))

#print(re.search(r'[(?P<asctime>.*?)] level: [(?P<level>.*?)] module: [(?P<module>.*?)] func: [(?P<func>.*?)] lineno: [(?P<lineno>.*?)] msg: [(?P<msg>.*)]', '[2023-11-02 14:33:16] level: [INFO ] module: [run.py] func: [init_license] lineno: [91] msg: [========== GateWayCore V1.0.31 20231030 ==========]'))
print(re.search(r'\[(?P<asctime>.*?)] level: \[(?P<level>.*?)] module: \[(?P<module>.*?)] func: \[(?P<func>.*?)] lineno: \[(?P<lineno>.*?)] msg: \[(?P<msg>.*)]', r'[2023-11-02 14:33:16] level: [INFO ] module: [run.py] func: [init_license] lineno: [91] msg: [========== GateWayCore V1.0.31 20231030 ==========]').groupdict())



print(contain_match('Keypad Medical Alarm Closing1, Area: {area}, Point: {param1}', r'Closing|Restor|Cancel'))
print(contain_match('Alarm, Area: {area}, Point: {param1}', r'.*?Alarm.*?Area.*?Point.*?'))
print(contain_match('    日期\t名称', r'[\u4e00-\u9fa5]'))
print(re.compile(r'[\u4e00-\u9fa5]').search('    日期\t名称'))
print(find_match('bit(v,1)', r'bit\(v,(.*?)\)'))

