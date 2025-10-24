import torch
import io
import base64


# --- PyTorch 模型参数序列化工具 ---

def serialize_model_params(state_dict: dict) -> str:
    """
    将 PyTorch 模型的 state_dict (张量字典) 序列化为 base64 编码的字符串。

    用于通过 JSON 或 HTTP POST 请求体传输模型参数。
    :param state_dict: PyTorch 模型的 state_dict (张量字典)。
    :return: base64 编码的字符串。
    """
    buffer = io.BytesIO()
    # 使用 torch.save 将 state_dict 写入内存缓冲区
    torch.save(state_dict, buffer)
    # 获取字节内容并进行 base64 编码，方便 JSON 传输
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def deserialize_model_params(serialized_data: str) -> dict:
    """
    将 base64 编码的字符串反序列化为 PyTorch 模型的 state_dict (张量字典)。

    :param serialized_data: base64 编码的字符串。
    :return: PyTorch 模型的 state_dict (张量字典)。
    """
    # 解码 base64 字符串
    buffer = io.BytesIO(base64.b64decode(serialized_data))
    # 使用 torch.load 从内存缓冲区加载 state_dict
    # map_location='cpu' 确保加载时不依赖 GPU
    state_dict = torch.load(buffer, map_location='cpu')
    return state_dict
