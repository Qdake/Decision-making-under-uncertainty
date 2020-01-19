import pyAgrum as gum
from projet_madi import * 
import numpy as np

debug = False
class TreeMaxProductInference:
    def __init__(self,fg):
        self.fg = fg.copy();
        # fixer un ordre pour l'envoie des messages
        self.order = None
        # cpt received for every node:    { node1 : { node2 : cpt }  } pour node1 received cpt from node2  
        self.dict_dict_cpt = dict(); 
        # root de l'arbre
        self.root_id = None
    
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
                    if debug:
                        print("node {} envoie un message de type **{}** au node_factor {}".format(node_id,type(message),node_id2))
                else:
                    #####################  calcul message ################################
                    message = message * self.dict_dict_cpt[node_id][node_id3];
                    # m = self.dict_dict_cpt[node_id][node_id3]

                    # cpt1 = gum.Potential()
                    # cpt1.add(self.fg.node[node_id]);
                    # name_id = self.fg.node[node_id].name();

                    # cpt1(name_id)[0] = message[0]*m[0];
                    # cpt1(name_id)[1] = message[1]*m[1];

                    # message = cpt1;

                    # if debug:
                    #     print("node {} envoie un message de type **{}** au node_factor {}".format(name_id,type(message),node_id2))
                    ######################################################################
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
                        #print("id2 = {} dict_dict_cpt[{}][{}] = None".format(node_id2,node_id,node_id3))
                    if debug:
                        print("type of message ",type(message), "type of dictdict {}".format(type(self.dict_dict_cpt[node_id][node_id3])))
                    if debug:
                        print("node_factor {} envoie un message de type **{}** au node_variable {}".format(node_id,type(message),node_id2))
                    message = message * self.dict_dict_cpt[node_id][node_id3];
            if not(flag):
                continue;

            ############################### max ######################  
            for name in message.var_names:
                if name != self.fg.node[node_id2].name():
                    message = message.margSumOut(name);

            argmax = message.argmax();
            maxvalue = message.max();

            ###########################################################
            # envoie de message
            self.dict_dict_cpt[node_id2][node_id] = message;
    
    def makeInference(self):
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
        
        self.order = ordre(self.fg)
        # cpt received for every node:    { node1 : { node2 : cpt }  } pour node1 received cpt from node2  
        for node_id in self.fg.nodes():
            self.dict_dict_cpt[node_id] = dict();
            for node_id2 in self.fg.neighbours(node_id):
                self.dict_dict_cpt[node_id][node_id2] = None;

        # root de l'arbre
        self.root_id = self.order[-1];
        
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

    def argmax(self):
        res = dict();
        for node_id in self.fg.nodes():
            if self.fg.node_type[node_id] == "variable":
                re = self.posterior(node_id);
                for key,value in re.items():
                    res[key] = value;
        return res;
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
        
        return cpt.argmax()[0]

    def addEvidence(self,evidence):
        for name,label in evidence.items():
            # print("name {} label {}".format(name,label));
            for node_id in self.fg.nodes():
                if self.fg.node_type[node_id] == "factor":
                    continue;
                if self.fg.node[node_id].name() != name:
                    continue;
                
                # print("dingdingding node_id= {}  name = {}  ".format(node_id,self.fg.node[node_id].name())) 
                cpt = gum.Potential().add(self.fg.node[node_id]);
                cpt.fillWith(0);
                cpt[label] = 1;
                node_id_factor = self.fg.addFactor(cpt);
                self.fg.addEdge(node_id ,node_id_factor)
                
                break;


class LBPMaxProductInference:
    def __init__(self,fg):
        self.fg = fg.copy();
        # fixer un ordre pour l'envoie des messages
        self.order = None
        # cpt received for every node:    { node1 : { node2 : cpt }  } pour node1 received cpt from node2  
        self.dict_dict_cpt = dict(); 
        # root de l'arbre
        self.root_id = None
    
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
                    if debug:
                        print("node {} envoie un message de type **{}** au node_factor {}".format(node_id,type(message),node_id2))
                else:
                    #####################  calcul message ################################
                    message = message * self.dict_dict_cpt[node_id][node_id3];
                    # m = self.dict_dict_cpt[node_id][node_id3]

                    # cpt1 = gum.Potential()
                    # cpt1.add(self.fg.node[node_id]);
                    # name_id = self.fg.node[node_id].name();

                    # cpt1(name_id)[0] = message[0]*m[0];
                    # cpt1(name_id)[1] = message[1]*m[1];

                    # message = cpt1;

                    # if debug:
                    #     print("node {} envoie un message de type **{}** au node_factor {}".format(name_id,type(message),node_id2))
                    ######################################################################
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
                        #print("id2 = {} dict_dict_cpt[{}][{}] = None".format(node_id2,node_id,node_id3))
                    if debug:
                        print("type of message ",type(message), "type of dictdict {}".format(type(self.dict_dict_cpt[node_id][node_id3])))
                    if debug:
                        print("node_factor {} envoie un message de type **{}** au node_variable {}".format(node_id,type(message),node_id2))
                    message = message * self.dict_dict_cpt[node_id][node_id3];
            if not(flag):
                continue;

            ############################### max ######################  
            for name in message.var_names:
                if name != self.fg.node[node_id2].name():
                    message = message.margSumOut(name);

            argmax = message.argmax();
            maxvalue = message.max();

            ###########################################################
            # envoie de message
            self.dict_dict_cpt[node_id2][node_id] = message;
    
    def makeInference(self):
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
        
        self.order = ordre(self.fg)
        # cpt received for every node:    { node1 : { node2 : cpt }  } pour node1 received cpt from node2  
        for node_id in self.fg.nodes():
            self.dict_dict_cpt[node_id] = dict();
            for node_id2 in self.fg.neighbours(node_id):
                self.dict_dict_cpt[node_id][node_id2] = None;

        # root de l'arbre
        self.root_id = self.order[-1];
        
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

    def argmax(self):
        res = dict();
        for node_id in self.fg.nodes():
            if self.fg.node_type[node_id] == "variable":
                re = self.posterior(node_id);
                for key,value in re.items():
                    res[key] = value;
        return res;
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
        
        return cpt.argmax()[0]

    def addEvidence(self,evidence):
        for name,label in evidence.items():
            # print("name {} label {}".format(name,label));
            for node_id in self.fg.nodes():
                if self.fg.node_type[node_id] == "factor":
                    continue;
                if self.fg.node[node_id].name() != name:
                    continue;
                
                # print("dingdingding node_id= {}  name = {}  ".format(node_id,self.fg.node[node_id].name())) 
                cpt = gum.Potential().add(self.fg.node[node_id]);
                cpt.fillWith(0);
                cpt[label] = 1;
                node_id_factor = self.fg.addFactor(cpt);
                self.fg.addEdge(node_id ,node_id_factor)
                
                break;
