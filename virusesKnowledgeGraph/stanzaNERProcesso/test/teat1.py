import json
import re
import stanza
import pandas as pd

# Initialize Stanza pipeline for English language
stanza.download('en')
nlp = stanza.Pipeline(lang='en', processors='tokenize,mwt,pos,lemma,depparse,ner')

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
                if ent.type in {"ORG", "PRODUCT", "QUANTITY", "CARDINAL"}:
                    for label in ent.type.split(","):
                        self.entities.append((ent.text, label.strip()))

    def extract_relations_and_attributes(self):
        doc = nlp(self.text)
        for sentence in doc.sentences:
            for word in sentence.words:
                # Attribute extraction
                if word.text.lower() in {"infected", "available", "free"}:
                    self.attributes.append((word.text.lower(), "status"))
                elif word.text.lower() == "bytes" and word.head != word.id:
                    size_value = sentence.words[word.head - 1].text
                    self.attributes.append(("size", size_value))

                # Flexible relation extraction with filtered criteria
                if word.deprel in {"obj", "nmod", "obl", "nsubj"}:
                    head_word = sentence.words[word.head - 1]
                    if head_word.upos == "VERB" or head_word.deprel == "root":
                        subject = head_word.text
                        object_text = word.text
                        relation = head_word.lemma
                        if subject.lower() not in {"systems"}:  # filter out noise
                            self.relations.append((subject, relation, object_text))

    def extract_virus_characteristics(self, virus_characteristics):
        # 使用正则表达式提取症状
        symptoms_pattern = re.compile(r'Symptoms(.*?)Infected', re.DOTALL)
        symptoms_matches = symptoms_pattern.search(virus_characteristics)
        symptoms = symptoms_matches.group(1).strip() if symptoms_matches else "N/A"

        # 提取文件长度增加信息
        file_increase_pattern = re.compile(r'Infected \.(.*?) files have a file length increase of (.*?)(?=\.\s|$)', re.DOTALL)
        increases = file_increase_pattern.findall(virus_characteristics)

        file_length_increases = {}
        for match in increases:
            if len(match) == 2:  # 确保匹配只有两个元素
                file_type, length = match
                file_length_increases[file_type.strip()] = length.strip()

        return symptoms, file_length_increases

    def create_triples(self):
        for entity in self.entities:
            self.triples.append((entity[0], "is_a", entity[1]))

        for attr in self.attributes:
            self.triples.append((attr[0], "has", attr[1]))

        for relation in self.relations:
            self.triples.append(relation)

    def process(self):
        # 解析 JSON 数据
        json_data = json.loads(self.text)
        virus_characteristics = json_data.get("virus_characteristics", "")

        self.extract_entities()
        self.extract_relations_and_attributes()

        # 提取病毒特征信息并生成属性
        symptoms, file_length_increases = self.extract_virus_characteristics(virus_characteristics)
        self.attributes.append(("symptoms", symptoms))

        # 添加文件长度增加信息为属性
        for file_type, length in file_length_increases.items():
            self.attributes.append((f"{file_type}_length_increase", length))

        self.create_triples()

    def display_results(self):
        print("Entities:")
        for entity in self.entities:
            print(entity)

        print("\nRelations:")
        for relation in self.relations:
            print(relation)

        print("\nAttributes:")
        for attribute in self.attributes:
            print(attribute)

        print("\nKnowledge Graph Triples:")
        for triple in self.triples:
            print(triple)

# 从 JSON 文件读取数据
with open('/virusesKnowledgeGraph/stanzaNERProcesso/test.jsonl', 'r') as file:
    text = file.read()

# Run the processor
processor = TextProcessor(text)
processor.process()
processor.display_results()
