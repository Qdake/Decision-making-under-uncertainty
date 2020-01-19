
def buildLDPC(bits,parity):
      bn=gum.BayesNet('LDPC')
      
      for variable in bits:
          bn.add(gum.LabelizedVariable(variable,variable,2))

      for variable in parity.keys():
          bn.add(gum.LabelizedVariable(variable,variable,2))

      for node_1 in parity.keys():    
          for node_2 in parity[node_1]:
              bn.addArc(node_2,node_1)

      return bn        


#Pour la tester avec l'exemple du proph 

#Test de la fonction LDPC
bits=['x1','x2','x3']
parity={'pc1':['x1','x2'],'pc2':['x1','x2','x3']}

bn1 = buildLDPC(bits,parity)
bn1
