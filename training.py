import torch
import random
import time
from network import ClassificationNetwork
from imitations import load_imitations


def train(data_folder, trained_network_file):
    """
    Function for training the network.
    """
    infer_action = ClassificationNetwork()
    optimizer = torch.optim.Adam(infer_action.parameters(), lr=1e-2)
    observations, actions = load_imitations(data_folder)
    observations = [torch.Tensor(observation) for observation in observations]
    actions = [torch.Tensor(action) for action in actions]
    # tensor is a matrix

    batches = [batch for batch in zip(observations,
                                      infer_action.actions_to_classes(actions))]
    gpu = torch.device('cuda')

    nr_epochs = 100
    batch_size = 64
    number_of_classes = 9  # needs to be changed
    start_time = time.time()

    for epoch in range(nr_epochs): # epoch is number of times you goes thru entire datset
        random.shuffle(batches)

        total_loss = 0
        batch_in = []
        batch_gt = []
        for batch_idx, batch in enumerate(batches):
            batch_in.append(batch[0].to(gpu))
            batch_gt.append(batch[1].to(gpu))

            if (batch_idx + 1) % batch_size == 0 or batch_idx == len(batches) - 1:
                batch_in = torch.reshape(torch.cat(batch_in, dim=0),
                                         (-1, 96, 96, 3))
                batch_gt = torch.reshape(torch.cat(batch_gt, dim=0),
                                         (-1, number_of_classes))

                batch_out = infer_action(batch_in)
                loss = cross_entropy_loss(batch_out, batch_gt)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                total_loss += loss

                batch_in = []
                batch_gt = []

        time_per_epoch = (time.time() - start_time) / (epoch + 1)
        time_left = (1.0 * time_per_epoch) * (nr_epochs - 1 - epoch)
        print("Epoch %5d\t[Train]\tloss: %.6f \tETA: +%fs" % (
            epoch + 1, total_loss, time_left))

    torch.save(infer_action, trained_network_file)


def cross_entropy_loss(batch_out, batch_gt):
    epsilon = 0.000001
    loss = batch_gt * torch.log(batch_out + epsilon) + (1 - batch_gt) * torch.log(1 - batch_out + epsilon)
    loss_returned = -torch.mean(torch.sum(loss, dim=1), dim=0)

    # batch_out = batch_out.permute(0, 2, 3, 1).contiguous().view(-1, class_numer)  # size is 196 x 80
    # loss = torch.nn.functional.CrossEntropyLoss(batch_out, batch_gt)
    """
    Calculates the cross entropy loss between the prediction of the network and
    the ground truth class for one batch.
    batch_out:      torch.Tensor of size (batch_size, number_of_classes)
    batch_gt:       torch.Tensor of size (batch_size, number_of_classes)
    return          float
    """
    return loss_returned
