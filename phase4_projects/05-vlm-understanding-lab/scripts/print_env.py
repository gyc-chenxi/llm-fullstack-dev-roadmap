import platform
import torch
import transformers

print("python:", platform.python_version())
print("platform:", platform.platform())
print("torch:", torch.__version__)
print("transformers:", transformers.__version__)
print("mps available:", torch.backends.mps.is_available())
print("mps built:", torch.backends.mps.is_built())