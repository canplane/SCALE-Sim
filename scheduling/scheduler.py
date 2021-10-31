import random

from scale_error import SCALE_Error

from scheduling.ready_queue import FCFS, RRB, HPF, TOKEN, SJF, PREMA
from task import Task

from misc import set_style, set_color


class Preemption(Exception):
    pass


class Scheduler:
    def __init__(self, out_dir="./outputs", csv_path=None, 
                algorithm_name: str=None, 
                time_quota: int=None, 
                layerwise_preemption: bool=False,
                drain: bool=True,
            ):
        self.epoch_time = 0     # 단위: cycle
        self.current_task_id = None

        self.algorithm_name = algorithm_name
        if algorithm_name == 'FCFS':
            self.ready_q = FCFS(
                    preemptive=False, layerwise_preemption=layerwise_preemption,
                )
        elif algorithm_name == 'RRB':
            self.ready_q = RRB(
                    preemptive=True, layerwise_preemption=layerwise_preemption,
                    time_quota=time_quota
                )
        elif algorithm_name == 'HPF':
            self.ready_q = HPF(
                    preemptive=True, layerwise_preemption=layerwise_preemption,
                )
        elif algorithm_name == 'TOKEN':
            self.ready_q = TOKEN
        elif algorithm_name == 'SJF':
            self.ready_q = SJF
        elif algorithm_name == 'PREMA':
            self.ready_q = PREMA
        else:
            raise SCALE_Error('Unknown scheduler name')

        self.ready_q.layerwise_preemption = layerwise_preemption

        self.tasks = {}

        self.out_dir = out_dir
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
                parent=self,

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
                task.state = 'READY'
                self.ready_q.push(task_id)
            else:
                task.state = 'NEW'
    #

    def _refresh_time(self):
        if self.current_task_id == None:
            return


        running_task = self.tasks[self.current_task_id]

        ## Get diff cycles 
        _cycles = 0
        for num in running_task.cycles_per_layer:                       # 이전까지 실행 완료된 레이어의 cycle 합
            _cycles += num

        if running_task.current_layer_idx == running_task.last_executed_layer_idx:  # 레이어 실행 중 멈춤
            _cycles += running_task.layers[running_task.current_layer_idx].load_var('cycles')
        
        diff_cycles = _cycles - running_task.execution_time['executed']

        ## Refresh epoch time
        self.epoch_time += diff_cycles

        ## Refresh time for current task and all ready tasks
        _li = running_task.execution_timeline[running_task.last_executed_layer_idx]
        if bool(_li) and _li[-1][1] == self.epoch_time - diff_cycles:
            _li[-1][1] = self.epoch_time
        else:
            _li.append([ self.epoch_time - diff_cycles, self.epoch_time ])

        running_task.execution_time['executed'] += diff_cycles
        for task_id in self.ready_q.get_list():
            self.tasks[task_id].execution_time['waited'] += diff_cycles
        
        ## for debug
        #print(f"epoch time: {self.epoch_time}")
        #for task_id, task in self.tasks.items():
        #    print(f"[{task_id}] execution time: {task.execution_time['executed']} + {task.execution_time['waited']} = {task.execution_time['executed'] + task.execution_time['waited']}")
        #print(f"[{self.current_task_id}] executed timeline (tail): {running_task.execution_timeline[-3:]}")
    #

    def refresh(self, preempt: bool=True, a_layer_end: bool=False):
        ## Refresh time
        self._refresh_time()

        ## Add newly arriving tasks
        for task_id, task in self.tasks.items():
            if task.state == 'NEW' and task.arrival_time <= self.epoch_time:
                task.state = 'READY'
                self.ready_q.push(task_id)
        
        ## if CHECKPOINT and not DRAIN
        if preempt and self.ready_q.is_preempting_condition(
                    tasks=self.tasks, 
                    epoch_time=self.epoch_time, 
                    a_layer_end=a_layer_end,
                ):
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
                print(f"Execution timeline: {current_task.execution_timeline}")

                current_task.state = 'END'
                print(set_style(" TASK ENDED ", key='INVERSE'))
            ## RUN
            else:
                _task_swap = True

        ## Dispatch next task
        next_task_id = self.ready_q.pop(tasks=self.tasks, epoch_time=self.epoch_time)
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
