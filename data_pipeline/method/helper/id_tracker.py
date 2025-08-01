# id_registry.py
import itertools
import json
import pathlib


class IdRegistry:
    def __init__(self, mode="test"):

        if mode.lower() == "test":
            path = "./method/helper/id_seeds_test.json"
        else:
            path = "./method/helper/id_seeds.json"

        self.path = pathlib.Path(path)
        if self.path.exists():
            self._seeds = json.loads(self.path.read_text())
        else:  # first ever run
            self._seeds = {
                "Cust1": 0,
                "Cust2": 5000,
                "Product": 10000,
                "total_transaction": 0,
                "total_customer1": 0,
                "total_customer2": 0,
                "total_product": 0,
            }
        self._counters = {k: itertools.count(v) for k, v in self._seeds.items()}

    def next(self, entity):  # entity = 'customer' | 'product' | 'transaction'
        if "1" in entity:
            next(self._counters["total_customer1"])
        elif "2" in entity:
            next(self._counters["total_customer2"])
        elif "product" in entity.lower():
            next(self._counters["total_product"])
        return next(self._counters[entity])

    def get_initial_value(self, entity):
        return self._seeds[entity]

    def get_id_range(self):
        """
        Get id range from lowest to highest.
        Output:
            - id_range = {class_name: [lower, upper],...}
        """
        id_range = {"Cust1": [0], "Cust2": [5000], "Product": [10000]}

        for k in id_range.keys():
            id_range[k].append(self.get_initial_value(k))

        return id_range

    def advance(self):  # call once at the END of the run
        new_seeds = {k: next(c) for k, c in self._counters.items()}
        self.path.write_text(json.dumps(new_seeds, indent=2))

    def reload(self):
        if self.path.exists():
            self._seeds = json.loads(self.path.read_text())
