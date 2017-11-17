def choppedRO(t,period=2e-3,RO_onoff=[0,.5],Trap_onoff=[.5,1]):
    '''
    
    period: time in ms 
    RO_onoff: tuple containing [on,off] as a percentage of period 
    Trap_onoff: tuple containing [on,off] as a percentage of period 
    
    '''
    D2_switch(t,0)
    vODT_switch(t,0)
    D2_switch(t+RO_onoff[0]*period,1)
    D2_switch(t+RO_onoff[1]*period,0)
    vODT_switch(t+Trap_onoff[0]*period,1)
    vODT_switch(t+Trap_onoff[1]*period,0)
    return t+period