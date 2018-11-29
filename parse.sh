#!/bin/sh

pipenv run jupyter nbconvert --to notebook --execute --inplace parse.ipynb
