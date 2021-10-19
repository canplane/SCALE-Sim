import random

from task import Task


class Preemption(Exception):
    pass


class Scheduler:
    def __init__(self, out_dir="./outputs", csv_path=None):
        self.tasks = {}
        self.next_task_id = 0

        self.out_dir = out_dir
        if not csv_path == None:
            self._load_from_csv(csv_path)
    #
    def _load_from_csv(self, path):
        with open(path, 'r') as f:
            first = True
            for row in f:
                if first:
                    first = False
                    continue
                elems = row.strip().split(',')
                if len(elems) < 5:      # Do not continue if incomplete line
                    continue

                self.add_task(
                    net_name=elems[0].strip().strip("'\""),
                    net_path=elems[1].strip().strip("'\""),
                    priority=int(elems[2]),
                    arrival_time=int(elems[3])
                )
            #
        #
    #
    def add_task(self, net_name=None, net_path=None, priority=None, arrival_time=None):
        ## Set color for the task
        color_pallet = [ 'GREEN', 'BLUE', 'CYAN', 'MAGENTA', 'YELLOW' ]
        _color_pallet = color_pallet.copy()
        for task_id in self.tasks:
            try:
                color_pallet.remove(self.tasks[task_id].color)
            except ValueError:
                pass
        task_color = random.choice( color_pallet if bool(color_pallet) else _color_pallet )

        self.tasks[self.next_task_id] = Task(
                parent=self,

                task_id=self.next_task_id,
                net_name=net_name,
                net_path=net_path,
                priority=priority,
                arrival_time=arrival_time,

                color=task_color
            )
        self.next_task_id += 1
    #


    ## Scheduling
    def start(self):
        self.time = 0

        self.ready_q = []
        self.running_task_id = None
        self.candidate_task_id = None

        for task_id, task in self.tasks.items():
            if not task.arrival_time > self.time:
                task.state = 'READY'
                self.ready_q.append(task_id)
            else:
                task.state = 'NEW'
        
        # task selecting algorithm
        ######## 이 부분만 추가하면 됨
        try:
            self.candidate_task_id = self.ready_q.pop(0)
        except IndexError:
            self.candidate_task_id = None
        ########
    #

    def refresh(self):
        self.time += 0      # refresh time ######## 이 부분만 추가하면 됨

        for task_id, task in self.tasks.items():
            if task.state == 'NEW' and not task.arrival_time > self.time:
                task.state = 'READY'
                self.ready_q.append(task_id)

        # task selecting algorithm
        ######## 이 부분만 추가하면 됨
        try:
            self.candidate_task_id = self.ready_q.pop(0)
        except IndexError:
            self.candidate_task_id = None
        ########
        
        # if CHECKPOINT and not DRAIN
        if not self.candidate_task_id == None:
            raise Preemption()
    #

    def switch(self):
        if not self.running_task_id == None:
            preempted_task = self.tasks[self.running_task_id]
            if not preempted_task.state == 'END':   # RUN
                preempted_task.state = 'READY'
                self.ready_q.append(self.running_task_id)
        
        preempting_task = None
        if not self.candidate_task_id == None:
            preempting_task = self.tasks[self.candidate_task_id]
            preempting_task.state = 'RUN'

        self.running_task_id, self.candidate_task_id = self.candidate_task_id, None
        return preempting_task
    #
#
