# 商品分類アプリ (GPT + 学習)

入力した商品名を GPT で分類するシンプルな Web アプリです。  
分類できなかった場合はユーザーが分類を教えることで、ローカル JSON に学習されます。

## 起動

```bash
export OPENAI_API_KEY="your_api_key"
python app.py
```

ブラウザで `http://localhost:5000` を開きます。

## 仕様

- まずローカル学習データ (`data/learned_categories.json`) を参照
- 見つからない場合に GPT (`/v1/responses`) へ問い合わせ
- GPT が `不明` を返した場合、学習入力を促す
- 学習データは商品名を小文字化して保存

## API

- `POST /classify` `{ "product": "ねぎ" }`
- `POST /learn` `{ "product": "ねぎ", "category": "野菜" }`
