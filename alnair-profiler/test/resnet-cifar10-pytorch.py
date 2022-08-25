# A quick intro to implement the Distributed Data Parallel (DDP) training in Pytorch.
# To simply this example, we directly load the ResNet50 using ```torch.hub.load()```,
# and train it from the scratch using the CIFAR10 dataset.

# Run this python script in terminal like "python3 DDP_training.py -n 1 -g 8 -nr 0"

import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime
import argparse
import torch.multiprocessing as mp
import torchvision
import torchvision.transforms as transforms
import torch
import torch.nn as nn
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.tensorboard import SummaryWriter


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--nodes', default=1, type=int, metavar='N',
                        help='number of data loading workers (default: 4)')
    parser.add_argument('-g', '--gpus', default=1, type=int,
                        help='number of gpus per node')
    parser.add_argument('-nr', '--nr', default=0, type=int,
                        help='ranking within the nodes')
    parser.add_argument('--epochs', default=20, type=int, metavar='N',
                        help='number of total epochs to run')
    args = parser.parse_args()
    args.world_size = args.gpus * args.nodes
    os.environ['MASTER_ADDR'] = 'localhost'
    os.environ['MASTER_PORT'] = '8889'
    mp.spawn(train, nprocs=args.gpus, args=(args,))

# helper function to show an image
# (used in the `plot_classes_preds` function below)
def matplotlib_imshow(img, one_channel=False):
    if one_channel:
        img = img.mean(dim=0)
    img = img / 2 + 0.5     # unnormalize
    npimg = img.numpy()
    if one_channel:
        plt.imshow(npimg, cmap="Greys")
    else:
        plt.imshow(np.transpose(npimg, (1, 2, 0)))

def train(gpu, args):
    use_nvme = False

    if use_nvme:
        data_dir = '/data'
    else:
        data_dir = '/tmp/test'
    # writer = SummaryWriter('/data/runs/cifar10_experiment')

    model = torch.hub.load('pytorch/vision:v0.9.0', 'resnet50', pretrained=False)
    rank = args.nr * args.gpus + gpu

    dist.init_process_group(backend='nccl', init_method='env://', world_size=args.world_size, rank=rank)
    torch.manual_seed(0)
    torch.cuda.set_device(gpu)
    model.cuda(gpu)

    transform = transforms.Compose(
        [transforms.ToTensor(),
         transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])

    batch_size = 100
    # define loss function (criterion) and optimizer
    criterion = nn.CrossEntropyLoss().cuda(gpu)
    optimizer = torch.optim.SGD(model.parameters(), 1e-4)
    # Wrap the model
    model = nn.parallel.DistributedDataParallel(model, device_ids=[gpu])
    # Data loading code


    trainset = torchvision.datasets.CIFAR10(root=data_dir,
                                            train=True,
                                            download=True,
                                            transform=transform)
    trainsampler = torch.utils.data.distributed.DistributedSampler(trainset,
                                                                    num_replicas=args.world_size,
                                                                    rank=rank)
    trainloader = torch.utils.data.DataLoader(trainset,
                                              batch_size=batch_size,
                                              shuffle=False,
                                              num_workers=4,
                                              pin_memory=False,
                                              sampler=trainsampler)

    total_step = len(trainloader)
    train_start = datetime.now()
    for epoch in range(args.epochs):
        start = datetime.now()
        for i, (images, labels) in enumerate(trainloader):
            images = images.cuda(non_blocking=True)
            labels = labels.cuda(non_blocking=True)
            # img_grid = torchvision.utils.make_grid(images).cpu()            

            # Forward pass
            outputs = model(images)
            loss = criterion(outputs, labels)

            # Backward and optimize
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            # tensorboard calls
            #
            # matplotlib_imshow(img_grid, one_channel=True)
            # writer.add_image('cifar_images', img_grid)

        if gpu == 0:
            print('Epoch [{}/{}], Loss: {:.4f}, elapse: {}'.format(epoch + 1, args.epochs,  loss.item(), datetime.now() - start))
    print("Training done, total epoch {}, total time {}".format(args.epochs, datetime.now()-train_start))

if __name__ == '__main__':
    main()
