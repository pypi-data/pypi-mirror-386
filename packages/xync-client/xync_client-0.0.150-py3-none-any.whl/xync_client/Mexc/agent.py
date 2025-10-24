from asyncio import run
from uuid import uuid4

from pyro_client.client.file import FileClient
from xync_bot import XyncBot
from xync_client.Bybit.etype.order import TakeAdReq

from xync_client.loader import PAY_TOKEN, NET_TOKEN
from xync_schema import models
from xync_schema.enums import UserStatus

from xync_client.Abc.Agent import BaseAgentClient


class AgentClient(BaseAgentClient):
    i: int = 0
    headers = {
        "accept-language": "ru,en;q=0.9",
        "language:": "ru-RU",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    }

    async def _take_ad(self, req: TakeAdReq):
        self.i = 33 if self.i > 9998 else self.i + 2
        hdrs = self.headers | {"trochilus-trace-id": f"{uuid4()}-{self.i:04d}"}
        auth = {
            "p0": "hzE/loX7MBr0j8vnx7n5qY72DCChDHOiNG/ZAXbc0BrKIiwLc7cqg0vDdK15x/qArCO1xCX2jNqmtGO0aUxa0yrspnh2xX8tJnZ1oDbvkqPjcJuKdnvehVL2rMHVXOtC0ImfcZ++zfmIXrNFchhC+u2O9LqyjiHw8F5XNtdkMVWzcgs2tNAZmZiyliHDQso3WslCuRyp0iAogxT99DdP2A5bNoqOFvcurk0+/mMFskoeGwykq7OBVAGKhHwr4jbFFURGE5DYN1tKHUtIYkDaul5b+wpLn83IEYSEhwwxfSE+cy3VvKE7xPiAOf/ptmZa9s0FyALNb8jCeTLwa8Wh4stO0qM/flL0oOHXXA+dxiQtQIDOdFqOIKoDhPrZ9nnqq0V/UyhACk4Omf7dc9ElVtbNuX4Q/bgZefAE674y+IXvBHl9ss36kVOImui2xpT0lH+sc35pR8xht5SndOTz6+oiHLIr+z850DYSVpj06i343sSjTfQxNj1bKATpRTXgOVwPTUO67hMFSFFpNLQ7Mxl5IeKEXI7dZjud1qlxIVSPJAYe6m3vomY6jm4U50C11Nh9CXC9p9TcD0e7QPfchzoSiFjzkwCxfOjAsxWzKkSpSnoaQTHO58c6RieHszMsahazVqCQ9rtLJV4kJ65lKLPegKrBY/yI4gXQs0NdvtdFjdGd5EBTC1inr3g7PeSvNZc9PzN5y/x0oC5r2KGBY4CdxqWxzAnr7Tvnl2sL8MPZ6WDcizCnK6aegfl0Kk976MOlC221ZfPutfYTuyB4d1utADE82g2X63idNtF/h6iUl9bIsAKisoNzgUz26MCzkG/K++Cm/0/Sip40znh4lmT0z6XNhA4GiXmjbkxrhUsI4M8HiVRjuNWvrdq7D2l81j5K+JYHFWOaAUQuDNx+bB4eB9KJnHX03hxkJYfhYQtxr+X1LAPITWWfb+qmFy8x4+mWP1TVTBl27j7FAqWXnCL8FeJQ4sSP7Xphj3t7Fd62RtQewiq5L/BYegJGD3c9NvQBvC2gOXMuhTIE9RcQAUdXDsKKizZ4mXpXTvcGYXwednrVwz1SaLe8WhEe54e6tSLRf5Or3pce/7epsDqrKQXDeKugo6so//SN8y7wPsd8xpGeBtUjhvrESwNcRp305pYm4f+2A4lF71a92P6PHSOQm5ruGT7qB+9uwvzXIoFY985dI8aRq7g7GbAyQ1z7LhhjJzS11xUEpekunxdAxySl6OOFcAlTjnx8FgGBl2xiP+KtTJeSVB4b07OsqoUmAS54I0Sj19Tm8WQz+FKbKZ0eReApT+gyyqFJBSRcJYIyA3dLL/fYSNfNmNUu76KGR+o3xMHTSb8V/kVHmgWs6qmE98NE1BcXWnABiHVkqZU0lU/R0b9jhuUaYXB0md0VjyY61MztgfEk6VQnWfPQT/POuic6lBf4UJ3IWolsGttYlLo9sa9mAUqLXuDeSo+mTs7nDECVyYGZK/E+BCG+eEnhmwKB8dvY500kE/0Megf4i4Ymi0GG0jjy3z8VLsjP2cnUGrQHfe8d/etqgPN0CFI7crxEFoAeo8fl9VfEyr+ug61MWt+jcFtU2wfK66A75iPHobQpZVxW1tOv72PhiKTDWjgsLifJlYmFG1Eoadq8kiSEgkldsSCEYPTSjj4anXGSVBicRiaNliyQTuDT8DOjKmv3jGgu7opv/wKQ8Lz1FZDwL6i9WJExFzebdgJn+RNRZjpjWWKH0A9c0ZTd0Xa9q9WZyxEe8bycEkf4e4jnoalL4w==",
            "k0": "Dt/l/MGcXIAOoCeR1L1VW5vTgqRcc4qqXzXrb6O+/a/2c9pHywRAVhPZZm46Us91VyNi2zg3S6Dzpe3FiwnC/NC1zwFAfKLIcKYgnDxTHesv5jUEYghDFlDsZFzCeY6b0TJ6ZlNr7+/NOQ4Hx1gbCsOlO0BrcMJ+DlqJlR7KM0od2SBWmbmJO1Dh25H/PzKnPhzq4NDuzHGcsDMrlkqmsKFHvkF01IiPVOCMFMdOWfCy3O4HGsSu3r9b/JvhxsC8hdfOZg1JKKDtKOGaHo8Fmajqozp39akG8EKk4C27hf2qDT2zh0LLrb3ZL0Gnd0y33LJTvUbYBSfFK1b7xv0i0A==",
            "chash": "ccef0ebde038ce0e7cb086851c51781c498a429be65ab70bf4f46671c637516e",
            "mtoken": "9482d04a3235e3090e954d3b6a8871e1",
            "mhash": "06cabb6939e0262495aa5d55e44dfc27",
        }
        data = {
            "scene": "TRADE_BUY",
            "quantity": req.quantity,
            "amount": req.amount,
            "orderId": req.ad_id,
            "authVersion": "v2",
            "deviceId": auth["mtoken"],
        }
        res = await self._post("/api/verify/second_auth/risk/scene", json=data, hdrs=hdrs)
        data = {
            "amount": req.amount,
            "authVersion": "v2",
            "orderId": req.ad_id,
            "price": req.price,
            "ts": int(1761155700.8372989 * 1000),
            "userConfirmPaymentId" if req.is_sell else "userConfirmPayMethodId": req.pm_id,
        }
        self.i = 33 if self.i > 9999 else self.i + 1
        hdrs = self.headers | {"trochilus-trace-id": f"{uuid4()}-{self.i:04d}"}
        res = await self._post("/api/order/deal?mhash=" + auth["mhash"], data=auth | data, hdrs=hdrs)
        return res["data"]


async def main():
    from x_model import init_db
    from xync_client.loader import TORM

    cn = await init_db(TORM, True)

    agent = (
        await models.Agent.filter(
            actor__ex_id=12,
            active=True,
            auth__isnull=False,
            actor__person__user__status=UserStatus.ACTIVE,
            actor__person__user__pm_agents__isnull=False,
        )
        .prefetch_related("actor__ex", "actor__person__user__gmail")
        .first()
    )

    bbot = XyncBot(PAY_TOKEN, cn)
    fbot = FileClient(NET_TOKEN)

    cl = agent.client(fbot, bbot)
    req = TakeAdReq(ad_id="a1574088909645125632", amount=500, pm_id=366, cur_="RUB", price=85.8, is_sell=True)
    res = await cl.take_ad(req)
    print(res)


if __name__ == "__main__":
    run(main())
