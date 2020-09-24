
min_volume = 10.0
current_volume = 958.234158

len_tick_decimal = len(str(min_volume).split(".")[1])
current_volume = float(format(current_volume, f".{len_tick_decimal}f"))

print(current_volume)
