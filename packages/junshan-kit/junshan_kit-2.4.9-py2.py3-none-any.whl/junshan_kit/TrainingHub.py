import torch.nn as nn

from junshan_kit import DataHub



def chosen_loss_fn(model_name, Paras):
    # ---------------------------------------
    # There have an addition parameter
    if model_name == "LogRegressionBinaryL2":
        Paras["lambda"] = 1e-3
    # ---------------------------------------

    if model_name in ["LeastSquares"]:
        loss_fn = nn.MSELoss()

    else:
        if Paras["model_type"][model_name] == "binary":
            loss_fn = nn.BCEWithLogitsLoss()

        elif Paras["model_type"][model_name] == "multi":
            loss_fn = nn.CrossEntropyLoss()

        else:
            loss_fn = nn.MSELoss()
            print("\033[91m The loss function is error!\033[0m")
            assert False
            
    Paras["loss_fn"] = loss_fn

    return loss_fn, Paras


def load_data(model_name, data_name, Paras):
    # load data
    train_path = f"./exp_data/{data_name}/training_data"
    test_path = f"./exp_data/{data_name}/test_data"

    if data_name == "MNIST":
        train_dataset, test_dataset, transform = DataHub.MNIST(Paras, model_name)

    elif data_name == "CIFAR100":
        train_dataset, test_dataset, transform = DataHub.CIFAR100(Paras, model_name)

    elif data_name == "Adult_Income_Prediction":
        train_dataset, test_dataset, transform = DataHub.Adult_Income_Prediction(Paras)

    elif data_name == "Credit_Card_Fraud_Detection":
        train_dataset, test_dataset, transform = DataHub.Credit_Card_Fraud_Detection(Paras)
    

    # elif data_name == "CALTECH101_Resize_32":
    #     Paras["train_ratio"] = 0.7
    #     train_dataset, test_dataset, transform = datahub.caltech101_Resize_32(
    #         Paras["seed"], Paras["train_ratio"], split=True
    #     )

    # elif data_name in ["Vowel", "Letter", "Shuttle", "w8a"]:
    #     Paras["train_ratio"] = Paras["split_train_data"][data_name]
    #     train_dataset, test_dataset, transform = datahub.get_libsvm_data(
    #         train_path + ".txt", test_path + ".txt", data_name
    #     )

    # elif data_name in ["RCV1", "Duke", "Ijcnn"]:
    #     Paras["train_ratio"] = Paras["split_train_data"][data_name]
    #     train_dataset, test_dataset, transform = datahub.get_libsvm_bz2_data(
    #         train_path + ".bz2", test_path + ".bz2", data_name, Paras
    #     )

    else:
        transform = None
        print(f"The data_name is error!")
        assert False

    return train_dataset, test_dataset, transform