
import requests


host = "https://api.hbdm.com/swap-ex/market/history/kline?contract_code=ZEC-USD&period=1min&from=1603610760&to=1603670760"


_HOST = "https://api.hbdm.com/swap-ex/market/history/kline"

params = {'symbol': 'ZEC-USD', 'period': '1min', 'from': 1603610760, 'to': 1603670760}
requests = requests.request(
    method="GET",
    url=host,
    # params=params

)


print(requests.json()["data"])