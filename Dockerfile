FROM ubuntu:18.04

RUN apt-get update \
    && apt-get -y install \
        python3 \
        python3-pip \
        git \
        zlib1g-dev \
        build-essential \
    && pip3 install \
        python-telegram-bot \
        pyyaml

RUN cd /tmp \
    && git clone https://github.com/pyinstaller/pyinstaller \
    && cd pyinstaller/bootloader \
    && python3 ./waf distclean all \
    && cd .. \
    && python3 setup.py install

WORKDIR /app

CMD ["pyinstaller",  "--onefile", "--distpath=/src", "/src/telegram-bot.py"]
