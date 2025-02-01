# NGMD-client: Nvidia GPU Monitoring Dashboard API Clients

## 概要
NGMD-client は、Nvidia GPU のモニタリングデータを収集し、API サーバーに送信するためのクライアントツールです。

## 構成ファイル

- `agent.ps1`：Windows 用クライアント
- `agent.py`：Linux 用クライアント
- `Dockerfile`：Docker 仮環境構築用
- `req.sh`：API の疎通確認用（Curl）
- `run_all.sh`：30 秒ごとにデータを定期送信

## 使い方

### Windows での実行
PowerShell を使用して `agent.ps1` を実行します。
```powershell
./agent.ps1
```

### Linux での実行
Python を使用して `agent.py` を実行します。
```bash
python3 agent.py
```

### Docker 環境の構築と実行
Docker を利用する場合、以下のコマンドを実行してください。
```bash
docker build -t ngmd-client .
docker run -d --name ngmd-client ngmd-client
```

### API 疎通確認
`req.sh` を実行して、API サーバーとの通信を確認できます。
```bash
./req.sh
```

### 30 秒ごとの定期送信
`run_all.sh` を実行すると、30 秒ごとにデータを送信します。
```bash
./run_all.sh
```

## 実行時の注意点
実行する前に、以下の API 設定を自分の環境に合わせて変更してください。

```bash
API_HOST = "127.0.0.1"  # 使用する IP アドレスを設定してください
API_PORT = 8000         # 使用するポート番号を設定してください
API_PATH = "/monitor"   # API エンドポイントを設定してください
```

設定を反映させることで、適切にデータが送信されるようになります。



