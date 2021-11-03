import math

## Original: sram_traffic() in sram_traffic_ws.py
def prediction_layer_time(arch, layer):
    E_h = math.floor((layer.ifmap['h'] - layer.filt['h']) / layer.stride) + 1
    E_w = math.floor((layer.ifmap['w'] - layer.filt['w']) / layer.stride) + 1
    e2  = E_h * E_w
    #### gen_trace_ifmap_partial에 floor 안 하고 쓰는 버그 있음
    E_h_BUG = (layer.ifmap['h'] - layer.filt['h'] + layer.stride) / layer.stride
    E_w_BUG = (layer.ifmap['w'] - layer.filt['w'] + layer.stride) / layer.stride
    e2_BUG = int(E_h_BUG * E_w_BUG)
    ####
    
    r2c = layer.filt['h'] * layer.filt['w'] * layer.ch  # px_per_filt

    if arch.array['h'] < r2c:
        num_h_fold = math.ceil(r2c / arch.array['h'])
        max_parallel_window = 1
    else:
        num_h_fold = 1
        max_parallel_window = math.floor(arch.array['h'] / r2c)

    required_cols = layer.num_filt
    max_cols_per_v_fold = max_parallel_window * arch.array['w']
    num_v_fold = math.ceil(required_cols / max_cols_per_v_fold)

    util = 0
    cycles = 0
    prev_cycles = cycles

    try:
        rem_c = required_cols
        v = 0
        while v < num_v_fold:
            cols_this_fold = min(rem_c, max_parallel_window * arch.array['w'])
            filt_done = v * arch.array['w'] * max_parallel_window

            if num_h_fold > 1:
                rem_h = r2c
                h = 0
                while h < num_h_fold:
                    rows_this_fold = min(rem_h, arch.array['h'])

                    cycles_filt = gen_trace_filt_partial(cycles=cycles, 
                            remaining=rows_this_fold
                        )
                    cycles_ifmap = gen_trace_ifmap_partial(cycles=cycles_filt, 
                            e2_BUG=e2_BUG
                        )
                    cycles_ofmap = gen_trace_ofmap(
                            cycles=cycles_filt, 
                            num_cols=arch.array['w'], parallel_window=1,
                            window_size=rows_this_fold, e2=e2,
                            num_filt=layer.num_filt, filt_done=filt_done
                        )
                    cycles = max(cycles_ifmap, cycles_ofmap)

                    rem_h -= rows_this_fold
                    
                    util_this_fold = (rows_this_fold * cols_this_fold) / (arch.array['h'] * arch.array['w'])

                    del_cycles = cycles - prev_cycles
                    util += util_this_fold * del_cycles
                    prev_cycles = cycles

                    ####
                    h += 1
                    ####
                #
            #
            else:
                filt_done = v * arch.array['w'] * max_parallel_window
                _rem_filt = layer.num_filt - filt_done
                _parallel_window = math.ceil(_rem_filt / arch.array['w'])
                parallel_window = min(max_parallel_window, _parallel_window)
            
                cycles_filt = gen_trace_filt(cycles=cycles, 
                        r2c=r2c, parallel_window=parallel_window
                    )
                cycles_ifmap = gen_trace_ifmap(cycles=cycles_filt, 
                        e2=e2
                    )
                cycles_ofmap = gen_trace_ofmap(
                        cycles=cycles_filt,
                        num_cols=arch.array['w'], parallel_window=parallel_window,
                        window_size=r2c, e2=e2,
                        num_filt=layer.num_filt, filt_done=filt_done
                    )
                cycles = max(cycles_ifmap, cycles_ofmap)

                _tmp_util = 0
                _rem = cols_this_fold
                for _ in range(parallel_window):
                    col_used = min(_rem, arch.array['w'])
                    row_used = r2c
                    _tmp_util += row_used * col_used
                    _rem -= col_used
                util_this_fold = _tmp_util / (arch.array['h'] * arch.array['w'])

                del_cycles = cycles - prev_cycles
                util += util_this_fold * del_cycles
                prev_cycles = cycles
            #
            rem_c -= cols_this_fold

            ####
            v += 1
            ####
        #
    finally:
        pass
    
    final_cycles = cycles
    final_util = (util / cycles) * 100
    return final_cycles, final_util


def gen_trace_filt(cycles=None, r2c=None, parallel_window=None):
    cycles += r2c * parallel_window
    return cycles
def gen_trace_ifmap(cycles=None, e2=None):
    cycles += e2
    return cycles

def gen_trace_filt_partial(cycles=None, remaining=None):
    cycles += remaining
    return cycles
def gen_trace_ifmap_partial(cycles=None, e2_BUG=None):
    cycles += e2_BUG
    return cycles

def gen_trace_ofmap(
            cycles=None,
            num_cols=None, parallel_window=None,
            window_size=None, e2=None,
            num_filt=None, filt_done=None
        ):
    if parallel_window > 1:
        cycles += num_cols
    else:
        rem = num_filt - filt_done
        cycles += min(rem, num_cols)
    cycles += window_size

    cycles += e2
    return cycles
