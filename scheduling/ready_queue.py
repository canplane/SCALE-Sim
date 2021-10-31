class _ReadyQueue:
    def __init__(self, **keywords):
        self.li = []

        self.current_task_id = None

        self.preemptive = keywords['preemptive']
        self.layerwise_preemptive = keywords['layerwise_preemption']

        if 'time_quota' in keywords:
            self.time_quota = keywords['time_quota']

    def get_list(self) -> list:
        return self.li

    def is_preempting_condition(self, **keywords) -> bool:
        return False
    
    def push(self, task_id: int) -> None:
        self.li.append(task_id)

    def pop(self, **keywords) -> int:
        self.recent_switch_time = keywords['epoch_time']

        candidate_task_id = self.li[0] if bool(self.li) else None
        if candidate_task_id != None:
            self.current_task_id = self.li.pop(0)
        return candidate_task_id


class FCFS(_ReadyQueue):
    def is_preempting_condition(self, **keywords) -> bool:
        if bool(self.li):
            if self.layerwise_preemptive == True and keywords['a_layer_end'] == True:
                return True
        return False

class RRB(_ReadyQueue):
    def is_preempting_condition(self, **keywords) -> bool:
        if bool(self.li):
            if keywords['epoch_time'] - self.recent_switch_time >= self.time_quota:
                self.recent_switch_time = keywords['epoch_time']
                return True
        return False

class HPF(_ReadyQueue):
    def _get_candidate_task_id(self, tasks):
        idx, candidate_task_id = None, None
        for _i, _task_id in list(enumerate(self.li)):
            if candidate_task_id == None or tasks[_task_id].priority > tasks[candidate_task_id].priority:
                idx, candidate_task_id = _i, _task_id

        if candidate_task_id == None:
            return idx, candidate_task_id
        if self.current_task_id == None or tasks[self.current_task_id].state == 'END':
            return idx, candidate_task_id

        if tasks[self.current_task_id].priority >= tasks[candidate_task_id].priority:
            idx, candidate_task_id = None, None
        return idx, candidate_task_id

    def is_preempting_condition(self, **keywords) -> bool:
        tasks = keywords['tasks']

        idx, candidate_task_id = self._get_candidate_task_id(tasks)
        return candidate_task_id != None

    def pop(self, **keywords) -> int:
        tasks = keywords['tasks']

        idx, candidate_task_id = self._get_candidate_task_id(tasks)
        if candidate_task_id != None:
            self.current_task_id = self.li.pop(idx)
        return candidate_task_id

class TOKEN(_ReadyQueue):
    pass

class SJF(_ReadyQueue):
    pass

class PREMA(_ReadyQueue):
    pass
