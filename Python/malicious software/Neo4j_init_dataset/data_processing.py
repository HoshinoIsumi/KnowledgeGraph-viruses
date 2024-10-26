import json
import codecs

data_path = "/home/isumi/Progect/Python/malicious software/Neo4j_init_dataset/data_init.txt"
save_path = "/home/isumi/Progect/Python/malicious software/Neo4j_init_dataset/data.json"
#read data
with codecs.open(data_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

data_dict = {}
index = 1
for line in lines:
    line = line.replace('\t', '')
    try:
        key, value = line.strip().split('：')
        data_dict[key] = value
        index += 1
    except ValueError as e:
        print('数据集第%d行有‘：’ 请将‘：’修改为其他字符' % index)
        index += 1
json_data = json.dumps(data_dict, ensure_ascii=False)
#print(data_dict)
#print(json_data)
with codecs.open(save_path, "w", encoding="utf-8") as w:
    w.write(json_data)

print("写入完成")