class PreemptionModule():
    def __init__(self, path):
        self.next_task_id = 0
        self.context_table = {}

        with open(path, 'r') as f:
            first = True
            for row in f:
                if first:
                    first = False
                    continue
                elems = row.strip().split(',')

                self.add_task(
                    net_name=elems[0],
                    net_path=elems[1],
                    priority=elems[2],
                    arrive_time=elems[3],
                )
                # net_name = self.net_path.split('/')[-1].split('.')[0]
            #
        #
    #

    def add_task(self,
                net_name=None, 
                net_path=None, 
                priority=None, 
                arrive_time=None
            ):
        self.context_table[self.next_task_id] = {

        }



        


        #
        self.next_task_id += 1
    #
#

