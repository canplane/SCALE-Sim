import argparse

import run_nets as r

from arch import Architecture
from scheduler import Scheduler, Foo_Error


def _df_string(dataflow):
    ret = 'Output Stationary'  # os
    if dataflow == 'ws':
        ret = 'Weight Stationary'
    elif dataflow == 'is':
        ret = 'Input Stationary'
    return ret


class Scale:
    arch: Architecture = None
    scheduler: Scheduler = None

    def __init__(self, a='', t=''):
        if a == '':
            a = './architectures/eyeriss.cfg'
        if t == '':
            t = './task_list.csv'

        self.arch = Architecture(cfg_path=a)
        self.scheduler = Scheduler(out_dir=self.arch.out_dir, csv_path=t)
    #

    def run(self):
        print("====================================================")
        print("******************* SCALE SIM **********************")
        print("====================================================")
        print(f"Architecture: \t{self.arch.name}")
        print("----------------------------------------------------")
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
            try:
                r.run_slot(self.arch, task, self.scheduler)
            except Foo_Error:
                print("잡았다 요놈!")

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
