import numpy as np
import torch
from tqdm import tqdm
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score


# train
def train_one_epoch(model, loader, optimizer, device):
    model.train()
    total_loss = 0.0

    for batch in tqdm(loader, desc="Train", leave=True):
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)

        optimizer.zero_grad()

        outputs = model(input_ids, attention_mask=attention_mask, labels=labels)
        loss = outputs.loss
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    return total_loss / max(1, len(loader)) # 0으로 나누는 거 방지

# eval
@torch.no_grad() # 데코레이터
def eval_model(model, loader, device):
    model.eval()
    losses = []
    y_true, y_pred = [], []

    for batch in tqdm(loader, desc="Eval", leave=True):
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)

        outputs = model(input_ids, attention_mask=attention_mask, labels=labels)
        logits = outputs.logits
        loss = outputs.loss

        preds = torch.argmax(logits, dim=-1) # (batch_size, num_classes) -> (batch_size,)

        losses.append(loss.item())
        y_true.extend(labels.detach().cpu().numpy().tolist()) # numpy는 cpu에서만
        y_pred.extend(preds.detach().cpu().numpy().tolist())

    avg_loss = float(np.mean(losses))
    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average="macro") # 다중클래스일때는 average='macro'

    # "확정" 클래스
    # precision: TP/(TP+FP) recall: TP/(TP+FN)
    # recall 기준으로 베스트 모델을 저장하다보면 모델이 과도하게 "확정"으로 분류해서 recall을 좋게 만들 수도 있음. 때문에 precision이 낮아질 수 있으므로 확인 필요.
    class2_precision = precision_score(
        y_true, y_pred,
        labels=[2],
        average=None,
        zero_division=0
    )[0]

    class2_recall = recall_score(
        y_true, y_pred,
        labels=[2],
        average=None,
        zero_division=0
    )[0]
    return {"loss": avg_loss, "acc": acc, "f1": f1, "class2_precision": float(class2_precision), "class2_recall": float(class2_recall)}

