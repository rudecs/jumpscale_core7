FROM phusion/baseimage

CMD /sbin/my_init

RUN rm /etc/service/sshd/down
RUN apt-get update

RUN curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/install.sh | bash
RUN ays install -n singlenode_grid

RUN echo "root:rooter" | chpasswd
