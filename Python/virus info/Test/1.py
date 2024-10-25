import requests


def fetch_and_save_html(url, output_file):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(response.text)

        print(f"HTML content has been saved to {output_file}")
        return True
    except requests.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return False


def main():
    while True:
        url = input("请输入要获取的URL (输入 'q' 退出): ")
        if url.lower() == 'q':
            break

        output_file = input("请输入保存文件名 (例如: output.html): ")

        if fetch_and_save_html(url, output_file):
            print("HTML内容已成功保存。")
        else:
            print("获取HTML内容失败，请检查URL是否正确。")

        print("\n")  # 为了更好的可读性添加空行


if __name__ == "__main__":
    main()