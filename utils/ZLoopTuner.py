import numpy as np
from matplotlib import pyplot
import labrad
import time


class ZLoopTuner:
    def __init__(self):
        self.sample_time = 60 # amount of time to collect temperature data before changing kp
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
            print 'Editing Kp, curr value = ' + self.kp
            while time.time() < end_time:
                #TODO FIX THIS LINE
                curr_temp = self.adr.temperatures()[3]
                curr_time = time.time()
                time_diff = curr_time - last_time
                last_time = curr_time
                self.temperatures.append(curr_temp)
                self.update_period(time_diff)

            # CHECK FOR PERIODIC BEHAVIOR
            temp_fft = np.fft.fft(self.temperatures)
            time_fft = np.fft.fftfreq(len(self.temperatures), self.sampling_period)
            dc_index = time_fft.index(0)
            temp_fft[dc_index] = 0
            avg_fft = np.average(abs(temp_fft))
            std_fft = np.std(abs(temp_fft))

            max_temp_fft = max(temp_fft)
            index_fft = temp_fft.index(max_temp_fft)
            max_freq = time_fft[index_fft]

            pyplot.plot(time_fft, temp_fft)
            pyplot.show()

            if max_temp_fft > (avg_fft + (3 * std_fft)):
                self.periodic = True
                self.tu = (1 / max_freq)
                self.ku = self.kp

            else:
                self.kp = self.kp + 0.01
                self.adr.set_pid_kp(self.kp)


        # DETERMINE FINAL GAINS
        # final gains set according to Ziegler-Nichols method
        self.kp = self.ku * 0.6
        self.ki = self.ku / self.tu * 1.2
        self.kd = self.ku * self.tu * 3 / 40

        self.adr.set_pid_kp(self.kp)
        self.adr.set_pid_ki(self.ki)
        self.adr.set_pid_kd(self.kd)

        print('PID is tuned. Have nice day.')

        # x = np.arange(0.0001, 10, .005)
        # noise = np.random.normal(0, 1, 2000)
        # print noise
        # y = np.exp(2j * np.pi * x + 1.63)
        # for i in range(0, 2000):
        #     y[i] = y[i] + noise[i]
        # # pyplot.plot(x, y)
        # # pyplot.show()
        #
        # x_fft = np.fft.fftfreq(x.size, d=0.005)
        # y_fft = np.fft.fft(y)
        # #
        # # pyplot.plot(x_fft, y_fft)
        # # axes = pyplot.gca()
        # # axes.set_xlim([-2.5, 2.5])
        # # pyplot.show()
        #
        # y_abs = abs(y_fft)
        #
        # average = np.average(y_abs)
        # print average
        #
        # if max(y_abs) > 3 * average:
        #     print 'true'
        # else:
        #     print 'false'
        #
        # noise_fft = np.fft.fft(noise)
        # # pyplot.plot(x_fft, np.fft.fft(noise_fft))
        # # axes = pyplot.gca()
        # # pyplot.title('noise')
        # # pyplot.show()
        # avg_arr = []
        # std_arr = []
        # average = np.average(abs(noise_fft))
        # for i in range(0, 2000):
        #     avg_arr.append(average)
        #
        # std_dev = np.std(y_abs)
        # for i in range(0, 2000):
        #     std_arr.append(average + 5 * std_dev)
        #
        # print std_dev
        #
        # pyplot.plot(x_fft, y_abs,  x_fft, std_arr)
        # axes = pyplot.gca()
        # pyplot.title('abs')
        # pyplot.show()
        #
        # if max(noise_fft) > average + (3 * std_dev):
        #     print 'true'
        # else:
        #     print 'false'
    
    def update_period(self, time_diff):
        td_weight = (1 / self.num_periods) * time_diff
        ex_weight = ((self.num_periods - 1) / self.num_periods) * self.sampling_period
        self.sampling_period = td_weight + ex_weight
        self.num_periods = self.num_periods + 1


if __name__ == "__main__":
    ZLoopTuner().main()
