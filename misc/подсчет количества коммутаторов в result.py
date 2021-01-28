import json
f = open('output/result.json','r', encoding='utf-8-sig')
_data = json.load(f)
print(len(_data))
