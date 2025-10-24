# pylebanon 
### A  Python package for ... Lebanon. And yes I had nothing better to do.


```python
from pylebanon import Lebanon
lb = Lebanon()
```

    Habibi welcome to Lebanon 🇱🇧



```python
import random 

print("Flag:", lb.get_flag())
print("Names:", lb.get_names())
print("Capital:", lb.get_capital())
print("Area:", lb.get_area())
print("Location:", lb.get_location())
print("Timezone:", lb.get_timezone())
governorates =  lb.get_governorates()
print("Governorates:", governorates)
idx = random.randint(0, len(governorates)-1)
print(f"Cities in {governorates[idx]}:", lb.get_governorate_cities(governorates[idx]))
print("Phone codes:", lb.get_phone_code())
print("Currency:", lb.get_currency())
print("Languages:", lb.get_languages())
print("Wiki:", lb.get_wiki())
```

    Flag: 🇱🇧
    Names: ['LB', 'Lebanese Republic', 'Al-Jumhūrīyah Al-Libnānīyah', 'Lebanon', 'لبنان', 'Líbano', 'Liban', 'レバノン', 'Libano']
    Capital: Beirut
    Area: 10452
    Location: Middle East
    Timezone: UTC+02:00
    Governorates: ['Akkar Governorate', 'Baalbek-Hermel Governorate', 'Beirut Governorate', 'Beqaa Governorate', 'Mount Lebanon Governorate', 'Nabatieh Governorate', 'North Governorate', 'South Governorate']
    Cities in Mount Lebanon Governorate: ['Baabda', 'Bhamdoun', 'Bhamdoûn el Mhatta', 'Caza de Baabda', 'Jbaïl', 'Jounieh']
    Phone codes: +961
    Currency: LBP
    Languages: ['Arabic', 'Armenian', 'French']
    Wiki: http://en.wikipedia.org/wiki/lebanon

