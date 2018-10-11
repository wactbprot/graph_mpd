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
        
        self.id = mpd_doc.get("_id")
        self.mpd = mpd_doc.get('Mp', {})
        self.name = self.mpd.get('Name').replace(' ','_')
        self.definitions = self.mpd.get('Definitions', [])
        self.container = self.mpd.get('Container', [])

        self.dc_dict={}
        self.label_start="<<TABLE BORDER='5' CELLBORDER='5' CELLSPACING='10'>"
        self.label_end = "</TABLE>>"
        
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
            with self.g.subgraph(name='cluster_defin_{}'.format(defin_i)) as c:
                c.attr(color='darkorchid', penwidth = '20')
                self.make_defin_node(c, defin, defin_token)
                for seq_i, steps in enumerate(defin.get('Definition')):
                    for par_i, step in enumerate(steps):
                        task_token = "defin_step_{}_{}_{}".format(defin_i, seq_i, par_i)
                        self.make_task_node(c, step, task_token)
                        if seq_i == 0:
                            self.g.edge(defin_token, "{}:f1".format(task_token))
                        else:
                            self.g.edge( "defin_step_{}_{}_{}".format(defin_i, seq_i-1,0), "{}:f1".format(task_token))
                        
        for cont_i, cont in enumerate(self.container):
            cont_token = "cont_{}".format(cont_i)
            self.g.edge('Name',  cont_token)
            with self.g.subgraph(name='cluster_cont_{}'.format(cont_i)) as c:
                c.attr(color='lightgoldenrod4',penwidth = '20')
                self.make_container_node(c, cont, cont_token)
                for seq_i, steps in enumerate(cont.get('Definition')):
                    for par_i, step in enumerate(steps):
                        task_token = "cont_step_{}_{}_{}".format(cont_i,seq_i,par_i)
                        self.make_task_node(c ,step, task_token)
                        if seq_i == 0:
                            self.g.edge(cont_token, "{}:f1".format(task_token))
                        else:
                            self.g.edge( "cont_step_{}_{}_{}".format(cont_i, seq_i-1,0), "{}:f1".format(task_token))

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
        label_body = "<TR><TD PORT='f1'>definition class: <b>{}</b></TD></TR>".format(self.safe_label(name))
        
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
                if k == '@definitionclass':
                    if v in self.dc_dict:
                        for h in self.dc_dict[v]:
                            self.g.edge(token, "defin_{}_{}".format(v, h))

        if 'Use' in step:
            for k, v in step.get('Use').items():
                label_body = "{}<TR><TD>use <b>{}</b> in <b>{}</b></TD></TR>".format(label_body, self.safe_label(v), k)
        
        label = "{}{}{}".format(self.label_start, label_body, self.label_end)
       
        graph.node(token, label, shape= 'plaintext', color=color)
    
    def make_container_node(self, graph, cont, token):
        label_title  = "<TR><TD PORT='f1'>title: <b>{}</b></TD></TR>".format(self.safe_label(cont.get('Title')))
        title_descr = "<TR><TD>description: <i>{}</i></TD></TR>".format(self.safe_label(cont.get('Description')))
      
        label = "{}{}{}{}".format(self.label_start,label_title,title_descr,self.label_end)
        graph.node(token, label, shape='plaintext', color='lightgoldenrod4')

    def make_mpd_node(self, mpd, token):
        title = mpd.get('Name')
        descr =mpd.get('Description')
        label_title  = "<TR><TD PORT='f1'>measurement definition name: <b>{}</b></TD></TR>".format(self.safe_label(title))
        title_descr = "<TR><TD>description: <i>{}</i></TD></TR>".format(self.safe_label( descr))
        label = "{}{}{}{}".format(self.label_start,label_title,title_descr, self.label_end)
        self.g.node(token, label, shape='plaintext', color='blueviolet')


    def render(self):
        self.g.render(filename=self.id)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--doc', help='id of the document which should be drawn')
    args = parser.parse_args()
 
    db = DB()
    mp = db.get_doc(args.doc)
    draw = Draw(mp)
    draw.loop_all() 
    draw.render()