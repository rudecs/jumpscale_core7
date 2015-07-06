#Creating the image

This need to run once, or anytime you need to rebuild the image

```bash
docker build -t codescalers/jumpscale:7 .
```

#Running the container

```bash
# make sure you have fig first, if you don't
# install fig with `sudo pip install -U fig`
fig up

# to kill your container do
^C
```

#Accessing your running container

```bash
docker ps 

# will show something like
CONTAINER ID        IMAGE                     COMMAND             CREATED             STATUS              PORTS               NAMES
6b5aa0e1110f        codescalers/jumpscale:7   "/sbin/my_init"     5 minutes ago       Up 5 minutes                            docker_js_1

docker inspect 6b5aa0e1110f | grep -i ipaddress

# will show something like
"IPAddress": "172.17.0.15"

ssh root@172.17.0.15 
#Hint: password is rooter

```
