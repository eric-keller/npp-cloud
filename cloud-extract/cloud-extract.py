# Utilities to perform some checks on a terraform controlled GCP infrastructure
# Copyright: Eric Keller 2024

#    usage = ("python3 cloud-extract.py <module> <json_file>\n" 
#            "   module is one of mod2 or mod3\n" 
#            "   json_file is the output of terraform show --json")

import subprocess
import time
#import socket
import json
import sys

class VMDesc:
    name = ""
    project = ""
    zone = ""
    subnet = ""
    vpc = ""
    ip_int = ""
    ip_ext = None
    def __init__ (self, name, project, zone, vpc, subnet, ip_int, ip_ext):
        self.name = name 
        self.project = project
        self.zone = zone
        self.vpc = vpc 
        self.subnet = subnet 
        self.ip_int = ip_int 
        self.ip_ext = ip_ext 
    
    def __str__(self):
        return (
            "VMDesc{"
            f"name:{self.name}, project:{self.project}, zone:{self.zone}, "
            f"vpc:{self.vpc}, subnet:{self.subnet}, ip_int:{self.ip_int}, ip_ext:{self.ip_ext}"
            "}"
        )

# Tests a connection between vm1 and vm2 using the given port number
#   Will use the external IP addresses of each VM
def test_connection_ext(vm1:VMDesc, vm2:VMDesc, port, expected):
    return test_connection(vm1.zone, vm1.name, vm1.project,
                    vm2.zone, vm2.name, vm2.project, vm2.ip_ext, port, expected)

# Tests a connection between vm1 and vm2 using the given port number
#   Will use the internal IP addresses of each VM
def test_connection_int(vm1:VMDesc, vm2:VMDesc, port, expected):
    return test_connection(vm1.zone, vm1.name, vm1.project,
                    vm2.zone, vm2.name, vm2.project, vm2.ip_int, port, expected)

# Tests a connection between two VMs, provided:
#   zone - GCP zone, host - hostname of VM, project - GCP project
#   ip, port - the address of the destination to use (can be internal or external)
# Works by using the gcloud utility to ssh into each VM and run a command.
# On the to host, it will run nc (netcat) in listen mode
# On the from host, it will run nc to connect to the to host
def test_connection(from_zone, from_host, from_project,
                    to_zone, to_host, to_project, 
                    ip, port, expected):

    print(f"Testing Connection from {from_host} to {to_host} using {ip} {port}, expected to {expected}")

    cmd_srv = f"/usr/bin/nc -l -p {port}"
    print(f"Command on server: {cmd_srv}")
    cmd_cli = f"/usr/bin/nc -zv -w2 {ip} {port}"
    print(f"Command on client: {cmd_cli}")

    proc_srv = subprocess.Popen(["gcloud", "compute", "ssh", 
                             "--zone", to_zone,
                             to_host,
                             "--project", to_project,
                             "--command", cmd_srv
                             ], stdout=subprocess.PIPE) 

    time.sleep(3) # wait for 3 seconds to make sure server is running

    proc_cli = subprocess.Popen(["gcloud", "compute", "ssh", 
                                 "--zone", from_zone,
                                 from_host,
                                 "--project", from_project,
                                 "--command", cmd_cli
                                 ], stderr=subprocess.PIPE) 

    err = True
    msg = ""
    print(f"proc_cli: = {proc_cli.returncode}")
    for line in proc_cli.stderr:
        # the real code does filtering here
        print("proc_cli.stdout:", line.rstrip())
        # succeeded, failed, timed out
        if (b"Connected" in line):
            err=False
        elif (b"refused" in line):
            err=True
            msg = msg + str(line)
        elif (b"TIMEOUT" in line):
            err=True 
            msg = msg + str(line)


    proc_cli.terminate()
    proc_srv.terminate()
    return err, msg

# Helper function that gets the network name from a full URI
# For example, in the json, there might be this:
# "network": "https://www.googleapis.com/compute/v1/projects/orbital-linker-398719/global/networks/tf-mod2-demo1-network1",
# This function will strip off all by the last part (tf-mod2-demo1-network1) and return that string
def get_network_from_uri(str):
    split_str = str.split("/")
    network = split_str[-1]
    return network


# Helper function to iterate through values / root_module / resources[]
#  if the type is google_compute_subnetwork, it adds it to a map
#  keys are the subnet names, values are the network names
def extract_subnet_to_vpc_map(json_tf):
    subnet_to_vpc_map = {}
    resources = json_tf["values"]["root_module"]["resources"]
    for res in resources:
        if (res["type"] == "google_compute_subnetwork"):
            name = res["name"]
            network = get_network_from_uri(res["values"]["network"])
            subnet_to_vpc_map[name] = network
    return subnet_to_vpc_map 


# From a json object that is the output of terraform show, 
# this function will extract each of the VMs into a array of python objects (VMDesc).
def extract_vm_info(json_tf, subnet_to_vpc_map):
    vms = {} 
    resources = json_tf["values"]["root_module"]["resources"]
    for res in resources:
        if (res["type"] == "google_compute_instance"):
            name = res["name"]
            zone = res["values"]["zone"]
            project = res["values"]["project"]
            nif = res["values"]["network_interface"][0] # for now, assume the first one
            ip_int = nif["network_ip"]
            if (len(nif["access_config"]) > 0):
                ip_ext = nif["access_config"][0]["nat_ip"]
            else:
                ip_ext = None    

            subnet = get_network_from_uri(nif["subnetwork"])
            vpc = subnet_to_vpc_map[subnet]

            vms[name] = VMDesc(name, project, zone, vpc, subnet, ip_int, ip_ext)
    return vms




# Checks the basic structure of VPCs, Subnets, and VMs
# correct_structure is an array of tuples with the vm name, the subnet it should be in,
#   and the vpc that subnet should be in.  example with 1 entry:
#   [{"vm":"tf-mod2-lab1-vm1", "sub":"tf-mod2-lab1-sub1", "vpc":"tf-mod2-lab1-vpc1"}]
# vms is an array of VMDesc (and can be obtained with the extract_vm_info function)
def check_structure(vms, correct_structure):
    msg =""
    err = False
    for c in correct_structure:
        # find in vms array
        if c["vm"] in vms.keys():
            v = vms[c["vm"]]
            print(f"Found vm: {v.name}, vpc: {v.vpc}, subnet: {v.subnet}")
            # check correct subnet and VPC
            if (v.vpc != c["vpc"]):
                msg = msg + f'For {v.name} expecting vpc {c["vpc"]} got {v.vpc}\n'
                err = True
            if (v.subnet != c["sub"]):
                msg = msg + f'For {v.name} expecting subnet {c["sub"]} got {v.subnet}\n'
                err = True
        else:
            msg = msg + f'VM {c["vm"]} not found in infrastructure\n'
            err = True

    return err,msg



# Checks for Module 2 programming assignment
      # VPC named a 
      # VPC named b 
   
      # subnet c in VPC a in region y
      # subnet d in VPC b in region z
      # subnet e in VPC b in region z

      # VM f in subnet c   
      # VM g in subnet d
      # VM h in subnet d
      # VM i in subnet e

   # pull out zone, project, hostname, private IP, and public IP of vm f, g, h, and i


# Checks for module 2.  First checking the structure, then testing a connection
def mod2_check(json_obj):
    correct_structure = [{"vm":"tf-mod2-lab1-vm1", "sub":"tf-mod2-lab1-sub1", "vpc":"tf-mod2-lab1-vpc1"},
                        {"vm":"tf-mod2-lab1-vm2", "sub":"tf-mod2-lab1-sub2", "vpc":"tf-mod2-lab1-vpc2"},
                        {"vm":"tf-mod2-lab1-vm3", "sub":"tf-mod2-lab1-sub2", "vpc":"tf-mod2-lab1-vpc2"},
                        {"vm":"tf-mod2-lab1-vm4", "sub":"tf-mod2-lab1-sub3", "vpc":"tf-mod2-lab1-vpc2"}]
    err,msg = check_structure(vms, correct_structure)
    if(err):
        print(msg)
    else:
        print(f"Check structure succeeded")
        
    err, msg = test_connection_ext(vms["tf-mod2-lab1-vm1"], vms["tf-mod2-lab1-vm2"], 1234, "SUCCEED")
    if(err):
        print(f"Test Connection FAILED, but it shouldn't have")
    else: 
        print(f"Test Connection SUCCEEDED (correctly)")

    err, msg = test_connection_int(vms["tf-mod2-lab1-vm1"], vms["tf-mod2-lab1-vm2"], 1234, "FAIL")
    if(err):
        print(f"Test Connection FAILED (correctly)")
    else: 
        print(f"Test Connection SUCCEEDED, but it shouldn't have")


    # NOTE: Since vm3 and v4 don't have external IP addresses, they cannot reach the internet
    #       As such, they will not be able to install nc
    #       TODO: Add test_connection with ping

    print("Done.")



 
if __name__ =="__main__":

    usage = ("python3 cloud-extract.py <module> <json_file>\n" 
            "   module is one of mod2 or mod3\n" 
            "   json_file is the output of terraform show --json")

    if (len(sys.argv) != 3):
        print("Error usage.")
        print(usage)
        sys.exit(1)

    mod=sys.argv[1]
    filename=sys.argv[2]

    try:
       file = open(filename, 'rb')
    except OSError:
        print("Could not open file:", filename)
        sys.exit(1)

    json_tf = json.load(file)
    subnet_to_vpc_map = extract_subnet_to_vpc_map(json_tf)
    #print(subnet_to_vpc_map)
    vms = extract_vm_info(json_tf, subnet_to_vpc_map)
    #print(vms, sep="\n")
   

    if (mod == "mod2"):
        mod2_check(json_tf)
    elif (mod == "mod3"):
        mod3_check(json_tf)
    else:
        print("Unsupported module:", mod)


