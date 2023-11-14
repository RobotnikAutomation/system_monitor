#! /usr/bin/env python3
import sys
import rospy
from diagnostic_msgs.msg import DiagnosticArray
from system_monitor.msg import *

class Monitor():

    def __init__(self):
        self._pub = rospy.Publisher('~diagnostics', Diagnostic, queue_size=1)
        self._diag_net = DiagnosticNET()
        self._node_diagnostics = {} 
        self._diag_mem = DiagnosticMEM()
        self._diag_cpu_temp = DiagnosticCPUTemperature()
        self._diag_cpu_usa = DiagnosticCPUUsage()
        self._diag_hdd = DiagnosticHDD()
        r = rospy.get_param("rate_param", 0.5)
        self._rate = rospy.Rate(r)

    def update_diagnostics(self, status):
            node_name = status.name

            # Check if the node is already in the dictionary
            if node_name not in self._node_diagnostics:
                self._node_diagnostics[node_name] = {
                    'Net': DiagnosticNET(),
                    'Mem': DiagnosticMEM(),
                    'CpuTemp': DiagnosticCPUTemperature(),
                    'CpuUsage': DiagnosticCPUUsage(),
                    'Hdd': DiagnosticHDD()
                }

            # Update the diagnostics for the corresponding node
            self.update_net_values(status, node_name)
            self.update_mem_values(status, node_name)
            self.update_cpu_temp_values(status, node_name)
            self.update_cpu_usa_values(status, node_name)
            self.update_hdd_values(status, node_name)

    #Update network values
    def update_net_values(self, status):
        diag_net = self._node_diagnostics[node_name]['Net']
        diag_net.name = status.name
        # self._diag_net.name = status.name
        # self._diag_net.message = status.message
        self._diag_net.hardware_id = status.hardware_id
        net_status = NetStatus()
        net_status.status = status.values[0].value
        net_status.time = float(status.values[1].value)
        ifaces = (len(status.values) - 2) // 10
        ifaces = int(ifaces)
        for i in range(0, ifaces):
            inter = Interface()
            inter.name = status.values[2+10*i].value.decode('utf-8') if isinstance(status.values[2+10*i].value, bytes) else status.values[2+10*i].value            
            inter.state = status.values[3+10*i].value
            inter.input = float(status.values[4+10*i].value[:-6])
            inter.output = float(status.values[5+10*i].value[:-6])
            inter.mtu = int(status.values[6+10*i].value)
            inter.received = float(status.values[7+10*i].value)
            inter.transmitted = float(status.values[8+10*i].value)
            inter.collisions = int(status.values[9+10*i].value)
            inter.rxError = int(status.values[10+10*i].value)
            inter.txError = int(status.values[11+10*i].value)
            net_status.interfaces.append(inter)
        self._diag_net.status = net_status
        #self.publish_info()

    #Update memory values
    def update_mem_values(self, status):
        self._diag_mem.name = status.name
        self._diag_mem.message = status.message
        self._diag_mem.hardware_id = status.hardware_id
        mem_status = MEMStatus()
        mem_status.time = float(status.values[1].value)
        mem_status.totalM = int(status.values[-3].value[:-1])
        mem_status.usedM = int(status.values[-2].value[:-1])
        mem_status.freeM = int(status.values[-1].value[:-1])
        names = ['Physical','Swap']
        for i in range(0, 2):
            mem = Memory()
            mem.name = names[i]
            mem.total = int(status.values[3+5*i].value[:-1])
            mem.used = int(status.values[4+5*i].value[:-1])
            mem.free = int(status.values[5+5*i].value[:-1])
            mem_status.memories.append(mem)
        mem = Memory()
        mem.name = "Physical w/o buffers"
        mem.used = int(status.values[6].value[:-1])
        mem.free = int(status.values[7].value[:-1])
        mem_status.memories.append(mem)
        self._diag_mem.status = mem_status
        #self.publish_info()

    #Update cpu_temp values
    def update_cpu_temp_values(self, status):
        self._diag_cpu_temp.name = status.name
        self._diag_cpu_temp.message = status.message
        self._diag_cpu_temp.hardware_id = status.hardware_id
        aux_temp = CPUTemperatureStatus()
        aux_temp.status = status.values[0].value
        aux_temp.time = float(status.values[1].value)
        for i in range(2, len(status.values)):
            core = CoreTemp()
            core.id = i - 2
            try:
                core.temp = float(status.values[i].value[:-4]) if isinstance(status.values[i].value, bytes) else float(status.values[i].value[:-4])            
            except ValueError as e:
                core.temp = -1
            aux_temp.cores.append(core)
        self._diag_cpu_temp.status = aux_temp
        #self.publish_info()

    #Update cpu_usage values
    def update_cpu_usa_values(self, status):
        self._diag_cpu_usa.name = status.name
        self._diag_cpu_usa.message = status.message
        self._diag_cpu_usa.hardware_id = status.hardware_id
        aux_usa = CPUUsageStatus()
        len_values = len(status.values)
        num_cores = (len_values - 6) // 6
        num_cores = int(num_cores)
        aux_usa.status = status.values[0].value
        aux_usa.time = float(status.values[1].value)
        aux_usa.load_status = status.values[len_values - 4].value
        aux_usa.load_avg1 = float(status.values[len_values - 3].value[:-1])
        aux_usa.load_avg5 = float(status.values[len_values - 2].value[:-1])
        aux_usa.load_avg15 = float(status.values[len_values - 1].value[:-1])
        for i in range(0, num_cores):
            try:
                core = CoreUsage()
                core.id = i
                core.speed = float(status.values[i +2].value[:-3])
                core.status = status.values[2 + num_cores + 5*i].value
                if sys.version_info.major == 3:
                    core.system = float(status.values[3 + num_cores + 5*i].value[:-1])
                    core.user = float(status.values[4 + num_cores + 5*i].value[:-3])
                    core.nice = float(status.values[5 + num_cores + 5*i].value[:-3])
                    core.idle = float(status.values[6 + num_cores + 5*i].value[:-3].replace(",","."))
                else:
                    core.system = float(status.values[3 + num_cores + 5*i].value[:-1])
                    core.user = float(status.values[4 + num_cores + 5*i].value[:-1])
                    core.nice = float(status.values[5 + num_cores + 5*i].value[:-1])
                    core.idle = float(status.values[6 + num_cores + 5*i].value[:-1].replace(",","."))
                aux_usa.cores.append(core)
            except Exception as ex:
                    core = CoreUsage()
                    core.id = i
                    core.speed = 0
                    core.status = "Unknown"
                    core.system = 0
                    core.user = 0
                    core.nice = 0
                    core.idle = 0
                    aux_usa.cores.append(core)
        self._diag_cpu_usa.status = aux_usa
        #self.publish_info()

    #Update hdd values
    def update_hdd_values(self, status):
        self._diag_hdd.name = status.name
        self._diag_hdd.message = status.message
        self._diag_hdd.hardware_id = status.hardware_id
        aux_stat = HDDStatus()
        aux_stat.status = status.values[0].value
        aux_stat.time = float(status.values[1].value)
        aux_stat.space_reading = status.values[2].value
        num_disks = (len(status.values) - 3)/6
        num_disks = int(num_disks)
        for i in range(0,num_disks):
            disk = Disk()
            disk.id = i + 1
                disk.name = status.values[3 + i * 6].value.decode('utf-8') if isinstance(status.values[3 + i * 6].value, bytes) else status.values[3 + i * 6].value            
            disk.size = float(status.values[4 + i * 6].value[:-1])
            disk.available = float(status.values[5 + i * 6].value[:-1])
            disk.use = float(status.values[6 + i * 6].value[:-1])
            disk.status = status.values[7 + i * 6].value
            disk.mount_point = status.values[8 + i * 6].value
            aux_stat.disks.append(disk)
        self._diag_hdd.status = aux_stat
        #self.publish_info()

    #Publish info
    def publish_info(self):
        for node_name, diagnostics in self._node_diagnostics.items():
            msg = Diagnostic()
            msg.diagNet = diagnostics['Net']
            msg.diagMem = diagnostics['Mem']
            msg.diagCpuTemp = diagnostics['CpuTemp']
            msg.diagCpuUsage = diagnostics['CpuUsage']
            msg.diagHdd = diagnostics['Hdd']
            self._pub.publish(msg)

# Print CPU status
def callback(data):
    if data.status[0].name.startswith('Memory'):
        #Extract useful data from memory
        mon.update_mem_values(data.status[0])
    elif data.status[0].name.startswith('Network'):
        #Extract useful data from network
        mon.update_net_values(data.status[0])
    elif data.status[0].name.startswith('CPU Temperature'):
        mon.update_cpu_temp_values(data.status[0])
    #elif data.status[0].name.startswith('CPU Usage'):
        mon.update_cpu_usa_values(data.status[1])
    elif data.status[0].name.startswith("HDD Usage"):
        #Extract useful data from disk
        mon.update_hdd_values(data.status[0])
    mon.publish_info()

if __name__ == '__main__':
    rospy.init_node('system_monitor_node')
    mon = Monitor()
    rospy.Subscriber('/diagnostics', DiagnosticArray, callback)
    rospy.spin()
