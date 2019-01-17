# parameters for sketching
NUM_QUANTILES=100
NUM_THETAS=2000
CLIPTO=5000

# parameters for SWF
INPUT_DIM=28
NUM_SAMPLES=5000

STEPSIZE=10
REG=0

if [ $1 = "toy.npy" ]; then
  echo "generating toy data, and then SWF on it"

  # Generate data:
  NUM_SAMPLES_TOY=50000
  NUM_COMPONENTS_TOY=5
  SEED_STRING="--seed 10"

  python ./generate_toydata.py  --output toy --dim $INPUT_DIM --num_samples $NUM_SAMPLES_TOY --num_components $NUM_COMPONENTS_TOY $SEED_STRING
fi

# now launch the sliced Wasserstein flow
python swf.py $1 --root_data_dir ~/data/$1 --clip $CLIPTO --num_quantiles $NUM_QUANTILES --input_dim $INPUT_DIM --num_samples $NUM_SAMPLES --stepsize $STEPSIZE --reg $REG --num_thetas $NUM_THETAS --plot_dir ~/samples_$1 --logdir logs/$1 --plot_every 1
