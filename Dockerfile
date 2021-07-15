FROM ubuntu:latest
LABEL koala.authors "egmkang@outlook.com"

ENV TZ=Asia/Shanghai DEBIAN_FRONTEND=noninteractive

COPY requirements.txt /tmp/requirements.txt
RUN sed -i s@/archive.ubuntu.com/@/mirrors.aliyun.com/@g /etc/apt/sources.list \
  && alias ll='ls -alF' \
  && alias l='ls -aF' \
  && apt-get update \
  && apt-get install -y python3.9-full curl wget lrzsz vim build-essential g++ gcc tzdata \
  && ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime \
  && echo ${TZ} > /etc/timezone \
  && dpkg-reconfigure --frontend noninteractive tzdata \
  && curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
  && python3.9 get-pip.py \
  && cd /usr/local/bin \
  && ln -s /usr/bin/python3.9 python \
  && ln -s /usr/bin/python3.9 python3 \
  && pip3.9 config set global.index-url https://pypi.mirrors.ustc.edu.cn/simple \
  && pip3.9 install -r /tmp/requirements.txt -i https://pypi.mirrors.ustc.edu.cn/simple

ENTRYPOINT ["python3"]