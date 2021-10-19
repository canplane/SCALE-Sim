import random

from task import Task


class Preemption(Exception):
    pass


class Scheduler:
    def __init__(self, out_dir="./outputs", csv_path=None):
        self.tasks = {}
        self.next_task_id = 0

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
        self.epoch_time = 0     # 단위: cycle

        self.ready_q = []
        self.running_task_id = None
        self.candidate_task_id = None

        for task_id, task in self.tasks.items():
            if task.arrival_time <= self.epoch_time:
                task.state = 'READY'
                self.ready_q.append(task_id)
            else:
                task.state = 'NEW'
        
        ## task selecting algorithm
        ######## 이 부분만 추가하면 됨
        try:
            self.candidate_task_id = self.ready_q.pop(0)
        except IndexError:
            self.candidate_task_id = None
        ########
    #

    def refresh_time(self):
        running_task = self.tasks[self.running_task_id]

        ## Get diff cycles 
        _cycles = 0
        for num in running_task.cycles_per_layer:                       # 이전까지 실행 완료된 레이어의 cycle 합
            _cycles += num

        if running_task.current_layer_idx < len(running_task.layers):   # 현재 실행 중이던 레이어의 현재까지의 cycle
            _layer = running_task.layers[running_task.current_layer_idx]
            if not _layer.is_empty_var('cycles'):   # 다음 레이어 아직 실행 안 한 상태라면 empty
                _cycles += running_task.layers[running_task.current_layer_idx].load_var('cycles', init=0)
        diff_cycles = _cycles - running_task.execution_time['executed']

        ## Refresh epoch time
        self.epoch_time += diff_cycles

        ## Refresh time for current task and all ready tasks
        running_task.execution_timeline.append([ self.epoch_time - diff_cycles, self.epoch_time ])

        running_task.execution_time['executed'] += diff_cycles
        for task_id in self.ready_q:
            self.tasks[task_id].execution_time['waited'] += diff_cycles
        
        ## Debug
        #print(f"epoch time: {self.epoch_time}")
        #for task_id, task in self.tasks.items():
        #    print(f"{task_id}: execution time: {task.execution_time['executed']} + {task.execution_time['waited']} = {task.execution_time['executed'] + task.execution_time['waited']}")
        #print(f"executed timeline: {running_task.execution_timeline}")
    #

    def refresh(self, preempt=True):
        ## Refresh time
        self.refresh_time()

        for task_id, task in self.tasks.items():
            if task.state == 'NEW' and task.arrival_time <= self.epoch_time:
                task.state = 'READY'
                self.ready_q.append(task_id)

        ## task selecting algorithm
        ######## 이 부분만 추가하면 됨
        try:
            self.candidate_task_id = self.ready_q.pop(0)
        except IndexError:
            self.candidate_task_id = None
        ########
        
        ## if CHECKPOINT and not DRAIN
        if preempt and self.candidate_task_id != None:
            raise Preemption()
    #

    def switch(self):
        if self.running_task_id != None:
            preempted_task = self.tasks[self.running_task_id]
            if preempted_task.state == 'RUN':
                preempted_task.state = 'READY'
                self.ready_q.append(self.running_task_id)
            else:   # END
                self.refresh(preempt=False)
        
        preempting_task = None
        if self.candidate_task_id != None:
            preempting_task = self.tasks[self.candidate_task_id]
            preempting_task.state = 'RUN'
            #print(f"Preempting task: \'{preempting_task.name}\'")
        #print("Ready queue: { ", end="")
        #for task_id in self.ready_q:
        #    print(f"\'{self.tasks[task_id].name}\'", end=", ")
        #print("}")

        self.running_task_id, self.candidate_task_id = self.candidate_task_id, None
        return preempting_task
    #
#
