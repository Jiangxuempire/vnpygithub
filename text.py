import numpy as np

data = np.arange(20)

def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)

a = rolling_window(data,10)
print(a)
exit()



np.mean(rolling_window(data,10))


np.mean(rolling_window(data,10),-1)
