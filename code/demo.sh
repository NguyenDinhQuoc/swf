 python ./generate_toydata.py  -o toydata -d 2 -n 50000 -c 50
 python qsketch/sketch.py ./toydata.npy -n 300 -q 100 -o toysketch
 python sketchIDT.py toysketch.npy  -d 2 -n 3000 --plot_target toydata.npy --plot -r 2 -e 100
