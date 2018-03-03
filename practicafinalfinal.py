#!/usr/bin/python
import sys
import subprocess
import time


#ARRANCAR ESCENARIO ( SE SUPONE QUE YA HEMOS GUARDADO EL FW.FW AQUI):
subprocess.call("sudo vnx -f pfinal.xml --destroy", shell = True)
subprocess.call("sudo vnx -f s4.xml --destroy", shell = True)
subprocess.call("sudo vnx -f pfinal.xml --create", shell = True)
subprocess.call("sudo vnx -f s4.xml --create", shell = True)
subprocess.call("sudo vnx -f gesxml --destroy", shell = True)
subprocess.call("sudo vnx -f ges.xml --create", shell = True)

time.sleep(20)


#CONFIGURAMOS LA BBDD

cmd1 = "sudo lxc-attach --clear-env -n bbdd -- bash -c \" echo 'listen_addresses = '\\\"'10.1.4.31'\\\"'' >> /etc/postgresql/9.6/main/postgresql.conf \" "
cmd2 = "sudo lxc-attach --clear-env -n bbdd -- bash -c \"echo 'host all all 10.1.4.0/24 trust' >> /etc/postgresql/9.6/main/pg_hba.conf\""
cmd3 = "sudo lxc-attach --clear-env -n bbdd -- bash -c \"echo 'CREATE USER crm with PASSWORD' \\\"'xxxx'\\\"';' | sudo -u postgres psql\""
cmd4 = "sudo lxc-attach --clear-env -n bbdd -- bash -c \"echo 'CREATE DATABASE crm;' | sudo -u postgres psql\""
cmd5 = "sudo lxc-attach --clear-env -n bbdd -- bash -c \"echo 'GRANT ALL PRIVILEGES ON DATABASE crm to crm;' | sudo -u postgres psql\""

subprocess.call("sudo lxc-attach --clear-env -n bbdd -- apt update", shell = True)
subprocess.call("sudo lxc-attach --clear-env -n bbdd -- apt -y install postgresql", shell = True)
subprocess.call(cmd1, shell = True)
subprocess.call(cmd2, shell = True)
subprocess.call(cmd3, shell = True)
subprocess.call(cmd4, shell = True)
subprocess.call(cmd5, shell = True)
subprocess.call("sudo lxc-attach --clear-env -n bbdd -- systemctl restart postgresql", shell = True)


#CONFIGURAR CLUSTERFS DESDE NAS1

subprocess.call("sudo lxc-attach --clear-env -n nas1 -- bash -c \"cd /root; gluster peer probe 10.1.4.21; gluster peer probe 10.1.4.22; gluster peer probe 10.1.4.23; gluster peer status\"", shell = True)
time.sleep(5)
subprocess.call("sudo lxc-attach --clear-env -n nas1 -- bash -c \"cd /root; gluster volume create nas replica 3 10.1.4.21:/nas 10.1.4.22:/nas 10.1.4.23:/nas force \"", shell = True)
time.sleep(5)
subprocess.call("sudo lxc-attach --clear-env -n nas1 -- bash -c \" cd /root; gluster volume start nas;  gluster volume set nas network.ping-timeout 5\"", shell = True)
subprocess.call("sudo lxc-attach --clear-env -n nas2 -- bash -c \" cd /root;gluster volume set nas network.ping-timeout 5\"", shell = True)
subprocess.call("sudo lxc-attach --clear-env -n nas3 -- bash -c \" cd /root;gluster volume set nas network.ping-timeout 5\"", shell = True)




#CONFIGURACION DE CRM



#S1

subprocess.call("sudo lxc-attach --clear-env --set-var DATABASE_URL=postgres://crm:xxxx@10.1.4.31:5432/crm -n s1 -- bash -c \"cd /root; apt-get update; curl -sL https://deb.nodesource.com/setup_9.x | sudo bash -; apt-get install -y nodejs; git clone https://github.com/CORE-UPM/CRM_2017; cd /root/CRM_2017; mkdir /root/CRM_2017/public/uploads; mount -t glusterfs 10.1.4.21:/nas /root/CRM_2017/public/uploads; npm install; npm install forever; npm run-script migrate_local; npm run-script seed_local; ./node_modules/forever/bin/forever start ./bin/www\"", shell = True)

#S2

subprocess.call("sudo lxc-attach --clear-env --set-var DATABASE_URL=postgres://crm:xxxx@10.1.4.31:5432/crm -n s2 -- bash -c \"cd /root; apt-get update; curl -sL https://deb.nodesource.com/setup_9.x | sudo bash -; apt-get install -y nodejs; git clone https://github.com/CORE-UPM/CRM_2017; cd /root/CRM_2017; npm install; npm install forever; ./node_modules/forever/bin/forever start ./bin/www; mkdir /root/CRM_2017/public/uploads; mount -t glusterfs 10.1.4.21:/nas /root/CRM_2017/public/uploads\"", shell = True)

#S3

subprocess.call("sudo lxc-attach --clear-env --set-var DATABASE_URL=postgres://crm:xxxx@10.1.4.31:5432/crm -n s3 -- bash -c \"cd /root; apt-get update; curl -sL https://deb.nodesource.com/setup_9.x | sudo bash -; apt-get install -y nodejs; git clone https://github.com/CORE-UPM/CRM_2017; cd /root/CRM_2017; npm install; npm install forever; ./node_modules/forever/bin/forever start ./bin/www; mkdir /root/CRM_2017/public/uploads; mount -t glusterfs 10.1.4.21:/nas /root/CRM_2017/public/uploads\"", shell = True)

#S4

subprocess.call("sudo lxc-attach --clear-env --set-var DATABASE_URL=postgres://crm:xxxx@10.1.4.31:5432/crm -n s4 -- bash -c \"cd /root; apt-get update; curl -sL https://deb.nodesource.com/setup_9.x | sudo bash -; apt-get install -y nodejs; git clone https://github.com/CORE-UPM/CRM_2017; cd /root/CRM_2017; npm install; npm install forever; ./node_modules/forever/bin/forever start ./bin/www; mkdir /root/CRM_2017/public/uploads; mount -t glusterfs 10.1.4.21:/nas /root/CRM_2017/public/uploads\"", shell = True)


#CONFIGURACION LB
subprocess.call("sudo lxc-attach --clear-env -n lb -- service apache2 stop", shell = True)
subprocess.call("sudo lxc-attach --clear-env -n lb -- xr -dr --verbose --server tcp:0:80 --backend 10.1.3.11:3000 --backend 10.1.3.12:3000 --backend 10.1.3.13:3000 --backend 10.1.3.14:3000 --web-interface 0:8001 &", shell = True)

#Para GES 	

subprocess.call("sudo lxc-attach --clear-env -n c1 -- bash -c \"cd /root/.ssh; ssh-keygen -N '' -f idrsa1\"", shell = True)
subprocess.call("sudo cp /var/lib/lxc/c1/rootfs/root/.ssh/idrsa1.pub  /var/lib/lxc/GES/rootfs/root/.ssh",shell=True)
subprocess.call("sudo lxc-attach --clear-env -n GES -- bash -c \"cd /root/.ssh; cat idrsa1.pub >> /root/.ssh/authorized_keys; \"", shell = True)
subprocess.call("sudo lxc-attach --clear-env -n c1 -- bash -c \"cd /root/.ssh; echo 'Host GES' >> config; echo 'Hostname 10.1.3.15' >> config; echo 'IdentityFile /root/.ssh/idsa1' >> config \"", shell = True)

#COPIAR EL SCRIPT AL FW (preguntar si esta bien solo icmp reply):
subprocess.call("sudo cp fw.fw /var/lib/lxc/fw/rootfs/root", shell = True)

#EJECUTAMOS EL SCRIPT EN EL FW DESDE LA CONSOLA DE NUESTRO LINUX:
subprocess.call("sudo lxc-attach --clear-env -n fw -- sh /root/fw.fw", shell = True)












