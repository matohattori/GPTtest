import json
import os
from pathlib import Path
from urllib import error, request


class ProductClassifier:
    def __init__(self, learning_file: str | None = None):
        # Vercel の /var/task は read-only なので、既定は /tmp に保存する
        default_path = '/tmp/learned_categories.json' if os.getenv('VERCEL') else 'data/learned_categories.json'
        self.learning_path = Path(learning_file or default_path)
        self.persistence_available = self._prepare_storage()
        self.knowledge = self._load_knowledge()
        self.base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1').rstrip('/')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

    def _prepare_storage(self) -> bool:
        try:
            self.learning_path.parent.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False

    def _load_knowledge(self) -> dict[str, str]:
        if not self.persistence_available:
            return {}
        try:
            if not self.learning_path.exists():
                return {}
            with self.learning_path.open('r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_knowledge(self) -> bool:
        if not self.persistence_available:
            return False
        try:
            with self.learning_path.open('w', encoding='utf-8') as f:
                json.dump(self.knowledge, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def _prompt(self, product: str) -> str:
        return (
            'あなたは商品の分類アシスタントです。\n'
            '商品名を1つの分類名に短く分類してください。\n'
            '例: ねぎ→野菜, 豆腐→加工品\n'
            '分類不能な場合は「不明」とだけ返してください。\n'
            f'商品名: {product}'
        )

    def _post_json(self, endpoint: str, payload: dict, api_key: str) -> dict:
        req = request.Request(
            f'{self.base_url}{endpoint}',
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            method='POST',
        )
        with request.urlopen(req, timeout=20) as res:
            return json.loads(res.read().decode('utf-8'))

    def _extract_from_responses(self, body: dict) -> str:
        text = (body.get('output_text') or '').strip()
        if text:
            return text
        output = body.get('output') or []
        for item in output:
            for content in item.get('content', []):
                if content.get('type') == 'output_text' and content.get('text'):
                    return content['text'].strip()
        return ''

    def _extract_from_chat_completions(self, body: dict) -> str:
        choices = body.get('choices') or []
        if not choices:
            return ''
        message = choices[0].get('message') or {}
        return (message.get('content') or '').strip()

    def _classify_with_gpt(self, product: str) -> str:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return '不明'

        prompt = self._prompt(product)

        try:
            body = self._post_json(
                '/responses',
                {
                    'model': self.model,
                    'input': prompt,
                    'temperature': 0,
                },
                api_key,
            )
            category = self._extract_from_responses(body)
            return category or '不明'
        except error.HTTPError as e:
            if e.code not in (400, 404, 405):
                return '不明'
        except Exception:
            return '不明'

        try:
            body = self._post_json(
                '/chat/completions',
                {
                    'model': self.model,
                    'messages': [
                        {'role': 'system', 'content': 'あなたは商品の分類アシスタントです。'},
                        {'role': 'user', 'content': prompt},
                    ],
                    'temperature': 0,
                },
                api_key,
            )
            category = self._extract_from_chat_completions(body)
            return category or '不明'
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

    def learn(self, product: str, category: str) -> bool:
        self.knowledge[product.strip().lower()] = category.strip()
        return self._save_knowledge()
