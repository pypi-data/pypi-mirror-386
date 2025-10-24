import numpy as np
import copy
import warnings
from biomechzoo.utils.peak_sign import peak_sign
from biomechzoo.biomech_ops.movement_onset import movement_onset

def addevent_data(data, channels, ename, etype, constant=None):

    data_new = copy.deepcopy(data)

    if isinstance(channels, str):
        channels = [channels]

    if len(channels) == 1 and channels[0].lower() == 'all':
        channels = [key for key in data if key != 'zoosystem']

    for channel in channels:
        if ename == '':
            data[channel]['event'] = {}
            continue

        if channel not in data:
            raise KeyError('Channel {} does not exist'.format(channel))

        yd = data_new[channel]['line']  # 1D array
        etype = etype.lower()
        if etype == 'absmax':
            exd = int(np.argmax(np.abs(yd)))
            eyd = float(yd[exd])
        elif etype == 'first':
            exd = 0
            eyd = float(yd[exd])
        elif etype == 'last':
            exd = len(yd) - 1
            eyd = float(yd[exd])
        elif etype == 'max':
            exd = int(np.argmax(yd))
            eyd = float(yd[exd])
        elif etype == 'min':
            exd = int(np.argmin(yd))
            eyd = float(yd[exd])
        elif etype == 'rom':
            eyd = float(np.max(yd) - np.min(yd))
            exd = 0  # dummy index (like MATLAB version)
        elif etype == 'max_stance':
            # special event for gait and running
            exd = max_stance(yd)
            eyd = float(yd[exd])
            eyd = float(yd[exd])
        elif etype == 'movement_onset':
            exd = movement_onset(yd, constant)
            eyd = yd[exd]
        elif etype == 'movement_offset':
            exd = movement_onset(yd,constant)
            eyd = yd[exd]
        elif etype in ['fs_fp', 'fo_fp']:
            # --- Handle constant ---
            if constant is None:
                print('Warning: Force plate threshold not set, defaulting to 0.')
                constant = 0.0

            # --- Check sampling rates ---
            AVR = data['zoosystem']['AVR']
            if AVR != 1:
                warnings.warn('Video and Analog channels must be at the same sampling rate or events will be incorrect.')

            # --- Handle units ---
            units = data['zoosystem']['Units']['Forces']
            if units == 'N/kg':
                m = data['zoosystem']['Anthro']['Bodymass']
            else:
                m = 1.0

            # --- Extract force signal ---
            if '_' not in channel:
                yd = data_new[channel]['line'][:, 2]  # looking for GRF Z
            else:
                yd = data_new[channel]['line']

            # --- Determine peak sign ---
            peak = peak_sign(yd)  # user-defined function

            # --- Find threshold crossing ---
            threshold_signal = peak * yd * m
            if 'fs' in etype:
                exd_array = np.where(threshold_signal > constant)[0]
                exd = exd_array[0] - 1  # MATLAB indexing correction
                eyd = yd[exd]
            else:  # 'FO' type
                exd_array = np.where(threshold_signal > constant)[0]
                exd = exd_array[-1] + 1
                eyd = yd[exd]

        else:
            raise ValueError(f'Unknown event type: {etype}')

        # Add event to the channel's event dict
        data_new[channel]['event'][ename] = [exd, eyd, 0]

    return data_new

def max_stance(yd):
    """ extracts max from first 40% of the gait cycle"""
    raise NotImplementedError
    return exd