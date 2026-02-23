# 商品分類アプリ (GPT + 学習)

入力した商品名を GPT で分類するシンプルな Web アプリです。  
分類できなかった場合はユーザーが分類を教えることで、ローカル JSON に学習されます。

## 起動

```bash
export OPENAI_API_KEY="your_api_key"
# 任意: 既定は gpt-4o-mini
export OPENAI_MODEL="gpt-4o-mini"
# 任意: OpenAI互換APIを使う場合に指定（既定: https://api.openai.com/v1）
export OPENAI_BASE_URL="https://api.openai.com/v1"
python app.py
```

ブラウザで `http://localhost:5000` を開きます。

## 仕様

- まずローカル学習データ (`data/learned_categories.json`) を参照
- 見つからない場合に GPT API へ問い合わせ
- まず `responses` API を利用し、未対応環境（404等）の場合は `chat/completions` へフォールバック
- GPT が `不明` を返した場合、学習入力を促す
- 学習データは商品名を小文字化して保存

## API

- `POST /classify` `{ "product": "ねぎ" }`
- `POST /learn` `{ "product": "ねぎ", "category": "野菜" }`
