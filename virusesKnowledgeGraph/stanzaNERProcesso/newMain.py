import json
import re
import stanza
import logging
from neo4j import GraphDatabase
import argparse

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Stanza pipeline
stanza.download('en', processors='tokenize,mwt,pos,lemma,depparse,ner', verbose=False)
NLP_PIPELINE = stanza.Pipeline(lang='en', processors='tokenize,mwt,pos,lemma,depparse,ner', verbose=False)

def load_virus_data(file_path):
    """
    Load virus data from a JSONL file line by line using a generator.

    :param file_path: Path to the input JSONL file.
    :yield: Parsed JSON object for each line.
    """
    try:
        with open(file_path, 'r') as file:
            for line in file:
                yield json.loads(line.strip())
    except Exception as e:
        logging.error(f"Error loading data from {file_path}: {e}")

def extract_virus_characteristics(virus_characteristics):
    """
    Extract symptoms and file length increases from virus characteristics text.

    :param virus_characteristics: String containing virus characteristics.
    :return: Tuple of symptoms (str) and file length increases (dict).
    """
    try:
        # Extract symptoms
        symptoms_start = virus_characteristics.find("Symptoms")
        infected_start = virus_characteristics.find("Infected")
        symptoms = (
            virus_characteristics[symptoms_start + 8:infected_start].strip()
            if symptoms_start != -1 and infected_start != -1 else "N/A"
        )

        # Extract file length increases
        file_length_increases = {}
        for line in virus_characteristics.splitlines():
            if "file length increase" in line:
                parts = line.split()
                if len(parts) >= 6:
                    file_length_increases[parts[1]] = parts[-1]
        return symptoms, file_length_increases
    except Exception as e:
        logging.error(f"Error extracting virus characteristics: {e}")
        return "N/A", {}

def extract_entities_relations_attributes(text):
    """
    Extract entities, relations, and attributes from text using Stanza.

    :param text: Text to process.
    :return: Tuple of entities (list), relations (list), attributes (list).
    """
    entities, relations, attributes = [], [], []
    try:
        doc = NLP_PIPELINE(text)
        for sentence in doc.sentences:
            # Extract entities
            for ent in sentence.ents:
                if ent.type in {"ORG", "PRODUCT", "QUANTITY", "CARDINAL", "DISEASE"}:
                    entities.append((ent.text, ent.type))

            # Extract relations and attributes
            for word in sentence.words:
                # Attributes
                if word.text.lower() in {"infected", "available", "free", "active", "malicious"}:
                    attributes.append((word.text.lower(), "status"))
                if word.text.lower() == "bytes" and word.head != word.id:
                    size_value = sentence.words[word.head - 1].text
                    attributes.append(("size", size_value))

                # Relations
                if word.deprel in {"obj", "nmod", "obl", "nsubj", "nsubjpass"}:
                    head_word = sentence.words[word.head - 1]
                    if head_word.upos == "VERB" or head_word.deprel == "root":
                        relations.append((head_word.text, head_word.lemma, word.text))
    except Exception as e:
        logging.error(f"Error extracting entities, relations, and attributes: {e}")
    return entities, relations, attributes

def create_knowledge_graph_in_neo4j(triples, uri, user, password):
    """
    Insert triples into Neo4j knowledge graph using batch operations.

    :param triples: List of triples (subject, relation, object).
    :param uri: Neo4j URI.
    :param user: Neo4j username.
    :param password: Neo4j password.
    """
    def normalize_relation_name(rel):
        return re.sub(r'[^a-zA-Z0-9_]', '_', rel).upper()

    try:
        with GraphDatabase.driver(uri, auth=(user, password)) as driver:
            with driver.session() as session:
                def batch_insert(triples_batch):
                    query = """
                    UNWIND $triples as triple
                    MERGE (a:Entity {name: triple.subject})
                    MERGE (b:Entity {name: triple.object})
                    MERGE (a)-[:`has_relation` {type: triple.relation}]->(b)
                    """
                    session.run(query, triples=[
                        {"subject": subj, "relation": normalize_relation_name(rel), "object": obj}
                        for subj, rel, obj in triples_batch
                    ])

                batch_size = 100
                for i in range(0, len(triples), batch_size):
                    batch_insert(triples[i:i + batch_size])
    except Exception as e:
        logging.error(f"Error inserting into Neo4j: {e}")

def build_knowledge_graph(data, output_file, neo4j_uri, neo4j_user, neo4j_password):
    """
    Build knowledge graph from virus data and save triples to a file and Neo4j.

    :param data: Virus data generator.
    :param output_file: Path to output file for saving triples.
    :param neo4j_uri: Neo4j URI.
    :param neo4j_user: Neo4j username.
    :param neo4j_password: Neo4j password.
    """
    try:
        with open(output_file, 'w') as file:
            for entry in data:
                virus_name = entry.get("virus_name", "Unknown")
                if virus_name == "Unknown":
                    continue  # Skip entries without a virus name

                # Base triples
                triples = [(virus_name, "is_a", "Virus")]

                # Add basic attributes
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
                triples.extend([(virus_name, f"has_{attr}", value) for attr, value in attributes if value])

                # Extract virus characteristics
                symptoms, file_length_increases = extract_virus_characteristics(entry.get("virus_characteristics", ""))
                triples.append((virus_name, "has_symptoms", symptoms))
                triples.extend([
                    (virus_name, f"{file_type.replace('-', '_')}_length_increase", length)
                    for file_type, length in file_length_increases.items()
                ])

                # Extract entities, relations, and attributes
                entities, relations, attributes = extract_entities_relations_attributes(entry.get("virus_characteristics", ""))
                triples.extend([(entity[0], "is_a", entity[1]) for entity in entities])
                triples.extend([(attr[0], "has", attr[1]) for attr in attributes])
                triples.extend(relations)

                # Write triples to file
                for subj, rel, obj in triples:
                    file.write(json.dumps({"subject": subj, "relation": rel, "object": obj}) + '\n')

                # Insert triples into Neo4j
                create_knowledge_graph_in_neo4j(triples, neo4j_uri, neo4j_user, neo4j_password)

                logging.info(f"Processed virus: {virus_name}")
    except Exception as e:
        logging.error(f"Error building knowledge graph: {e}")

def main():
    parser = argparse.ArgumentParser(description="Build Virus Knowledge Graph")
    parser.add_argument('--input_file', type=str, required=True, help='Path to input JSON file')
    parser.add_argument('--output_file', type=str, required=True, help='Path to output JSON file')
    parser.add_argument('--neo4j_uri', type=str, default='bolt://localhost:7687', help='Neo4j URI')
    parser.add_argument('--neo4j_user', type=str, default='neo4j', help='Neo4j username')
    parser.add_argument('--neo4j_password', type=str, help='Neo4j password')
    parser.add_argument('--output_to_file', action='store_true', help='Output triples to a JSON file')
    parser.add_argument('--insert_into_neo4j', action='store_true', help='Insert triples into Neo4j')
    parser.add_argument('--config_file', type=str, help='Optional configuration file in JSON format')

    args = parser.parse_args()

    # Load configuration from file if specified
    if args.config_file:
        try:
            with open(args.config_file, 'r') as config_file:
                config = json.load(config_file)
                args.input_file = config.get("input_file", args.input_file)
                args.output_file = config.get("output_file", args.output_file)
                args.neo4j_uri = config.get("neo4j_uri", args.neo4j_uri)
                args.neo4j_user = config.get("neo4j_user", args.neo4j_user)
                args.neo4j_password = config.get("neo4j_password", args.neo4j_password)
                args.output_to_file = config.get("output_to_file", args.output_to_file)
                args.insert_into_neo4j = config.get("insert_into_neo4j", args.insert_into_neo4j)
        except Exception as e:
            logging.error(f"Error reading configuration file: {e}")
            return

    # Validate inputs
    if not args.input_file or not args.output_file:
        logging.error("Input and output files must be specified.")
        return

    if args.insert_into_neo4j and not args.neo4j_password:
        logging.error("Neo4j password is required for database insertion.")
        return

    # Load virus data
    data = load_virus_data(args.input_file)

    # Perform operations based on user inputs
    if args.output_to_file or args.insert_into_neo4j:
        build_knowledge_graph(
            data,
            output_file=args.output_file if args.output_to_file else None,
            neo4j_uri=args.neo4j_uri if args.insert_into_neo4j else None,
            neo4j_user=args.neo4j_user if args.insert_into_neo4j else None,
            neo4j_password=args.neo4j_password if args.insert_into_neo4j else None,
        )
    else:
        logging.info("No operation specified. Use --output_to_file or --insert_into_neo4j.")
        
if __name__ == "__main__":
    main()
    
