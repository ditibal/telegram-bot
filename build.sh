#!/bin/bash

docker image build -t telegram-bot-build . \
&& docker run --rm -v ${PWD}:/src telegram-bot-build
