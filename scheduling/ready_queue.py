class _ReadyQueue:
    def __init__(self, scheduler, 
                layerwise_preemption: bool=False,
                preemptive: bool=False,
                time_quota: int=None, 
            ):
        self.scheduler = scheduler

        self.preemptive = preemptive
        self.layerwise_preemptive = layerwise_preemption
        self.time_quota = time_quota

        self.li = []

        self.next_i, self.next_id = None, None

    def get_list(self) -> list:
        return self.li
    
    def push(self, task_id: int) -> None:
        self.li.append(task_id)
    
    def pop(self) -> int:
        if self.next_id == None:
            self._select_next_task()

        if self.next_id != None:
            self.recent_switch_time = self.scheduler.epoch_time

            self.li.pop(self.next_i)
        
        ret = self.next_id
        self.next_i, self.next_id = None, None
        return ret
    
    ## Abstract methods
    def _select_next_task(self):
        pass
    def is_in_preempting_condition(self):
        pass


class FCFS(_ReadyQueue):
    def _select_next_task(self):
        self.next_i, self.next_id = None, None
        if not bool(self.li):
            return
        
        self.next_i, self.next_id = 0, self.li[0]

    def is_in_preempting_condition(self, a_layer_end: bool=False) -> bool:
        self._select_next_task()
        if self.next_id == None:
            return False
        if self.layerwise_preemptive and a_layer_end:
            return True
        return False

class RRB(_ReadyQueue):
    def _select_next_task(self):
        self.next_i, self.next_id = None, None
        if not bool(self.li):
            return
        
        self.next_i, self.next_id = 0, self.li[0]

    def is_in_preempting_condition(self, a_layer_end: bool=False) -> bool:
        self._select_next_task()
        if self.next_id == None:
            return False

        if self.layerwise_preemptive and a_layer_end:
            return True
        if self.scheduler.epoch_time - self.recent_switch_time >= self.time_quota:
            self.recent_switch_time = self.scheduler.epoch_time
            return True
        return False


class HPF(_ReadyQueue):
    def _select_next_task(self, a_layer_end: bool=False):
        tasks = self.scheduler.tasks
        current_id = self.scheduler.current_task_id


        self.next_i, self.next_id = None, None
        if not bool(self.li):
            return
        
        next_i, next_id = None, None

        i, id = 0, self.li[0]
        for _i, _id in enumerate(self.li):
            if tasks[_id].priority > tasks[id].priority:
                i, id = _i, _id

        if current_id == None or tasks[current_id].state == 'END':
            next_i, next_id = i, id
        elif self.preemptive:
            if tasks[id].priority > tasks[current_id].priority:
                next_i, next_id = i, id
            elif self.layerwise_preemptive and a_layer_end:
                if tasks[id].priority >= tasks[current_id].priority:
                    next_i, next_id = i, id

        self.next_i, self.next_id = next_i, next_id

    def is_in_preempting_condition(self, a_layer_end: bool=False) -> bool:
        self._select_next_task(a_layer_end=a_layer_end)
        if self.next_id == None:
            return False

        return True


class TOKEN(_ReadyQueue):
    pass

class SJF(_ReadyQueue):
    pass

class PREMA(_ReadyQueue):
    pass
