import stanza

class TextProcessor:
    def __init__(self, language='en'):
        # 初始化并加载语言模型
        self.nlp = stanza.Pipeline(language, processors='tokenize,mwt,pos,lemma,depparse,ner')

    def process_text(self, text):
        # 处理文本并提取实体、关系和属性
        doc = self.nlp(text)
        entities = self.extract_entities(doc)
        relations = self.extract_relations(doc)
        attributes = self.extract_attributes(doc)
        
        # 构建知识图谱三元组
        triples = self.build_triples(entities, relations, attributes)
        
        return entities, relations, attributes, triples

    def extract_entities(self, doc):
        # 提取命名实体，避免重复
        unique_entities = {}
        for ent in doc.ents:
            # 处理重复实体，保留最具代表性的类型
            if ent.text in unique_entities:
                unique_entities[ent.text].add(ent.type)
            else:
                unique_entities[ent.text] = {ent.type}
        
        return [(text, ', '.join(types)) for text, types in unique_entities.items()]

    def extract_relations(self, doc):
        # 提取关系（主语与动词）
        relations = []
        for sentence in doc.sentences:
            for word in sentence.words:
                if word.deprel == 'nsubj':
                    subject = word.text
                    relation = self.get_root_relation(sentence)
                    if relation:
                        relations.append((subject, relation))
        return relations

    def get_root_relation(self, sentence):
        # 获取根动词
        for word in sentence.words:
            if word.deprel == 'root' and word.head == 0:
                return word.text
        return None

    def extract_attributes(self, doc):
        # 提取属性（形容词修饰名词）
        attributes = []
        quantity_pairs = {}
        
        for sentence in doc.sentences:
            for word in sentence.words:
                # 如果是形容词，查找其修饰的名词
                if word.deprel == 'amod':
                    noun = self.get_noun_from_attribute(word, sentence)
                    if noun and (noun.text, word.text) not in attributes:
                        attributes.append((noun.text, word.text))

                # 处理数量修饰词
                if word.deprel == 'nummod':  # 数字修饰词
                    noun = self.get_noun_from_nummod(word, sentence)
                    if noun:
                        quantity_pairs[noun.text] = word.text  # 将数量与其名词关联

        # 合并数量属性
        for noun, quantity in quantity_pairs.items():
            attributes.append((noun, quantity))
        
        return attributes

    def get_noun_from_attribute(self, adjective, sentence):
        # 找到形容词对应的名词
        for word in sentence.words:
            if word.head == adjective.id and (word.deprel in ['nsubj', 'obj', 'nmod']):
                return word
        return None

    def get_noun_from_nummod(self, number, sentence):
        # 找到数量对应的名词
        for word in sentence.words:
            if word.head == number.id and (word.deprel in ['nsubj', 'obj', 'nmod']):
                return word
        return None

    def build_triples(self, entities, relations, attributes):
        triples = []
        
        # 创建实体三元组
        for entity in entities:
            for entity_type in entity[1].split(', '):
                triples.append((entity[0], "is_a", entity_type.strip()))  # 实体类别

        # 添加关系三元组
        for relation in relations:
            subject = relation[0]  # 主体
            predicate = relation[1]  # 谓词
            triples.append((subject, predicate, "Entity"))  # 使用通用对象

        # 属性三元组
        for attribute in attributes:
            triples.append((attribute[0], "has", attribute[1]))

        return triples

# 使用示例
if __name__ == "__main__":
    processor = TextProcessor()
    text = (
        "Symptoms: No text strings are visible within the viral code in infected .EXE files, "
        "although the following text strings are encrypted within the virus: \"ABC_FFEA\", "
        "\"Minsk 8.01.92\", \"ABC\". Systems infected with the ABC virus may experience keystrokes "
        "on the system keyboard frequently repeated, as well as system hangs occurring when some files "
        "are executed. Total system memory, as measured by the DOS CHKDSK program, is not altered, "
        "but available free memory decreases by approximately 8,960 bytes. .COM files are not infected "
        "by the virus, but may be altered, adding 4 to 30 bytes to their length. Infected .EXE files "
        "have a file length increase of 2,952 to 2,972 bytes. The virus is located at the end of the "
        "file. .EXE files which are not infected may be altered, adding 4 to 30 bytes to their length. "
        "The file's date and time in the DOS disk directory listing may have been updated to the current "
        "system date and time when the file was altered/infected."
    )
    
    entities, relations, attributes, triples = processor.process_text(text)

    # 输出结果
    print("Entities:")
    for entity in entities:
        print(entity)

    print("\nRelations:")
    for relation in relations:
        print(relation)

    print("\nAttributes:")
    for attribute in attributes:
        print(attribute)

    print("\nKnowledge Graph Triples:")
    for triple in triples:
        print(triple)
