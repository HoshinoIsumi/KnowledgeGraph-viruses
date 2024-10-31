import json
import re
from neo4j import GraphDatabase


# 从文件中读取数据
def load_virus_data(file_path):
    try:
        with open(file_path, 'r') as file:
            data = [json.loads(line.strip()) for line in file]
        return data
    except Exception as e:
        print(f"Error loading data: {e}")
        return []


# 提取病毒特征信息
def extract_virus_characteristics(virus_characteristics):
    symptoms_pattern = re.compile(r'Symptoms(.*?)Infected', re.DOTALL)
    symptoms_matches = symptoms_pattern.search(virus_characteristics)
    symptoms = symptoms_matches.group(1).strip() if symptoms_matches else "N/A"

    file_increase_pattern = re.compile(r'Infected \.(.*?) files have a file length increase of (.*?)(?=\.\s|$)',
                                       re.DOTALL)
    increases = file_increase_pattern.findall(virus_characteristics)

    file_length_increases = {match[0].strip(): match[1].strip() for match in increases if len(match) == 2}

    return symptoms, file_length_increases


# 知识图谱
def build_knowledge_graph(data):
    knowledge_graph_triples = []

    for entry in data:
        virus_name = entry.get("virus_name", "Unknown")

        if virus_name == "Unknown":
            continue  # 跳过无效条目

        # 处理病毒节点
        knowledge_graph_triples.append((virus_name, "is_a", "Virus"))

        # 处理特征和属性
        attributes = [
            ("aliases", entry.get("aliases")),
            ("discovery_date", entry.get("discovery_date")),
            ("length", entry.get("length")),
            ("origin", entry.get("origin")),
            ("risk_assessment", entry.get("risk_assessment")),
            ("minimum_dat", entry.get("minimum_dat")),
            ("dat_release_date", entry.get("dat_release_date")),
            ("symptoms", entry.get("symptoms")),
            ("method_of_infection", entry.get("method_of_infection")),
            ("removal_instructions", entry.get("removal_instructions")),
        ]

        for attr, value in attributes:
            if value:  # 仅在值不为空时添加三元组
                knowledge_graph_triples.append((virus_name, "has_" + attr, value))

        # 提取文件长度增加信息
        symptoms, file_length_increases = extract_virus_characteristics(entry.get("virus_characteristics", ""))
        if symptoms:
            knowledge_graph_triples.append((virus_name, "has_symptoms", symptoms))

        for file_type, length in file_length_increases.items():
            if length:  # 仅在长度不为空时添加三元组
                # 使用下划线替换非法字符
                sanitized_file_type = re.sub(r'\W|^(?=\d)', '_', file_type)
                knowledge_graph_triples.append((virus_name, f"{sanitized_file_type}_length_increase", length))

    return knowledge_graph_triples


# 保存三元组到文件
def save_triples_to_file(triples, output_file):
    try:
        with open(output_file, 'w') as file:
            for triple in triples:
                file.write(json.dumps(triple) + '\n')
    except Exception as e:
        print(f"Error saving triples to file: {e}")


# 构建 Neo4j 知识图谱
def sanitize_relationship_name(rel):
    # 用下划线替换所有非字母数字字符
    return re.sub(r'\W|^(?=\d)', '_', rel)


def create_knowledge_graph_in_neo4j(triples, uri, user, password):
    try:
        with GraphDatabase.driver(uri, auth=(user, password)) as driver:
            with driver.session() as session:
                for subj, rel, obj in triples:
                    sanitized_rel = sanitize_relationship_name(rel)
                    session.run(f"""
                        MERGE (a:Virus {{name: $subj}})
                        MERGE (b:Entity {{name: $obj}})
                        MERGE (a)-[:{sanitized_rel}]->(b)
                    """, subj=subj, obj=obj)
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")


# 主函数
if __name__ == "__main__":
    file_path = "/home/isumi/Progect/virusesKnowledgeGraph/stanzaNERProcesso/all_virus_info.json"  # 文件路径
    output_file = "/home/isumi/Progect/virusesKnowledgeGraph/stanzaNERProcesso/triples0.json"  # 输出文件路径
    neo4j_uri = "bolt://localhost:7687"  # Neo4j URI
    neo4j_user = "newneo4j"  # Neo4j 用户名
    neo4j_password = "20040113ming"  # Neo4j 密码

    virus_data = load_virus_data(file_path)
    knowledge_graph_triples = build_knowledge_graph(virus_data)

    # 保存三元组到文件
    save_triples_to_file(knowledge_graph_triples, output_file)

    print("Knowledge Graph Triples:")
    for triple in knowledge_graph_triples:
        print(triple)

    # 将三元组导入 Neo4j
    create_knowledge_graph_in_neo4j(knowledge_graph_triples, neo4j_uri, neo4j_user, neo4j_password)