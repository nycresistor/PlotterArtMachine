# The Plotter Art Machine

## Summary

This is a machine for producing "signed", numbered editions of generative art on the Apple 410 Color Plotter.

By default, every piece will generate an edition of 100. After the full edition has been run, the generating
script is ceremonially deleted from the machine.

## Hardware

This consists of:

* An Apple 410 Color Plotter
* A specific set of pens for said plotter
* A BeagleBone Black
  * Optionally WiFi
  * Serial will be run on PRU to ensure proper HW flow control
* A mounting stand
* Instructions for use

## Setup Instructions

## Frame Script

The frame script keeps track of edition numbers, artist name, paper boundries, and signs and
numbers the piece once the art has been drawn. (It should also keep track of "failed" plots, so
as not to ruin edition numbering.)

## Writing Generative Art Plugins

