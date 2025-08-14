import json
import pathlib


class IdRegistry:
    def __init__(self, mode):
        path = (
            "./method/helper/id_seeds_test.json"
            if mode.lower() == "test"
            else "./method/helper/id_seeds.json"
        )
        self.path = pathlib.Path(path)
        if self.path.exists():
            self._next_values = json.loads(self.path.read_text())
        else:
            self._next_values = {
                "Cust1": 0,
                "Cust2": 5000,
                "Product": 10000,
                "Transaction": 100000,
                "total_transaction": 0,
                "total_customer1": 0,
                "total_customer2": 0,
                "total_product": 0,
            }
        self._seeds = dict(self._next_values)  # initial seeds (for ranges)

    def _bump_total_for(self, entity: str) -> None:
        name = entity.lower()
        if "1" in name:
            self._next_values["total_customer1"] += 1
        elif "2" in name:
            self._next_values["total_customer2"] += 1
        elif "product" in name:
            self._next_values["total_product"] += 1
        elif "transaction" in name:
            self._next_values["total_transaction"] += 1

    def next(self, entity: str) -> int:
        self._bump_total_for(entity)
        v = self._next_values[entity]
        self._next_values[entity] += 1
        return v

    def get_current_id(self, entity: str):
        seed = self._seeds[entity]
        next_val = self._next_values[entity]
        return (next_val - 1) if next_val > seed else None

    def get_initial_value(self, entity):
        return self._seeds[entity]

    def get_id_range(self):
        id_range = {"Cust1": [0], "Cust2": [5000], "Product": [10000]}
        for k in id_range.keys():
            lower = id_range[k][0]
            current = self.get_initial_value(k)
            upper = current if current is not None else (lower - 1)
            id_range[k].append(upper)
        return id_range

    def advance(self):
        self.path.write_text(json.dumps(self._next_values, indent=2))

    def reload(self):
        if self.path.exists():
            self._next_values = json.loads(self.path.read_text())
