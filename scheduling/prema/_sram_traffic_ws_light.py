import math
import sys
from tqdm import tqdm

from scale_error import *
from misc import set_style, set_color


def sram_traffic(arch, layer, scheduler):
    task = layer.parent

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

    util = layer.load_var('util', init=0)    
    cycles = layer.load_var('cycles', init=0)
    prev_cycles = cycles

    try:
        pbar_v = tqdm(total=num_v_fold, desc="v_fold", bar_format="{l_bar}" + set_color("{bar}", key=task.color) + "{r_bar}")
        pbar_h = tqdm(total=num_h_fold, desc="h_fold", bar_format="{l_bar}" + set_color("{bar}", key=task.color) + "{r_bar}")

        rem_c = layer.load_var('rem_c', init=required_cols)
        v = layer.load_var('v', init=0); pbar_v.update(v)
        while v < num_v_fold:
            pbar_h.reset()

            cols_this_fold = min(rem_c, max_parallel_window * arch.array['w'])
            filt_done = v * arch.array['w'] * max_parallel_window

            if num_h_fold > 1:
                rem_h = layer.load_var('rem_h', init=r2c)
                h = layer.load_var('h', init=0); pbar_h.update(h)
                while h < num_h_fold:
                    rows_this_fold = min(rem_h, arch.array['h'])

                    #print("\ncycles:", cycles, "--")
                    cycles_filt = gen_trace_filt_partial(cycles=cycles, 
                            remaining=rows_this_fold
                        )
                    #print("filt:", cycles_filt, "--")
                    cycles_ifmap = gen_trace_ifmap_partial(cycles=cycles_filt, 
                            e2_BUG=e2_BUG
                        )
                    #print("ifmap", cycles_ifmap, "--")
                    cycles_ofmap = gen_trace_ofmap(
                            cycles=cycles_filt, 
                            num_cols=arch.array['w'], parallel_window=1,
                            window_size=rows_this_fold, e2=e2,
                            num_filt=layer.num_filt, filt_done=filt_done
                        )
                    #print("ofmap", cycles_ofmap, "--")
                    cycles = max(cycles_ifmap, cycles_ofmap)

                    rem_h -= rows_this_fold
                    
                    util_this_fold = (rows_this_fold * cols_this_fold) / (arch.array['h'] * arch.array['w'])

                    del_cycles = cycles - prev_cycles
                    util += util_this_fold * del_cycles
                    prev_cycles = cycles

                    ####
                    scheduler.epoch_time += del_cycles

                    sys.stderr.write("\033[F")  # back to previous line
                    sys.stderr.write("\033[K")  # clear line
                    print(f"Epoch time: \t{scheduler.recent_switched_epoch_time} -> {set_color(scheduler.epoch_time, key=task.color)}", file=sys.stderr)

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
                filt_done = v * arch.array['w'] * max_parallel_window
                _rem_filt = layer.num_filt - filt_done
                _parallel_window = math.ceil(_rem_filt / arch.array['w'])
                parallel_window = min(max_parallel_window, _parallel_window)
            
                #print("\ncycles:", cycles, "--")
                cycles_filt = gen_trace_filt(cycles=cycles, 
                        r2c=r2c, parallel_window=parallel_window
                    )
                #print("filt:", cycles_filt, "--")
                cycles_ifmap = gen_trace_ifmap(cycles=cycles_filt, 
                        e2=e2
                    )
                #print("ifmap", cycles_ifmap, "--")
                cycles_ofmap = gen_trace_ofmap(
                        cycles=cycles_filt,
                        num_cols=arch.array['w'], parallel_window=parallel_window,
                        window_size=r2c, e2=e2,
                        num_filt=layer.num_filt, filt_done=filt_done
                    )
                #print("ofmap", cycles_ofmap, "--")
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

                ####
                scheduler.epoch_time += del_cycles

                sys.stderr.write("\033[F")  # back to previous line
                sys.stderr.write("\033[K")  # clear line
                print(f"Epoch time: \t{scheduler.recent_switched_epoch_time} -> {set_color(scheduler.epoch_time, key=task.color)}", file=sys.stderr)
                
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
