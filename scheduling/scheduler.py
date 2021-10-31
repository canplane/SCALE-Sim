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
            self.ready_q = FCFS()
        elif algorithm_name == 'RRB':
            self.ready_q = RRB(time_quota=time_quota)
        elif algorithm_name == 'HPF':
            self.ready_q = HPF
        elif algorithm_name == 'TOKEN':
            self.ready_q = TOKEN
        elif algorithm_name == 'SJF':
            self.ready_q = SJF
        elif algorithm_name == 'PREMA':
            self.ready_q = PREMA
        else:
            raise SCALE_Error('Unknown scheduler name')

        self.layerwise_preemption = layerwise_preemption

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


    ## Scheduling
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
        running_task = self.tasks[self.current_task_id]

        ## Get diff cycles 
        _cycles = 0
        for num in running_task.cycles_per_layer:                       # 이전까지 실행 완료된 레이어의 cycle 합
            _cycles += num

        ###if running_task.current_layer_idx < len(running_task.layers):   # 현재 실행 중이던 레이어의 현재까지의 cycle
        ###    _layer = running_task.layers[running_task.current_layer_idx]
        ###    if not _layer.is_empty_var('cycles'):   # 다음 레이어 아직 실행 안 한 상태라면 empty
        ###        _cycles += running_task.layers[running_task.current_layer_idx].load_var('cycles', init=0)
        ###diff_cycles = _cycles - running_task.execution_time['executed']
        
        ###if last_executed_idx == len(running_task.layers) or running_task.layers[last_executed_idx].is_empty_var('cycles'):    # 다음 레이어 아직 실행 안 한 상태라면 empty
        ###    last_executed_idx -= 1
        ###else:
        ###    # 현재 실행 중이던 레이어의 현재까지의 cycle
        ###    _cycles += running_task.layers[last_executed_idx].load_var('cycles')

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
        if preempt and self.ready_q.front() != None:
            if a_layer_end == True and self.layerwise_preemption == True:
                raise Preemption()
            if self.ready_q.is_preempting_condition(epoch_time=self.epoch_time):
                raise Preemption()
    #

    ## Context switch
    def switch(self):
        ## Dispatch next task
        next_task_id = self.ready_q.pop(epoch_time=self.epoch_time)
        next_task = None
        if next_task_id != None:
            next_task = self.tasks[next_task_id]
            next_task.state = 'RUN'

            ## for debug
            #print(f"Next task: \'{next_task.name}\'")

        ## for debug
        #print("Ready queue: { ", end="")
        #for task_id in self.ready_q.get_list():
        #    print(f"\'{self.tasks[task_id].name}\'", end=", ")
        #print("}")


        ## Push current task into ready queue
        if self.current_task_id != None:
            current_task = self.tasks[self.current_task_id]

            ## END
            if current_task.current_layer_idx == len(current_task.layers):
                self.refresh(preempt=False)
                print(current_task.execution_timeline)

                current_task.state = 'END'
                print(set_style(" TASK ENDED ", key='INVERSE'))
            ## RUN
            else:
                current_task.state = 'READY'
                self.ready_q.push(self.current_task_id)

        self.current_task_id = next_task_id
        return next_task
    #
#
