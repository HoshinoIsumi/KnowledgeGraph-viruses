import os


def split_text(input_file, output_file1, output_file2, output_file3, ratios=(7, 2, 1)):
    with open(input_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    total_lines = len(lines)
    ratio_sum = sum(ratios)
    ratios = [ratio / ratio_sum for ratio in ratios]

    split_points = [int(total_lines * ratio) for ratio in ratios]

    file1_lines = lines[:split_points[0]]
    file2_lines = lines[split_points[0]:split_points[0] + split_points[1]]
    file3_lines = lines[split_points[0] + split_points[1]:]

    with open(output_file1, 'w', encoding='utf-8') as file:
        file.writelines(file1_lines)

    with open(output_file2, 'w', encoding='utf-8') as file:
        file.writelines(file2_lines)

    with open(output_file3, 'w', encoding='utf-8') as file:
        file.writelines(file3_lines)


# 例如，假设你有一个文本文件input.txt，想要将其按照7:2:1的比例划分为output1.txt、output2.txt和output3.txt：
input_file_path = 'output.txt'
output_file1_path = 'train.txt'
output_file2_path = 'dev.txt'
output_file3_path = 'test.txt'

split_text(input_file_path, output_file1_path, output_file2_path, output_file3_path)
