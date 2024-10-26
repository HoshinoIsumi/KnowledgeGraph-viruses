
from py2neo import Graph, Node, Relationship,NodeMatcher

class DateToNeo4j(object):

    def __init__(self):
        link = Graph("http://localhost:7474", username="neo4j", password="20040113Ming@")
        self.graph = link
        #self.graph = NodeMatcher(link)
        #定义Label
        self.buy = 'buy'
        self.sell ='sell'
        self.graph.delete_all()
        self.matcher = NodeMatcher(link)