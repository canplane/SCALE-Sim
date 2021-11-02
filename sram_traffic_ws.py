import math
from tqdm import tqdm

from scale_error import *
from misc import set_style, set_color


def sram_traffic(arch, layer, scheduler):
    task = layer.parent

    # Dimensions of output feature map channel : (ofmap[w] - 1) * stride + filt[w] <= ifmap[w]
    E_h = math.floor((layer.ifmap['h'] - layer.filt['h']) / layer.stride) + 1
    E_w = math.floor((layer.ifmap['w'] - layer.filt['w']) / layer.stride) + 1
    
    # Number of pixels in one convolution window (한 필터 윈도우에 들어가는 픽셀 수?)
    px_per_filt = layer.filt['h'] * layer.filt['w'] * layer.ch
    r2c = px_per_filt

    # Total number of ofmap px across all channels
    e2 = E_h * E_w
    #num_ofmap_px = E_h * E_w * layer.num_filt
    #e2m = num_ofmap_px

    # Variables to calculate folds in runtime
    # num_h_fold : horizontal선으로 접기 : 하나의 컨볼루션 필터 커널의 칸 수 * 채널 수와 관련
    # num_v_fold : vertical선으로 접기: 필터 개수와 관련
    if arch.array['h'] < px_per_filt:
        num_h_fold = math.ceil(px_per_filt / arch.array['h'])
        max_parallel_window = 1
    else:
        num_h_fold = 1
        max_parallel_window = math.floor(arch.array['h'] / px_per_filt)

    required_cols = layer.num_filt                    # Total number of cols to be mapped
    max_cols_per_v_fold = max_parallel_window * arch.array['w']
    num_v_fold = math.ceil(required_cols / max_cols_per_v_fold)

    # Variables for utilization calculation
    util = layer.load_var('util', init=0)
    cycles = layer.load_var('cycles', init=0)
    prev_cycles = cycles

    #print("Vertical folds = {num_v_fold}")
   
    # These are the starting addresses of filter weights in the memory 
    all_col_addr_list = [(i * r2c + arch.base_addr['filt']) for i in range(layer.num_filt)]

    # These are the starting addresses of ifmap windows in the memory
    '''hc = layer.ifmap['w'] * layer.ch
    all_ifmap_base_addr = []
    for px in range(e2):         #number of ofmap px in a ofmap channel
        addr = (px / E_w) * layer.stride * hc + (px % E_w) * layer.stride
        all_ifmap_base_addr.append(addr)'''

    try:
        pbar_v = tqdm(total=num_v_fold, desc="v_fold", bar_format="{l_bar}" + set_color("{bar}", key=task.color) + "{r_bar}")
        pbar_h = tqdm(total=num_h_fold, desc="h_fold", bar_format="{l_bar}" + set_color("{bar}", key=task.color) + "{r_bar}")

        rem_c = layer.load_var('rem_c', init=required_cols)
        v = layer.load_var('v', init=0); pbar_v.update(v)
        while v < num_v_fold:
            pbar_h.reset()

            #print(f"V fold id: {v}")
                
            # Take a slice of the starting addresses that are relevant for this v_fold 
            cols_this_fold = min(rem_c, max_parallel_window * arch.array['w'])
            idx_start = v * arch.array['w']
            idx_end = idx_start + cols_this_fold
            col_addr_list = all_col_addr_list[idx_start:idx_end]

            filt_done = v * arch.array['w'] * max_parallel_window

            if num_h_fold > 1:
                #next_ifmap_addr = arch.base_addr['ifmap']    # Starts from the top left corner of the IFMAP matrix
                
                rem_h = layer.load_var('rem_h', init=r2c)                    # Tracks the elements processed within a conv filter 
                h = layer.load_var('h', init=0); pbar_h.update(h)
                while h < num_h_fold:
                    rows_this_fold = min(rem_h, arch.array['h'])
                    #print(f"h fold id: {h}")

                    # Values returned
                    # cycle         -> Cycle count for the next operation ie. cycles elapsed + 1
                    # col_addr_list -> The starting filter address for the next iteration
                    #print("\ncycles:", cycles, "--")
                    cycles_filt, col_addr_list = gen_trace_filt_partial(
                            col_addrs   = col_addr_list,
                            cycles      = cycles,
                            num_rows    = arch.array['h'],
                            remaining   = rows_this_fold,
                            sram_read_trace_file = layer.trace_paths['sram']['read']
                        )
                    #print("filt:", cycles_filt, "--")
                    #print(f"Weights loaded by {cycle} cycles")
                    #data_out_cycle = cycle    #Store this cycle for parallel readout
                    cycles_ifmap = gen_trace_ifmap_partial(
                            cycles = cycles_filt, 
                            num_rows = arch.array['h'], num_cols = arch.array['w'],
                            num_filt = layer.num_filt,
                            remaining = rem_h,
                            rem_filt = rem_c, 
                            ifmap_h = layer.ifmap['h'], ifmap_w = layer.ifmap['w'],
                            filt_h = layer.filt['h'], filt_w = layer.filt['w'],
                            num_ch = layer.ch,
                            stride = layer.stride, ifmap_base = arch.base_addr['ifmap'],
                            sram_read_trace_file = layer.trace_paths['sram']['read']
                        )
                    #print("ifmap", cycles_ifmap, "--")
                    cycles_ofmap = gen_trace_ofmap(
                            cycles = cycles_filt, 
                            num_rows = arch.array['h'],
                            num_cols = arch.array['w'],
                            ofmap_base = arch.base_addr['ofmap'],
                            window_size= rows_this_fold,
                            parallel_window = 1,
                            num_ofmap_px = e2,
                            filt_done = filt_done,
                            num_filt = layer.num_filt,
                            sram_write_trace_file = layer.trace_paths['sram']['write']
                        )
                    #print("ofmap", cycles_ofmap, "--")
                    cycles = max(cycles_ifmap, cycles_ofmap)

                    rem_h -= rows_this_fold
                    
                    util_this_fold = (rows_this_fold * cols_this_fold) / (arch.array['h'] * arch.array['w'])

                    _del_cycles = cycles - prev_cycles
                    util += util_this_fold * _del_cycles
                    prev_cycles = cycles

                    ####
                    h += 1; pbar_h.update(1)
                    if h < num_h_fold:
                        layer.store_var({ 'h': h, 'rem_h': rem_h })
                        layer.store_var({ 'cycles': cycles, 'util': util })
                        scheduler.refresh()
                    ####
                #
                layer.clear_var([ 'h', 'rem_h' ])
            #
            else:
                #filters_this_fold = min(rem_c, max_cols_per_v_fold)
                _rem_filt = layer.num_filt - filt_done
                _parallel_window = math.ceil(_rem_filt / arch.array['w'])
                parallel_window = min(max_parallel_window, _parallel_window)
            
                #print("\ncycles:", cycles, "--")
                cycles_filt = gen_trace_filt(
                        cycles = cycles,
                        num_rows = arch.array['h'], num_cols = arch.array['w'],
                        filt_h = layer.filt['h'], filt_w = layer.filt['w'], num_ch = layer.ch,
                        col_addr = col_addr_list, 
                        parallel_window = parallel_window,
                        filters_this_fold = cols_this_fold,
                        sram_read_trace_file = layer.trace_paths['sram']['read']
                    )
                #print("filt:", cycles_filt, "--")
                cycles_ifmap, rows_this_fold = gen_trace_ifmap(
                        cycles = cycles_filt,
                        num_rows = arch.array['h'], num_cols = arch.array['w'],
                        ifmap_h = layer.ifmap['h'], ifmap_w = layer.ifmap['w'],
                        filt_h = layer.filt['h'], filt_w = layer.filt['w'],
                        num_ch = layer.ch, stride = layer.stride,
                        parallel_window = parallel_window,
                        sram_read_trace_file = layer.trace_paths['sram']['read']
                    )
                #print("ifmap", cycles_ifmap, "--")
                cycles_ofmap = gen_trace_ofmap(
                        cycles = cycles_filt,
                        num_rows = arch.array['h'], num_cols = arch.array['w'],
                        ofmap_base = arch.base_addr['ofmap'], 
                        parallel_window = parallel_window,
                        window_size = r2c,
                        num_ofmap_px = e2,
                        num_filt = layer.num_filt,
                        filt_done = filt_done,
                        sram_write_trace_file = layer.trace_paths['sram']['write']
                    )
                #print("ofmap", cycles_ofmap, "--")
                cycles = max(cycles_ifmap, cycles_ofmap)

                # Since multiple filters are being mapped on a single col due to large number of rows
                # util calculation is a little involved,
                # cols_this_fold --> number of filters mapped this fold

                _tmp_util = 0
                _rem = cols_this_fold
                for _ in range(parallel_window):
                    col_used = min(_rem, arch.array['w'])
                    row_used = r2c                      # Number of row used will always be in multiple of r2c,
                                                        # parallel window calc took care of this
                    _tmp_util += row_used * col_used
                    _rem -= col_used
                util_this_fold = _tmp_util / (arch.array['h'] * arch.array['w'])

                _del_cycles = cycles - prev_cycles
                util += util_this_fold * _del_cycles
                prev_cycles = cycles

                ####
                pbar_h.update(1)
                ####
            #
            rem_c -= cols_this_fold

            ####
            v += 1; pbar_v.update(1)
            if v < num_v_fold:
                layer.store_var({ 'v': v, 'rem_c': rem_c })
                layer.store_var({ 'cycles': cycles, 'util': util })
                scheduler.refresh()
            ####
        #
        layer.clear_var([ 'v', 'rem_c' ])
    finally:
        pbar_v.close(); pbar_h.close()
    
    final_cycles = cycles
    final_util = (util / cycles) * 100

    ####
    layer.clear_var([ 'cycles', 'util' ])
    if not layer.is_no_vars():
        raise SCALE_Error("Variables remained in completed layer")
    
    layer.store_var({ 'cycles': cycles, 'util': util })
    ####
    
    #print(f"Compute finished at: {final} cycles")
    return final_cycles, final_util


def gen_trace_filt(
            cycles = 0,
            num_rows = 4, num_cols = 4,
            filt_h = 3, filt_w = 3, num_ch = 3,
            col_addr = [],
            parallel_window = 1,
            filters_this_fold = 4,
            sram_read_trace_file = "sram_read.csv"
        ):
    outfile = open(sram_read_trace_file,'a')
 
    # There is no data from the left side till the weights are fed in
    # This prefix is to mark the blanks
    prefix  = ""
    for r in range(num_rows):
        prefix += ", "

    # Calculate the convolution window size
    r2c = filt_h * filt_w * num_ch

    rem = filters_this_fold                 # Track the number of filters yet to process

    #For each wrap around
    for w in range(parallel_window):
        # Number of active columns in this wrap
        cols = min(num_cols, rem)
        rem -= cols

        # For each row in the window
        for r in range(r2c):
            entry = str(cycles) + ", " + prefix
            cycles += 1
            
            # In each cycle, for each column feed one weight
            for c in range(cols):
                indx  = w * num_cols + c
                entry += str(col_addr[indx]) + ", "         
                col_addr[indx] += 1

            if cols < num_cols:
                for _ in range(c, num_cols):
                    entry += ", "

            entry += "\n"
            outfile.write(entry)
 
    outfile.close()
    return cycles


def gen_trace_ifmap(
            cycles = 0,
            num_rows = 4, num_cols = 4,
            ifmap_h = 7, ifmap_w = 7,
            filt_h = 3, filt_w = 3,
            num_ch = 3, stride = 1,
            parallel_window = 1,
            sram_read_trace_file = "sram_read.csv"
        ):
    outfile = open(sram_read_trace_file,'a')
    postfix = ""
    for c in range(num_cols):
        postfix += ", "
    
    E_h = math.floor((ifmap_h - filt_h) / stride) + 1
    E_w = math.floor((ifmap_w - filt_w) / stride) + 1
    e2  = E_h * E_w
    r2c = filt_h * filt_w * num_ch
    rc = filt_w * num_ch
    hc = ifmap_w * num_ch

    idle = num_rows - (r2c * parallel_window)
    idle = max(idle, 0)
    used_rows = num_rows - idle

    # Adding entries for columns and empty rows
    #print("Idle lanes = " + str(idle))
    idle += num_cols
    for i in range(idle):
        postfix += ", "
    postfix += "\n"

    base_addr = 0
    
    for e in range(e2):
        entry = str(cycles) + ", "
        cycles += 1    

        #print("Cycles = " + str(cycles))
        #Inner loop for all the rows in array
        num_rows = r2c 
        row_entry = []
        for r in range(num_rows):
            row_idx = math.floor(r / rc)  # math.floor to get in integral value
            col_idx = r % rc 
            add = base_addr + row_idx * hc + col_idx 
            #print("Row idx " + str(row_idx) + " col_idx " + str(col_idx) +" add " + str(add))
            row_entry.append(add)

        # Reverse the printing order
        # Reversal is needed because the filter are stored in upside down order in the array
        # ie. last row has the first weight element
        l = len(row_entry)
        #print("Parallel windows = " + str(parallel_window))
        for w in range(parallel_window):
            #print("Window = " + str(w))
            for ridx in range(l):
                entry += str(row_entry[l - ridx -1]) + ", "

        entry += postfix
        outfile.write(entry)

        # Calculate the IFMAP addresses for next cycle
        px_this_row = (e+1) % E_w
        if px_this_row == 0:
            #print("New row")
            ifmap_row = math.floor(base_addr / hc)
            base_addr = (ifmap_row +  stride) * hc
        else:
            base_addr += stride * num_ch
        #print("OFAMP px = " + str(e+1) + " base_addr: " + str(base_addr))

    outfile.close()
    return cycles, used_rows


def gen_trace_filt_partial(
            col_addrs=[],       #Ensure that this takes care of the v_folding
            cycles=0,
            num_rows=4,
            remaining=4,
            sram_read_trace_file="sram_read.csv"
        ):
    outfile = open(sram_read_trace_file, 'a')
    num_cols = len(col_addrs)

    # output formatting: Add empty commas for row addresses as no element is fed from the left
    prefix = ""
    for r in range(num_rows):
        prefix += ", "

    # Entries per cycle 
    for r in range(remaining):              # number of rows this cycle
        entry = str(cycles) + ", " + prefix

        for c in range(num_cols):
            entry += str(col_addrs[c]) + ", "
            col_addrs[c] += 1
        
        cycles += 1
        entry += "\n"
        outfile.write(entry)

    outfile.close()

    return cycles, col_addrs


def gen_trace_ifmap_partial(
            cycles = 0,
            num_rows = 4, num_cols = 4,
            remaining=4,
            num_filt = 8,            #   
            rem_filt = 0,      # These two are used to track the reads of PS
            ifmap_h = 4, ifmap_w = 4,
            filt_h = 3, filt_w = 3,
            num_ch = 3,
            stride = 1, 
            ifmap_base = 0, ofmap_base = 2000000,
            sram_read_trace_file = "sram_read.csv"
        ):
    outfile = open(sram_read_trace_file, 'a')
    postfix = ""
    for c in range(num_cols):
        postfix += ", "
    postfix += "\n"

    r2c = filt_h * filt_w * num_ch
    rc = filt_w * num_ch
    hc = ifmap_w * num_ch
    E_w = math.floor((ifmap_w - filt_w + stride) / stride)
    E_h = math.floor((ifmap_h - filt_h + stride) / stride)

    num_ofmap_px = E_h * E_w
    index = r2c - remaining
    base_addr = 0 
            
    filt_done = num_filt - rem_filt
    #outfile.write(str(filter_done) + ", " + str(num_filt)+", "+str(rem_filt)+", "+ "\n")
    #ofmap_offset = filter_done * e2
    ofmap_offset = filt_done
    effective_cols = min(rem_filt, num_cols)
    tick = 0                                # Proxy for clock to track input skewing

    # Outerloop for all ofmap pixels in an ofmap channel
    for e in range(num_ofmap_px):
        entry = str(cycles) + ", "
        cycles += 1    

        #print("Cycle= " + str(cycle))
        #Inner loop for all the rows in array
        num_rows = min(num_rows, remaining)
        row_entry = []
        for r in range(num_rows):
            row_idx = math.floor((index+r) / rc)  # math.floor to get in integral value
            col_idx = (index+r) % rc 
            add = base_addr + row_idx * hc + col_idx 
            #print("Row idx " + str(row_idx) + " col_idx " + str(col_idx) +" add " + str(add))
            row_entry.append(add)

        # Reverse the printing order
        # Reversal is needed because the filter are stored in upside down order in the array
        # ie. last row has the first weight element
        l = len(row_entry)
        for ridx in range(l):
            entry += str(row_entry[l - ridx -1]) + ", "

        # In case of partial mapping
        # index > 0 implies that there is a partial sum generated from prev h_fold
        # This partial sum is now fed from the top to be summed with the PS generated in this h_fold
        # The following part print the read addresses for PS
        # Anand : TODO, Implementation choice, do not support right now
        '''
        if index > 0:
            postfix = ""
            for c in range(effective_cols):
                if (tick - c) > -1:                       # Track PS reads for skew
                    a = (e - c) * num_filt + c        # e - c: Taking care of skew by c cycles
                    a = a + ofmap_base + ofmap_offset
                    postfix += str(a) + ", "
                else:
                    postfix += ", "
            tick += 1
            #print("Tick =", str(tick) + "Postfix= " + postfix)
            postfix += "\n"
        '''
        entry += postfix
        outfile.write(entry)

        px_this_row = (e+1) % E_w
        if px_this_row == 0:
            #print("New row")
            ifmap_row = math.floor(base_addr / hc)
            base_addr = (ifmap_row + stride) * hc
        else:
            base_addr += stride * num_ch
        #print("OFAMP px = " + str(e+1) + " base_addr: " + str(base_addr))

    outfile.close()
    return cycles


def gen_trace_ofmap(
            cycles = 0,
            num_rows = 4, num_cols =4,
            ofmap_base = 2000000,
            parallel_window = 1,
            window_size = 27,
            num_ofmap_px = 16,      # This is per ofmap channel
            filt_done = 0,       # To track v fold
            num_filt   = 8,       # To track if all filters have finished
            sram_write_trace_file = "sram_write.csv"
        ):
    outfile = open(sram_write_trace_file,'a')
    #cycles = num_cols + cycles     # Accounts for the time taken to reduce accross all cols

    # Corner case when parallel_window = 1, but num_filt < num_cols
    if parallel_window > 1:
        cycles += num_cols
        cycles += window_size                # window_size == r2c
    else:
        rem    = (num_filt - filt_done)
        cycles += min(rem, num_cols)
        cycles += window_size

    #ofmap_add_offset  = filt_done * num_ofmap_px
    ofmap_add_offset  = filt_done
    rem_filt = num_filt - filt_done
    
    effective_cols    = num_cols * parallel_window
    effective_cols    = min(effective_cols, rem_filt)

    for e in range(num_ofmap_px):
        entry = str(cycles) + ", "
        cycles += 1
        
        done = filt_done
        for col in range(effective_cols):
            if done < num_filt:
                a = e * num_filt + col                # z first row major
                a = a + ofmap_add_offset + ofmap_base
                entry += str(a) + ", "
            else: 
                # Code should not enter this part
                entry += "!, "

        entry += "\n"
        outfile.write(entry)

    outfile.close()
    return cycles


# Trace generation for moving generated ofmap data in cases when only partial window fits
# This implementation prints out the ofmap pixel in the exact cycle it is generated
# Not used in scale sim at the moment. 
# SCALE sim waits till all the columns finish generating OFMAP.
'''def gen_trace_ofmap_partial_imm(
                        cycles = 0,
                        num_rows = 4, num_cols =4,
                        ofmap_base = 2000000,
                        num_ofmap_px = 16,
                        num_filt = 8,
                        filt_done = 0,
                        sram_write_trace_file = "sram_write.csv"
):
    outfile = open(sram_write_trace_file,'a')
    start_cycles = num_rows + cycles

    col_addr = []
    for col in range(num_cols):
        a = (filt_done + col)
        col_addr.append(a)
    
    for tick in range(num_ofmap_px + num_cols):
        cycles = start_cycles + tick

        entry = str(cycles) + ", "
        for col in range(num_cols):
            # Condition to maintain skew
            if tick >= col and (tick - col)< num_ofmap_px:
                entry += str(col_addr[col]) + ", "
                col_addr[col] += num_filt
            else:
                entry += ", "
        
        entry += "\n"
        outfile.write(entry)

    outfile.close()'''


'''if __name__ == "__main__":
    h_h = 5 
    h_w = 5

    r_h = 2
    r_w = 2

    c = 2
    u =1

    m = 9

    dim_h = 16
    dim_v = 5

    sram_traffic(
        dimension_rows = dim_h,
        dimension_cols = dim_v,

        ifmap_h = h_h, ifmap_w = h_w,
        filt_h = r_h, filt_w = r_w, 
        num_ch = c,
        strides = u,

        num_filt = m
    )
'''
