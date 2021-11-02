import dram_trace as dram
import sram_traffic_os as sram_os
import sram_traffic_ws as sram_ws
import sram_traffic_is as sram_is


def gen_all_traces(arch, layer, scheduler):
    print('Generating traces and bw numbers')
    sram_cycles, util = \
            { 'os': sram_os, 'ws': sram_ws, 'is': sram_is }.get(arch.dataflow, 'os').sram_traffic(
                    arch, layer, scheduler
                )

    #print('Generating DRAM traffic')
    word_sz_bytes = 1
    dram.dram_trace_read_v2(
        sram_sz=arch.sram_sz['ifmap'],
        word_sz_bytes=word_sz_bytes,
        min_addr=arch.base_addr['ifmap'], max_addr=arch.base_addr['filt'],
        sram_trace_file=layer.trace_paths['sram']['read'],
        dram_trace_file=layer.trace_paths['dram']['ifmap']
    )
    dram.dram_trace_read_v2(
        sram_sz=arch.sram_sz['filt'],
        word_sz_bytes=word_sz_bytes,
        min_addr=arch.base_addr['filt'], max_addr=arch.base_addr['ofmap'],
        sram_trace_file=layer.trace_paths['sram']['read'],
        dram_trace_file=layer.trace_paths['dram']['filt']
    )
    dram.dram_trace_write(
        ofmap_sram_size=arch.sram_sz['ofmap'],
        data_width_bytes=word_sz_bytes,
        sram_write_trace_file=layer.trace_paths['sram']['write'],
        dram_write_trace_file=layer.trace_paths['dram']['ofmap']
    )

    print(f'Cycles for compute  : \t{sram_cycles} cycles')
    print(f'Average utilization : \t{util:.6f} %')
    bw_numbers, detail_log = gen_bw_numbers(layer.trace_paths)  #array_h, array_w)

    return bw_numbers, detail_log, sram_cycles, util
#

def gen_max_bw_numbers(trace_paths=None):
    ## dram_ifmap_trace_file
    max_dram_activation_bw, max_dram_act_clk = 0, ''
    with open(trace_paths['dram']['ifmap'], 'r') as f:
        for row in f:
            clk = row.split(',')[0]
            num_bytes = len(row.split(',')) - 2

            if max_dram_activation_bw < num_bytes:
                max_dram_activation_bw, max_dram_act_clk = num_bytes, clk
    
    ## dram_filter_trace_file
    max_dram_filter_bw, max_dram_filt_clk = 0, ''
    with open(trace_paths['dram']['filt'], 'r') as f:
        for row in f:
            clk = row.split(',')[0]
            num_bytes = len(row.split(',')) - 2

            if max_dram_filter_bw < num_bytes:
                max_dram_filter_bw, max_dram_filt_clk = num_bytes, clk

    ## dram_ofmap_trace_file
    max_dram_ofmap_bw, max_dram_ofmap_clk = 0, ''
    with open(trace_paths['dram']['ofmap'], 'r') as f:
        for row in f:
            clk = row.split(',')[0]
            num_bytes = len(row.split(',')) - 2

            if max_dram_ofmap_bw < num_bytes:
                max_dram_ofmap_bw, max_dram_ofmap_clk = num_bytes, clk
    
    ## sram_write_trace_file
    max_sram_ofmap_bw = 0
    with open(trace_paths['sram']['write'], 'r') as f:
        for row in f:
            num_bytes = len(row.split(',')) - 2

            if max_sram_ofmap_bw < num_bytes:
                max_sram_ofmap_bw = num_bytes

    ## sram_read_trace_file
    max_sram_read_bw = 0
    with open(trace_paths['sram']['read'], 'r') as f:
        for row in f:
            num_bytes = len(row.split(',')) - 2

            if max_sram_read_bw < num_bytes:
                max_sram_read_bw = num_bytes


    #print('DRAM IFMAP Read BW, DRAM Filter Read BW, DRAM OFMAP Write BW, SRAM OFMAP Write BW')
    log = f'{max_dram_activation_bw},\t{max_dram_filter_bw},\t{max_dram_ofmap_bw},\t{max_sram_read_bw},\t{max_sram_ofmap_bw},'
    # Anand: Enable the following for debug print
    #log += f'{max_dram_act_clk},\t{max_dram_filt_clk},\t{max_dram_ofmap_clk},'
    #print(log)
    return log
#

def gen_bw_numbers(trace_paths=None
            #array_h, array_w): # These are needed for utilization calculation
        ):
    min_clk, max_clk = 100000, -1
    detail_log = ''

    ## dram_ifmap_trace_file
    num_dram_activation_bytes = 0
    with open(trace_paths['dram']['ifmap'], 'r') as f:
        first = True
        for row in f:
            num_dram_activation_bytes += len(row.split(',')) - 2
            
            elems = row.strip().split(',')
            clk = float(elems[0])

            if first:
                first, start_clk = False, clk

            if clk < min_clk:
                min_clk = clk

        stop_clk = clk
        detail_log += f'{start_clk},\t{stop_clk},\t{num_dram_activation_bytes},\t'

    ## dram_filter_trace_file
    num_dram_filter_bytes = 0
    with open(trace_paths['dram']['filt'], 'r') as f:
        first = True
        for row in f:
            num_dram_filter_bytes += len(row.split(',')) - 2

            elems = row.strip().split(',')
            clk = float(elems[0])

            if first:
                first, start_clk = False, clk

            if clk < min_clk:
                min_clk = clk

        stop_clk = clk
        detail_log += f'{start_clk},\t{stop_clk},\t{num_dram_filter_bytes},\t'
    
    ## dram_ofmap_trace_file
    num_dram_ofmap_bytes = 0
    with open(trace_paths['dram']['ofmap'], 'r') as f:
        first = True
        for row in f:
            num_dram_ofmap_bytes += len(row.split(',')) - 2

            elems = row.strip().split(',')
            clk = float(elems[0])

            if first:
                first, start_clk = False, clk

        stop_clk = clk
        detail_log += f'{start_clk},\t{stop_clk},\t{num_dram_ofmap_bytes},\t'
    
    if clk > max_clk:
        max_clk = clk

    ## sram_write_trace_file
    num_sram_ofmap_bytes = 0
    with open(trace_paths['sram']['write'], 'r') as f:
        first = True
        for row in f:
            num_sram_ofmap_bytes += len(row.split(',')) - 2
            elems = row.strip().split(',')
            clk = float(elems[0])

            if first:
                first, start_clk = False, clk

        stop_clk = clk
        detail_log += f'{start_clk},\t{stop_clk},\t{num_sram_ofmap_bytes},\t'
    
    if clk > max_clk:
        max_clk = clk
    
    ## sram_read_trace_file
    num_sram_read_bytes = 0
    #total_util = 0
    with open(trace_paths['sram']['read'], 'r') as f:
        first = True
        for row in f:
            #num_sram_read_bytes += len(row.split(',')) - 2
            elems = row.strip().split(',')
            clk = float(elems[0])

            if first:
                first, start_clk = False, clk

            #util, valid_bytes = parse_sram_read_data(elems[1:-1], array_h, array_w)
            valid_bytes = parse_sram_read_data(elems[1:])
            num_sram_read_bytes += valid_bytes
            #total_util += util
            #print(f'Total Util {total_util}, util {util}')

        stop_clk = clk
        detail_log += f'{start_clk},\t{stop_clk},\t{num_sram_read_bytes},\t'
    
    #sram_clk = clk
    if clk > max_clk:
        max_clk = clk

    delta_clk = max_clk - min_clk

    dram_activation_bw  = num_dram_activation_bytes / delta_clk
    dram_filter_bw      = num_dram_filter_bytes / delta_clk
    dram_ofmap_bw       = num_dram_ofmap_bytes / delta_clk
    sram_ofmap_bw       = num_sram_ofmap_bytes / delta_clk
    sram_read_bw        = num_sram_read_bytes / delta_clk
    #print(f'total_util: {total_util}, sram_clk: {sram_clk}')
    #avg_util            = total_util / sram_clk * 100

    UNIT = 'Bytes/cycle'
    print(f'DRAM IFMAP Read BW  : \t{dram_activation_bw:.6f} {UNIT}')
    print(f'DRAM Filter Read BW : \t{dram_filter_bw:.6f} {UNIT}')
    print(f'DRAM OFMAP Write BW : \t{dram_ofmap_bw:.6f} {UNIT}')
    #print(f'Average utilization : \t{avg_util} %')
    #print('SRAM OFMAP Write BW, Min clk, Max clk')
    
    log = f'{dram_activation_bw},\t{dram_filter_bw},\t{dram_ofmap_bw},\t{sram_read_bw},\t{sram_ofmap_bw},'
    # Anand: Enable the following line for debug
    #log += f'{min_clk},\t{max_clk},'
    #print(log)
    #return log, avg_util
    return log, detail_log
#

def parse_sram_read_data(elems):  #array_h, array_w):
    #half = int(len(elems) /2)
    #nz_row = 0
    #nz_col = 0
    data = 0

    for i in range(len(elems)):
        e = elems[i]
        if e != ' ':
            data += 1
            #if i < half:
            #if i < array_h:
            #    nz_row += 1
            #else:
            #    nz_col += 1

    #util = (nz_row * nz_col) / (half * half)
    #util = (nz_row * nz_col) / (array_h * array_w)
    #data = nz_row + nz_col
    
    #return util, data
    return data
#
