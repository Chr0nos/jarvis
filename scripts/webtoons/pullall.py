# from credentials import credentials
from toomics import pullall as toomics_pullall
from webtoons import pullall as webtoons_pullall
import mongomodel
import asyncio


async def main():
    mongomodel.database.connect(host='192.168.1.12')
#    toomics_pullall(**credentials['toomics'])
    print('Connected to mongodb')
    await webtoons_pullall()



if __name__ == "__main__":
    asyncio.run(main())
