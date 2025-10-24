import json
from pathlib import Path


class Lebanon:

    def __init__(self):
        self.__datapath = Path(f"{Path(__file__).parent}/data/lebanon.json")

        self.__flag = "\U0001f1f1\U0001f1e7"
        self.__json = None

        self.__setup()

        print("Habibi welcome to Lebanon \U0001f1f1\U0001f1e7")

    def __setup(self):
        with self.__datapath.open("r", encoding="utf-8") as f:
            self.__json = json.load(f)

    def get_flag(self):
        return self.__flag

    def get_names(self):
        return (
            self.__json["altSpellings"]
            + [self.__json["name"]]
            + [self.__json["nativeName"]]
            + [self.__json["translations"]["es"]]
            + [self.__json["translations"]["fr"]]
            + [self.__json["translations"]["ja"]]
            + [self.__json["translations"]["it"]]
        )

    def get_location(self):
        return self.__json["location"]

    def get_area(self):
        return self.__json["area"]

    def get_timezone(self):
        return self.__json["timezones"][0]

    def get_governorates(self):
        return [s["name"] for s in self.__json["states"]]

    def get_governorate_cities(self, state_name):
        cities = []
        for state in self.__json["states"]:
            if state["name"] == state_name:
                cities = [c["name"] for c in state["cities"]]
                break
        return cities

    def get_wiki(self):
        return self.__json["wiki"]

    def get_capital(self):
        return self.__json["capital"]

    def get_phone_code(self):
        return "+" + self.__json["callingCodes"][0]

    def get_currency(self):
        return self.__json["currencies"][0]

    def get_languages(self):
        return self.__json["languages"]
