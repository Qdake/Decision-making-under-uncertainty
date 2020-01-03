import pyAgrum as gum
import pydotplus as dot

class FactorGraph(gum.UndiGraph):

    def __init__(self):
        gum.UndiGraph.__init__(self);
        self.node_type = dict();
        self.node = dict();
        self.bn = None
    # def addNode(self):
    #     return self.factor_graph.addNode();
    
    # def addEdge(self, n1, n2):
    #     self.factor_graph.addEdge(n1, n2);
        
    # def toDot(self):
    #     return self.factor_graph.toDot();
    
    
    def addVariable(self,v):
        node_id = self.addNode();
        self.node_type[node_id] = "variable";
        self.node[node_id] = v;
        return node_id;
    def addFactor(self,p):
        node_id = self.addNode();
        self.node_type[node_id] = "factor";
        self.node[node_id] = p;
        return node_id
        
    def build(self,bn):
        self.bn = bn
        self.factor_graph = gum.UndiGraph();
        # rappelle:
        # for i in bn.nodes():
        #     print("variable {} : {}".format(i,bn.variable(i)))
        #     print()
        # for i in bn.nodes():
        #     print("cpt {} : {}".format(i,bn.cpt(i)))
        # self.factor_graph = gum.UndiGraph()
        # ajout des nodes correspondant aux nodes de bn
        for node_id in bn.nodes():
            node_id2 = self.addVariable(bn.variable(node_id))
        # ajout des edges correspondant aux edges de bn
        for u,v in bn.arcs(): # pour arc u-->v
            self.addEdge(u,v);
        
        for node_id in bn.nodes():
            node_id_factor = self.addFactor(bn.cpt(node_id));
            parents_id = bn.parents(node_id);
            for node_id2 in parents_id:
                self.eraseEdge(node_id2, node_id);
                self.addEdge(node_id2,node_id_factor);
            self.addEdge(node_id_factor, node_id);
        
    def show(self):
        st = "graph FG {\n layout=neato; \n \n node [shape=rectangle,margin=0.04, \n width=0,height=0, style=filled,color=\"coral\"]\n \n"
        for node_id in self.nodes():
            if self.node_type[node_id] == "variable":
                st += (str(node_id) + ";");
        st += "\n\n     node [shape=point,width=0.1,height=0.1, style=filled,color=\"burlywood\"];\n"
                
        for node_id in self.nodes():
            if self.node_type[node_id] == "factor":
                st += (str(node_id) + ";");
        st += "\n\n"
        st += "edge [len=0.7];\n";
        for edge in self.edges():
            u,v = edge;
            st += str(u) + "--" + str(v) + "\n";
        st += "}"
        return st
bn = gum.fastBN("A->B<-C->D->E<-B")
fg = FactorGraph();
print(fg)
fg.build(bn)
print(fg)
st = fg.show();
print(st)

        