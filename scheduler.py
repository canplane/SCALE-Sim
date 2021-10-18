from task import Task


class Preemption(Exception):
    def __init__(self, msg=None):
        if not msg == None:
            print(msg)


class Scheduler:
    def __init__(self, out_dir="./outputs", csv_path=None):
        self.context_table = {}
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
        self.context_table[self.next_task_id] = Task(
                task_id=self.next_task_id,
                net_name=net_name,
                net_path=net_path,
                priority=priority,
                arrival_time=arrival_time,

                out_parent_dir=self.out_dir
            )
        self.next_task_id += 1
    #

    def start(self):
        pass
    #
    def refresh(self):
        raise Preemption()
    #
    def switch(self):
        return self.context_table[0]
    #
#
