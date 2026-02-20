import paramiko
import os
import base64

def run(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors='replace').strip()
    err = stderr.read().decode(errors='replace').strip()
    if out: print("STDOUT:\n" + out)
    if err: print("STDERR:\n" + err)
    return exit_status, out, err

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("100.94.92.50", port=5151, username="amiel", password="sy#Woofy9420")
    
    files_to_upload = [
        "src/constants.py",
        "src/embeds.py",
        "src/views.py"
    ]
    
    remote_dir = "/volume1/homes/amiel/bother_bot"
    pwd = "sy#Woofy9420"
    
    for f in files_to_upload:
        local_path = os.path.join(r"c:\Users\Amiel\Documents\Bother Bot", f)
        remote_path = f"{remote_dir}/{f}"
        print(f"Uploading {local_path} to {remote_path} via base64...")
        with open(local_path, "rb") as file:
            content = file.read()
            b64 = base64.b64encode(content).decode("ascii")
        
        # Upload using base64 decoding on remote
        run(ssh, f"echo '{b64}' | base64 -d > '{remote_path}'")
    
    print("Restarting Docker container on NAS...")
    # restart docker-compose or container
    run(ssh, f"echo {pwd} | sudo -S /usr/local/bin/docker compose -f {remote_dir}/docker-compose.yml restart")
finally:
    ssh.close()
