#!/bin/bash
docker run --rm --volume $( pwd ):/data --user $(id -u):$(id -g) --env JOURNAL=joss openjournals/inara
