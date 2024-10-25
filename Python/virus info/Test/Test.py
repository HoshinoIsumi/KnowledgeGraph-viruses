import json
import time
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from sqlalchemy import create_engine, Column, Integer, String, Text, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLAlchemy 基础类
Base = declarative_base()

# 定义病毒信息模型
class VirusInfo(Base):
    __tablename__ = 'virus_info'

    id = Column(Integer, primary_key=True, autoincrement=True)
    virus_name = Column(String(255))
    aliases = Column(Text)
    variants = Column(Text)
    description_added = Column(Date)
    discovery_date = Column(Date)
    origin = Column(String(255))
    length = Column(String(255))
    type = Column(String(255))
    subtype = Column(String(255))
    risk_assessment = Column(String(255))
    minimum_engine = Column(String(255))
    minimum_dat = Column(String(255))
    dat_release_date = Column(Date)
    virus_characteristics = Column(Text)
    symptoms = Column(Text)
    method_of_infection = Column(Text)
    removal_instructions = Column(Text)

# 创建数据库连接和表
def create_db_session():
    engine = create_engine('mysql+mysqlconnector://root:isumi@localhost/virus_db')
    Base.metadata.create_all(engine)  # 自动创建表
    Session = sessionmaker(bind=engine)
    return Session()

def fetch_page_content(url, max_retries=5, backoff_factor=0.5):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'
    }
    session = requests.Session()
    retry = Retry(total=max_retries, backoff_factor=backoff_factor, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    for attempt in range(max_retries):
        try:
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            if response.status_code == 404:
                print(f"404 error for {url}, skipping this link.")
                return None
            print(f"Attempt {attempt + 1} failed: {e}")
            if "SSLError" in str(e) or "Max retries exceeded" in str(e):
                print("SSL error encountered. Waiting for 30 s before retrying...")
                time.sleep(30)  # 等待后再重试
            if attempt + 1 == max_retries:
                raise
            time.sleep(backoff_factor * (2 ** attempt))

def parse_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    data = {}

    fonts = soup.find_all('font')
    for i, font in enumerate(fonts):
        text = font.get_text(strip=True)
        if "Virus Name" in text:
            data['病毒名称'] = fonts[i + 1].get_text(strip=True) if i + 1 < len(fonts) else ""
        elif "Aliases" in text:
            data['别名'] = fonts[i + 1].get_text(strip=True).replace('\n', ', ') if i + 1 < len(fonts) else ""
        elif "Variants" in text:
            data['变种'] = fonts[i + 1].get_text(strip=True) if i + 1 < len(fonts) else ""
        elif "Description Added" in text:
            data['描述添加日期'] = text.split(":", 1)[1].strip() if ":" in text else ""
        elif "Discovery Date" in text:
            data['发现日期'] = fonts[i + 1].get_text(strip=True) if i + 1 < len(fonts) else ""
        elif "Origin" in text:
            data['来源'] = fonts[i + 1].get_text(strip=True) if i + 1 < len(fonts) else ""
        elif "Length" in text:
            data['长度'] = fonts[i + 1].get_text(strip=True) if i + 1 < len(fonts) else ""
        elif "Type" in text:
            data['类型'] = fonts[i + 1].get_text(strip=True) if i + 1 < len(fonts) else ""
        elif "SubType" in text:
            data['子类型'] = fonts[i + 1].get_text(strip=True) if i + 1 < len(fonts) else ""
        elif "Risk Assessment" in text:
            data['风险评估'] = fonts[i + 1].get_text(strip=True) if i + 1 < len(fonts) else ""
        elif "Minimum Engine" in text:
            data['最低引擎'] = fonts[i + 1].get_text(strip=True) if i + 1 < len(fonts) else ""
        elif "Minimum Dat" in text:
            data['最低数据'] = fonts[i + 1].get_text(strip=True) if i + 1 < len(fonts) else ""
        elif "DAT Release Date" in text:
            data['DAT 发布日期'] = fonts[i + 1].get_text(strip=True) if i + 1 < len(fonts) else ""
        elif "Virus Characteristics" in text:
            data['病毒特征'] = fonts[i + 1].get_text(strip=True).replace('\n', ' ') if i + 1 < len(fonts) else ""
        elif "Symptoms" in text:
            data['症状'] = fonts[i + 1].get_text(strip=True).replace('\n', ' ') if i + 1 < len(fonts) else ""
        elif "Method Of Infection" in text:
            data['感染方式'] = fonts[i + 1].get_text(strip=True).replace('\n', ' ') if i + 1 < len(fonts) else ""
        elif "Removal Instructions" in text:
            data['移除指令'] = fonts[i + 1].get_text(strip=True).replace('\n', ' ') if i + 1 < len(fonts) else ""

            # 特别处理病毒名称
            virus_name_element = soup.find(string="Virus Name")
            if virus_name_element:
                data['病毒名称'] = virus_name_element.find_next('br').next_sibling.strip()

            return data

    return data

def extract_virus_links(url):
    html_content = fetch_page_content(url)
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []

    for a_tag in soup.find_all('a', href=True):
        if 'virus_k' in a_tag['href']:
            full_url = urljoin(url, a_tag['href'])
            links.append(full_url)

    return links

def append_to_json_file(data, filename='all_virus_info.json'):
    with open(filename, 'a', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False)
        file.write('\n')

def insert_virus_data(data, session):
    virus_info = VirusInfo(
        virus_name=data.get('病毒名称'),
        aliases=data.get('别名'),
        variants=data.get('变种'),
        description_added=parse_date(data.get('描述添加日期')),
        discovery_date=parse_date(data.get('发现日期')),
        origin=data.get('来源'),
        length=data.get('长度'),
        type=data.get('类型'),
        subtype=data.get('子类型', None),
        risk_assessment=data.get('风险评估'),
        minimum_engine=data.get('最低引擎', None),
        minimum_dat=data.get('最低数据'),
        dat_release_date=parse_date(data.get('DAT 发布日期')),
        virus_characteristics=data.get('病毒特征'),
        symptoms=data.get('症状'),
        method_of_infection=data.get('感染方式'),
        removal_instructions=data.get('移除指令')
    )

    session.add(virus_info)
    session.commit()

def parse_date(date_str):
    if not date_str:
        return None  # 如果是空字符串，返回 None
    try:
        if len(date_str.split('/')[-1]) == 2:  # 如果年份是两位数字
            return datetime.strptime(date_str, '%m/%d/%y')  # 将日期字符串解析为 datetime 对象
        else:  # 如果年份是四位数字
            return datetime.strptime(date_str, '%m/%d/%Y')  # 使用四位数年份格式
    except ValueError:
        print(f"日期格式错误: {date_str}")
        return None


def process_virus_page(url):
    print(f"Fetching data from: {url}")
    try:
        html_content = fetch_page_content(url)
        if html_content is None:  # 检查是否为 None
            return
        virus_data = parse_content(html_content)
        append_to_json_file(virus_data)  # 保存为 JSON 文件

        session = create_db_session()  # 创建数据库会话
        insert_virus_data(virus_data, session)  # 保存到 MySQL 数据库
        session.close()  # 关闭会话

        print(f"Data for {virus_data.get('病毒名称', 'Unknown virus')} has been saved.")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return  # 直接返回，继续处理下一个链接

def load_visited_links(filename='visited_links.json'):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            if file.readable() and file.read():  # 检查文件是否可读且非空
                file.seek(0)  # 重置文件指针到开头
                return json.load(file)
    except FileNotFoundError:
        return []  # 如果文件不存在，返回空列表
    return []

def save_visited_link(url, filename='visited_links.json'):
    visited_links = load_visited_links(filename)
    if url not in visited_links:
        visited_links.append(url)
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(visited_links, file, ensure_ascii=False)

def main(start_url):
    visited_links = load_visited_links()
    links_to_visit = extract_virus_links(start_url)

    for link in links_to_visit:
        if link not in visited_links:
            process_virus_page(link)
            save_visited_link(link)

# 主函数
if __name__ == "__main__":
    start_url = 'https://web.archive.org/web/20001210063100/http://vil.nai.com/villib/alphar.asp?char=a'
    main(start_url)
