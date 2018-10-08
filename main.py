from graphviz import Graph, nohtml
import couchdb
import json
import sys


class DB:
    url = 'http://localhost:5984'
    db_name = 'vl_db'

    def __init__(self):

        try:
            db_srv = couchdb.Server(self.url)
            self.db = db_srv[self.db_name]

        except Exception as inst:
            msg = "database problem"
            sys.exit(msg)

    def get_doc(self, _id):
        
        try:
            doc = self.db[_id]
        except Exception as inst:
            msg = "doc problem"
            sys.exit(msg)
        
        return doc

class Draw:

    def __init__(self, mpd_doc):

        self.g =  Graph('structs', format='pdf')#Digraph('structs', filename='mpd', engine='dot')
        self.g.attr(rankdir='TB')
        self.g.node_attr.update( fontsize='80')
        self.mpd = mpd_doc.get('Mp', {})
        self.name = self.mpd.get('Name').replace(' ','_')
        self.definitions = self.mpd.get('Definitions', [])
        self.container = self.mpd.get('Container', [])
        self.C = len(self.container)
        self.D = len(self.definitions)
        self.dc_dict={}

    def loop_all(self):

        self.make_mpd_node(self.mpd, 'Name')
        
        for defin_i, defin in enumerate(self.definitions):
            dc = defin.get('DefinitionClass')
            
            if dc in self.dc_dict:
                self.dc_dict[dc].append(defin_i)
            else:
                self.dc_dict[dc]= [defin_i]

        for defin_i, defin in enumerate(self.definitions):
            dc = defin.get('DefinitionClass')
            defin_token = "defin_{}_{}".format(dc, defin_i)
            self.make_defin_node(defin, defin_token)
            for seq_i, steps in enumerate(defin.get('Definition')):
                for par_i, step in enumerate(steps):
                    task_token = "defin_step_{}_{}_{}".format(defin_i, seq_i, par_i)
                    self.make_task_node( step, task_token)
                    self.g.edge(defin_token, task_token)

       

        for cont_i, cont in enumerate(self.container):
            cont_token = "cont_{}".format(cont_i)
            self.g.edge('Name',  cont_token)
            self.make_container_node(cont, cont_token)
            for seq_i, steps in enumerate(cont.get('Definition')):
                for par_i, step in enumerate(steps):
                    task_token = "cont_step_{}_{}_{}".format(cont_i,seq_i,par_i)
                    self.make_task_node(step, task_token)
                    if seq_i == 0:
                        self.g.edge(cont_token, task_token)
                    else:
                        self.g.edge( "cont_step_{}_{}_{}".format(cont_i,seq_i-1,0), task_token)

    def safe_label(self, label):
        
        label = str(label)
        label = label.replace(">", "[greater than]")
        label = label.replace("<", "[less than]")

        return label

    def make_defin_node(self, defin, token):
        name = defin.get('DefinitionClass')
        condition = defin.get('Condition')
        descr = defin.get('ShortDescr')
        label_body = "<TR><TD>definition class: <b>{}</b></TD></TR>".format(self.safe_label(name))
        label_start="<<TABLE BORDER='5' CELLBORDER='5' CELLSPACING='10'>"
        label_end = "</TABLE>>"
        for cond in condition:
            a = cond.get('ExchangePath')
            b = cond.get('Methode')
            c = cond.get('Value')
            label_body = "{}<TR><TD>ExchPath:  <b>{}</b></TD></TR> <TR><TD>operator: <b>{}</b></TD></TR> <TR><TD>Value:  <b>{}</b></TD></TR>".format(label_body, a, b, c)
        
        label = "{}{}{}".format(label_start, label_body ,label_end)
       
        self.g.node(token, label, shape= 'plaintext', color='lightgoldenrod4')


    def make_task_node(self, step, token):
        name = step.get("TaskName")
        if name = "Common-run_mp":
            color = "cyan4"
        else:
            color = "blue"
        label_start="<<TABLE BORDER='5' CELLBORDER='5' CELLSPACING='10'>"
        label_end = "</TABLE>>"
        
        label_body  = "<TR><TD>task name: <b>{}</b></TD></TR>".format(name)
        if 'Replace' in step:
            for k, v in step.get('Replace').items():
                
                label_body = "{}<TR><TD>{}: {}</TD></TR>".format(label_body,k, self.safe_label(v))
                if k == '@definitionclass':
                    if v in self.dc_dict:
                        for h in self.dc_dict[v]:
                            self.g.edge(token, "defin_{}_{}".format(v, h))
        
        label = "{}{}{}".format(label_start, label_body ,label_end)
       
        self.g.node(token, label, shape= 'plaintext', color=color)
    
    def make_container_node(self, cont, token):
        label_start="<<TABLE BORDER='5' CELLBORDER='5' CELLSPACING='10'>"
        label_end = "</TABLE>>"
        
        label_title  = "<TR><TD>title: <b>{}</b></TD></TR>".format(self.safe_label(cont.get('Title')))
        title_descr = "<TR><TD>description: <i>{}</i></TD></TR>".format(self.safe_label(cont.get('Description')))
      
        label = "{}{}{}{}".format(label_start,label_title,title_descr,label_end)
        self.g.node(token, label, shape='plaintext', color='lightgoldenrod4')

    def make_mpd_node(self, mpd, token):
        title = self.safe_label(mpd.get('Name'))
        descr = self.safe_label(mpd.get('Description'))
        label = "{}\n{}".format(title, descr)
        self.g.node(token, label, shape='doublecircle', color='blue')
      

    def render(self):
        self.g.render(filename=self.name)


if __name__ == '__main__':

    db = DB()
    mp = db.get_doc("mpd-se3-calib")
    draw = Draw(mp)
    draw.loop_all() 
    draw.render()