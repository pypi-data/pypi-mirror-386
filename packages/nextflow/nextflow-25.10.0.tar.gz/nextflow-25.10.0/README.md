# Nextflow launcher python package

## Description
This package is purely an installer for the Nextflow launcher (<https://nextflow.io/>) that allows
you to easily have the `nextflow` command line available on your system.

## How to install
 - Install Nextflow launcher using `pip install nextflow`. 
 - Now `nextflow` command is available on your path.
 - Run `nextflow info` to force it download all the dependencies the first time (optional).
 - Now you are ready to run a pipeline `nextflow run hello`. 

## Requirements
The Nextflow launcher requires Java and `curl` or `wget` available on your
system to be able to download Nextflow Java dependencies and launch Nextflow.

## Note
If you are looking for previous versions of this package that was a wrapper around the Nextflow
pipeline framework that lets you run pipelines from Python code, check `nextflowpy` package.
