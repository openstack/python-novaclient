#!/bin/bash

git shortlog -se | awk '{ print $2, $3, $4}'
