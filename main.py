from graphviz import Digraph, nohtml
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

        self.g =  Digraph('G', filename='cluster.gv')
        self.g.attr(rankdir='LR')
        self.g.node_attr={'shape': 'record'}
        self.g.node_attr.update(color='lightblue2', style='filled')
        self.mpd = mpd_doc.get('Mp', {})
        self.definitions = self.mpd.get('Definitions', [])
        self.container = self.mpd.get('Container', [])
        self.C = len(self.container)
        self.D = len(self.definitions)
        self.dc_dict={}

    def loop_all(self):

        self.g.node('Name', self.mpd.get('Name'))
        
        for i, defin in enumerate(self.definitions):
            dc = defin.get('DefinitionClass')
            defin_token = "defin_{}_{}".format(dc,i)
            if dc in self.dc_dict:
                self.dc_dict[dc].append(i)
            else:
                self.dc_dict[dc]= [i]

            self.make_defin_node(defin, defin_token)
            for j, steps in enumerate(defin.get('Definition')):
                for k, step in enumerate(steps):
                    task_token = "defin_step_{}_{}_{}".format(i,k,j)
                    self.make_defintask_node( step, task_token)
                    self.g.edge(defin_token, task_token)


        for i, cont in enumerate(self.container):
            cont_token = "cont_{}".format(i)
            self.g.edge('Name',  cont_token)
            self.make_container_node(cont, cont_token)
            for j, steps in enumerate(cont.get('Definition')):
                for k, step in enumerate(steps):
                    task_token = "cont_step_{}_{}_{}".format(i,k,j)
                    self.make_task_node(step, task_token)
                    self.g.edge(cont_token, task_token)


    def make_defin_node(self, defin, token):
        name = defin.get('DefinitionClass')
        condition = defin.get('Condition')
        descr = defin.get('ShortDescr')
        label = "{}".format(name)
        for cond in condition:
            a = cond.get('ExchangePath')
            b = cond.get('Methode')
            c = cond.get('Value')
            label = "{}|ExchPath: {}| Op: {}| Value: {}".format(label, a, b, c)


        self.g.node(token, label)

    def make_defintask_node(self, step, token):
        name = step.get("TaskName")
        label = "TaskName: {}".format(name)
        self.g.node(token, nohtml(label))

    def make_task_node(self, step, token):
        name = step.get("TaskName")
        label = "TaskName: {}".format(name)
        if 'Replace' in step:
            for k, v in step.get('Replace').items():
                label = "{}|{}: {}".format(label,k, v)
                if k == '@definitionclass':
                    if v in self.dc_dict:
                        for h in self.dc_dict[v]:
                            self.g.edge(token, "defin_{}_{}".format(v, h))

        self.g.node(token, label)
    
    def make_container_node(self, cont, token):
        name = cont.get('Title')
        self.g.node(token, name)
                    
    def view(self):
        self.g.view()


if __name__ == '__main__':

    db = DB()
    mp = db.get_doc("mpd-se3-calib")
    draw = Draw(mp)

    draw.loop_all() 
    draw.view()