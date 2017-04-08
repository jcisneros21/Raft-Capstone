#!/bin/bash

#rm -f "logfile1.txt"
#rm -f "logfile2.txt"
#rm -f "logfile3.txt"
#rm -f "logfile4.txt"
#rm -f "logfile5.txt"
#rm -f "logfile6.txt"

ls | grep 'logfile[0-9]*.txt' | xargs rm
