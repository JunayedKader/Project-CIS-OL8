#!/usr/bin/env python3

import os
import re
import subprocess
from glob import glob
from pathlib import Path

def main():
    l_mname = "cramfs"  # set module name
    l_mtype = "fs"       # set module type
    l_mpath = "/lib/modules/*/kernel/" + l_mtype
    l_mpname = l_mname.replace("-", "_")
    l_mndir = l_mname.replace("-", "/")

    def module_loadable_fix():
        """If the module is currently loadable, add 'install <module> /bin/false' to modprobe.d"""
        try:
            proc = subprocess.Popen(["modprobe", "-n", "-v", l_mname],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  universal_newlines=True)
            l_loadable, _ = proc.communicate()
            
            if len(l_loadable.splitlines()) > 1:
                filtered_lines = []
                for line in l_loadable.splitlines():
                    if re.match(r"(^\s*install|\b" + l_mname + r"\b)", line):
                        filtered_lines.append(line)
                l_loadable = "\n".join(filtered_lines)
            
            if not re.search(r'^\s*install \/bin\/(true|false)', l_loadable):
                print("\n - setting module: \"{}\" to be not loadable".format(l_mname))
                with open("/etc/modprobe.d/{}.conf".format(l_mpname), "a") as f:
                    f.write("install {} /bin/false\n".format(l_mname))
        except Exception as e:
            print("Error in module_loadable_fix: {}".format(e))

    def module_loaded_fix():
        """If the module is currently loaded, unload it"""
        try:
            proc = subprocess.Popen(["lsmod"],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True)
            lsmod, _ = proc.communicate()
            if l_mname in lsmod:
                print("\n - unloading module \"{}\"".format(l_mname))
                subprocess.check_call(["modprobe", "-r", l_mname])
        except subprocess.CalledProcessError as e:
            print("Error unloading module: {}".format(e))

    def module_deny_fix():
        """If the module isn't denylisted, add it to denylist"""
        try:
            proc = subprocess.Popen(["modprobe", "--showconfig"],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  universal_newlines=True)
            modprobe_config, _ = proc.communicate()
            if not re.search(r'^\s*blacklist\s+' + l_mpname + r'\b', modprobe_config):
                print("\n - deny listing \"{}\"".format(l_mname))
                with open("/etc/modprobe.d/{}.conf".format(l_mpname), "a") as f:
                    f.write("blacklist {}\n".format(l_mname))
        except Exception as e:
            print("Error in module_deny_fix: {}".format(e))

    # Check if module exists on the system
    for l_mdir in glob("/lib/modules/*/kernel/{}".format(l_mtype)):
        module_dir = os.path.join(l_mdir, l_mndir)
        if os.path.isdir(module_dir) and os.listdir(module_dir):
            print("\n - module: \"{}\" exists in \"{}\"\n - checking if disabled...".format(l_mname, l_mdir))
            module_deny_fix()
            
            if l_mdir == "/lib/modules/{}/kernel/{}".format(os.uname().release, l_mtype):
                module_loadable_fix()
                module_loaded_fix()
        else:
            print("\n - module: \"{}\" doesn't exist in \"{}\"\n".format(l_mname, l_mdir))

    print("\n - remediation of module: \"{}\" complete\n".format(l_mname))

if __name__ == "__main__":
    main()