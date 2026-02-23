from flask import Flask, jsonify, request

from classifier import ProductClassifier

app = Flask(__name__)
classifier = ProductClassifier()

INDEX_HTML = """<!doctype html>
<html lang=\"ja\">
  <head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <title>商品分類アプリ</title>
    <style>
      body { font-family: sans-serif; max-width: 640px; margin: 2rem auto; padding: 0 1rem; }
      input, button { font-size: 1rem; padding: .6rem; }
      input { width: 100%; box-sizing: border-box; margin-bottom: .8rem; }
      .row { display: flex; gap: .5rem; }
      .row button { flex: 1; }
      .result { margin-top: 1rem; padding: .8rem; border: 1px solid #ddd; border-radius: 8px; }
      .hidden { display: none; }
    </style>
  </head>
  <body>
    <h1>商品分類アプリ</h1>
    <p>商品名を入力すると GPT が分類します。分類できない場合は教えて学習させられます。</p>

    <label for=\"product\">商品名</label>
    <input id=\"product\" placeholder=\"例: ねぎ\" />
    <div class=\"row\">
      <button id=\"classifyBtn\">分類する</button>
    </div>

    <div id=\"result\" class=\"result hidden\"></div>

    <div id=\"learnBox\" class=\"hidden\">
      <h3>分類を教える</h3>
      <input id=\"category\" placeholder=\"例: 野菜\" />
      <button id=\"learnBtn\">学習する</button>
    </div>

    <script>
      const productEl = document.getElementById('product');
      const categoryEl = document.getElementById('category');
      const resultEl = document.getElementById('result');
      const learnBox = document.getElementById('learnBox');

      document.getElementById('classifyBtn').addEventListener('click', async () => {
        const product = productEl.value.trim();
        if (!product) return;

        const res = await fetch('/classify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ product })
        });
        const data = await res.json();

        resultEl.classList.remove('hidden');
        if (data.error) {
          resultEl.textContent = data.error;
          learnBox.classList.add('hidden');
          return;
        }

        resultEl.textContent = `結果: ${data.product} → ${data.category} (source: ${data.source})`;
        if (data.needs_learning) {
          learnBox.classList.remove('hidden');
          categoryEl.value = '';
          categoryEl.focus();
        } else {
          learnBox.classList.add('hidden');
        }
      });

      document.getElementById('learnBtn').addEventListener('click', async () => {
        const product = productEl.value.trim();
        const category = categoryEl.value.trim();
        if (!product || !category) return;

        const res = await fetch('/learn', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ product, category })
        });
        const data = await res.json();
        resultEl.classList.remove('hidden');
        resultEl.textContent = data.message || data.error;
      });
    </script>
  </body>
</html>
"""


@app.get('/')
def index():
    return INDEX_HTML


@app.post('/classify')
def classify():
    data = request.get_json(silent=True) or {}
    product = (data.get('product') or '').strip()
    if not product:
        return jsonify({'error': '商品名を入力してください。'}), 400
    return jsonify(classifier.classify(product))


@app.post('/learn')
def learn():
    data = request.get_json(silent=True) or {}
    product = (data.get('product') or '').strip()
    category = (data.get('category') or '').strip()
    if not product or not category:
        return jsonify({'error': '商品名と分類の両方を入力してください。'}), 400

    classifier.learn(product, category)
    return jsonify({'message': f'「{product} → {category}」を学習しました。'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
