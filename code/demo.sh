# parameters for sketching
NUM_SKETCHES=10 # 10 for MNIST/celeba
NUM_THETAS=4000 # 4000 for MNIST/celeba
NUM_QUANTILES=500
NUM_EXAMPLES=5000


# images dimensions
IMG_SIZE=32

# number of workers, increase or decrease depending on your equipment
# note that if you are CUDA-equipped, AND using autoencoder, then the number
# of dataworkers specified here will be ignored: only one will be used
NUM_DATAWORKERS=2
NUM_SKETCHERS=2

# parameters for auto encoder
AE_STRING="--ae" # put "--ae" for using an autoencoder
CONV_AE_STRING="--conv_ae" # put "--conv_ae" for a conv AE
BOTTLENECK_SIZE=32

# parameters for SWF
STEPSIZE=5 # pick 0.5 for toy, 5 for MNIST/image stuff
REG=0 # 0 works just fine: discretization of quantile is just like additive noise
NUM_EPOCHS=500

# whether to change the sketches at each epoch or not.
# to change the sketch, set this to "--no_fixed_sketch"
NO_FIXED_SKETCH_STRING=""

# number of particles
NUM_SAMPLES=5000

# controls the dimension of the input. -1 for the dimension of the bottleneck
INPUT_DIM=10

# number of test
NUM_TEST=5000
TEST_TYPE='RANDOM'

# plot options
PLOT_EVERY=10
PLOT_NUM_TRAIN=104
PLOT_NUM_TEST=96
PLOT_NUM_FEATURES=2
MATCH_EVERY=500

if [ $1 = "toy" ]; then
  echo "generating toy data, and then SWF on it"

  # Generate data:
  NUM_SAMPLES_TOY=50000
  NUM_COMPONENTS_TOY=10
  INPUT_DIM=2
  SEED_STRING="--seed 0"

  python ./generate_toydata.py  --output toy --dim $INPUT_DIM --num_samples $NUM_SAMPLES_TOY --num_components $NUM_COMPONENTS_TOY $SEED_STRING
fi

# now launch the sliced Wasserstein flow
python swf.py $1 $NO_FIXED_SKETCH_STRING  --root_data_dir ~/data --img_size $IMG_SIZE --num_sketches $NUM_SKETCHES --num_sketchers $NUM_SKETCHERS --num_dataworkers $NUM_DATAWORKERS --num_examples $NUM_EXAMPLES --num_quantiles $NUM_QUANTILES --input_dim $INPUT_DIM  --num_samples $NUM_SAMPLES --stepsize $STEPSIZE --regularization $REG --num_thetas $NUM_THETAS --num_epochs $NUM_EPOCHS $AE_STRING $CONV_AE_STRING --bottleneck_size $BOTTLENECK_SIZE --ae_model ae --num_test $NUM_TEST --test_type $TEST_TYPE --plot_dir ~/swf_samples_$1 --plot_every $PLOT_EVERY --match_every $MATCH_EVERY --plot_num_train $PLOT_NUM_TRAIN --plot_num_test $PLOT_NUM_TEST
