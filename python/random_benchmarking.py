def script(n, delay_before_excitation_pulse, microwave_pi_by_2, clockRate):
    
    header='''script script1
  compressedGenerate MOT_Loading
  compressedGenerate PGC_1
  compressedGenerate MOT_drop
  compressedGenerate PreReadout
  compressedGenerate Readout
  compressedGenerate PGC_2
  compressedGenerate close_3D_shutter
  compressedGenerate close_HF_shutter
  compressedGenerate Optical_Pumping
'''
    #script names were 1 based
    n=int(n)-1

    full_order=[1,3,1,3,1,4,1,4,2,2,3,1,9,7,9,9,2,4,1,7,9,2,3,1,3,7,2,4,9,2,4,7,9,1,3,2,9,2,3,7,3,1,3,7,4,1,3,2,1,4,4,7,3,7,9,7,9,2,2,4,2,4,1,2,4,1,1,4,1,3,2,4,9,7,3,7,1,4,1,2,4,1,4,1,3,2,2,3,1,2,4,1,9,1,1,1,4,1,2,4,3,2,1,4,4,7,9,1,2,4,2,3,2,2,4,1,9,2,3,2,2,4,3,7,9,2,4,2,1,4,2,2,2,4,7,2,4,1,3,1,7,3,7,1,4,1,3,2,4,2,7,4,1,9,7,2,3,1,3,1,1,3,9,2,2,4,1,1,4,1,2,3,9,1,1,4,3,7,4,7,9,7,9,2,4,2,4,1,4,7,1,4,1,1,3,1,2,4,2,4,1,4,1,4,4,7,2,3,1,4,1,1,3,1,2,4,1,2,3,1,4,1,1,3,9,2,2,4,2,7,4,7,2,3,2,4,2,4,1,3,7,4,1,1,3,1,9,4,7,4,4,1,3,2,4,2,1,4,1,1,4,1,3,2,1,3,1,9,1,2,9,7,1,4,2,3,3,3,1,2,4,3,3,3,3,7,4,2,1,4,1,4,9,2,4,7,3,4,9,4,7,2,4,2,4,1,2,4,2,4,2,3,1,9,7,1,4,1,3,1,3,9,2,7,4,7,2,1,3,1,1,3,1,3,2,4,1,9,2,1,4,1,1,3,1,3,2,1,4,1,4,7,1,4,2,2,3,9,1,2,4,1,1,7,9,1,2,3,1,2,3,2,4,1,4,1,1,3,2,4,2,2,4,1,4,2,2,4,9,1,1,4,2,1,3,7,4,2,3,2,9,2,4,2,3,1,4,2,4,4,1,1,3,1,3,1,1,1,4,1,9,2,9,2,3,2,4,1,2,3,1,4,1,3,2,3,1,1,3,1,4,1,2,3,1,2,1,3,7,2,2,9,4,2,1,3,3,1,4,3,2,2,3,1,2,3,1,4,7,4,4,3,1,3,2,3,7,1,3,1,9,2,1,3,7,2,3,1,2,3,1,4,1,3,1,2,4,2,4,3,7,4,7,4,7,2,4,2,3,4,9,1,4,2,7,3,1,1,3,1,2,9,2,1,4,1,4,1,9,1,9,2,1,4,2,3,1,3,1,3,3,1,9,2,4,7,2,3,1,3,1,4,1,1,4,1,2,4,1,3,2,3,7,3]
    truncation=[3,59,125,186,253,309,375,441,502,564]
    order=full_order[:truncation[n]]

    delays = [(561,1111),(505,1001),(439,859),(378,736),(311,597),(255,485),(189,362),(123,232),(62,118),(0,0)]

    middle = '\n'.join(['  compressedGenerate RB'+str(x) for x in order])+'\n'
    
    delay = int((delays[n][0]*delay_before_excitation_pulse + delays[n][1]*microwave_pi_by_2) * clockRate/1000)
    wait = '  compressedGenerate RB_wait\n'+('' if delay==0 else '  wait {}\n'.format(delay))
    footer='''  compressedGenerate Blowaway
  compressedGenerate Camera_delay
  compressedGenerate Readout
  compressedGenerate slow_noise_eater_3ms
  compressedGenerate idle
end script'''
    
    return header+middle+wait+footer

def script_from_file(n):
    with open(r'C:\Users\Saffmanlab\Documents\AQuA_settings\RB\script'+str(n)+'.txt') as f:
        return f.read()

def parse_script_wait(script, k8, l5):
    lines = script.split('\n')
    for i,line in enumerate(lines):
        if line.strip().split(' ')[0]=='wait':
            delay=eval(line.strip().split(' ')[1])
            lines[i]='wait '+str(int(delay))
    return '\n'.join(lines)
