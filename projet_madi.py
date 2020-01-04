import copy
import pyAgrum as gum
import pydotplus as dot

class FactorGraph(gum.UndiGraph):

    def __init__(self):
        # init super classe
        gum.UndiGraph.__init__(self);
        # dictionnaire pour stocker le type de chaque noeud   { int node_id : str node_type }
        self.node_type = dict();
        # dictionnaire pour stocker le contenu d'un noeud:  
        # gum.DiscreteVariable si le noeud est de type variable, et gum.Potential si de type factor
        self.node = dict();
        # init
        self.bn = None

    def addVariable(self,v):
        # créer un noeud
        node_id = self.addNode();
        # stocker le type du noeud dans un dictionaire
        self.node_type[node_id] = "variable";
        # stoker le contenu du noeud
        self.node[node_id] = v;
        # self.node[node_id].setName(str(node_id))
        return node_id;
    def addFactor(self,p):
        # créer un noeud
        node_id = self.addNode();
        # stocker le type du noeud
        self.node_type[node_id] = "factor";
        #  stocker le contenu du noeud
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
            # trouver tous les noeuds qui sont parents du noeud dans bn
            parents_id = self.bn.parents(node_id);
            # ajout et supprime des arêtes
            for node_id2 in parents_id:
                self.eraseEdge(node_id2, node_id);
                self.addEdge(node_id2,node_id_factor);
            self.addEdge(node_id_factor, node_id);
        
    def show(self):
        #  produit une chqine de caractère pour afficher le graphe au format DOT 
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
            # cette methode d'inference fonctionne seulement pour les arebres
            assert not(fg.hasUndirectedCycle())
            # trouver un ordre pour l'envoie des messages
            # par les noeuds de degree croissante
            nodes = list(fg.nodes());  
            nb_voisins = [len(fg.neighbours(node)) for node in nodes]
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
                        for j in range(len(nodes)):
                            if fg.existsEdge(nodes[i],nodes[j]):
                                nb_voisins[j] -= 1;
            return ordre;
        
        self.fg = fg;
        # fixer un ordre pour l'envoie des messages
        self.order = ordre(fg)
        # cpt received for every node:    { node1 : { node2 : cpt }  } pour node1 received cpt from node2  
        self.dict_dict_cpt = dict(); 
        for node_id in self.fg.nodes():
            self.dict_dict_cpt[node_id] = dict();
            for node_id2 in self.fg.neighbours(node_id):
                self.dict_dict_cpt[node_id][node_id2] = None;

        # root de l'arbre
        self.root_id = self.order[-1];
    
    def nodeMessage(self,node_id):            
        # un node message pour chaque voisin
        for node_id2 in self.fg.neighbours(node_id):
            # si on l'a deja envoye un message
            if self.dict_dict_cpt[node_id2][node_id] != None:
                continue;
            # message est en fait cpt a envoyer
            message = 1;
            # pour tous les voisins sauf node_id2
            flag = True
            for node_id3 in self.fg.neighbours(node_id):
                # si c'est node_id2
                if node_id2 == node_id3:
                    continue;
                # si node_id ne peut pas envoyer de message a node2, i.e. il mqnaue un message d'un noeud node_id3
                if self.dict_dict_cpt[node_id][node_id3] == None:
                    flag = False
                    break;
                # si node_id3 est un neoud_variable feuille, alors on n'a pas besoin de MAJ le message
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
                # si node_id ne peut pas envoyer de message a node2, i.e. il mqnaue un message d'un noeud node_id3
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
        # message vers la racine
        for node_id in self.order:
            # si le noeud est de type "variable"
            if self.fg.node_type[node_id] == "variable":
                self.nodeMessage(node_id);
            # si le noeud est de type "factor"
            if self.fg.node_type[node_id] == "factor":
                self.factorMessage(node_id);
        # message vers les feuilles
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
        # calculer la probabilite jointe
        cpt = None
        for cpt2 in self.dict_dict_cpt[node_id].values():
            if cpt == None:
                cpt = cpt2;
            else:
                cpt = cpt * cpt2;
        # calculer la probabilite marginale
        for name in cpt.var_names:
            if self.fg.node[node_id].name() != name:
                cpt = cpt.margSumOut(name);
        
        return cpt;
        
        
# class LBPSumProductInference:
#     def __init__(self,fg):
#         # def ordre(fg):
#         #     '''
#         #     pour un arbre
#         #     '''
#         #     # cette methode d'inference fonctionne seulement pour les arebres
#         #     assert not(fg.hasUndirectedCycle())
#         #     # trouver un ordre pour l'envoie des messages
#         #     # par les noeuds de degree croissante
#         #     nodes = list(fg.nodes());  
#         #     nb_voisins = [len(fg.neighbours(node)) for node in nodes]
#         #     ordre = [];
#         #     while len(ordre) < len(nodes):
#         #         if len(ordre) == len(nodes)-1:
#         #             for i in range(len(nodes)):
#         #                 if nodes[i] not in ordre:
#         #                     ordre.append(nodes[i])
#         #         for i in range(len(nodes)):
#         #             if nb_voisins[i] == 1:
#         #                 ordre.append(nodes[i]);
#         #                 nb_voisins[i] = 0;
#         #                 for j in range(len(nodes)):
#         #                     if fg.existsEdge(nodes[i],nodes[j]):
#         #                         nb_voisins[j] -= 1;
#         #     return ordre;
        
#         self.fg = fg;
#         # fixer un ordre pour l'envoie des messages
#         self.order = self.fg.nodes();
#         # cpt received for every node:    { node1 : { node2 : cpt }  } pour node1 received cpt from node2  
#         self.dict_dict_cpt = dict(); 
#         for node_id in self.fg.nodes():
#             self.dict_dict_cpt[node_id] = dict();
#             for node_id2 in self.fg.neighbours(node_id):
#                 if self.fg.node_type[node_id2] == "variable":
#                     self.dict_dict_cpt[node_id][node_id2] = 1;
#                 if self.fg.node_type[node_id2] == "factor":
#                     self.dict_dict_cpt[node_id][node_id2] = self.fg.node[node_id2];

#         # root de l'arbre
#         # self.root_id = self.order[-1];
    
#     def nodeMessage(self,node_id) -> bool:            
#         # un node message pour chaque voisin
#         for node_id2 in self.fg.neighbours(node_id):
#             # si on l'a deja envoye un message
#             # if self.dict_dict_cpt[node_id2][node_id] != None:
#             #     continue;
#             # message est en fait cpt a envoyer
#             message = 1;
#             # pour tous les voisins sauf node_id2
#             # flag = True
#             for node_id3 in self.fg.neighbours(node_id):
#                 # si c'est node_id2
#                 if node_id2 == node_id3:
#                     continue;
#                 # si node_id ne peut pas envoyer de message a node2, i.e. il mqnaue un message d'un noeud node_id3
#                 # if self.dict_dict_cpt[node_id][node_id3] == None:
#                 #     flag = False
#                 #     break;
                    
#                 # si node_id3 est un neoud_variable feuille, alors on n'a pas besoin de MAJ le message
#                 if message == 1:
#                     message = self.dict_dict_cpt[node_id][node_id3]
#                 else:
#                     message = message * self.dict_dict_cpt[node_id][node_id3];
#             # if not(flag):
#             #     continue;
#             # envoie de message
#             if self.dict_dict_cpt[node_id2][node_id] != message:
#                 self.dict_dict_cpt[node_id2][node_id] = message;
#                 return True;
#             else:
#                 return False;
#     def factorMessage(self,node_id) -> bool:
#         # un factor message pour chaque voisin 
#         for node_id2 in self.fg.neighbours(node_id):
#             # si on l'a deja envoye un message
#             # if self.dict_dict_cpt[node_id2][node_id] != None:
#             #     continue;
#             # init message
#             message = self.fg.node[node_id];
#             # pour tous les voisins sauf node_id2
#             # flag = True
#             for node_id3 in self.fg.neighbours(node_id):
#                 # si c'est node_id2
#                 if node_id2 == node_id3:
#                     continue;
#                 # si node_id ne peut pas envoyer de message a node2, i.e. il mqnaue un message d'un noeud node_id3
#                 if self.dict_dict_cpt[node_id][node_id3] == 1:
#                     continue;
#                 else:
#                 #     if self.dict_dict_cpt[node_id][node_id3] == None:
#                 #         flag = False
#                 #         break;
#                     message = message * self.dict_dict_cpt[node_id][node_id3];
#             # if not(flag):
#             #     continue;
#             for name in message.var_names:
#                 if name != self.fg.node[node_id2].name():
#                     message = message.margSumOut(name);
#             # envoie de message
#             if self.dict_dict_cpt[node_id2][node_id] != message:
#                 self.dict_dict_cpt[node_id2][node_id] = message;
#                 return True;
#             else:
#                 return False;

#     def makeInference(self):
        
#         # message vers la racine
#         flag = True;
#         while flag:
#             flag = False;
#             for node_id in self.order:
#                 # si le noeud est de type "variable"
#                 if self.fg.node_type[node_id] == "variable":
#                     flag = flag or self.nodeMessage(node_id);
#                 # si le noeud est de type "factor"
#                 if self.fg.node_type[node_id] == "factor":
#                     flag = flag or self.factorMessage(node_id);
#         # message vers les feuilles
#         # for node_id in reversed(self.order):
#         #     # if it's a node
#         #     if self.fg.node_type[node_id] == "variable":
#         #         self.nodeMessage(node_id);
#         #     # if it's a factor
#         #     if self.fg.node_type[node_id] == "factor":
#         #         self.factorMessage(node_id);
        
#         #variable.name()
#         #variable.setName(str)
#     def posterior(self,node_id):
#         assert self.fg.node_type[node_id] == "variable"
#         # calculer la probabilite jointe
#         cpt = None
#         for cpt2 in self.dict_dict_cpt[node_id].values():
#             if cpt == None:
#                 cpt = cpt2;
#             else:
#                 cpt = cpt * cpt2;
#         # calculer la probabilite marginale
#         for name in cpt.var_names:
#             if self.fg.node[node_id].name() != name:
#                 cpt = cpt.margSumOut(name);
        
#         return cpt;
        
    
class LBPSumProductInference:
    def __init__(self,fg):
        def ordre(fg):
            # '''
            # pour un arbre
            # '''
            # # cette methode d'inference fonctionne seulement pour les arebres
            # assert not(fg.hasUndirectedCycle())
            # # trouver un ordre pour l'envoie des messages
            # # par les noeuds de degree croissante
            # nodes = list(fg.nodes());  
            # nb_voisins = [len(fg.neighbours(node)) for node in nodes]
            # ordre = [];
            # while len(ordre) < len(nodes):
            #     if len(ordre) == len(nodes)-1:
            #         for i in range(len(nodes)):
            #             if nodes[i] not in ordre:
            #                 ordre.append(nodes[i])
            #     for i in range(len(nodes)):
            #         if nb_voisins[i] == 1:
            #             ordre.append(nodes[i]);
            #             nb_voisins[i] = 0;
            #             for j in range(len(nodes)):
            #                 if fg.existsEdge(nodes[i],nodes[j]):
            #                     nb_voisins[j] -= 1;
            # return ordre;
            return list(fg.nodes());
        
        self.fg = fg;
        # fixer un ordre pour l'envoie des messages
        self.order = ordre(fg)
        # cpt received for every node:    { node1 : { node2 : cpt }  } pour node1 received cpt from node2  
        self.dict_dict_cpt = dict(); 
        for node_id in self.fg.nodes():
            self.dict_dict_cpt[node_id] = dict();
            for node_id2 in self.fg.neighbours(node_id):
                self.dict_dict_cpt[node_id][node_id2] = None;

        # root de l'arbre
        self.root_id = self.order[-1];
    
    def nodeMessage(self,node_id):            
        # un node message pour chaque voisin
        for node_id2 in self.fg.neighbours(node_id):
            # si on l'a deja envoye un message
            if self.dict_dict_cpt[node_id2][node_id] != None:
                continue;
            # message est en fait cpt a envoyer
            message = 1;
            # pour tous les voisins sauf node_id2
            # flag = True
            for node_id3 in self.fg.neighbours(node_id):
                # si c'est node_id2
                if node_id2 == node_id3:
                    continue;
                # si node_id ne peut pas envoyer de message a node2, i.e. il mqnaue un message d'un noeud node_id3
                # if self.dict_dict_cpt[node_id][node_id3] == None:
                #     flag = False
                #     break;
                # si node_id3 est un neoud_variable feuille, alors on n'a pas besoin de MAJ le message
                if message == 1:
                    message = self.dict_dict_cpt[node_id][node_id3]
                else:
                    message = message * self.dict_dict_cpt[node_id][node_id3];
            # if not(flag):
                # continue;
            # envoie de message
            if self.dict_dict_cpt[node_id2][node_id] == message:
                return False;
            else:
                self.dict_dict_cpt[node_id2][node_id] = message;
                return True
            
    def factorMessage(self,node_id):
        # un factor message pour chaque voisin 
        for node_id2 in self.fg.neighbours(node_id):
            # si on l'a deja envoye un message
            if self.dict_dict_cpt[node_id2][node_id] != None:
                continue;
            # init message
            message = self.fg.node[node_id];
            # pour tous les voisins sauf node_id2
            # flag = True
            for node_id3 in self.fg.neighbours(node_id):
                # si c'est node_id2
                if node_id2 == node_id3:
                    continue;
                # si node_id ne peut pas envoyer de message a node2, i.e. il mqnaue un message d'un noeud node_id3
                if self.dict_dict_cpt[node_id][node_id3] == 1:
                    continue;
                else:
                    # if self.dict_dict_cpt[node_id][node_id3] == None:
                        # flag = False
                        # break;
                        # print("id2 = {} dict_dict_cpt[{}][{}] = None".format(node_id2,node_id,node_id3))
                    message = message * self.dict_dict_cpt[node_id][node_id3];
            # if not(flag):
                # continue;
            for name in message.var_names:
                if name != self.fg.node[node_id2].name():
                    message = message.margSumOut(name);
            # envoie de message
            if self.dict_dict_cpt[node_id2][node_id] == message:
                return False;
            else:
                self.dict_dict_cpt[node_id2][node_id] = message;
                return True
    
    def makeInference(self):
        
        for node_id in self.fg.nodes():
            self.dict_dict_cpt[node_id] = dict();
            for node_id2 in self.fg.neighbours(node_id):
                if self.fg.node_type[node_id2] == "variable":
                    self.dict_dict_cpt[node_id][node_id2] = 1;
                if self.fg.node_type[node_id2] == "factor":
                    self.dict_dict_cpt[node_id][node_id2] = self.fg.node[node_id2];
                    
        flag = True;
        while flag:
            flag = False;
            # message vers la racine
            for node_id in self.order:
                # si le noeud est de type "variable"
                if self.fg.node_type[node_id] == "variable":
                    flag = flag or self.nodeMessage(node_id);
                # si le noeud est de type "factor"
                if self.fg.node_type[node_id] == "factor":
                    flag = flag or self.factorMessage(node_id);
            # message vers les feuilles
            # for node_id in reversed(self.order):
            #     # if it's a node
            #     if self.fg.node_type[node_id] == "variable":
            #         flag = flag or self.nodeMessage(node_id);
            #     # if it's a factor
            #     if self.fg.node_type[node_id] == "factor":
            #         flag = flag or self.factorMessage(node_id);
        
        
        #variable.name()
        #variable.setName(str)
    def posterior(self,node_id):
        assert self.fg.node_type[node_id] == "variable"
        # calculer la probabilite jointe
        cpt = None
        for cpt2 in self.dict_dict_cpt[node_id].values():
            if cpt == None:
                cpt = cpt2;
            else:
                cpt = cpt * cpt2;
        # calculer la probabilite marginale
        for name in cpt.var_names:
            if self.fg.node[node_id].name() != name:
                cpt = cpt.margSumOut(name);
        
        return cpt.normalize();
    

        