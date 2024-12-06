import json
import re
import stanza
from neo4j import GraphDatabase

# Initialize Stanza pipeline for English language
stanza.download('en')
nlp = stanza.Pipeline(lang='en', processors='tokenize,mwt,pos,lemma,depparse,ner')

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

class TextProcessor:
    def __init__(self, text):
        self.text = text
        self.entities = []
        self.relations = []
        self.attributes = []
        self.triples = []

    def extract_entities(self):
        doc = nlp(self.text)
        for sentence in doc.sentences:
            for ent in sentence.ents:
                if ent.type in {"ORG", "PRODUCT", "QUANTITY", "CARDINAL", "DISEASE"}:
                    self.entities.append((ent.text, ent.type))

    def extract_relations_and_attributes(self):
        doc = nlp(self.text)
        for sentence in doc.sentences:
            for word in sentence.words:
                # Attribute extraction
                if word.text.lower() in {"infected", "available", "free", "active", "malicious"}:
                    self.attributes.append((word.text.lower(), "status"))
                elif word.text.lower() == "bytes" and word.head != word.id:
                    size_value = sentence.words[word.head - 1].text
                    self.attributes.append(("size", size_value))

                # Flexible relation extraction
                if word.deprel in {"obj", "nmod", "obl", "nsubj", "nsubjpass"}:
                    head_word = sentence.words[word.head - 1]
                    if head_word.upos == "VERB" or head_word.deprel == "root":
                        subject = head_word.text
                        object_text = word.text
                        relation = head_word.lemma
                        if subject.lower() != "systems":
                            self.relations.append((subject, relation, object_text))

    def create_triples(self):
        self.triples.extend([(entity[0], "is_a", entity[1]) for entity in self.entities])
        self.triples.extend([(attr[0], "has", attr[1]) for attr in self.attributes])
        self.triples.extend(self.relations)

    def process(self):
        self.extract_entities()
        self.extract_relations_and_attributes()
        self.create_triples()

# 构建知识图谱
def build_knowledge_graph(data, output_file):
    try:
        with open(output_file, 'w') as file:
            for entry in data:
                virus_name = entry.get("virus_name", "Unknown")

                if virus_name == "Unknown":
                    continue  # 跳过病毒名未知的条目

                # 处理病毒节点
                knowledge_graph_triples = [(virus_name, "is_a", "Virus")]

                # 处理病毒的各类属性，直接将字段名称作为节点类型
                virus_properties = {
                    "Alias": entry.get("aliases", None),
                    "Discovery Date": entry.get("discovery_date", None),
                    "Length": entry.get("length", None),
                    "Origin": entry.get("origin", None),
                    "Risk Assessment": entry.get("risk_assessment", None),
                    "Minimum DAT": entry.get("minimum_dat", None),
                    "DAT Release Date": entry.get("dat_release_date", None),
                    "Symptoms": entry.get("symptoms", None),
                    "Method of Infection": entry.get("method_of_infection", None),
                    "Removal Instructions": entry.get("removal_instructions", None),
                }

                # 将字段名称作为属性标签，并将属性值存储在节点上
                for prop, value in virus_properties.items():
                    if value:  # 仅在值不为空时添加属性节点
                        # 替换空格为下划线，确保节点标签合法
                        prop_label = prop.replace(" ", "_")
                        property_node = f"{prop_label}_{value[:10]}"  # 使用属性值的前10个字符作为节点的唯一标识
                        knowledge_graph_triples.append((virus_name, "has_" + prop_label, property_node))
                        knowledge_graph_triples.append((property_node, "is_a", prop_label))  # 每个属性节点的类型为属性名称
                        knowledge_graph_triples.append((property_node, "has_value", value))  # 属性值作为该节点的属性

                # 提取病毒特征信息并生成属性
                symptoms, file_length_increases = extract_virus_characteristics(entry.get("virus_characteristics", ""))
                if symptoms:
                    knowledge_graph_triples.append((virus_name, "has_Symptoms", "Symptoms_" + symptoms[:10]))
                    knowledge_graph_triples.append(("Symptoms_" + symptoms[:10], "is_a", "Symptoms"))
                    knowledge_graph_triples.append(("Symptoms_" + symptoms[:10], "has_value", symptoms))

                for file_type, length in file_length_increases.items():
                    if length:  # 仅在长度不为空时添加属性节点
                        length_node = f"{file_type.replace('-', '_')}_Length_{length[:10]}"
                        knowledge_graph_triples.append((virus_name, "has_" + file_type.replace("-", "_"), length_node))
                        knowledge_graph_triples.append((length_node, "is_a", file_type.replace("-", "_")))
                        knowledge_graph_triples.append((length_node, "has_value", length))

                # 添加更多的关系或属性提取
                processor = TextProcessor(entry.get("virus_characteristics", ""))
                processor.process()
                knowledge_graph_triples.extend(processor.triples)

                # 将三元组实时写入文件
                for subj, rel, obj in knowledge_graph_triples:
                    file.write(json.dumps({"subject": subj, "relation": rel, "object": obj}) + '\n')

                print(f"Processed: {virus_name}")

                # 将每条三元组实时插入 Neo4j
                create_knowledge_graph_in_neo4j(knowledge_graph_triples, neo4j_uri, neo4j_user, neo4j_password)

    except Exception as e:
        print(f"Error processing data: {e}")

# 构建 Neo4j 知识图谱
def create_knowledge_graph_in_neo4j(triples, uri, user, password):
    try:
        with GraphDatabase.driver(uri, auth=(user, password)) as driver:
            with driver.session() as session:
                for subj, rel, obj in triples:
                    # 如果属性节点的类型是 Alias, Discovery Date 等，直接创建属性节点
                    if "has_" in rel:
                        session.run(f"""
                            MERGE (a:Virus {{name: $subj}})
                            MERGE (b:{rel.replace('has_', '')} {{name: $obj}})
                            MERGE (a)-[:HAS_PROPERTY]->(b)
                        """, subj=subj, obj=obj)
                    elif "is_a" in rel:
                        session.run(f"""
                            MERGE (a:{obj} {{name: $subj}})
                            MERGE (b:{obj} {{name: $obj}})
                            MERGE (a)-[:IS_A]->(b)
                        """, subj=subj, obj=obj)
                    else:
                        session.run(f"""
                            MERGE (a:Virus {{name: $subj}})
                            MERGE (b:Entity {{name: $obj}})
                            MERGE (a)-[:{rel.replace('-', '_')}]->(b)
                        """, subj=subj, obj=obj)
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")

# 主函数
if __name__ == "__main__":
    file_path = "/home/isumi/Progect/virusesKnowledgeGraph/stanzaNERProcesso/all_virus_info.json"  # 文件路径
    output_file = "/home/isumi/Progect/virusesKnowledgeGraph/stanzaNERProcesso/triples.json"  # 输出文件路径
    neo4j_uri = "bolt://localhost:7687"  # Neo4j URI
    neo4j_user = "neo4j"  # Neo4j 用户名
    neo4j_password = "20040113Ming@"  # Neo4j 密码

    virus_data = load_virus_data(file_path)

    # 处理每个病毒数据并构建知识图谱
    build_knowledge_graph(virus_data, output_file)

    print("Knowledge Graph building completed.")
