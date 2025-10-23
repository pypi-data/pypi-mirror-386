class ruft:
    def is_a_noun_rule(self,s):
        tokens = nltk.word_tokenize(s)
        pos_tags = nltk.pos_tag(tokens)
        
        for i in range(len(pos_tags)-3):
            if pos_tags[i][1] == 'NN' and pos_tags[i+1][1] =='VBZ' and pos_tags[i+2][1] =='DT' and pos_tags[i+3][1] =='NN':
                return 'IF '+pos_tags[i+1][0]+' '+pos_tags[i+2][0]+' '+pos_tags[i+3][0]+' THEN '+pos_tags[i][0]
    
    def is_a_adj_noun_rule(self,s1):
        tokens = nltk.word_tokenize(s1)
        pos_tags = nltk.pos_tag(tokens)
        
        for i in range(len(pos_tags)-4):
            if pos_tags[i][1] == 'NN' and pos_tags[i+1][1] =='VBZ' and pos_tags[i+2][1] =='DT' and pos_tags[i+3][1] =='JJ' and pos_tags[i+4][1] =='NN':
                return 'IF '+pos_tags[i+1][0]+' '+pos_tags[i+2][0]+' '+pos_tags[i+3][0]+' '+pos_tags[i+4][0]+' THEN '+pos_tags[i][0]
    
    def is_adj_rule(self,s2):
        tokens = nltk.word_tokenize(s2)
        pos_tags = nltk.pos_tag(tokens)
        
        for i in range(len(pos_tags)-2):
            if pos_tags[i][1] == 'NN' and pos_tags[i+1][1] =='VBZ' and pos_tags[i+2][1] =='JJ':
                return 'IF '+pos_tags[i+1][0]+' '+pos_tags[i+2][0]+' THEN '+pos_tags[i][0]
    
    
    def nnp_vbd_vbn_in_nns_rule(self,s3):
        tokens = nltk.word_tokenize(s3)
        pos_tags = nltk.pos_tag(tokens)
        
        for i in range(len(pos_tags)):
            #print(pos_tags[i][1])
            if pos_tags[i][1] == 'NNP' and pos_tags[i+1][1] =='VBD' and pos_tags[i+2][1] =='VBN' and pos_tags[i+3][0] =='by' and pos_tags[i+4][1] =='NNPS':
                return 'IF '+pos_tags[i+1][0]+' '+pos_tags[i+2][0]+' '+pos_tags[i+3][0]+' '+pos_tags[i+4][0]+' THEN '+pos_tags[i][0]
    
    
    def nn_consists_of_nn_and_nn_rule(self,s4):
        tokens = nltk.word_tokenize(s4)
        pos_tags = nltk.pos_tag(tokens)
        
        for i in range(len(pos_tags)-5):
            if pos_tags[i][1] == 'NN' and pos_tags[i+1][0] =='consists' and pos_tags[i+2][0] =='of' and pos_tags[i+3][1] =='NN' and pos_tags[i+4][0] =='and' and pos_tags[i+5][1] =='NN':
                return 'IF '+pos_tags[i+1][0]+' '+pos_tags[i+2][0]+' '+pos_tags[i+3][0]+' '+pos_tags[i+4][0]+' '+pos_tags[i+5][0]+' THEN '+pos_tags[i][0]    

    def get_all_rules(self,ss):
        s=''
        t=''
        sent_text = nltk.sent_tokenize(ss)
        for sent in sent_text:
            print(sent)
            s=self.is_a_noun_rule(sent)   
            if s!=None: t+=str(s)+"\n"
            
            s=self.is_a_adj_noun_rule(sent) 
            if s!=None:t+=str(s)+"\n"
            
            s=self.is_adj_rule(sent) 
            if s!=None:t+=str(s)+"\n"
            
            s=self.nnp_vbd_vbn_in_nns_rule(sent) 
            if s!=None:t+=str(s)+"\n"
            
            s=self.nn_consists_of_nn_and_nn_rule(sent) 
            if s!=None:t+=str(s)+"\n"
        return t