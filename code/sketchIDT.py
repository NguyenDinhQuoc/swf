# imports
import os
import torch
from torchvision.utils import save_image
from torchvision.utils import make_grid
import numpy as np
import tqdm
import copy
from qsketch.sketch import Projectors, load_data
import argparse
from scipy.interpolate import interp1d
import seaborn as sns
import matplotlib.pyplot as plt

plt.ion()


class Chain:

    def __init__(self, num_sketches, epochs, reg=1):
        self.num_sketches = num_sketches
        self.epochs = epochs
        self.reg = reg
        self.qf = None

    def __copy__(self):
        return Chain(self.num_sketches, self.epochs, self.lamb)


def IDT(sketch_file, chain_in, samples_gen_fn,
        plot_function, compute_chain_out=True):

    # Load the sketch data for target
    print('Loading the sketching data for target')
    data = np.load(sketch_file).item()
    qf = data['qf']

    [num_sketches, data_dim, num_quantiles] = qf.shape
    data_dim = data['data_dim']
    print('done')

    # prepare the projectors
    projectors = Projectors(data_dim=data_dim, size=num_sketches)
    quantiles = np.linspace(0, 100, num_quantiles)

    if compute_chain_out:
        # prepare the chain_out
        chain_out = copy.copy(chain_in)
        chain_out.qf = np.empty((chain_in.epochs,
                                 chain_in.num_sketches,
                                 data_dim, num_quantiles))

    samples = samples_gen_fn(data_dim)
    for epoch in tqdm.tqdm(range(chain_in.epochs)):
        for sketch_index in tqdm.tqdm(range(min(chain_in.num_sketches,
                                                num_sketches))):
            projector = projectors[sketch_index]
            samples += chain_in.reg*np.random.randn(*samples.shape)
            projections = np.dot(samples, projector.T)

            if chain_in.qf is None:
                # we need to compute the quantile function for the particles
                # in the projected domain
                source_qf = np.percentile(projections, quantiles, axis=0).T
            else:
                source_qf = chain_in.qf[epoch, sketch_index]

            transported = np.empty(projections.shape)

            for d in range(data_dim):
                F = interp1d(source_qf[d], quantiles, kind='linear',
                             bounds_error=False, fill_value='extrapolate')
                Ginv = interp1d(quantiles, qf[sketch_index, d], kind='linear',
                                bounds_error=False, fill_value='extrapolate')
                zd = np.clip(projections[:, d],
                             source_qf[d, 0], source_qf[d, -1])
                zd = F(zd)
                zd = np.clip(zd, 0, 100)
                transported[:, d] = Ginv(zd)

            samples += (np.dot(transported - projections, projector)
                        + 0*np.random.randn(*samples.shape))

            if compute_chain_out:
                chain_out.qf[epoch, sketch_index] = source_qf

            if plot_function is not None:
                plot_function(samples, epoch, sketch_index)

    if not compute_chain_out:
        chain_out = None
    return samples, chain_out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=
                                     'Performs iterative distribution transfer'
                                     ' with sliced Wasserstein flow.')
    parser.add_argument("sketch_file", help="path to the sketch file as "
                        "generated by the `sketch.py` script")
    parser.add_argument("-w", "--write",
                        help="If provided, save the generated samples to "
                             "this file path after transportation")
    parser.add_argument("-i", "--input_chain",
                        help="Input chain to use, as returned by this same "
                             "script. If provided, overrides any other of "
                             "the parameters `epochs`, `dim`, `lambda`")
    parser.add_argument("-o", "--output_chain",
                        help="keep output chain, and save it to "
                             "provided filepath")
    parser.add_argument("-s", "--samples",
                        help="Initial samples to use, must be a file"
                             "containing a ndarray of dimension num_samples x "
                             "dim, saved with numpy. If provided, overrides"
                             "the parameters `dim`, `num_samples`")
    parser.add_argument("-d", "--dim",
                        help="Dimension of the random input",
                        type=int,
                        default=100)
    parser.add_argument("-n", "--num_samples",
                        help="Number of samples to draw and to transport",
                        type=int,
                        default=3000)
    parser.add_argument("-l", "--num_sketches",
                        help="Number of sketches to use per epoch. "
                             "In case the sketch file contains less, will be "
                             "cropped.",
                        type=int,
                        default=3000)
    parser.add_argument("-e", "--epochs",
                        help="Number of epochs",
                        type=int,
                        default=10)
    parser.add_argument("-r", "--reg",
                        help="Regularization term",
                        type=float,
                        default=1.)
    parser.add_argument("--plot",
                        help="Flag indicating whether or not to plot samples",
                        action="store_true")
    parser.add_argument("-t", "--plot_target",
                        help="Samples from the target "
                             "distribution for plotting purposes. Either a "
                             "file saved by numpy.save containing a ndarray "
                             "of shape num_samples x data_dim, or the name of "
                             "a DATASET in torchvision.datasets")
    parser.add_argument("-p", "--plot_dir",
                        help="Output directory for saving the plots",
                        default="./samples")

    args = parser.parse_args()

    if args.input_chain is not None:
        input_chain = np.load(args.input_chain).item()
    else:
        input_chain = Chain(args.num_sketches, args.epochs, args.reg)

    if args.samples is None:
        def generate_samples(data_dim):
            z = np.random.randn(args.num_samples, args.dim)
            if args.dim != data_dim:
                np.random.seed(0)
                up_sampling = np.random.randn(args.dim, data_dim)
                z = np.dot(z, up_sampling)
            return z
    else:
        def generate_samples(data_dim):
            samples = np.load(args.samples)
            if len(samples.shape) != 2 or samples.shape[1] != data_dim:
                raise ValueError('Samples in %s do not have the right shape. '
                                 'They should be num_samples x %d for this '
                                 'sketch file.' % (args.samples, data_dim))
            return samples
    if args.output_chain is not None:
        compute_output_chain = True
    else:
        compute_output_chain = False

    if args.plot_target is not None:
        # just handle numpy arrays now
        target_samples = load_data(args.plot_target, None)[0]
        ntarget = min(10000, target_samples.shape[0])
        axis_lim = [[v.min(), v.max()] for v in target_samples.T]
        target_samples = target_samples[:ntarget]
    if args.plot:
        if not os.path.exists(args.plot_dir):
            os.mkdir(args.plot_dir)

        def plot_function(samples, epoch, sketch_index):
            data_dim = samples.shape[-1]
            image = False

            if data_dim > 700:
                square_dim_bw = np.sqrt(data_dim)
                square_dim_col = np.sqrt(data_dim/3)
                if not (square_dim_col % 1):
                    image = True
                    nchan = 3
                    img_dim = int(square_dim_col)
                elif not (square_dim_bw % 1):
                    image = True
                    nchan = 1
                    img_dim = int(square_dim_bw)
            if not image:
                plt.figure(1, figsize=(8, 8))
                plt.clf()
                if args.plot_target is not None:
                    plt.plot(target_samples[:, 0], target_samples[:, 1], 'or')
                #ax = sns.kdeplot(samples[:, 0], samples[:, 1],
                #                 cmap="Blues", shade=True, shade_lowest=False)

                plt.plot(samples[:, 0], samples[:, 1], 'ob')
                plt.xlim(axis_lim[0])
                plt.ylim(axis_lim[1])
                plt.grid(True)
                plt.title('epoch %d, sketch %d' % (epoch, sketch_index+1))

                plt.pause(0.05)
                plt.show()
                return
            [num_samples, data_dim] = samples.shape
            samples = samples[:min(100, num_samples)]
            num_samples = samples.shape[0]

            samples = np.reshape(samples,
                                 [num_samples, nchan, img_dim, img_dim])
            pic = make_grid(torch.Tensor(samples),
                            nrow=8, padding=2, normalize=True)
            save_image(pic, '{}/image_{}_{}.png'.format(args.plot_dir, epoch,
                                                        sketch_index))
    else:
        plot_function = None

    samples, chain_out = IDT(args.sketch_file, input_chain, generate_samples,
                             plot_function, compute_output_chain)

    if compute_output_chain:
        np.save(args.output_chain, chain_out)
    if args.write is not None:
        np.save(args.write, samples)
