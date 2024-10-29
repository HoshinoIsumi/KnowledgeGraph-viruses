import json
import time
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from sqlalchemy import create_engine, Column, Integer, String, Text, Date
from sqlalchemy.orm import sessionmaker, declarative_base


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
            if isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 404:
                print(f"404 error for {url}, skipping this link.")
                return None
            print(f"Attempt {attempt + 1} failed: {e}")
            if "SSLError" in str(e) or "Max retries exceeded" in str(e):
                print("SSL error encountered. Waiting for 30 s before retrying...")
                time.sleep(30)
            if attempt + 1 == max_retries:
                raise
            time.sleep(backoff_factor * (2 ** attempt))


def parse_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    data = {}

    # Extract virus name
    virus_name_element = soup.find('b', string="Virus Name")
    if virus_name_element:
        # 获取下一个 <br> 标签
        br_element = virus_name_element.find_next('br')
        if br_element:
            # 获取 <br> 后的下一个兄弟节点
            virus_name = br_element.next_sibling
            if virus_name:  # 确保存在有效文本
                data['virus_name'] = virus_name.strip()

    # Extract aliases
    aliases_element = soup.find('b', string="Aliases")
    if aliases_element:
        alias_font = aliases_element.find_next('font')
        if alias_font:
            aliases_text = alias_font.get_text(separator='<br>', strip=True)
            aliases_list = [alias.strip() for alias in aliases_text.split('<br>') if alias.strip()]
            data['aliases'] = ', '.join(aliases_list)
        else:
            data['aliases'] = ""
    else:
        data['aliases'] = ""

    # Continue extracting other information
    fonts = soup.find_all('font')
    for i, font in enumerate(fonts):
        text = font.get_text(strip=True)
        if "Discovery Date" in text:
            data['discovery_date'] = fonts[i + 1].get_text(strip=True) if i + 1 < len(fonts) else ""
        elif "Origin" in text:
            data['origin'] = fonts[i + 1].get_text(strip=True) if i + 1 < len(fonts) else ""
        elif "Length" in text:
            data['length'] = fonts[i + 1].get_text(strip=True) if i + 1 < len(fonts) else ""
        elif "Type" in text:
            data['type'] = fonts[i + 1].get_text(strip=True) if i + 1 < len(fonts) else ""
        elif "Risk Assessment" in text:
            data['risk_assessment'] = fonts[i + 1].get_text(strip=True) if i + 1 < len(fonts) else ""
        elif "Minimum Engine" in text:
            data['minimum_engine'] = fonts[i + 1].get_text(strip=True) if i + 1 < len(fonts) else ""
        elif "Minimum Dat" in text:
            data['minimum_dat'] = fonts[i + 1].get_text(strip=True) if i + 1 < len(fonts) else ""
        elif "DAT Release Date" in text:
            data['dat_release_date'] = fonts[i + 1].get_text(strip=True) if i + 1 < len(fonts) else ""
        elif "Virus Characteristics" in text:
            data['virus_characteristics'] = fonts[i + 1].get_text(strip=True).replace('\n', ' ') if i + 1 < len(fonts) else ""
        elif "Symptoms" in text:
            data['symptoms'] = fonts[i + 1].get_text(strip=True).replace('\n', ' ') if i + 1 < len(fonts) else ""
        elif "Method Of Infection" in text:
            data['method_of_infection'] = fonts[i + 1].get_text(strip=True).replace('\n', ' ') if i + 1 < len(fonts) else ""
        elif "Removal Instructions" in text:
            data['removal_instructions'] = fonts[i + 1].get_text(strip=True).replace('\n', ' ') if i + 1 < len(fonts) else ""

            return data
    return data


def extract_virus_links(url):
    html_content = fetch_page_content(url)
    if html_content is None:
        return []
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []

    for a_tag in soup.find_all('a', href=True):
        if 'virus_k' in a_tag['href']:
            full_url = urljoin(url, a_tag['href'])
            links.append(full_url)

    return links


def append_to_json_file(data, filename='/home/isumi/Progect/Python/virus info/all_virus_info.json'):
    with open(filename, 'a', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False)
        file.write('\n')

# SQLAlchemy Base class
Base = declarative_base()

# Define VirusInfo model
class VirusInfo(Base):
    __tablename__ = 'virus_info'

    id = Column(Integer, primary_key=True, autoincrement=True)
    virus_name = Column(String(255))
    aliases = Column(Text)
    discovery_date = Column(Date)
    origin = Column(String(255))
    length = Column(String(255))
    type = Column(String(255))
    risk_assessment = Column(String(255))
    minimum_engine = Column(String(255))
    minimum_dat = Column(String(255))
    dat_release_date = Column(Date)
    virus_characteristics = Column(Text)
    symptoms = Column(Text)
    method_of_infection = Column(Text)
    removal_instructions = Column(Text)

# Create database connection and table
engine = create_engine('mysql+mysqlconnector://virus_user:20040113Ming%40@localhost/virus_db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def parse_date(date_str):
    """Improved date parsing function with support for more date formats"""
    if not date_str or not isinstance(date_str, str):
        return None
    date_formats = [
        '%m/%d/%y',
        '%m/%d/%Y',
        '%Y-%m-%d',
        '%y-%m-%d'
    ]
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    print(f"Unparseable date format: {date_str}")
    return None


def clean_data(data):
    """Clean data, including date field formatting"""
    cleaned_data = data.copy()

    for date_field in ['discovery_date', 'dat_release_date']:
        if date_field in cleaned_data and cleaned_data[date_field]:
            cleaned_data[date_field] = parse_date(cleaned_data[date_field])

    return cleaned_data

def format_date(date_str):
    if date_str:
        try:
            return datetime.strptime(date_str, '%m/%d/%Y').date()
        except ValueError:
            try:
                return datetime.strptime(date_str, '%m/%d/%y').date()
            except ValueError:
                try:
                    return datetime.strptime(date_str, '%-m/%-d/%Y').date()
                except ValueError:
                    try:
                        return datetime.strptime(date_str, '%-m/%-d/%y').date()
                    except ValueError:
                        print(f"Date format error: {date_str}")
                        return None
    return None


def insert_virus_data(data, session):
    print("Inserting data:")
    for key, value in data.items():
        print(f"{key}: {value}")

    try:
        dat_release_date = format_date(data.get('dat_release_date'))

        discovery_date = format_date(data.get('discovery_date'))

        new_virus = VirusInfo(
            virus_name=data.get('virus_name'),
            aliases=data.get('aliases'),
            discovery_date=discovery_date,
            origin=data.get('origin'),
            length=data.get('length'),
            type=data.get('type'),
            risk_assessment=data.get('risk_assessment'),
            minimum_engine=data.get('minimum_engine'),
            minimum_dat=data.get('minimum_dat'),
            dat_release_date=dat_release_date,
            virus_characteristics=data.get('virus_characteristics'),
            symptoms=data.get('symptoms'),
            method_of_infection=data.get('method_of_infection'),
            removal_instructions=data.get('removal_instructions')
        )

        session.add(new_virus)
        session.commit()
        print(f"Data inserted successfully: {data.get('virus_name')}")

    except Exception as e:
        print(f"Data insertion failed: {data.get('virus_name')}, Error: {e}")
        session.rollback()

def process_virus_page(url):
    print(f"Processing page: {url}")
    html_content = fetch_page_content(url)
    if html_content is None:
        print(f"Unable to access page: {url}, skipped.")
        return

    data = parse_content(html_content)
    if data:
        insert_virus_data(data, session)
        append_to_json_file(data)
        print(f"Successfully inserted data: {data.get('virus_name', 'Unknown Virus')}")
    else:
        print(f"Parsing failed or data is empty: {url}")


def main(start_url):
    global session
    session = Session()

    visited_links = set()
    try:
        with open('/home/isumi/Progect/Python/virus info/visited_links.txt', 'r', encoding='utf-8') as file:
            visited_links = set(line.strip() for line in file)
    except FileNotFoundError:
        print("visited_links.txt not found, starting fresh.")

    virus_links = extract_virus_links(start_url)
    for link in virus_links:
        if link not in visited_links:
            process_virus_page(link)
            visited_links.add(link)
            with open('/home/isumi/Progect/Python/virus info/visited_links.txt', 'a', encoding='utf-8') as file:
                file.write(link + '\n')

if __name__ == '__main__':
    start_urls = [
        'https://web.archive.org/web/20001211042000/http://vil.nai.com/villib/alphar.asp?char=v',
        'https://web.archive.org/web/20001211052000/http://vil.nai.com/villib/alphar.asp?char=w',
        'https://web.archive.org/web/20001211074400/http://vil.nai.com/villib/alphar.asp?char=x',
        'https://web.archive.org/web/20000623120552/http://vil.nai.com/villib/alphar.asp?char=y',
        'https://web.archive.org/web/20000930095509/http://vil.nai.com/villib/alphar.asp?char=z',
    ]

    for start_url in start_urls:
        main(start_url)
