import decimal

d = decimal.Decimal(3)
a = decimal.Decimal(3.1415926)

print(d)  # 3
print(a)  # 3.14159260000000006840537025709636509418487548828125
print(d + a + a)  # 9.283185200000000136810740514

# 设置全局精度
decimal.getcontext().prec = 2
d = decimal.Decimal(3)
a = decimal.Decimal('3.1415926')
print(d)  # 3
print(a)  # 3.1415926
print(d + a + a)  # 9.28

