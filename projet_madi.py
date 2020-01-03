import copy
import pyAgrum as gum
import pydotplus as dot

class FactorGraph(gum.UndiGraph):

    def __init__(self):
        gum.UndiGraph.__init__(self);
        self.node_type = dict();
        self.node = dict();
        self.bn = None

    def addVariable(self,v):
        node_id = self.addNode();
        self.node_type[node_id] = "variable";
        self.node[node_id] = v;
        # self.node[node_id].setName(str(node_id))
        return node_id;
    def addFactor(self,p):
        node_id = self.addNode();
        self.node_type[node_id] = "factor";
        self.node[node_id] = p;
        # self.node[node_id].setName(str(node_id))
        return node_id
        
    def build(self,bn):
        self.bn = bn
        # self.bn = copy.deepcopy(bn)
        # pour chaque node dans bn, on ajoute un node_variable dans gf
        for node_id in self.bn.nodes():
            node_id2 = self.addVariable(self.bn.variable(node_id))
        # ajout des edges correspondant aux edges de bn
        for u,v in self.bn.arcs(): # pour arc u-->v
            self.addEdge(u,v);
        # ajout des node_factors
        for node_id in self.bn.nodes():
            node_id_factor = self.addFactor(self.bn.cpt(node_id));
            parents_id = self.bn.parents(node_id);
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


class TreeSumProductInference:
    def __init__(self,fg):
        def ordre(fg):
            '''
            pour un arbre
            '''
            print("cycle ",fg.hasUndirectedCycle())
            assert not(fg.hasUndirectedCycle())
            nodes = list(fg.nodes());
            nb_voisins = [len(fg.neighbours(node)) for node in nodes]
            print(nb_voisins);
            ordre = [];
            while len(ordre) < len(nodes):
                if len(ordre) == len(nodes)-1:
                    for i in range(len(nodes)):
                        if nodes[i] not in ordre:
                            ordre.append(nodes[i])
                for i in range(len(nodes)):
                    if nb_voisins[i] == 1:
                        ordre.append(nodes[i]);
                        nb_voisins[i] = 0;
                        print(nb_voisins)
                        for j in range(len(nodes)):
                            if fg.existsEdge(nodes[i],nodes[j]):
                                nb_voisins[j] -= 1;
                        print(nb_voisins)
                        print("ordre ",ordre)
            return ordre;
        self.fg = fg;
        self.order = ordre(fg)
        # cpt received for every node
        self.dict_dict_cpt = dict();
        for node_id in self.fg.nodes():
            self.dict_dict_cpt[node_id] = dict();
            for node_id2 in self.fg.neighbours(node_id):
                self.dict_dict_cpt[node_id][node_id2] = None;

        # root 
        self.root_id = self.order[-1];
    
    def nodeMessage(self,node_id):            
        # un node message pour chaque voisin
        for node_id2 in self.fg.neighbours(node_id):
            # si on l'a deja envoye un message
            if self.dict_dict_cpt[node_id2][node_id] != None:
                continue;
            # init message
            message = 1;
            # pour tous les voisins sauf node_id2
            flag = True
            for node_id3 in self.fg.neighbours(node_id):
                # si c'est node_id2
                if node_id2 == node_id3:
                    continue;
                # MAJ message
                if self.dict_dict_cpt[node_id][node_id3] == None:
                    flag = False
                    break;
                    print("id2 = {} dict_dict_cpt[{}][{}] = None".format(node_id2,node_id,node_id3))
                if message == 1:
                    message = self.dict_dict_cpt[node_id][node_id3]
                else:
                    message = message * self.dict_dict_cpt[node_id][node_id3];
            if not(flag):
                continue;
            # envoie de message
            self.dict_dict_cpt[node_id2][node_id] = message;
            
    def factorMessage(self,node_id):
        # un factor message pour chaque voisin 
        for node_id2 in self.fg.neighbours(node_id):
            # si on l'a deja envoye un message
            if self.dict_dict_cpt[node_id2][node_id] != None:
                continue;
            # init message
            message = self.fg.node[node_id];
            # pour tous les voisins sauf node_id2
            flag = True
            for node_id3 in self.fg.neighbours(node_id):
                # si c'est node_id2
                if node_id2 == node_id3:
                    continue;
                # MAJ message
                if self.dict_dict_cpt[node_id][node_id3] == 1:
                    continue;
                else:
                    if self.dict_dict_cpt[node_id][node_id3] == None:
                        flag = False
                        break;
                        print("id2 = {} dict_dict_cpt[{}][{}] = None".format(node_id2,node_id,node_id3))
                    message = message * self.dict_dict_cpt[node_id][node_id3];
            if not(flag):
                continue;
            for name in message.var_names:
                if name != self.fg.node[node_id2].name():
                    message = message.margSumOut(name);
            # envoie de message
            self.dict_dict_cpt[node_id2][node_id] = message;
    
    def makeInference(self):
        for node_id in self.order:
            # if it's a node
            if self.fg.node_type[node_id] == "variable":
                self.nodeMessage(node_id);
            # if it's a factor
            if self.fg.node_type[node_id] == "factor":
                self.factorMessage(node_id);
        
        for node_id in reversed(self.order):
            # if it's a node
            if self.fg.node_type[node_id] == "variable":
                self.nodeMessage(node_id);
            # if it's a factor
            if self.fg.node_type[node_id] == "factor":
                self.factorMessage(node_id);
        
        #variable.name()
        #variable.setName(str)
    def posterior(self,node_id):
        assert self.fg.node_type[node_id] == "variable"
        cpt = None
        for cpt2 in self.dict_dict_cpt[node_id].values():
            if cpt == None:
                cpt = cpt2;
            else:
                cpt = cpt * cpt2;
        # sum
        for name in cpt.var_names:
            if self.fg.node[node_id].name() != name:
                cpt = cpt.margSumOut(name);
        
        return cpt;
        
        

    

        