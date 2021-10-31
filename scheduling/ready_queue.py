class _ReadyQueue:
    def __init__(self, **_keywords):
        self.li = []

        if 'time_quota' in _keywords:
            self.time_quota = _keywords['time_quota']

    def get_list(self) -> list:
        return self.li

    def is_preempting_condition(self, **_keywords) -> bool:
        return False

    
    def push(self, task_id: int):
        self.li.append(task_id)
    def pop(self, epoch_time: int=None) -> int:
        self.recent_switch_time = epoch_time
        return self.li.pop(0) if bool(self.li) else None
    def front(self):
        return self.li[0] if bool(self.li) else None

    



class FCFS(_ReadyQueue):
    pass

class RRB(_ReadyQueue):
    def is_preempting_condition(self, epoch_time: int=None) -> bool:
        if epoch_time - self.recent_switch_time >= self.time_quota:
            self.recent_switch_time = epoch_time
            return True
        else:
            return False


class HPF(_ReadyQueue):
    pass

class TOKEN(_ReadyQueue):
    pass

class SJF(_ReadyQueue):
    pass

class PREMA(_ReadyQueue):
    pass
