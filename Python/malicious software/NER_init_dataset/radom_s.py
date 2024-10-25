import random

def shuffle_sentences(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        sentences = file.readlines()

    random.shuffle(sentences)

    with open(output_file, 'w', encoding='utf-8') as file:
        file.writelines(sentences)
# 例如，假设你有一个文本文件input.txt，想要将其句子顺序打乱后保存到output.txt：
input_file_path = 'input.txt'
output_file_path = 'output.txt'

shuffle_sentences(input_file_path, output_file_path)