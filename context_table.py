import os
import math


class ContextTable:
    ## load from csv
    def __init__(self, path):
        self.next_task_id = 0
        self.table = {}

        with open(path, 'r') as f:
            first = True
            for row in f:
                if first:
                    first = False
                    continue
                elems = row.strip().split(',')
                if len(elems) < 5:      # Do not continue if incomplete line
                    continue

                self.table[self.next_task_id] = Network(
                        net_name=elems[0],
                        net_path=elems[1],
                        priority=int(elems[2]),
                        arrival_time=int(elems[3])
                    )
                self.next_task_id += 1
            #
        #
    #
#

class Network:
    def __init__(self,
                net_name=None,
                net_path=None,
                priority=None,
                arrival_time=None
            ):
        self.net_name = net_name
        self.priority = priority
        self.arrival_time = arrival_time
        ###

        self.layers = []

        with open(net_path, 'r') as f:
            first = True
            for row in f:
                if first:
                    first = False
                    continue
                elems = row.strip().split(',')
                if len(elems) < 9:      # Do not continue if incomplete line
                    continue

                self.layers.append(Layer(
                        layer_name=elems[0],
                        ifmap={ 'h': int(elems[1]), 'w': int(elems[2]) },
                        filt={ 'h': int(elems[3]), 'w': int(elems[4]) },
                        ch=int(elems[5]),
                        num_filt=int(elems[6]),
                        stride=int(elems[7])
                    ))
            #
        #
    #

    class Layer:
        def __init__(self,
                    layer_name=None, 
                    ifmap=None, filt=None, ch=None,
                    num_filt=None,
                    stride=None
                ):
            self.layer_name = layer_name
            self.ifmap, self.filt, self.ch = ifmap, filt, ch
            self.num_filt = num_filt
            self.stride = stride
            ###

            self.sram_cycles, self.util = 0, 0

 