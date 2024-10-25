import codecs
data_path = "./init_data.txt"
save_path = "./data_set.txt"
lines = ''
seq = ''
#读取数据
with codecs.open(data_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.replace("\n", "")
        line = line.replace(" ", "")
        for i in line:
            if i == '\r':
               i = i.replace("\r", "")
               seq = seq + "\n"
               continue
               #print(line)
            else:
                seq = seq + i +"\tO"+"\n"
#写入数据
with codecs.open(save_path, 'w', encoding='utf-8') as w:
    w.write(seq)
    print("写入完毕")
        #print(seq)
        #line = line.replace("\r", "")
        #lines = lines+line
        #print(line)
        # result = "\n".join(lines)
        # print(result)
        #print(i)