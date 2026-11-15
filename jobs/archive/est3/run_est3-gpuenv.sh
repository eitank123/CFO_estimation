#!/bin/bash
# GPU probe + CUDA PyTorch env (new folder env/torch-cuda; polar-sionna is not touched)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
ENV=/gpfs0/bgu-haimp/users/karpei/env/torch-cuda
{
echo "=== node $(hostname)"; nvidia-smi; nvidia-smi -L
echo "=== internet"; curl -sI https://download.pytorch.org/whl/ | head -1
echo "=== versions in polar-sionna"; $PY -m pip freeze | grep -iE "^(numpy|scipy|matplotlib)==" | tee /tmp/req.txt
echo "=== venv"; $PY -m venv $ENV && $ENV/bin/pip install -q --upgrade pip && $ENV/bin/pip install -q -r /tmp/req.txt
for cu in cu126 cu124 cu121; do
  echo "=== torch $cu"; $ENV/bin/pip install -q --force-reinstall torch --index-url https://download.pytorch.org/whl/$cu || continue
  $ENV/bin/python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available()); print(torch.cuda.get_device_name(0)); x=torch.randn(4096,4096,device='cuda'); print('matmul ok', float((x@x).sum()))" && break
done
echo "=== check est3 imports"; $ENV/bin/python -c "import sys; sys.path.insert(0,'.'); import est3.nn, est3.common; print('est3 ok')"
echo "=== done"
} > logs/run_est3-gpuenv.out 2>&1
