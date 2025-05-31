import requests

# url = "https://api.hh.ru/vacancies"
# headers = {"User-Agent": "HH-User-Agent"}
# response = requests.get(url, headers=headers, params={"page":0, "per_page": 2})
# print(response.status_code)
# data = response.json()
# for item in data["items"]:
#     print(item)
#     print ("="*20)

url = "https://api.hh.ru/employers"
headers = {"User-Agent": "HH-User-Agent"}
response = requests.get(url, headers=headers, params={"text": "Дельтасвар", "page":0, "per_page": 20})
data = response.json()

for item in data["items"]:
    print(item)
    print ("="*20)


# url2 = "https://api.hh.ru/vacancies?employer_id=1329403"
# response = requests.get(url2, headers=headers, params={"per_page": 20})
# data = response.json()
#
# for item in data["items"]:
#     print(item)
#     print ("="*20)