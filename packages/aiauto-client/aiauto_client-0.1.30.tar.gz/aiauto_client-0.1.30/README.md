# AIAuto - Hyperparameter Optimization Client Library

AIAuto는 Kubernetes 기반의 분산 HPO(Hyperparameter Optimization) 시스템을 위한 클라이언트 라이브러리입니다.
사용자 python lib <-> Next.js 서버 사이 Connect RPC (HTTP/1.1) 통신 담당

## 설치
- `pip install aiauto-client optuna`

## API 레퍼런스

### create_study 파라미터
- `study_name` (str): Study 이름
- `direction` (str): 단일 목적 최적화 방향 ("minimize" 또는 "maximize")
- `directions` (List[str]): 다중 목적 최적화 방향 리스트 (direction과 상호 배타적)
- `sampler` (object/dict): Optuna sampler 객체 또는 dict (선택적)
- `pruner` (object/dict): Optuna pruner 객체 또는 dict (선택적)

**주의**: `direction`과 `directions`는 둘 중 하나만 지정해야 합니다.

### optimize 파라미터
- `objective` (Callable): Trial을 인자로 받는 목적 함수
- `n_trials` (int): 총 trial 수
- `parallelism` (int): 동시 실행 Pod 수 (기본값: 2)
- `requirements_file` (str): requirements.txt 파일 경로 (requirements_list와 상호 배타적)
- `requirements_list` (List[str]): 패키지 리스트 (requirements_file과 상호 배타적)
- `resources_requests` (Dict[str, str]): 리소스 요청 (기본값: {"cpu": "256m", "memory": "256Mi"})
- `resources_limits` (Dict[str, str]): 리소스 제한 (기본값: {"cpu": "256m", "memory": "256Mi"})
- `runtime_image` (str): 커스텀 런타임 이미지 (None이면 자동 선택)
- `use_gpu` (bool): GPU 사용 여부 (기본값: False)

**주의**: `requirements_file`과 `requirements_list`는 둘 중 하나만 지정해야 합니다.

## 지원 런타임 이미지 확인
```python
import aiauto

# 사용 가능한 이미지 확인
for image in aiauto.RUNTIME_IMAGES:
    print(image)
```

## 실행 흐름
### token 발급
- `https://dashboard.common.aiauto.pangyo.ainode.ai` 에 접속하여 ainode 에 로그인 한 후
- `https://dashboard.common.aiauto.pangyo.ainode.ai/token` 으로 이동하여 aiauto 의 token 을 발급
- 아래 코드 처럼 발급한 token 을 넣어 AIAutoController singleton 객체를 초기화, OptunaWorkspace 를 활성화 시킨다
```python
import aiauto
import time

ac = aiauto.AIAutoController('<token>')
```
- `https://dashboard.common.aiauto.pangyo.ainode.ai/workspace` 에서 생성된 OptunaWorkspace 와 optuna-dashboard 링크를 확인할 수 있음
- 아래 코드 처럼 study 를 생성하면 `https://dashboard.common.aiauto.pangyo.ainode.ai/study` 에서 확인할 수 있고 optuna-dashboard 링크에서도 확인 가능 
```python
study_wrapper = ac.create_study(
    study_name='test',
    direction='maximize',  # or 'minimize'
)
time.sleep(5)
```
- 아래 코드 처럼 생성한 study 애서 objective 함수를 작성하여 넘겨주면 optimize 를 호출하면 `https://dashboard.common.aiauto.pangyo.ainode.ai/trialbatch` 에서 확인할 수 있고 optuna-dashboard 링크에서도 확인 가능
```python
study_wrapper.optimize(
    objective=func_with_parameter_trial,
    n_trials=4,
    parallelism=2,
    use_gpu=False,
    runtime_image=aiauto.RUNTIME_IMAGES[0],
)
time.sleep(5)
```
- 종료 됐는지 optuna-dashboard 가 아닌 코드로 확인하는 법
```python
study_wrapper.get_status()
# {'study_name': 'test', 'count_active': 0, 'count_succeeded': 10, 'count_pruned': 0, 'count_failed': 0, 'count_total': 10, 'count_completed': 10, 'dashboard_url': 'https://optuna-dashboard-10f804bb-52be-48e8-aa06-9f5411ed4b0d.aiauto.pangyo.ainode.ai', 'last_error': '', 'updated_at': '2025-09-01T11:31:49.375Z'}
while study_wrapper.get_status()['count_completed'] < study_wrapper.get_status()['count_total']:
    time.sleep(10)  # 10초마다 확인
```
- best trial 을 가져오는 법
```python
# 진짜 optuna study 를 받아옴
real_study = study_wrapper.get_study()
best_trial = real_study.best_trial
print(best_trial.params)
```

## Jupyter Notebook 사용 시 주의사항

Jupyter Notebook이나 Python REPL에서 정의한 함수는 Serialize 할 수 없습니다
대신 `%%writefile` magic 울 사용하여 파일로 저장한 후 import 하세요.

### Jupyter에서 objective 함수 작성 방법
- objective 함수를 파일로 저장
```python
%%writefile my_objective.py
import aiauto
import optuna

def objective(trial):
    """
    이 함수는 외부 서버에서 실행됩니다.
    모든 import는 함수 내부에 작성하세요.
    """
    import torch  # 함수 내부에서 import
    
    x = trial.suggest_float('x', -10, 10)
    y = trial.suggest_float('y', -10, 10)
    return (x - 2) ** 2 + (y - 3) ** 2
```
- 저장한 함수를 import해서 사용
```python
import aiauto
import time
from my_objective import objective

ac = aiauto.AIAutoController('<token>')
study = ac.create_study('test', 'minimize')
time.sleep(5)
study.optimize(objective, n_trials=10, parallelism=2)
time.sleep(5)
```

## 빠른 시작

### 1. 간단한 예제 (수학 함수 최적화)

```python
import optuna
import aiauto
import time


# `https://dashboard.common.aiauto.pangyo.ainode.ai` 에 접속하여 ainode 에 로그인 한 후 aiauto 의 token 을 발급
# AIAutoController singleton 객체를 초기화 하여, OptunaWorkspace 를 활성화 시킨다 (토큰은 한 번만 설정)
ac = aiauto.AIAutoController('<token>')
# `https://dashboard.common.aiauto.pangyo.ainode.ai/workspace` 에서 생성된 OptunaWorkspace 와 optuna-dashboard 링크를 확인할 수 있음

# StudyWrapper 생성
study_wrapper = ac.create_study(
    study_name="simple_optimization",
    direction="minimize"
    # sampler=optuna.samplers.TPESampler(),  # optuna 에서 제공하는 sampler 그대로 사용 가능, 참고 https://optuna.readthedocs.io/en/stable/reference/samplers/index.html
)
time.sleep(5)
# `https://dashboard.common.aiauto.pangyo.ainode.ai/study` 에서 생성된 study 확인 가능

# objective 함수 정의
def objective(trial):
    """실제 실행은 사용자 로컬 컴퓨터가 아닌 서버에서 실행 될 함수"""
    x = trial.suggest_float('x', -10, 10)
    y = trial.suggest_float('y', -10, 10)
    return (x - 2) ** 2 + (y - 3) ** 2

# 사용자 모델 학습 or 최적화 실행 (서버에서 병렬 실행)
study_wrapper.optimize(
    objective,
    n_trials=100,
    parallelism=4  # 동시 실행 Pod 수
)
time.sleep(5)
# `https://dashboard.common.aiauto.pangyo.ainode.ai/workspace` 에서 생성된 optuna-dashboard 링크에서 결과 확인 가능
```

### 2. PyTorch 모델 최적화 (Single Objective)

```python
import optuna
import aiauto
import time


# `https://dashboard.common.aiauto.pangyo.ainode.ai` 에 접속하여 ainode 에 로그인 한 후 aiauto 의 token 을 발급
# AIAutoController singleton 객체를 초기화 하여, OptunaWorkspace 를 활성화 시킨다 (토큰은 한 번만 설정)
ac = aiauto.AIAutoController('<token>')
# `https://dashboard.common.aiauto.pangyo.ainode.ai/workspace` 에서 생성된 OptunaWorkspace 와 optuna-dashboard 링크를 확인할 수 있음

# StudyWrapper 생성
study_wrapper = ac.create_study(
    study_name="pytorch_optimization",
    direction="minimize",
    # sampler=optuna.samplers.TPESampler(),  # optuna 에서 제공하는 sampler 그대로 사용 가능, 참고 https://optuna.readthedocs.io/en/stable/reference/samplers/index.html
    pruner=optuna.pruners.PatientPruner(  # optuna 에서 제공하는 pruner 그대로 사용 가능, 참고 https://optuna.readthedocs.io/en/stable/reference/pruners.html
        optuna.pruners.MedianPruner(),
        patience=4,
    ),
)
time.sleep(5)
# `https://dashboard.common.aiauto.pangyo.ainode.ai/study` 에서 생성된 study 확인 가능

# objective 함수 정의
# https://docs.pytorch.org/tutorials/beginner/blitz/cifar10_tutorial.html 참고
def objective(trial):
    """
    실제 실행은 사용자 로컬 컴퓨터가 아닌 서버에서 실행 될 함수
    모든 import는 함수 내부에 존재해야 함
    """
    import torch
    from torch import nn, optim
    from torch.utils.data import DataLoader, random_split, Subset
    from torchvision import transforms, datasets
    import torch.nn.functional as F
    
    import optuna

    # 하이퍼파라미터 샘플링
    lr = trial.suggest_float('learning_rate', 1e-5, 1e-1, log=True)
    momentom = trial.suggest_float('momentom', 0.1, 0.99)
    batch_size = trial.suggest_categorical('batch_size', [16, 32, 64, 128])
    epochs = trial.suggest_int('epochs', 10, 100, step=10)
    
    # 모델 정의
    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1 = nn.Conv2d(3, 6, 5)
            self.pool = nn.MaxPool2d(2, 2)
            self.conv2 = nn.Conv2d(6, 16, 5)
            self.fc1 = nn.Linear(16 * 5 * 5, 120)
            self.fc2 = nn.Linear(120, 84)
            self.fc3 = nn.Linear(84, 10)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = torch.flatten(x, 1) # flatten all dimensions except batch
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x 
    
    # 모델 정의 및 학습 (GPU 자동 사용)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = Net().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=lr, momentum=momentom)
    
    # 데이터 로드
    train_set = datasets.CIFAR10(
        root="/tmp/cifar10_data",  # Pod의 임시 디렉토리 사용
        train=True,
        download=True,
        transform=[
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ],
    )
    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True, num_workers=2)

    test_set = datasets.CIFAR10(
        root="/tmp/cifar10_data",  # Pod의 임시 디렉토리 사용
        train=False,
        download=True,
        transform=[
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ],
    )
    test_loader = DataLoader(test_set, batch_size=batch_size, shuffle=True, num_workers=2)
    
    # 학습
    min_epochs_for_pruning = max(50, epochs // 5)  # 최소 50 epoch 또는 전체의 1/5 후부터 pruning
    total_loss = 0.0
    for epoch in range(epochs):  # loop over the dataset multiple times
        running_loss = 0.0
        model.train()
        for i, (inputs, targets) in enumerate(train_loader, 0):
            inputs, targets = inputs.to(device), targets.to(device)
            # zero the parameter gradients
            optimizer.zero_grad()
            # forward + backward + optimize
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
    
            # print statistics
            running_loss += loss.item()
            if i % 2000 == 1999:    # print every 2000 mini-batches
                print(f'[{epoch + 1}, {i + 1:5d}] loss: {running_loss / 2000:.3f}')
        
        # intermediate result 보고 및 초기 중단 검사 - 최소 epochs 후 부터만 pruning
        trial.report(running_loss, epoch)
        total_loss += running_loss
        if epoch >= min_epochs_for_pruning and trial.should_prune():
            raise optuna.TrialPruned()
        
    return total_loss

# GPU Pod에서 실행
study_wrapper.optimize(
    objective,
    n_trials=100,
    parallelism=4,
    use_gpu=True,  # GPU 사용
    runtime_image='pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime',  # default image for use_gpu True
    # requirements_list=['torch', 'torchvision']  # Pod에서 자동 설치  # pip list 명시는 다운로드 받는데 느림, runtime_image 를 torch 로 명시하는게 나음
    resources_requests={
        "cpu": "2",
        "memory": "4Gi",
    },
)
time.sleep(5)
```

### 3. Multi-Objective 최적화 (Accuracy + FLOPS)

```python
import optuna
import aiauto
import time


# `https://dashboard.common.aiauto.pangyo.ainode.ai` 에 접속하여 ainode 에 로그인 한 후 aiauto 의 token 을 발급
# AIAutoController singleton 객체를 초기화 하여, OptunaWorkspace 를 활성화 시킨다 (토큰은 한 번만 설정)
ac = aiauto.AIAutoController('<token>')
# `https://dashboard.common.aiauto.pangyo.ainode.ai/workspace` 에서 생성된 OptunaWorkspace 와 optuna-dashboard 링크를 확인할 수 있음

# StudyWrapper 생성
study_wrapper = ac.create_study(
    study_name="pytorch_multiple_optimization",
    direction=["minimize", "minimize"],  # loss minimize, FLOPS minimize
    # sampler=optuna.samplers.TPESampler(),  # optuna 에서 제공하는 sampler 그대로 사용 가능, 참고 https://optuna.readthedocs.io/en/stable/reference/samplers/index.html
)
time.sleep(5)
# `https://dashboard.common.aiauto.pangyo.ainode.ai/study` 에서 생성된 study 확인 가능

# objective 함수 정의
# https://docs.pytorch.org/tutorials/beginner/blitz/cifar10_tutorial.html 참고
def objective(trial):
    """
    실제 실행은 사용자 로컬 컴퓨터가 아닌 서버에서 실행 될 함수
    모든 import는 함수 내부에 존재해야 함
    """
    import torch
    from torch import nn, optim
    from torch.utils.data import DataLoader, random_split, Subset
    from torchvision import transforms, datasets
    import torch.nn.functional as F
    from fvcore.nn import FlopCountAnalysis

    # 하이퍼파라미터 샘플링
    lr = trial.suggest_float('learning_rate', 1e-5, 1e-1, log=True)
    momentom = trial.suggest_float('momentom', 0.1, 0.99)
    batch_size = trial.suggest_categorical('batch_size', [16, 32, 64, 128])
    epochs = trial.suggest_int('epochs', 10, 100, step=10)

    # 모델 정의
    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1 = nn.Conv2d(3, 6, 5)
            self.pool = nn.MaxPool2d(2, 2)
            self.conv2 = nn.Conv2d(6, 16, 5)
            self.fc1 = nn.Linear(16 * 5 * 5, 120)
            self.fc2 = nn.Linear(120, 84)
            self.fc3 = nn.Linear(84, 10)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = torch.flatten(x, 1) # flatten all dimensions except batch
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x

        # 모델 정의 및 학습 (GPU 자동 사용)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = Net().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=lr, momentum=momentom)

    # 데이터 로드
    train_set = datasets.CIFAR10(
        root="/tmp/cifar10_data",  # Pod의 임시 디렉토리 사용
        train=True,
        download=True,
        transform=[
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ],
    )
    train_loader = DataLoader(train_set, batch_size=batch_size, shuffle=True, num_workers=2)

    test_set = datasets.CIFAR10(
        root="/tmp/cifar10_data",  # Pod의 임시 디렉토리 사용
        train=False,
        download=True,
        transform=[
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ],
    )
    test_loader = DataLoader(test_set, batch_size=batch_size, shuffle=True, num_workers=2)

    # 학습
    total_loss = 0.0
    # multiple objective 는 pruning 미지원
    for epoch in range(epochs):  # loop over the dataset multiple times
        running_loss = 0.0
        model.train()
        for i, (inputs, targets) in enumerate(train_loader, 0):
            inputs, targets = inputs.to(device), targets.to(device)
            # zero the parameter gradients
            optimizer.zero_grad()
            # forward + backward + optimize
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            # print statistics
            running_loss += loss.item()
            if i % 2000 == 1999:    # print every 2000 mini-batches
                print(f'[{epoch + 1}, {i + 1:5d}] loss: {running_loss / 2000:.3f}')

        # multiple objective 는 pruning 미지원
    
    # FLOPS 계산
    dummy_input = torch.randn(1, 3, 32, 32).to(device)
    flops = FlopCountAnalysis(model, (dummy_input,)).total()
        
    return total_loss, flops

# GPU Pod에서 실행
study_wrapper.optimize(
    objective,
    n_trials=100,
    parallelism=4,
    use_gpu=True,  # GPU 사용
    runtime_image='pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime',  # default image for use_gpu True
    requirements_list=[  # pip list 명시는 다운로드 받는데 느림, runtime_image 를 torch 로 명시하는게 나음
        # 'torch', 
        # 'torchvision', 
        'fvcore',
    ],  # Pod에서 자동 설치
    resources_requests={
        "cpu": "2",
        "memory": "4Gi",
    },
)
time.sleep(5)
```

### 4. Ask/Tell 패턴 및 Optuna 자체의 Study

```python
import optuna
import aiauto
import time

# `https://dashboard.common.aiauto.pangyo.ainode.ai` 에 접속하여 ainode 에 로그인 한 후 aiauto 의 token 을 발급
# AIAutoController singleton 객체를 초기화 하여, OptunaWorkspace 를 활성화 시킨다 (토큰은 한 번만 설정)
ac = aiauto.AIAutoController('<token>')
# `https://dashboard.common.aiauto.pangyo.ainode.ai/workspace` 에서 생성된 OptunaWorkspace 와 optuna-dashboard 링크를 확인할 수 있음 

# Study 생성
study_wrapper = ac.create_study(
    study_name="test",
    direction='minimize',
    # sampler=optuna.samplers.TPESampler(),  # optuna 에서 제공하는 sampler 그대로 사용 가능, 참고 https://optuna.readthedocs.io/en/stable/reference/samplers/index.html
    # pruner=optuna.pruners.PatientPruner(  # optuna 에서 제공하는 pruner 그대로 사용 가능, 참고 https://optuna.readthedocs.io/en/stable/reference/pruners.html
    #     optuna.pruners.MedianPruner(),
    #     patience=4,
    # )
)
time.sleep(5)
# `https://dashboard.common.aiauto.pangyo.ainode.ai/study` 에서 생성된 study 확인 가능

# 실제 optuna.Study 객체 획득 (로컬에서 ask/tell 가능)
study = study_wrapper.get_study()

# Ask/Tell 패턴으로 최적화
trial = study.ask()

# 파라미터 최적화
x = trial.suggest_float('x', -10, 10)
y = trial.suggest_float('y', -10, 10)

# 사용자 모델 학습 or 최적화 실행 (서버에서 병렬 실행)
ret = (x - 2) ** 2 + (y - 3) ** 2

# 결과 보고
study.tell(trial, ret)
# `https://dashboard.common.aiauto.pangyo.ainode.ai/workspace` 에서 생성된 optuna-dashboard 링크에서 결과 확인 가능
```

# lib build
```bash
make build push
```


## LLM을 위한 설명 (for code assistants / agents)

이 섹션은 **코드 어시스턴트/에이전트**가 AIAuto를 자동으로 사용할 때 참고하는 규칙 모음입니다.  
사람 사용자는 위 본문 가이드를 우선적으로 따르세요.

### 1) 목적과 사용 흐름 (요약)
- AIAuto는 **Optuna를 Kubernetes에서 분산 실행**하도록 해주는 Python 클라이언트입니다.
- 두 가지 흐름을 지원합니다:
    1) `StudyWrapper.optimize(...)` → 원격(K8s) 병렬 실행
    2) `StudyWrapper.get_study()` → 실제 `optuna.Study` 로드 후 **ask/tell** 직접 사용

### 2) 네트워크/도메인 규칙 (필수)
- **Connect RPC (HTTPS/443)**: `https://api.common.aiauto.pangyo.ainode.ai`
- **Optuna Storage (gRPC, 평문 h2c/13000)**:  
  `{userID}.journal-grpc-storage-proxy.aiauto.pangyo.ainode.ai:13000`  
  → **항상 평문(h2c)**. 443/TLS 시도 **금지**.
- 대시보드(웹): `https://dashboard.common.aiauto.pangyo.ainode.ai`

### 3) 호출 순서 (결정 트리)
1) 컨트롤러 생성: `AIAutoController(token)` → 토큰 검증 & 워크스페이스/엔드포인트 획득
2) 스터디 생성: `controller.create_study(study_name, direction=… | directions=[…])`
    - 제약: `direction` **또는** `directions` 중 **하나만** 사용
3) 분기:
    - **분산 실행**: `study.optimize(objective, n_trials, parallelism, …)`
    - **네이티브 제어**: `real = study.get_study()` 후 `real.ask() / real.tell(...)`

### 4) 인자/작성 제약(LLM이 반드시 지킬 불변식)
- `direction` **XOR** `directions` (동시 지정 금지)
- `requirements_file` **XOR** `requirements_list` (동시 지정 금지)
- `objective` 작성 규칙:
    - 모든 **import는 함수 내부**에 작성
    - 함수 시그니처에 **타입 힌트 금지** (예: `trial: optuna.trial.Trial` 사용 금지)
    - 로컬 파일 경로 의존 금지(원격에서 다운로드/생성)

### 5) 최소 예제

#### (A) 분산 실행
```python
import aiauto, optuna, time

controller = aiauto.AIAutoController('aiauto_xxx')
study = controller.create_study('exp1', direction='minimize')
time.sleep(5)

def objective(trial):
    import numpy as np
    x = trial.suggest_float('x', -10, 10)
    return (x - 1.23) ** 2

study.optimize(
    objective,
    n_trials=64,
    parallelism=8,
    requirements_list=['numpy'],
)
time.sleep(5)
```

#### (B) ask/tell (실제 optuna.Study 사용)
```python
import aiauto, optuna, time

controller = aiauto.AIAutoController('aiauto_xxx')
sw = controller.create_study('manual', direction='minimize')
time.sleep(5)

real = sw.get_study()           # 실제 optuna.Study 로드 (gRPC: h2c 13000)
t = real.ask()
x = t.suggest_float('x', -10, 10)
real.tell(t, (x - 2) ** 2)
```

### 6) 에러 응답 템플릿(자동 응답 가이드)
- 초기화/토큰 문제 감지:
    - “대시보드에서 토큰을 재발급한 뒤 다시 시도하세요: https://dashboard.common.aiauto.pangyo.ainode.ai”
- `get_study()` 연결 실패(스토리지 준비 전):
    - “Workspace/Storage가 아직 준비 중일 수 있어요. 잠시 후 다시 시도하거나 대시보드에서 상태를 확인해 주세요.”

### 7) 금지/주의 목록
- gRPC를 **443/TLS**로 붙이려는 시도 **금지** (항상 **13000/h2c**).
- `direction & directions`, `requirements_file & requirements_list` 동시 지정 **금지**.
- `objective`는 함수 내부 import, 타입 힌트 금지, 로컬 파일 경로 의존 금지.

### 8) Optuna 호환성 (Sampler/Pruner & Study API)
- **Sampler/Pruner 호환**: `create_study()`에 **Optuna 원본** `sampler`/`pruner` 인스턴스를 그대로 전달하면 됩니다.  
  Study 생성 시 지정된 sampler/pruner는 **Optuna Journal Storage**에 저장되고, 원격 Pod에서 `optuna.load_study()`로 로드될 때 **자동으로 동일 설정이 적용**됩니다. 별도 복원 로직이 필요 없습니다.
- **네이티브 Study 사용**: `StudyWrapper.get_study()`는 **실제 `optuna.Study` 객체**를 반환합니다.  
  따라서 `best_trial`, `best_trials`(다중 목적), `trials_dataframe()`, `get_trials()`, `ask()/tell()` 등 **Optuna API를 그대로** 사용할 수 있습니다.

**공식 문서 링크**
- Samplers: https://optuna.readthedocs.io/en/stable/reference/samplers/index.html
- Pruners: https://optuna.readthedocs.io/en/stable/reference/pruners.html
- Study API: https://optuna.readthedocs.io/en/stable/reference/generated/optuna.study.Study.html

#### 예시: Sampler/Pruner 그대로 사용
```python
import optuna, aiauto, time

controller = aiauto.AIAutoController('aiauto_xxx')
study = controller.create_study(
    study_name='cnn',
    direction='minimize',
    sampler=optuna.samplers.TPESampler(seed=42),
    pruner=optuna.pruners.MedianPruner(n_startup_trials=5),
)
time.sleep(5)

def objective(trial):
    import numpy as np
    lr = trial.suggest_float('lr', 1e-5, 1e-1, log=True)
    return (np.log10(lr) + 2) ** 2

study.optimize(objective, n_trials=50, parallelism=4)
time.sleep(5)
```

#### 예시: get_study() 후 Optuna API 그대로 사용
```python
# 실제 optuna.Study 로드
real = study.get_study()

# 단일 목적: best_trial
print('best value:', real.best_trial.value)
print('best params:', real.best_trial.params)

# (옵션) 다중 목적: Pareto front
# print(real.best_trials)  # multi-objective일 때 사용

# 분석/시각화용 DataFrame
df = real.trials_dataframe(attrs=('number', 'value', 'params', 'state'))
print(df.head())

# 세밀 제어: ask/tell
t = real.ask()
x = t.suggest_float('x', -10, 10)
real.tell(t, (x - 1.23) ** 2)
```
