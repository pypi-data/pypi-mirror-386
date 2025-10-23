"""
Contains functions for training and testing a PyTorch model.
"""
from typing import Dict, List, Tuple, Optional

import torch

from tqdm.auto import tqdm

from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, precision_score, recall_score, f1_score, classification_report
import matplotlib.pyplot as plt

import wandb

def train_step(model: torch.nn.Module,
               dataloader: torch.utils.data.DataLoader,
               loss_fn: torch.nn.Module,
               optimizer: torch.optim.Optimizer,
               device: torch.device) -> Tuple[float, float]:
    """Trains a PyTorch model for a single epoch.

    Turns a target PyTorch model to training mode and then
    runs through all of the required training steps (forward
    pass, loss calculation, optimizer step).

    Args:
    model: A PyTorch model to be trained.
    dataloader: A DataLoader instance for the model to be trained on.
    loss_fn: A PyTorch loss function to minimize.
    optimizer: A PyTorch optimizer to help minimize the loss function.
    device: A target device to compute on (e.g. "cuda" or "cpu").

    Returns:
    A tuple of training loss and training accuracy metrics.
    In the form (train_loss, train_accuracy). For example:

    (0.1112, 0.8743)
    """
    # Put model in train mode
    model.train()

    # Setup train loss and train accuracy values
    train_loss, train_acc = 0, 0

    # Loop through data loader data batches
    for batch, (X, y) in enumerate(dataloader):
        # Send data to target device
        X, y = X.to(device), y.to(device)

        # 1. Forward pass
        y_pred = model(X)

        # 2. Calculate and accumulate loss
        loss = loss_fn(y_pred, y)
        train_loss += loss.item()

        # 3. Optimizer zero grad
        optimizer.zero_grad()

        # 4. Loss backward
        loss.backward()

        # 5. Optimizer step
        optimizer.step()

        # Calculate and accumulate accuracy metric across all batches
        y_pred_class = y_pred.argmax(dim=1)
        train_acc += (y_pred_class == y).sum().item()/len(y_pred)

    # Adjust metrics to get average loss and accuracy per batch
    train_loss = train_loss / len(dataloader)
    train_acc = train_acc / len(dataloader)
    return train_loss, train_acc

def test_step(model: torch.nn.Module,
              dataloader: torch.utils.data.DataLoader,
              loss_fn: torch.nn.Module,
              device: torch.device) -> Tuple[float, float]:
    """Tests a PyTorch model for a single epoch.

    Turns a target PyTorch model to "eval" mode and then performs
    a forward pass on a testing dataset.

    Args:
    model: A PyTorch model to be tested.
    dataloader: A DataLoader instance for the model to be tested on.
    loss_fn: A PyTorch loss function to calculate loss on the test data.
    device: A target device to compute on (e.g. "cuda" or "cpu").

    Returns:
    A tuple of testing loss and testing accuracy metrics.
    In the form (test_loss, test_accuracy). For example:

    (0.0223, 0.8985)
    """
    # Put model in eval mode
    model.eval()

    # Setup test loss and test accuracy values
    test_loss, test_acc = 0, 0

    # Turn on inference context manager
    with torch.inference_mode():
        # Loop through DataLoader batches
        for batch, (X, y) in enumerate(dataloader):
            # Send data to target device
            X, y = X.to(device), y.to(device)

            # 1. Forward pass
            test_pred_logits = model(X)

            # 2. Calculate and accumulate loss
            loss = loss_fn(test_pred_logits, y)
            test_loss += loss.item()

            # Calculate and accumulate accuracy
            test_pred_labels = test_pred_logits.argmax(dim=1)
            test_acc += ((test_pred_labels == y).sum().item()/len(test_pred_labels))

    # Adjust metrics to get average loss and accuracy per batch
    test_loss = test_loss / len(dataloader)
    test_acc = test_acc / len(dataloader)
    return test_loss, test_acc

def train(model: torch.nn.Module,
          train_dataloader: torch.utils.data.DataLoader,
          val_dataloader: torch.utils.data.DataLoader,
          optimizer: torch.optim.Optimizer,
          loss_fn: torch.nn.Module,
          num_epochs: int,
          device: torch.device,
          config: Optional[dict] = None,
          early_stopping: Optional[object] = None,
          scheduler: Optional[object] = None) -> Dict[str, List[float]]:
    """Trains and tests a PyTorch model.

    Passes a target PyTorch models through train_step() and test_step()
    functions for a number of epochs, training and testing the model
    in the same epoch loop.

    Calculates, prints and stores evaluation metrics throughout.

    Args:
    model: A PyTorch model to be trained and tested.
    train_dataloader: A DataLoader instance for the model to be trained on.
    val_dataloader: A DataLoader instance for the model to be tested on.
    optimizer: A PyTorch optimizer to help minimize the loss function.
    loss_fn: A PyTorch loss function to calculate loss on both datasets.
    num_epochs: An integer indicating how many epochs to train for.
    device: A target device to compute on (e.g. "cuda" or "cpu").

    Returns:
    A dictionary of training and testing loss as well as training and
    testing accuracy metrics. Each metric has a value in a list for 
    each epoch.
    In the form: {train_loss: [...],
              train_acc: [...],
              test_loss: [...],
              test_acc: [...],
              best_epoch: Int } 
    For example if training for epochs=2: 
             {train_loss: [2.0616, 1.0537],
              train_acc: [0.3945, 0.3945],
              test_loss: [1.2641, 1.5706],
              test_acc: [0.3400, 0.2973]} 
    """
    # start a new wandb run to track this script if use_wandb=True
    use_wandb = config is not None and config.get('flags', {}).get('use_wandb', False)
    if use_wandb:
        wandb.init(
            # set the wandb project where this run will be logged
            project=config.get('project_name', 'pytorch-training'),
            # track hyperparameters and run metadata
            config=config
        )

    # Create empty results dictionary
    results = {"train_loss": [],
               "train_acc": [],
               "test_loss": [],
               "test_acc": [],
               "best_epoch": None 
    }

    # Ensure model is on target device
    model.to(device)

    # Loop through training and testing steps for a number of epochs
    for epoch in tqdm(range(num_epochs)):
        train_loss, train_acc = train_step(model=model,
                                          dataloader=train_dataloader,
                                          loss_fn=loss_fn,
                                          optimizer=optimizer,
                                          device=device)
        test_loss, test_acc = test_step(model=model,
          dataloader=val_dataloader,
          loss_fn=loss_fn,
          device=device)

        # Track metrics with wandb
        if use_wandb:
            wandb.log({
                "train/loss": train_loss,
                "train/accuracy": train_acc,
                "val/loss": test_loss,
                "val/accuracy": test_acc,
            })

        # Print out what's happening
        print(f"{'*'*10} EPOCH: {epoch} {'*'*10}")
        print(f"Train loss: {train_loss:.5f} \t test loss: {test_loss:.5f}")
        print(f"Train acc: {train_acc:.3f} \t Test acc: {test_acc:.3f}")
        
        # Update results dictionary
        results["train_loss"].append(train_loss)
        results["train_acc"].append(train_acc)
        results["test_loss"].append(test_loss)
        results["test_acc"].append(test_acc)
        
        # Check for early stopping 
        if early_stopping:
            early_stopping(test_loss, model, epoch)
            if early_stopping.early_stop:
                break

        # Use scheduler for learning rate 
        if scheduler:
            scheduler.step(test_loss)

    # Return the filled results at the end of the epochs
    if early_stopping:
        results["best_epoch"] = early_stopping.best_epoch
        early_stopping.load_best_model(model)

    return results



def evaluate_model(model: torch.nn.Module,
                   test_dataloader: torch.utils.data.DataLoader,
                   loss_fn: torch.nn.Module,
                   device: torch.device,
                   class_names: List[str],
                   log_to_wandb: bool = False):
        """
        Evaluates a PyTorch model on test data and displays performance metrics.

        This function performs model evaluation on a test dataset, calculating loss and accuracy metrics,
        and visualizes the results using a confusion matrix.

        Args:
            model: PyTorch model to evaluate
            test_dataloader: DataLoader containing the test dataset
            loss_fn: Loss function to calculate model loss
            device: Device to run the model on (CPU/GPU)
            class_names: List of class names for confusion matrix labels
            log_to_wandb: If True, log metrics and visualizations to wandb

        Returns:
            None: Displays test metrics and confusion matrix plot
        """
        # Collect all true and predicted labels
        all_true_labels = []
        all_pred_labels = []

        # Inference and metric calculation
        test_loss, test_acc = 0, 0

        with torch.inference_mode():
            for batch, (X, y) in enumerate(test_dataloader):
                # Send data to target device
                X, y = X.to(device), y.to(device)

                # Forward pass
                test_pred_logits = model(X)

                # Calculate and accumulate loss
                loss = loss_fn(test_pred_logits, y)
                test_loss += loss.item()

                # Calculate predictions
                test_pred_labels = test_pred_logits.argmax(dim=1)
                test_acc += ((test_pred_labels == y).sum().item() / len(test_pred_labels))

                # Store labels for confusion matrix
                all_true_labels.extend(y.cpu().numpy())
                all_pred_labels.extend(test_pred_labels.cpu().numpy())

        # Adjust metrics to get average loss and accuracy
        test_loss /= len(test_dataloader)
        test_acc /= len(test_dataloader)

        print(f"Test loss: {test_loss:.3f}, test accuracy: {test_acc:.3f}")

        # Confusion matrix
        conf_matrix = confusion_matrix(all_true_labels, all_pred_labels)

        # Plot the confusion matrix with class names
        disp = ConfusionMatrixDisplay(confusion_matrix=conf_matrix, display_labels=class_names)
        disp.plot(cmap=plt.cm.Blues)
        plt.xticks(rotation=90)
        plt.title("Confusion Matrix")
        plt.show()

        # Calculate precision, recall, and F1-score (macro and weighted averages)
        precision_macro = precision_score(all_true_labels, all_pred_labels, average='macro')
        recall_macro = recall_score(all_true_labels, all_pred_labels, average='macro')
        f1_macro = f1_score(all_true_labels, all_pred_labels, average='macro')

        precision_weighted = precision_score(all_true_labels, all_pred_labels, average='weighted')
        recall_weighted = recall_score(all_true_labels, all_pred_labels, average='weighted')
        f1_weighted = f1_score(all_true_labels, all_pred_labels, average='weighted')

        print(f"Macro Average Precision: {precision_macro:.3f}")
        print(f"Macro Average Recall: {recall_macro:.3f}")
        print(f"Macro Average F1-Score: {f1_macro:.3f}")

        # Print a full classification report
        print("\nClassification Report:")
        print(classification_report(all_true_labels, all_pred_labels, target_names=class_names))

        # Log to wandb if requested
        if log_to_wandb:
            wandb.log({
                "eval/test_loss": test_loss,
                "eval/test_accuracy": test_acc,
                "eval/precision": precision_macro,
                "eval/recall": recall_macro,
                "eval/f1": f1_macro,
                # "eval/confusion_matrix": wandb.plot.confusion_matrix(
                #     probs=None,
                #     y_true=all_true_labels,
                #     preds=all_pred_labels,
                #     class_names=class_names
                # )
            })