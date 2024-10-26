import codecs
path = '/home/isumi/Progect/Python/malicious software/data/test.txt'
path_1 = '/home/isumi/Progect/Python/malicious software/test_1.txtt'
s = ''
with codecs.open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i in lines:
        i = i.replace('\t', ' ')
        s = s+i
    print(s)
with codecs.open(path_1, 'w', encoding='utf-8') as w:
    w.write(s)


