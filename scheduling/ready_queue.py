from scheduling.prema.prediction_layer_time import prediction_layer_time


class _ReadyQueue:
    def __init__(self, scheduler, time_quota: int=None, 
                preemptive: bool=None, layerwise_scheduling: bool=None, dynamic: bool=False,
            ):
        self.scheduler = scheduler

        self.li = []
        self.next_i, self.next_id = None, None

        self.time_quota = time_quota
        self.recent_wakeup_time = scheduler.epoch_time

        self.newly_arrived = False

        self.preemptive = preemptive
        self.layerwise_scheduling = layerwise_scheduling

        ## Used in PREMA
        self.dynamic = dynamic

    def get_list(self) -> list:
        return self.li
    
    def push(self, task_id: int) -> None:
        self.li.append(task_id)

        ## PREMA Algorithm 1: Inference Time Prediction Model
        if self.scheduler.tasks[task_id].state == 'NEW':
            self.newly_arrived = True

            task = self.scheduler.tasks[task_id]
            for layer in task.layers:
                estimated_cycles, estimated_util = prediction_layer_time(self.scheduler.arch, layer)
                task.estimated_time += estimated_cycles
                task.estimated_time_per_layer.append(estimated_cycles)
    
    def pop(self) -> int:
        self.newly_arrived = False

        if self.next_id == None:
            self._select_next_task()

        self.recent_wakeup_time = self.scheduler.epoch_time
        if self.next_id != None:
            self.li.pop(self.next_i)
        
        ret = self.next_id
        self.next_i, self.next_id = None, None
        return ret
    
    def _get_remaining_layer_time(self, task):
        return task.estimated_time_per_layer[task.current_layer_idx] - task.executed_time_per_layer[task.current_layer_idx]
    def _get_remaining_time(self, task):
        return task.estimated_time - task.executed_time

    ## PREMA Algorithm 3: Dynamic Preemption Mechanism Selection
    # True if CHECKPOINT, False if DRAIN
    def is_checkpoint(self, current_task, candidate_task):
        if not self.dynamic:
            return True

        if self.layerwise_scheduling:
            current_task_remaining_time = self._get_remaining_layer_time(current_task)
            candidate_task_remaining_time = self._get_remaining_layer_time(candidate_task)
            degradation_current = candidate_task_remaining_time / current_task.estimated_time_per_layer[current_task.current_layer_idx]
            degradation_candidate = current_task_remaining_time / candidate_task.estimated_time_per_layer[candidate_task.current_layer_idx]
        else:
            current_task_remaining_time = self._get_remaining_time(current_task)
            candidate_task_remaining_time = self._get_remaining_time(candidate_task)
            degradation_current = candidate_task_remaining_time / current_task.estimated_time
            degradation_candidate = current_task_remaining_time / candidate_task.estimated_time
        #print(degradation_current, degradation_candidate)

        if degradation_current > degradation_candidate:
            ret = False  ## DRAIN
        else:
            ret = True  ## CHECKPOINT
        return ret

    ## Abstract methods
    def _select_next_task(self):
        pass
    def is_in_preempting_condition(self):
        pass


class FCFS_RRB(_ReadyQueue):
    def _select_next_task(self):
        self.next_i, self.next_id = None, None
        if not bool(self.li):
            return
        ####
        next_i, next_id = 0, self.li[0]
        ####
        self.next_i, self.next_id = next_i, next_id

    def is_in_preempting_condition(self, a_layer_end: bool=False) -> bool:
        tasks = self.scheduler.tasks
        current_id = self.scheduler.current_task_id

        if not (current_id == None or tasks[current_id].state == 'END') and \
                not (self.layerwise_scheduling and a_layer_end) and \
                not (self.preemptive and (self.newly_arrived or (self.scheduler.epoch_time - self.recent_wakeup_time >= self.time_quota))):
            return False
        self._select_next_task()
        if self.next_id == None:
            return False
        ret = False

        if current_id == None or tasks[current_id].state == 'END':
            ret = True
        else:
            ####
            ret = True
            ####
        self.newly_arrived = False
        if self.scheduler.epoch_time - self.recent_wakeup_time >= self.time_quota:
            self.recent_wakeup_time = self.scheduler.epoch_time
        if not ret:
            self.next_i, self.next_id = None, None
        return ret


class HPF(_ReadyQueue):
    def _select_next_task(self):
        self.next_i, self.next_id = None, None
        if not bool(self.li):
            return
        next_i, next_id = None, None
        ####
        tasks = self.scheduler.tasks

        next_i, next_id = 0, self.li[0]
        for i, id in enumerate(self.li):
            if tasks[id].priority > tasks[next_id].priority:
                next_i, next_id = i, id
        ####
        self.next_i, self.next_id = next_i, next_id

    def is_in_preempting_condition(self, a_layer_end: bool=False) -> bool:
        tasks = self.scheduler.tasks
        current_id = self.scheduler.current_task_id

        if not (current_id == None or tasks[current_id].state == 'END') and \
                not (self.layerwise_scheduling and a_layer_end) and \
                not (self.preemptive and (self.newly_arrived or (self.scheduler.epoch_time - self.recent_wakeup_time >= self.time_quota))):
            return False
        self._select_next_task()
        if self.next_id == None:
            return False
        ret = False

        if current_id == None or tasks[current_id].state == 'END':
            ret = True
        else:
            ####
            if tasks[self.next_id].priority > tasks[current_id].priority:
                ret = True
            elif self.layerwise_scheduling and a_layer_end:
                if tasks[self.next_id].priority == tasks[current_id].priority:
                    ret = True

            if ret:
                ret = self.is_checkpoint(tasks[current_id], tasks[self.next_id])
            ####
        self.newly_arrived = False
        if self.scheduler.epoch_time - self.recent_wakeup_time >= self.time_quota:
            self.recent_wakeup_time = self.scheduler.epoch_time
        if not ret:
            self.next_i, self.next_id = None, None
        return ret


## PREMA: SJF, TOKEN, PREMA
class _PREMA(_ReadyQueue):
    ## Find shortest estimated job
    def _find_shortest_estimated_job(self, li_enumerate: list):
        tasks = self.scheduler.tasks

        if self.layerwise_scheduling:
            next_i, next_id = li_enumerate[0]
            for i, id in li_enumerate:
                #if tasks[id].estimated_time_per_layer[tasks[id].current_layer_idx] < tasks[next_id].estimated_time_per_layer[tasks[next_id].current_layer_idx]:
                if self._get_remaining_layer_time(tasks[id]) < self._get_remaining_layer_time(tasks[next_id]):  # SRTF
                    next_i, next_id = i, id
        else:
            next_i, next_id = li_enumerate[0]
            for i, id in li_enumerate:
                #if tasks[id].estimated_time < tasks[next_id].estimated_time:
                if self._get_remaining_time(tasks[id]) < self._get_remaining_time(tasks[next_id]):  # SRTF
                    next_i, next_id = i, id
        return next_i, next_id

    ## PREMA Algorithm 2: PREMA Scheduling Algorithm
    def _select_next_task(self):
        self.next_i, self.next_id = None, None
        if not bool(self.li):
            return
        next_i, next_id = None, None
        ####
        tasks = self.scheduler.tasks

        if self.type == 'SJF':
            next_i, next_id = self._find_shortest_estimated_job(list(enumerate(self.li)))
        else:
            ## Refresh token in all tasks in ready queue
            for id in self.li:
                task = tasks[id]
                if self.layerwise_scheduling:
                    slowdown = task.waited_time_per_layer[task.current_layer_idx] / task.estimated_time_per_layer[task.current_layer_idx]
                else:
                    slowdown = task.waited_time / task.estimated_time
                task.token += task.priority * slowdown

            candidates = { 9: [], 6: [], 3: [] }
            for i, id in enumerate(self.li):
                for threshold in [9, 6, 3]:
                    if tasks[id].token >= threshold:
                        candidates[threshold].append((i, id))
            
            for threshold in [9, 6, 3]:
                if bool(candidates[threshold]):
                    if self.type == 'TOKEN':
                        next_i, next_id = candidates[threshold][0]
                    else:
                        next_i, next_id = self._find_shortest_estimated_job(candidates[threshold])
                    break
        ####
        self.next_i, self.next_id = next_i, next_id
    
    def is_in_preempting_condition(self, a_layer_end: bool=False) -> bool:
        tasks = self.scheduler.tasks
        current_id = self.scheduler.current_task_id

        if not (current_id == None or tasks[current_id].state == 'END') and \
                not (self.layerwise_scheduling and a_layer_end) and \
                not (self.preemptive and (self.newly_arrived or (self.scheduler.epoch_time - self.recent_wakeup_time >= self.time_quota))):
            return False
        self._select_next_task()
        if self.next_id == None:
            return False
        ret = False

        if current_id == None or tasks[current_id].state == 'END':
            ret = True
        else:
            ####
            if ret:
                ret = self.is_checkpoint(tasks[current_id], tasks[self.next_id])
            ####
        self.newly_arrived = False
        if self.scheduler.epoch_time - self.recent_wakeup_time >= self.time_quota:
            self.recent_wakeup_time = self.scheduler.epoch_time
        if not ret:
            self.next_i, self.next_id = None, None
        return ret

class SJF(_PREMA):
    def __init__(self, *t, **s):
        super().__init__(*t, **s)
        self.type = 'SJF'
class TOKEN(_PREMA):
    def __init__(self, *t, **s):
        super().__init__(*t, **s)
        self.type = 'TOKEN'
class PREMA(_PREMA):
    def __init__(self, *t, **s):
        super().__init__(*t, **s)
        self.type = 'PREMA'