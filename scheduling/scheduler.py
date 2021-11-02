import random

from scale_error import SCALE_Error

from scheduling.ready_queue import FCFS_RRB, HPF, TOKEN, SJF, PREMA
from task import Task

from misc import set_style, set_color


class Preemption(Exception):
    pass


class Scheduler:
    def __init__(self, arch=None, csv_path=None, 
                algorithm_name: str=None, 
                preemptive: bool=True, layerwise_scheduling: bool=False,
                time_quota: int=None, dynamic: bool=True,
            ):
        self.epoch_time = 0     # unit: cycle
        self.current_task_id = None

        self.algorithm_name = algorithm_name
        if algorithm_name == 'FCFS':
            self.ready_q = FCFS_RRB(self, time_quota=time_quota, 
                    preemptive=False, layerwise_scheduling=layerwise_scheduling, dynamic=False
                )
        elif algorithm_name == 'RRB':
            self.ready_q = FCFS_RRB(self, time_quota=time_quota, 
                    preemptive=True, layerwise_scheduling=layerwise_scheduling, dynamic=False
                )
        elif algorithm_name == 'HPF':
            self.ready_q = HPF(self, time_quota=time_quota, 
                    preemptive=preemptive, layerwise_scheduling=layerwise_scheduling, dynamic=dynamic
                )
        elif algorithm_name == 'TOKEN':
            self.ready_q = TOKEN(self, time_quota=time_quota, 
                    preemptive=preemptive, layerwise_scheduling=layerwise_scheduling, dynamic=dynamic
                )
        elif algorithm_name == 'SJF':
            self.ready_q = SJF(self, time_quota=time_quota, 
                    preemptive=preemptive, layerwise_scheduling=layerwise_scheduling, dynamic=dynamic
                )
        elif algorithm_name == 'PREMA':
            self.ready_q = PREMA(self, time_quota=time_quota, 
                    preemptive=preemptive, layerwise_scheduling=layerwise_scheduling, dynamic=dynamic
                )
        else:
            raise SCALE_Error('Unknown scheduler name')

        self.tasks = {}

        self.arch = arch
        if csv_path != None:
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
                    arrival_time=int(elems[3]) ######## * pe_operating_freq 추가해야 함
                )
            #
        #
    #
    def add_task(self, net_name=None, net_path=None, priority=None, arrival_time=None):
        ## Set color for the task
        COLOR_PALLET = [ 'GREEN', 'BLUE', 'CYAN', 'MAGENTA', 'YELLOW' ]
        color_pallet = COLOR_PALLET.copy()
        for task_id in self.tasks:
            try:
                color_pallet.remove(self.tasks[task_id].color)
            except ValueError:
                pass
        this_task_color = random.choice( color_pallet if bool(color_pallet) else COLOR_PALLET )
        
        this_task_id = len(self.tasks)
        self.tasks[this_task_id] = Task(
                arch=self.arch,

                task_id=this_task_id,
                net_name=net_name,
                net_path=net_path,
                priority=priority,
                arrival_time=arrival_time,

                color=this_task_color
            )
    #


    #### Scheduling

    def start(self):
        ## Initialize ready queue and state of tasks
        for task_id, task in self.tasks.items():
            if task.arrival_time <= self.epoch_time:
                self.ready_q.push(task_id)
                task.state = 'READY'
            else:
                task.state = 'NEW'
    #

    def _refresh_time(self):
        if self.current_task_id == None:
            return

        running_task = self.tasks[self.current_task_id]

        ## Get diff cycles 
        diff_cycles = running_task.layers[running_task.last_executed_layer_idx].load_var('cycles') - running_task.executed_time_per_layer[running_task.last_executed_layer_idx]

        ## Refresh epoch time
        self.epoch_time += diff_cycles

        ## Refresh time for current task and all ready tasks
        running_task.executed_time += diff_cycles
        running_task.executed_time_per_layer[running_task.last_executed_layer_idx] += diff_cycles
        _li = running_task.executed_timeline[running_task.last_executed_layer_idx]
        if bool(_li) and _li[-1][1] == self.epoch_time - diff_cycles:
            _li[-1][1] = self.epoch_time
        else:
            _li.append([ self.epoch_time - diff_cycles, self.epoch_time ])

        for task_id in self.ready_q.get_list():
            task = self.tasks[task_id]

            task.waited_time += diff_cycles
            task.waited_time_per_layer[task.current_layer_idx] += diff_cycles
            _li = task.waited_timeline[task.current_layer_idx]
            if bool(_li) and _li[-1][1] == self.epoch_time - diff_cycles:
                _li[-1][1] = self.epoch_time
            else:
                _li.append([ self.epoch_time - diff_cycles, self.epoch_time ])
        
        ## for debug
        #print(f"epoch time: {self.epoch_time}")
        #for task_id, task in self.tasks.items():
        #    print(f"[{task_id}] executed time: {task.executed_time} + {task.waited_time} = {task.executed_time + task.waited_time}")
        #print(f"[{self.current_task_id}] executed timeline (tail): {running_task.executed_timeline[-3:]}")
    #

    def refresh(self, preempt: bool=True, a_layer_end: bool=False):
        ## Refresh time
        self._refresh_time()

        ## Add newly arriving tasks
        for task_id, task in self.tasks.items():
            if task.state == 'NEW' and task.arrival_time <= self.epoch_time:
                self.ready_q.push(task_id)
                task.state = 'READY'
        
        ## if CHECKPOINT and not DRAIN
        if preempt and self.ready_q.is_in_preempting_condition(a_layer_end=a_layer_end):
            raise Preemption()
    #

    ## Context switch
    def switch(self):
        _task_swap = False
        if self.current_task_id != None:
            current_task = self.tasks[self.current_task_id]

            ## END
            if current_task.current_layer_idx == len(current_task.layers):
                self.refresh(preempt=False)
                print(f"Executed timeline: {current_task.executed_timeline}")

                current_task.state = 'END'
                print(set_style(" TASK ENDED ", key='INVERSE'))
            ## RUN
            else:
                _task_swap = True

        ## Dispatch next task
        next_task_id = self.ready_q.pop()
        next_task = None
        if next_task_id != None:
            next_task = self.tasks[next_task_id]
            next_task.state = 'RUN'

            ## for debug
            #print(f"Next task: \'{next_task.name}\'")

        if _task_swap == True:
            current_task.state = 'READY'
            self.ready_q.push(self.current_task_id)

        ## for debug
        #print("Ready queue: { ", end="")
        #for task_id in self.ready_q.get_list():
        #    print(f"\'{self.tasks[task_id].name}\'", end=", ")
        #print("}")

        self.current_task_id = next_task_id
        return next_task
    #

    ## Process idle time
    def has_not_yet_arrived_tasks(self):
        _epoch_time = None
        for task_id in self.tasks:
            if self.tasks[task_id].state == 'NEW':
                if _epoch_time == None or self.tasks[task_id].arrival_time < _epoch_time:
                    _epoch_time = self.tasks[task_id].arrival_time

        if _epoch_time != None:
            print("")
            print(set_style(f" Jump idle time (epoch time: {self.epoch_time} -> {_epoch_time}) ", key='INVERSE'))

            self.epoch_time = _epoch_time
            self.refresh(preempt=False)
            return True
        else:
            return False
    #
#
