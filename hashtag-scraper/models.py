
from api import ERApi


class Settings:
    def __init__(self, category=None, eid=None, source=None, ename=None, env='DEV'):
        self.eid = eid
        self.category = category
        self.ename = ename
        self.source = source
        self.items = []
        self.env = env

    def prepare(self):
        page = 0
        req = ERApi(method="get", entity="setting/list", env=self.env)

        self.eid and req.add_params({'eid': self.eid})
        self.category and req.add_params({'categ': self.category})
        self.ename and req.add_params({'ename': self.ename})
        self.source and req.add_params({'src': self.source})

        while True:
            page += 1
            req.add_params({'page': page})
            res = req.execute()

            if len(res) > 0:
                self.items = self.items + res
            else:
                break
