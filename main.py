from graphviz import Digraph, nohtml
import couchdb
import json
import sys
import argparse

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
        
        self.g = Digraph('structs', format='pdf', engine="dot")
        self.g.node_attr.update(fontsize="80", fontname="Helvetica")
        self.g.edge_attr.update( penwidth = '7')
        self.mpd_token = "Name"
        self.id = mpd_doc.get("_id")
        self.mpd = mpd_doc.get('Mp', {})
        self.name = self.mpd.get('Name').replace(' ','_')
        self.definitions = self.mpd.get('Definitions', [])
        self.container = self.mpd.get('Container', [])
        self.defin_class_dict={}
        self.defin_dict = {}  
        self.cont_dict = {}
        self.label_start =  "<<TABLE BORDER='5' CELLBORDER='5' CELLSPACING='10'>"
        self.label_end = "</TABLE>>"
        
    def build_defin_class_dict(self):
        for i, defin in enumerate(self.definitions):
            dc = defin.get('DefinitionClass') 
            if dc in self.defin_class_dict:
                self.defin_class_dict[dc].append(i)
            else:
                self.defin_class_dict[dc]= [i]
    
    def build_cont_dict(self):
        for i, cont in enumerate(self.container):
            cont_key = "cont_{}".format(i)
            self.cont_dict[cont_key] = {}
            for j, steps in enumerate(cont.get('Definition')):
                seq_key = "cont_{}_{}".format(i, j)
                self.cont_dict[cont_key][seq_key] = {}
                for k, task in enumerate(steps):
                    par_key = "cont_{}_{}_{}".format(i, j, k)
                    self.cont_dict[cont_key][seq_key][par_key] = task
    
    def build_defin_dict(self):        
        for i, defin in enumerate(self.definitions):
            defin_key = "defin_{}_{}".format(defin.get('DefinitionClass'), i)
            self.defin_dict[defin_key] = {}
            for j, steps in enumerate(defin.get('Definition')):
                seq_key = "defin_{}_{}".format( i, j)
                self.defin_dict[defin_key][seq_key] = {}
                for k, task in enumerate(steps):
                    par_key = "defin_{}_{}_{}".format(i, j, k)
                    self.defin_dict[defin_key][seq_key][par_key] = task

    def make_defin_nodes(self):
        for i, defin_key in enumerate(self.defin_dict):
            defin = self.definitions[i]
            self.make_defin_node( self.g, defin, defin_key)
            
    def make_defin_task_nodes(self):
        for i, defin_key in enumerate(self.defin_dict):
            with self.g.subgraph(name='cluster_{}'.format(defin_key)) as defin_graph:
                defin_graph.attr(color='lightgoldenrod4', penwidth = '20')
                for j, seq_key in enumerate(self.defin_dict[defin_key]):
                    for par_key, task in self.defin_dict[defin_key][seq_key].items():
                        self.make_task_node(defin_graph, task, par_key)
    
    def connect_defin_task(self):
        for i, defin_key in enumerate(self.defin_dict):
            for j, seq_key in enumerate(self.defin_dict[defin_key]):
                for par_key, task in self.defin_dict[defin_key][seq_key].items():
                    if j == 0:
                        self.g.edge(defin_key, "{}:f1".format(par_key))
                    else:
                        self.g.edge( "defin_{}_{}_{}".format(i, j-1,0), "{}:f1".format(par_key))
               
    def connect_select_task_to_defin(self):
        for i, cont_key in enumerate(self.cont_dict):
            for j, seq_key in enumerate(self.cont_dict[cont_key]):
                for par_key, task in self.cont_dict[cont_key][seq_key].items():
                    if 'Replace' in task:
                        for k, v in task.get('Replace').items():
                            if k == '@definitionclass':
                                if v in self.defin_class_dict:
                                    for h in self.defin_class_dict[v]:
                                        self.g.edge(par_key, "defin_{}_{}".format(v, h))

        for i, defin_key in enumerate(self.defin_dict):
            for j, seq_key in enumerate(self.defin_dict[defin_key]):
                for par_key, task in self.defin_dict[defin_key][seq_key].items():
                    if 'Replace' in task:
                        for k, v in task.get('Replace').items():
                            if k == '@definitionclass':
                                if v in self.defin_class_dict:
                                    for h in self.defin_class_dict[v]:
                                        self.g.edge(par_key, "defin_{}_{}".format(v, h))

    def connect_mp_cont(self):
        for cont_key in self.cont_dict:
            self.g.edge(self.mpd_token,  cont_key)
            
    def make_cont_nodes(self):
        for i, cont_key in enumerate(self.cont_dict):
            cont = self.container[i]
            self.make_cont_node( self.g, cont, cont_key)
            
    
    def make_cont_task_nodes(self):
        for i, cont_key in enumerate(self.cont_dict):
            with self.g.subgraph(name='cluster_{}'.format(cont_key)) as cont_graph:
                cont_graph.attr(color='lightgoldenrod4', penwidth = '20')
                for j, seq_key in enumerate(self.cont_dict[cont_key]):
                    for par_key, task in self.cont_dict[cont_key][seq_key].items():
                        self.make_task_node(cont_graph, task, par_key)

    def connect_cont_task(self):
        for i, cont_key in enumerate(self.cont_dict):
            for j, seq_key in enumerate(self.cont_dict[cont_key]):
                for par_key, task in self.cont_dict[cont_key][seq_key].items():
                    if j == 0:
                        self.g.edge(cont_key, "{}:f1".format(par_key))
                    else:
                        self.g.edge( "cont_{}_{}_{}".format(i, j-1,0), "{}:f1".format(par_key))

   
    def safe_label(self, label):
        label = str(label)
        label = label.replace(">", "[greater than]")
        label = label.replace("<", "[less than]")
        label = label.replace("&", "[and]")
        return label

    def make_defin_node(self, graph, defin, token):
        name = defin.get('DefinitionClass')
        condition = defin.get('Condition')
        descr = defin.get('ShortDescr')
        label_body = """<TR><TD PORT='f1'>definition class: <b>{}</b></TD></TR>
                        <TR><TD>description: {}</TD></TR>
                    """.format(self.safe_label(name), self.safe_label(descr))
        for cond in condition:
            a = cond.get('ExchangePath')
            b = cond.get('Methode')
            c = cond.get('Value')
            label_body = """{}<TR><TD>ExchPath:  <b>{}</b></TD></TR> 
                             <TR><TD>operator: <b>{}</b></TD></TR> 
                             <TR><TD>Value:  <b>{}</b></TD></TR>""".format(label_body, a, b, c)
        label = "{}{}{}".format(self.label_start, label_body, self.label_end)
        graph.node(token, label, shape= 'plaintext', color='darkorchid')

    def make_task_node(self, graph, step, token):
        name = step.get("TaskName")
        color = "black"
        if name == "Common-run_mp":
            color = "cyan4"
        if name == "Commons-select_definition":
            color = "blue"
        label_body  = "<TR><TD PORT='f1'>task name: <b>{}</b></TD></TR>".format(name)
        if 'Replace' in step:
            for k, v in step.get('Replace').items():
                label_body = "{}<TR><TD>replace <b>{}</b> by <b>{}</b></TD></TR>".format(label_body,k, self.safe_label(v))
        if 'Use' in step:
            for k, v in step.get('Use').items():
                label_body = "{}<TR><TD>use <b>{}</b> in <b>{}</b></TD></TR>".format(label_body, self.safe_label(v), k)
        label = "{}{}{}".format(self.label_start, label_body, self.label_end)
        graph.node(token, label, shape= 'plaintext', color=color)
    
    def make_cont_node(self, graph, cont, key):
        label_title  = "<TR><TD PORT='f1'>title: <b>{}</b></TD></TR>".format(self.safe_label(cont.get('Title')))
        title_descr = "<TR><TD>description: <i>{}</i></TD></TR>".format(self.safe_label(cont.get('Description')))
        label = "{}{}{}{}".format(self.label_start,label_title,title_descr,self.label_end)
        graph.node(key, label, shape='plaintext', color='lightgoldenrod4')

    def make_mpd_node(self):
        title = self.mpd.get('Name')
        descr = self.mpd.get('Description')
        label_title  = "<TR><TD PORT='f1'>measurement definition name: <b>{}</b></TD></TR>".format(self.safe_label(title))
        title_descr = "<TR><TD>description: <i>{}</i></TD></TR>".format(self.safe_label( descr))
        label = "{}{}{}{}".format(self.label_start,label_title,title_descr, self.label_end)
        self.g.node(self.mpd_token, label, shape='plaintext', color='blueviolet')

    def render(self):
        self.g.render(filename="graph-{}".format(self.id))


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--doc', help='id of the document which should be drawn')
    args = parser.parse_args()
 
    db = DB()
    mp = db.get_doc(args.doc)
    draw = Draw(mp)
    draw.make_mpd_node()

    draw.build_defin_class_dict()
    draw.build_defin_dict()
    draw.build_cont_dict()

    draw.make_cont_nodes()
    draw.make_cont_task_nodes()
    draw.make_defin_task_nodes()
    draw.make_defin_nodes()

    draw.connect_mp_cont()
    draw.connect_defin_task() 
    draw.connect_cont_task()
    draw.connect_select_task_to_defin()
    draw.render()