import codecs
import json
path = "./data_init.txt"
save = "./data.json"
p = []
total = []
dict = {}
with codecs.open(path, "r", encoding="utf-8") as f:
    for line in f:
        if "####" in line:
            total.append(p)
            p = []
            #print(total)
            continue

        if "发现日期：" in line:
            line = line.replace("\t", "")
            line = line.strip().split("：")
            p = p+line
        elif "起源" in line:
            line = line.replace("\t", "")
            line = line.strip().split("：")
            p = p + line
        elif "长度：" in line:
            line = line.replace("\t", "")
            line = line.strip().split("：")
            p = p + line
        elif "类型：" in line:
            line = line.replace("\t", "")
            line = line.strip().split("：")
            p = p + line
        elif "子类型：" in line:
            line = line.replace("\t", "")
            line = line.strip().split("：")
            p = p + line
        elif "风险评估：" in line:
            line = line.replace("\t", "")
            line = line.strip().split("：")
            p = p + line
        elif "最小数据：" in line:
            line = line.replace("\t", "")
            line = line.strip().split("：")
            p = p + line
        elif "发布日期：" in line:
            line = line.replace("\t", "")
            line = line.strip().split("：")
            p = p + line
        else:
            line_t = line.replace("\t", "")
            line_r = line_t.replace("\r", "")
            line_n = line_r.replace("\n", "")
            if not line_n:
                continue
            p.append(line_n)


#print(total)
json_data = " "
i = 0
for x in total:
    for i in range(len(x)):
        if i % 2 == 0:
            dict[x[i]] = ""

        else:
            dict[x[i - 1]] = x[i]

    json_data = json_data + json.dumps(dict, ensure_ascii=False).join("\r\n")
   # jspn_data = jspn_data + json.dumps(dict, ensure_ascii=False).join("\r\n")
    dict = {}

with codecs.open(save, "w", encoding="utf-8") as w:
    w.write(json_data)

#print(dict)
#print(p)

#print(data_dict)
#print(json_data)

print("写入完成")