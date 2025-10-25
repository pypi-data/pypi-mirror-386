import torch
MODEL = 'ResNet'
DATASET = 'mnist'
PARTITION_TYPE = 'non_iid'
PARTITION_ALPHA = 0.5
LEARNING_RATE = 0.01  # 学习率
BATCH_SIZE = 10 # 批大小
LOCAL_EPOCHS = 3 # 本地迭代次数
ROUNDS_PER_TASK = 20 #全局迭代次数
TOTAL_TASKS = 10 # 总体任务数量
CLASSES_PER_TASK = 10 #每个任务包含的数量
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CLIENTS_NUMBER = 10 # 每个服务器包含的客户端数量
SERVER_IPV4 = "202.199.6.17"
SERVER_IPV6 = "http://[2001:da8:9000:a806:18ab:f005:a2ff:9641]"
SERVER_PORT = "5050"
CLIENT_PORT = "5051"
