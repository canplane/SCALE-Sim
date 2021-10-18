import math 
from tqdm import tqdm


def sram_traffic(
            array={ 'h': 4, 'w': 4 },  #dimension_rows=4, dimension_cols=4,

            ifmap={ 'h': 7, 'w': 7 }, filt={ 'h': 3, 'w': 3 }, ch=3,  #ifmap_h=7, ifmap_w=7, filt_h=3, filt_w=3, num_channels=3,
            num_filt=8,
            stride=1,
        ):

    # Dimensions of output feature map channel
    E_h = math.floor((ifmap['h'] - filt['h'] + stride) / stride)
    E_w = math.floor((ifmap['w'] - filt['w'] + stride) / stride)
    
    # Number of pixels in one convolution window (한 필터 윈도우에 들어가는 픽셀 수?)
    px_per_filt = filt['h'] * filt['w'] * ch
    r2c = px_per_filt

    # Total number of ofmap px across all channels
    num_ofmap_px = E_h * E_w * num_filt
    e2  = E_h * E_w
    e2m = num_ofmap_px

    # Variables for utilization calculation
    util = 0
    compute_cycles = 0

    # Variables to calculate folds in runtime
    # num_h_fold : horizontal선으로 접기 : 하나의 컨볼루션 필터 커널의 칸 수 * 채널 수와 관련
    # num_v_fold : vertical선으로 접기: 필터 개수와 관련
    if array['h'] < px_per_filt:
        num_h_fold = math.ceil(px_per_filt / array['h'])
        max_parallel_window = 1
    else:
        num_h_fold = 1
        max_parallel_window = math.floor(array['h'] / px_per_filt)

    reqd_cols = num_filt                    # Total number of cols to be mapped
    max_cols_per_v_fold = max_parallel_window * array['w']
    num_v_fold = math.ceil(reqd_cols / max_cols_per_v_fold)
    
    remaining_cols = reqd_cols
    cycles = 0
    prev_cycl = 0

    for v in tqdm(range(int(num_v_fold))):
        #print("V fold id: " + str(v))
            
        # Take a slice of the starting addresses that are relevant for this v_fold 
        cols_this_fold = min(remaining_cols, max_parallel_window * array['w'])

        if num_h_fold > 1:
           
            rem_h = r2c                     # Tracks the elements processed within a conv filter 

            for h in range(num_h_fold):
                rows_this_fold = min(rem_h, array['h'])
                #print("h fold id: " + str(h))

                # Values returned
                # cycles        -> Cycle count for the next operation ie. cycles elapsed + 1
                cycles = gen_trace_filter_partial(
                            cycle=cycles,
                            remaining=rows_this_fold,
                        )
                #print("Weights loaded by " + str(cycles) + " cycles")
                cycles_ifmap = gen_trace_ifmap_partial(
                            cycle=cycles,
                            ifmap_h=ifmap['h'], ifmap_w=ifmap['w'],
                            filt_h=filt['h'], filt_w=filt['w'],
                            stride=stride
                        )
                cycles_ofmap = gen_trace_ofmap(
                            cycle=cycles,
                            num_rows=array['h'], num_cols=array['w'],
                            window_size=rows_this_fold,
                            parallel_window=1,
                            num_ofmap_px=int(e2),
                            filters_done=(v * array['w']),
                            num_filter=num_filt,
                        )

                #print("IFMAPS processed by " + str(cycles) + " cycles")
                util_this_fold = (rows_this_fold * cols_this_fold) / (array['h'] * array['w'])

                rem_h -= rows_this_fold
                cycles = max(cycles_ifmap, cycles_ofmap)

                del_cycl = cycles - prev_cycl
                util += util_this_fold *  del_cycl
                compute_cycles += del_cycl
                prev_cycl = cycles
        #
        else:
            #filters_this_fold = min(remaining_cols, max_cols_per_v_fold)
            filt_done = v * max_parallel_window * array['w']
            rem = num_filt - filt_done

            parallel_window = math.ceil(rem / array['w'])
            parallel_window = int(min(max_parallel_window, parallel_window))
        
            cycles_filter = gen_filter_trace(
                        cycle=cycles,
                        num_rows=array['h'], num_cols=array['w'],
                        filt_h=filt['h'], filt_w=filt['w'], num_channels=ch,
                        parallel_window=parallel_window,
                        filters_this_fold = cols_this_fold,
                    )

            cycles_ifmap = gen_ifmap_trace(
                        cycle=cycles_filter,
                        num_rows=array['h'], num_cols=array['w'],
                        ifmap_h=ifmap['h'], ifmap_w=ifmap['w'],
                        filt_h=filt['h'], filt_w=filt['w'],
                        num_channels=ch, stride=stride,
                        parallel_window=parallel_window,
                    )

            cycles_ofmap = gen_trace_ofmap(
                        cycle=cycles_filter,
                        num_rows=array['h'], num_cols=array['w'],
                        parallel_window=parallel_window,
                        window_size=r2c,
                        num_ofmap_px=int(e2),
                        filters_done=int(v * max_parallel_window * array['w']),
                        num_filter=num_filt,
                    )
            cycles = max(cycles_ifmap, cycles_ofmap)
            del_cycl = cycles - prev_cycl

            # Since multiple filters are being mapped on a single col due to large number of rows
            # util calculation is a little involved,
            # cols_this_fold --> number of filters mapped this fold
            rem = cols_this_fold
            tmp_util = 0
            for _ in range(parallel_window):
                col_used = min(rem, array['w'])
                row_used = r2c                      # Number of row used will always be in multiple of r2c,
                                                    # parallel window calc took care of this
                tmp_util += row_used * col_used
                rem -= col_used

            util_this_fold = tmp_util / (array['h'] * array['w'])
            util += util_this_fold * del_cycl
            compute_cycles += del_cycl
            prev_cycl = cycles
        #

        remaining_cols -= cols_this_fold


    #

    final = str(cycles)
    final_util = (util / compute_cycles) * 100
    #print("Compute finished at: " + str(final) + " cycles")
    return (final, final_util)


def gen_filter_trace(
            cycle=0,
            num_rows=4, num_cols=4,
            filt_h=3, filt_w=3, num_channels=3,
            parallel_window=1,
            filters_this_fold=4,
        ):
    # Calculate the convolution window size
    r2c = filt_h * filt_w * num_channels 

    cycle += r2c * parallel_window
    return cycle


def gen_ifmap_trace(
            cycle=0,
            num_rows=4, num_cols=4,
            ifmap_h = 7, ifmap_w=7,
            filt_h=3, filt_w=3,
            num_channels=3, stride=1,
            parallel_window=1,
        ):  
    E_h = math.floor((ifmap_h - filt_h + stride) / stride)
    E_w = math.floor((ifmap_w - filt_w + stride) / stride)
    
    cycle += int(E_h * E_w)
    return cycle


def gen_trace_filter_partial(
            cycle=0,
            remaining=4,
        ):
    cycle += remaining
    return cycle


def gen_trace_ifmap_partial(
            cycle=0,
            ifmap_h=4, ifmap_w=4,
            filt_h=3, filt_w=3,
            stride=1, 
        ):
    E_w = (ifmap_w - filt_w + stride) / stride 
    E_h = (ifmap_h - filt_h + stride) / stride

    cycle += int(E_h * E_w)
    return cycle


def gen_trace_ofmap(
            cycle=0,
            num_rows=4, num_cols=4,
            parallel_window=1,
            window_size=27,
            num_ofmap_px=16,      # This is per ofmap channel
            filters_done=0,       # To track v fold
            num_filter=8,       # To track if all filters have finished
        ):
    # Corner case when parallel_window = 1, but num_filter < num_cols
    if parallel_window > 1:
        cycle += num_cols
    else:
        rem = (num_filter - filters_done)
        cycle += min(rem, num_cols)
    cycle += window_size

    cycle += int(num_ofmap_px)    
    return cycle
