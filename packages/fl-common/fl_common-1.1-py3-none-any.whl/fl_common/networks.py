import torch
import torch.nn as nn
import torch.nn.functional as F


class ResNet(nn.Module):
    """
    统一的 ResNet 类，包含 BasicBlock 作为其结构的一部分。
    通过传入不同的配置参数 (num_blocks) 实现可扩展性。
    """

    # --- 内部 BasicBlock 定义 ---
    class BasicBlock(nn.Module):
        expansion = 1  # 定义扩展因子

        def __init__(self, in_channels, out_channels, stride=1):
            super(ResNet.BasicBlock, self).__init__()

            # 3x3 卷积，处理下采样
            self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3,
                                   stride=stride, padding=1, bias=False)
            self.bn1 = nn.BatchNorm2d(out_channels)

            # 3x3 卷积
            self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3,
                                   stride=1, padding=1, bias=False)
            self.bn2 = nn.BatchNorm2d(out_channels)

            # 恒等映射（Shortcut）
            self.shortcut = nn.Sequential()
            # 维度不匹配时，使用 1x1 卷积进行匹配
            if stride != 1 or in_channels != out_channels * self.expansion:
                self.shortcut = nn.Sequential(
                    nn.Conv2d(in_channels, out_channels * self.expansion,
                              kernel_size=1, stride=stride, bias=False),
                    nn.BatchNorm2d(out_channels * self.expansion)
                )

        def forward(self, x):
            identity = x
            out = F.relu(self.bn1(self.conv1(x)))
            out = self.bn2(self.conv2(out))
            out += self.shortcut(identity)
            out = F.relu(out)
            return out

    # --- ResNet 主体结构 (ResNetBackbone 的逻辑) ---
    def __init__(self, block, num_blocks, num_channels=3, num_classes=10):
        super(ResNet, self).__init__()
        self.in_planes = 64
        self.num_classes = num_classes

        # 1. 初始输入层
        self.conv1 = nn.Conv2d(num_channels, 64, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(64)

        # 2. 堆叠残差层 (Stages)
        # 可扩展性：block 可以是 BasicBlock 或 Bottleneck，num_blocks 决定深度
        self.layer1 = self._make_layer(block, 64, num_blocks[0], stride=1)
        self.layer2 = self._make_layer(block, 128, num_blocks[1], stride=2)
        self.layer3 = self._make_layer(block, 256, num_blocks[2], stride=2)
        self.layer4 = self._make_layer(block, 512, num_blocks[3], stride=2)

        # 3. 全局平均池化层
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))

        # 4. 最终的分类层
        self.fc = nn.Linear(512 * block.expansion, num_classes)

    def _make_layer(self, block, planes, num_blocks, stride):
        """用于创建 ResNet 的一个 Stage（层），处理下采样和通道数变化。"""
        strides = [stride] + [1] * (num_blocks - 1)
        layers = []
        for stride in strides:
            layers.append(block(self.in_planes, planes, stride))
            self.in_planes = planes * block.expansion
        return nn.Sequential(*layers)

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.layer1(out)
        out = self.layer2(out)
        out = self.layer3(out)
        out = self.layer4(out)
        out = self.avgpool(out)
        out = torch.flatten(out, 1)
        out = self.fc(out)
        return out


