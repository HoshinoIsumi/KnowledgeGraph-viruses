import stanza

class TextProcessor:
    def __init__(self, language='en'):
        self.nlp = stanza.Pipeline(language, processors='tokenize,mwt,pos,lemma,depparse,ner')

    def process_text(self, text):
        doc = self.nlp(text)
        entities = self.extract_entities(doc)
        relations = self.extract_relations(doc)
        attributes = self.extract_attributes(doc)
        triples = self.build_triples(entities, relations, attributes)
        return entities, relations, attributes, triples

    def extract_entities(self, doc):
        unique_entities = {}
        for ent in doc.ents:
            unique_entities.setdefault(ent.text, set()).add(ent.type)
        return [(text, ', '.join(types)) for text, types in unique_entities.items()]

    def extract_relations(self, doc):
        relations = []
        for sentence in doc.sentences:
            for word in sentence.words:
                if word.deprel == 'nsubj':
                    subject = word.text
                    verb = self.get_root_relation(sentence)
                    obj = self.get_object_from_relation(word, sentence)
                    if verb and obj:
                        relations.append((subject, verb, obj))
        return relations

    def get_root_relation(self, sentence):
        for word in sentence.words:
            if word.deprel == 'root':
                return word.text
        return None

    def get_object_from_relation(self, word, sentence):
        for w in sentence.words:
            if w.head == word.id and w.deprel in ['obj', 'iobj']:
                return w.text
        return None

    def extract_attributes(self, doc):
        attributes = set()
        quantity_pairs = {}
        
        for sentence in doc.sentences:
            for word in sentence.words:
                if word.deprel == 'amod':
                    noun = self.get_noun_from_attribute(word, sentence)
                    if noun:
                        attributes.add((noun.text, word.text))

                if word.deprel == 'nummod':
                    noun = self.get_noun_from_nummod(word, sentence)
                    if noun:
                        quantity_pairs[noun.text] = word.text

        for noun, quantity in quantity_pairs.items():
            attributes.add((noun, quantity))
        
        return list(attributes)

    def get_noun_from_attribute(self, adjective, sentence):
        for word in sentence.words:
            if word.id == adjective.head and word.deprel in ['nsubj', 'obj', 'nmod']:
                return word
        return None

    def get_noun_from_nummod(self, number, sentence):
        for word in sentence.words:
            if word.id == number.head and word.deprel in ['nsubj', 'obj', 'nmod']:
                return word
        return None

    def build_triples(self, entities, relations, attributes):
        triples = []
        
        for entity in entities:
            for entity_type in entity[1].split(', '):
                triples.append((entity[0], "is_a", entity_type.strip()))

        for relation in relations:
            triples.append(relation)

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
