import json
import os
class Saveable:
    def __init__(self, fname: str) -> None:
        self.name = fname
        self.path = os.path.join("data", self.name)
        self._data = {}
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                self._data = json.load(f)
        elif not os.path.exists("data"):
            os.mkdir("data")
    
    def save(self):
        with open(self.path, "w") as f:
            json.dump(self._data, f, ensure_ascii=False)
    
    def data(self, oid: str):
        if oid not in self._data:
            self._data[oid] = {}
        return self._data[oid]