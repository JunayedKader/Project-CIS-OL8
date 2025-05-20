###   1.1.1.1 Ensure cramfs kernel module is not available (Automated)

import subprocess
import os
import glob

def run_cmd(cmd):
    """Run a shell command and return output."""
    result = subprocess.run(cmd, shell=True, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.strip()

def grep_file(pattern, file):
    """Run grep command and return matched lines."""
    try:
        output = subprocess.check_output(['grep', '-P', pattern, file], universal_newlines=True)
        return output.strip()
    except subprocess.CalledProcessError:
        return ""

def module_exists(module_name, module_type):
    paths = glob.glob(f"/lib/modules/**/kernel/{module_type}", recursive=True)
    mpname = module_name.replace("-", "_")
    mndir = module_name.replace("-", "/")
    exists_paths = []

    for path in paths:
        full_path = os.path.join(path, mndir)
        if os.path.isdir(full_path) and os.listdir(full_path):
            exists_paths.append(full_path)
    return exists_paths

def is_module_loaded(module_name):
    output = run_cmd("lsmod")
    return module_name in output

def is_module_loadable(module_name):
    output = run_cmd(f"modprobe -n -v {module_name}")
    if "install /bin/true" in output or "install /bin/false" in output:
        return False, output
    return True, output

def is_module_blacklisted(module_name):
    mpname = module_name.replace("-", "_")
    search_locations = [
        "/lib/modprobe.d/*.conf",
        "/usr/local/lib/modprobe.d/*.conf",
        "/run/modprobe.d/*.conf",
        "/etc/modprobe.d/*.conf",
    ]
    files = []
    for pattern in search_locations:
        files.extend(glob.glob(pattern))

    for file in files:
        if grep_file(fr"^\s*blacklist\s+{mpname}\b", file):
            return True, file
    return False, ""

# === Main logic for audit ===
module = "cramfs"
mtype = "fs"

output_pass = []
output_fail = []
output_info = []

module_paths = module_exists(module, mtype)

if module_paths:
    output_info.append(f" - module: \"{module}\" exists in:\n   " + "\n   ".join(module_paths))

    # Check if module is blacklisted
    blacklisted, bl_file = is_module_blacklisted(module)
    if blacklisted:
        output_pass.append(f" - module: \"{module}\" is deny listed in: {bl_file}")
    else:
        output_fail.append(f" - module: \"{module}\" is not deny listed")

    # Check loadable status
    loadable, load_output = is_module_loadable(module)
    if not loadable:
        output_pass.append(f" - module: \"{module}\" is not loadable: {load_output}")
    else:
        output_fail.append(f" - module: \"{module}\" is loadable: {load_output}")

    # Check if module is loaded
    if not is_module_loaded(module):
        output_pass.append(f" - module: \"{module}\" is not loaded")
    else:
        output_fail.append(f" - module: \"{module}\" is loaded")

else:
    output_fail.append(f" - module: \"{module}\" does not exist in expected paths")

# === Final Output ===
print("\n-- INFO --")
for info in output_info:
    print(info)

print("\n- Audit Result:")
if output_fail:
    print(" ** FAIL **\n - Reason(s) for audit failure:")
    for line in output_fail:
        print(line)
    if output_pass:
        print("\n- Correctly set:")
        for line in output_pass:
            print(line)
else:
    print(" ** PASS **")
    for line in output_pass:
        print(line)
