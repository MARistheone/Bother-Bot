import paramiko
import os
import base64

def run(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors='replace').strip()
    err = stderr.read().decode(errors='replace').strip()
    if out: print("STDOUT:\n" + out.encode('ascii', 'replace').decode('ascii'))
    if err: print("STDERR:\n" + err.encode('ascii', 'replace').decode('ascii'))
    return exit_status, out, err

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("100.94.92.50", port=5151, username="amiel", password="sy#Woofy9420")
    
    pwd = "sy#Woofy9420"

    print("Setting up new directory structure...")
    run(ssh, "mkdir -p /volume1/docker/bother-bot/src/cogs")
    run(ssh, "mkdir -p /volume1/docker/bother-bot/data")

    # Stop old container if running from old dir
    print("Stopping any old containers...")
    run(ssh, f"echo {pwd} | sudo -S /usr/local/bin/docker compose -f /volume1/homes/amiel/bother-bot/docker-compose.yml down")
    run(ssh, f"echo {pwd} | sudo -S /usr/local/bin/docker compose -f /volume1/docker/bother-bot/docker-compose.yml down")

    # Copy old database over if it hasn't been moved
    run(ssh, f"echo {pwd} | sudo -S cp -a /volume1/homes/amiel/bother-bot/data/* /volume1/docker/bother-bot/data/ 2>/dev/null || true")

    files_to_upload = [
        "Dockerfile",
        "docker-compose.yml",
        "requirements.txt",
        ".env",
        "src/__init__.py",
        "src/bot.py",
        "src/constants.py",
        "src/db.py",
        "src/embeds.py",
        "src/scoring.py",
        "src/views.py",
        "src/cogs/__init__.py",
        "src/cogs/accountability.py",
        "src/cogs/loops.py",
        "src/cogs/tasks.py",
    ]
    
    remote_dir = "/volume1/docker/bother-bot"
    
    for f in files_to_upload:
        local_path = os.path.join(r"c:\Users\Amiel\Documents\Bother Bot", f)
        remote_path = f"{remote_dir}/{f}"
        print(f"Uploading {local_path} to {remote_path} via base64...")
        
        # Only upload if the file exists locally
        if not os.path.exists(local_path):
            print(f"Warning: {local_path} does not exist. Skipping.")
            continue
            
        with open(local_path, "rb") as file:
            content = file.read()
            b64 = base64.b64encode(content).decode("ascii")
        
        # Upload using base64 decoding on remote
        run(ssh, f"echo '{b64}' | base64 -d > '{remote_path}'")
    
    print("Starting new Docker container on NAS...")
    # restart docker-compose with build context to install the new dateparser module
    run(ssh, f"cd {remote_dir} && echo {pwd} | sudo -S /usr/local/bin/docker compose build")
    run(ssh, f"cd {remote_dir} && echo {pwd} | sudo -S /usr/local/bin/docker compose up -d")

finally:
    ssh.close()
