from arch import Architecture
from scheduler import Scheduler

import run_nets as r

import os
import argparse


def _df_string(dataflow):
    ret = 'Output Stationary'  # os
    if dataflow == 'ws':
        ret = 'Weight Stationary'
    elif dataflow == 'is':
        ret = 'Input Stationary'
    return ret


class Scale:
    def __init__(self, a='', t=''):
        if a == '':
            a = './configs/eyeriss.cfg'
        if t == '':
            t = './task_list.csv'

        self.arch = Architecture(cfg_path=a)
        self.scheduler = Scheduler(out_dir=self.arch.out_dir, csv_path=t)
    #

    def run(self):
        print("====================================================")
        print("******************* SCALE SIM **********************")
        print("====================================================")
        print(f"Array Size: \t{self.arch.array['h']}x{self.arch.array['w']}")
        print(f"SRAM IFMAP: \t{self.arch.sram_sz['ifmap']}")
        print(f"SRAM Filter: \t{self.arch.sram_sz['filt']}")
        print(f"SRAM OFMAP: \t{self.arch.sram_sz['ofmap']}")
        print(f"Dataflow: \t{_df_string(self.arch.dataflow)}")
        print("====================================================")

        self.scheduler.start()
        while True:
            task = self.scheduler.switch()
            if task == None:
                break
            r.run_slot(self.arch, task, self.scheduler)
            break
        
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
                help='path to the task config file (.csv)'
            )
    
    args = parser.parse_args()
    s = Scale(a=args.a, t=args.t)
    s.run()
#
