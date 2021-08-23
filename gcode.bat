cd gcodeplot
python gcodeplot_original.py --no-stroke-all --tool-mode draw --tolerance 0.1 --min-x 0 --min-y 0 ^
 --max-x 300 --max-y 300 --work-z 15 --lift-delta-z 0 --safe-delta-z 0 --pen-up-speed 40 ^
 --pen-down-speed 35 --z-speed 5 --send-speed 115200 --direction 45 --optimization-time 60 ^
 ..\test.svg
pause