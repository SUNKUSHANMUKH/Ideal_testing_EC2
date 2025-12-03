# ec2_usage_check.py
import psutil
import time
import json
from datetime import datetime

CPU_THRESHOLD = 5
MEMORY_THRESHOLD = 20
DISK_IO_THRESHOLD = 1024
DISK_USAGE_THRESHOLD = 20
OBSERVATION_DURATION = 30
SAMPLE_INTERVAL = 3

def get_cpu_usage():
    return psutil.cpu_percent(interval=1)

def get_memory_usage():
    return psutil.virtual_memory().percent

def get_disk_io():
    disk1 = psutil.disk_io_counters()
    read1, write1 = disk1.read_bytes, disk1.write_bytes
    time.sleep(1)
    disk2 = psutil.disk_io_counters()
    read2, write2 = disk2.read_bytes, disk2.write_bytes
    return read2 - read1, write2 - write1

def get_disk_usage():
    return psutil.disk_usage('/').percent

def get_network_usage():
    net1 = psutil.net_io_counters()
    n1_in, n1_out = net1.bytes_recv, net1.bytes_sent
    time.sleep(1)
    net2 = psutil.net_io_counters()
    n2_in, n2_out = net2.bytes_recv, net2.bytes_sent
    return n2_in - n1_in, n2_out - n1_out

def determine_idle(cpu, memory, disk_read, disk_write):
    return cpu < CPU_THRESHOLD and memory < MEMORY_THRESHOLD and disk_read < DISK_IO_THRESHOLD and disk_write < DISK_IO_THRESHOLD

if __name__ == "__main__":
    print("Monitoring EC2 machine locally for idle detection...")
    cpu_samples, memory_samples, disk_read_samples, disk_write_samples = [], [], [], []

    start_time = datetime.now()

    for _ in range(int(OBSERVATION_DURATION / SAMPLE_INTERVAL)):
        cpu = get_cpu_usage()
        mem = get_memory_usage()
        d_read, d_write = get_disk_io()

        cpu_samples.append(cpu)
        memory_samples.append(mem)
        disk_read_samples.append(d_read)
        disk_write_samples.append(d_write)

        print(f"[Sample] CPU: {cpu}%, MEM: {mem}%, READ: {d_read} B/s, WRITE: {d_write} B/s")

    avg_cpu = sum(cpu_samples)/len(cpu_samples)
    avg_mem = sum(memory_samples)/len(memory_samples)
    avg_read = sum(disk_read_samples)/len(disk_read_samples)
    avg_write = sum(disk_write_samples)/len(disk_write_samples)
    disk_usage = get_disk_usage()
    net_in, net_out = get_network_usage()

    idle_status = determine_idle(avg_cpu, avg_mem, avg_read, avg_write)

    result = {
         "timestamp": str(start_time),
         "average_cpu_percent": avg_cpu,
         "average_memory_percent": avg_mem,
         "average_disk_read_Bps": avg_read,
         "average_disk_write_Bps": avg_write,
         "disk_usage_percent": disk_usage,
         "network_in_Bps": net_in,
         "network_out_Bps": net_out,
         "is_idle": idle_status
    }

