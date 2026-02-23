import json
import os
from pathlib import Path
from urllib import request


class ProductClassifier:
    def __init__(self, learning_file: str = 'data/learned_categories.json'):
        self.learning_path = Path(learning_file)
        self.learning_path.parent.mkdir(parents=True, exist_ok=True)
        self.knowledge = self._load_knowledge()

    def _load_knowledge(self) -> dict[str, str]:
        if not self.learning_path.exists():
            return {}
        with self.learning_path.open('r', encoding='utf-8') as f:
            return json.load(f)

    def _save_knowledge(self) -> None:
        with self.learning_path.open('w', encoding='utf-8') as f:
            json.dump(self.knowledge, f, ensure_ascii=False, indent=2)

    def _classify_with_gpt(self, product: str) -> str:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return '不明'

        prompt = (
            'あなたは商品の分類アシスタントです。\n'
            '商品名を1つの分類名に短く分類してください。\n'
            '例: ねぎ→野菜, 豆腐→加工品\n'
            '分類不能な場合は「不明」とだけ返してください。\n'
            f'商品名: {product}'
        )

        payload = {
            'model': 'gpt-4.1-mini',
            'input': prompt,
            'temperature': 0,
        }

        req = request.Request(
            'https://api.openai.com/v1/responses',
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )

        try:
            with request.urlopen(req, timeout=15) as res:
                body = json.loads(res.read().decode('utf-8'))
            return (body.get('output_text') or '').strip() or '不明'
        except Exception:
            return '不明'

    def classify(self, product: str) -> dict:
        normalized = product.strip().lower()

        if normalized in self.knowledge:
            return {
                'product': product,
                'category': self.knowledge[normalized],
                'source': 'learned',
                'needs_learning': False,
            }

        category = self._classify_with_gpt(product)
        return {
            'product': product,
            'category': category,
            'source': 'gpt',
            'needs_learning': category == '不明',
        }

    def learn(self, product: str, category: str) -> None:
        self.knowledge[product.strip().lower()] = category.strip()
        self._save_knowledge()
