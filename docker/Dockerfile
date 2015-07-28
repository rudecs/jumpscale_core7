FROM phusion/baseimage

CMD /sbin/my_init

RUN rm /etc/service/sshd/down

RUN apt-get update --fix-missing
RUN apt-get install -y python2.7
RUN apt-get install -y python-pip

RUN curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/install.sh | bash

RUN ays install -n singlenode_grid

RUN echo "root:rooter" | chpasswd
