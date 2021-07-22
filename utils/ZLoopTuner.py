import numpy as np
import labrad
import time
from scipy import signal
from matplotlib import pyplot


class ZLoopTuner:
    def __init__(self):
        self.sample_time = 360 # amount of time to collect temperature data before changing kp
        self.num_periods = 1
        self.cxn = labrad.connect()
        self.reg = self.cxn.registry
        self.reg.cd('ADR Settings', 'ADR3')
        self.adr = self.cxn.adr3
        self.kp = 0
        self.ki = 0
        self.kd = 0
        self.periodic = False
        self.temperatures = []
        self.sampling_period = 0
        self.tu = 0
        self.ku = 0

    def main(self):
        # increment KP until periodic behavior is detected

        self.adr.set_pid_kp(self.kp)
        self.adr.set_pid_ki(self.ki)
        self.adr.set_pid_kd(self.kd)

        while not self.periodic:
            # collect temperature data for given sample_time period
            last_time = time.time()
            end_time = time.time() + self.sample_time
            self.sampling_period = 0
            self.num_periods = 1
            print('Editing Kp, curr value = ' +str(self.kp))
            while time.time() < end_time:
                time.sleep(.1)
                #TODO FIX THIS LINE
                curr_temp = self.adr.temperatures()[3]['K']
                curr_time = time.time()
                time_diff = curr_time - last_time
                last_time = curr_time
                self.temperatures.append(curr_temp)
                self.update_period(time_diff)

            # CHECK FOR PERIODIC BEHAVIOR
            temp_fft = np.fft.fft(self.temperatures)
            temp_fft = signal.detrend(temp_fft)
            time_fft = np.fft.fftfreq(len(self.temperatures), self.sampling_period)
            dc_index = np.where(time_fft == 0)
            temp_fft[dc_index] = 0
            avg_fft = np.average(abs(temp_fft))
            std_fft = np.std(abs(temp_fft))

            max_temp_fft = max(temp_fft)
            index_fft = np.where(temp_fft == max_temp_fft)
            max_freq = time_fft[index_fft]

            if max_temp_fft > (avg_fft + (3 * std_fft)):
                print('Critical Kp determined.')
                pyplot.plot(time_fft, temp_fft)
                pyplot.show()
                self.periodic = True
                self.tu = (1 / max_freq)
                self.ku = self.kp

            else:
                print('Periodicity not detected.')
                pyplot.plot(time_fft, temp_fft)
                pyplot.show()
                self.kp = self.kp + 0.01
                self.adr.set_pid_kp(self.kp)

        # DETERMINE FINAL GAINS
        # final gains set according to Ziegler-Nichols method
        print('Setting final gains')
        self.kp = self.ku * 0.6
        self.ki = self.ku / self.tu * 1.2
        self.kd = self.ku * self.tu * 3 / 40

        self.adr.set_pid_kp(self.kp)
        self.adr.set_pid_ki(self.ki)
        self.adr.set_pid_kd(self.kd)

        print('PID is tuned. Have nice day.')
    
    def update_period(self, time_diff):
        td_weight = (1.0 / self.num_periods) * time_diff
        ex_weight = ((self.num_periods - 1.0) / self.num_periods) * self.sampling_period
        self.sampling_period = td_weight + ex_weight
        self.num_periods = self.num_periods + 1


if __name__ == "__main__":
    ZLoopTuner().main()
