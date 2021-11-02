import argparse
import time

import run_nets as r

from arch import Architecture
from scheduling.scheduler import Scheduler, Preemption

from misc import set_style, set_color


def _df_string(dataflow):
    ret = 'Output Stationary'  # os
    if dataflow == 'ws':
        ret = 'Weight Stationary'
    elif dataflow == 'is':
        ret = 'Input Stationary'
    return ret


class Scale:
    def __init__(self, a='', t='', s='', q=0):
        if a == '':
            a = './architectures/eyeriss.cfg'
        if t == '':
            t = './task_list.csv'
        if s == '':
            s = 'PREMA'
        if q <= 0:
            # TPU: 700 MHz, PREMA default time-quota: 0.25 ms
            # -> (700 * 10 ** 6) * 0.25 = 175000000 cycles
            q = 100000
        preemptive = True
        layerwise_scheduling = True
        dynamic = True

        self.arch = Architecture(cfg_path=a)
        self.scheduler = Scheduler(arch=self.arch, csv_path=t, 
                algorithm_name=s, 
                preemptive=preemptive, 
                time_quota=q, 
                layerwise_scheduling=layerwise_scheduling, 
                dynamic=dynamic, 
            )
    #

    def run(self):
        print("====================================================")
        print("******************* SCALE SIM **********************")
        print("====================================================")
        print(f"Architecture: \t{self.arch.name}")
        print("----------------------------------------------------")
        print(f"Array size: \t{self.arch.array['h']}x{self.arch.array['w']}")
        print(f"SRAM IFMAP: \t{int(self.arch.sram_sz['ifmap'] / 1024)}")
        print(f"SRAM Filter: \t{int(self.arch.sram_sz['filt'] / 1024)}")
        print(f"SRAM OFMAP: \t{int(self.arch.sram_sz['ofmap'] / 1024)}")
        print(f"Dataflow: \t{_df_string(self.arch.dataflow)}")
        print("====================================================")
        print(f"Scheduler: \t{set_style(set_style(f' {self.scheduler.algorithm_name} ', key='BOLD'), key='INVERSE')}")
        print(f"Preemptive: \t\t{self.scheduler.ready_q.preemptive}")
        print(f"Layerwise scheduling: \t{self.scheduler.ready_q.layerwise_scheduling}")
        print(f"Dynamic: \t\t{self.scheduler.ready_q.dynamic}")
        print("====================================================")

        self.scheduler.start()
        while True:
            task = self.scheduler.switch()
            if task == None:
                if self.scheduler.has_not_yet_arrived_tasks():
                    continue
                break
            ####
            try:
                r.run_slot(self.arch, task, self.scheduler)
            except Preemption:
                print(set_style(set_color(" PREEMPTED!! ", key='RED'), key='INVERSE'))
                #time.sleep(1)
            ####
        
        print("")
        print("************ SCALE SIM Run Complete ****************")
    #
#


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', metavar='filename', type=str,
                default='',
                help='path to the architecture config file (.cfg)'
            )
    parser.add_argument('-t', metavar='filename', type=str,
                default='',
                help='path to the task list file (.csv)'
            )
    parser.add_argument('-s', metavar='filename', type=str,
                default='',
                help='scheduler algorithm ([FCFS | RRB | HPF | TOKEN | SJF | PREMA])'
            )
    parser.add_argument('-q', metavar='filename', type=int,
                default=0,
                help='time quota of scheduler algorithm (unit: clocks)'
            )
    
    args = parser.parse_args()
    scale = Scale(a=args.a, t=args.t, s=args.s, q=args.q)
    scale.run()
#
