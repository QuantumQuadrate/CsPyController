""" 
    Preston's Rb code garage. 
    
    If I have a code snippet that might be useful down the road but is just
    cluttering CsPy waveform for now, put here in the garage.
"""

# test the FORT VCA
        # tramp = linspace(t_start,t_start+t_PGC_duration,100)
        # for t in tramp:
        #     Vi = 10
        #     Vf = 7
        #     V_FORT = ((Vf-Vi)/t_PGC_duration)*(t-t_start)+Vi
        #     AO(t,5,V_FORT)


# Shutter 3DMOT if checking FORT loss
# exp.mot_3d_x_shutter_switch.profile(t_start2,'off')
# exp.mot_3d_x_shutter_switch.profile(t_end,'on')
# exp.mot_3d_y_shutter_switch.profile(t_start2,'off')
# exp.mot_3d_y_shutter_switch.profile(t_end,'on')
# exp.mot_3d_z1_shutter_switch.profile(t_start2,'off')
# exp.mot_3d_z1_shutter_switch.profile(t_end,'on')
