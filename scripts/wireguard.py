import mongomodel
from subprocess import run
from typing import List


mongomodel.database.connect(host='mongodb://192.168.1.12/test')


class WgClient(mongomodel.Document):
    name = mongomodel.StringField()
    public_key = mongomodel.StringField()
    address = mongomodel.StringField(required=False)

    def __str__(self):
        return self.name

    @property
    def data(self):
        return (self.name, self.public_key, self.address)

    def connect(self, username: str, command: List[str] = None):
        if command is None:
            command = []
        run(['/usr/bin/ssh', f'{username}@{self.address}', *command])
        return self

    @classmethod
    def show_all(cls):
        from tabulate import tabulate

        print(tabulate(
            [client.data for client in cls.objects.sort(['address'])],
            headers=('name', 'public_key', 'address'),
            tablefmt='orgtbl'
        ))

    def ping(self, timeout=1000, count=1, **kwargs):
        run(['/usr/bin/ping', self.address, f'-c{count}'],
            timeout=timeout,
            check=True,
            **kwargs)
