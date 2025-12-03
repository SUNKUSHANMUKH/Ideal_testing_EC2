# ec2_idle_check.py
import boto3
from datetime import datetime, timedelta, timezone

# ----------------------------
# CONFIGURATION
# ----------------------------
INSTANCE_ID = "i-0ad79521e121179ca"  # Replace with your EC2 instance ID
IDLE_CPU_THRESHOLD = 10        # %
IDLE_MEMORY_THRESHOLD = 30     # %
IDLE_DISK_THRESHOLD = 30       # %
IDLE_NETWORK_THRESHOLD = 1024  # bytes
LOOKBACK_MINUTES = 15

cw = boto3.client("cloudwatch")

# ----------------------------
# FETCH METRIC FROM CLOUDWATCH
# ----------------------------
def get_metric(namespace, metric, stat, dimension_name, dimension_value):
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=LOOKBACK_MINUTES)

    response = cw.get_metric_statistics(
        Namespace=namespace,
        MetricName=metric,
        Dimensions=[{"Name": dimension_name, "Value": dimension_value}],
        StartTime=start,
        EndTime=end,
        Period=300,
        Statistics=[stat],
    )

    datapoints = response.get("Datapoints", [])
    if not datapoints:
        return None
    return datapoints[-1][stat]

# ----------------------------
# GET METRICS
# ----------------------------
def get_cpu(): return get_metric("AWS/EC2", "CPUUtilization", "Average", "InstanceId", INSTANCE_ID)
def get_network_in(): return get_metric("AWS/EC2", "NetworkIn", "Sum", "InstanceId", INSTANCE_ID)
def get_network_out(): return get_metric("AWS/EC2", "NetworkOut", "Sum", "InstanceId", INSTANCE_ID)
def get_ebs_read_ops(): return get_metric("AWS/EC2", "EBSReadOps", "Sum", "InstanceId", INSTANCE_ID)
def get_ebs_write_ops(): return get_metric("AWS/EC2", "EBSWriteOps", "Sum", "InstanceId", INSTANCE_ID)
def get_memory(): return get_metric("CWAgent", "mem_used_percent", "Average", "InstanceId", INSTANCE_ID)
def get_disk(): return get_metric("CWAgent", "disk_used_percent", "Average", "InstanceId", INSTANCE_ID)

# ----------------------------
# EVALUATE IDLE
# ----------------------------
def evaluate_idle(cpu, mem, disk, net_in, net_out, ebs_read, ebs_write):
    idle_cpu = cpu is not None and cpu < IDLE_CPU_THRESHOLD
    idle_mem = mem is not None and mem < IDLE_MEMORY_THRESHOLD
    idle_disk = disk is not None and disk < IDLE_DISK_THRESHOLD
    idle_net = (net_in is not None and net_in < IDLE_NETWORK_THRESHOLD) and (net_out is not None and net_out < IDLE_NETWORK_THRESHOLD)
    idle_ebs = (ebs_read is not None and ebs_read < 10) and (ebs_write is not None and ebs_write < 10)
    return "IDLE" if idle_cpu and idle_mem and idle_disk and idle_net and idle_ebs else "ACTIVE"

# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    cpu = get_cpu()
    mem = get_memory()
    disk = get_disk()
    net_in = get_network_in()
    net_out = get_network_out()
    ebs_read = get_ebs_read_ops()
    ebs_write = get_ebs_write_ops()

    print("----- METRICS -----")
    print(f"CPU: {cpu}")
    print(f"Memory: {mem}")
    print(f"Disk % used: {disk}")
    print(f"Network In: {net_in}")
    print(f"Network Out: {net_out}")
    print(f"EBS Read Ops: {ebs_read}")
    print(f"EBS Write Ops: {ebs_write}")

    status = evaluate_idle(cpu, mem, disk, net_in, net_out, ebs_read, ebs_write)
    print(f"\nINSTANCE STATUS: {status}")
