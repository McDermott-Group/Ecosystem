import labrad
import json

cxn = labrad.connect()

boards = cxn.ghz_fpgas()

adc = boards.list_adcs()[0]
boards.select_device(adc)

passed = False
counter = 0
successes = 0
while not passed:
    counter += 1
    if not successes:
        boards.adc_bringup()
    status = boards.adc_register_readback()
    adc_status = status.replace("'", "\"")
    adc_status = adc_status.replace('True', 'true')
    adc_status = adc_status.replace('False', 'false')
    adc_dict = json.loads(adc_status)
    print(('%d: %s' %(counter, status)))
    if adc_dict['noPllLatch'] and adc_dict['dClkBits'] == 15:
        successes += 1
    else:
        successes = 0
        
    if successes == 4:
        passed = True
       
    if successes == 0 and counter % 25 == 0:
        for dac in boards.list_dacs():
            boards.select_device(dac)
            boards.dac_bringup()
        boards.select_device(adc)

    if successes == 0 and counter % 1000 == 0:
        boards.adc_recalibrate()

cxn.disconnect()