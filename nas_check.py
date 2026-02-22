import paramiko

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
    
    remote_dir = "/volume1/docker/bother-bot"
    pwd = "sy#Woofy9420"
    print("Checking Docker containers on NAS...")
    run(ssh, f"echo {pwd} | sudo -S /usr/local/bin/docker ps | grep bother-bot")
finally:
    ssh.close()
