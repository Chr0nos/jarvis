from credentials import credentials
from toomics import pullall as toomics_pullall
from webtoons import pullall as webtoons_pullall
import mongomodel


if __name__ == "__main__":
#    toomics_pullall(**credentials['toomics'])
    mongomodel.database.connect(host='192.168.1.12')
    print('Connected to mongodb')
    webtoons_pullall()
