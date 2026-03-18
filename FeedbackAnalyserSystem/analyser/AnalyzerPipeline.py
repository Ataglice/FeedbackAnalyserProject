from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sentence_transformers import SentenceTransformer, util
from transformers import pipeline
import re
import json
import os

class SentimentAnalyzer:

    def __init__(self, ru_anchors_path = 'sentiment_anchors_ru.json', en_anchors_path = 'anchors.json'):
        base_dir = os.path.dirname(os.path.abspath(__file__))

        ru_path = os.path.join(base_dir, ru_anchors_path)
        en_path = os.path.join(base_dir, en_anchors_path)

        #и нициализация моделей и эмбедингов
        self.embedder_en = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedder_ru = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

        # инициализация Vader
        self.analyzer = SentimentIntensityAnalyzer()

        # инициализация пайплайнов классификации
        self.sentiment_pipe_ru = pipeline("sentiment-analysis", model="blanchefort/rubert-base-cased-sentiment")
        self.sentiment_pipe_en = pipeline("sentiment-analysis", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")

        # Загрузка и кодирование якорей
        self.ru_sentiment_anchors = self._load_and_encode_anchors(ru_path, self.embedder_ru)
        self.en_sentiment_anchors = self._load_and_encode_anchors(en_path, self.embedder_en)


    
    def _load_and_encode_anchors(self, file_path, embedder_model):
        encoded_anchors = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_anchors = json.load(f)
            for sentiment, sentences in raw_anchors.items():
                encoded_anchors[sentiment.upper()] = embedder_model.encode(sentences)
        except FileNotFoundError:
            print(f"Файл {file_path} не найден. Якоря не загружены.")
        return encoded_anchors




    @staticmethod
    def _is_russian(text):
        return bool(re.search('[а-яА-Я]', text))


    def _get_embedding_sentiment(self, active_model, active_anchor, text):
        """Метод 1: Оценка тональности через косинусное сходство векторов."""
        input_vec = active_model.encode(text)
        
        best_score = -1.0
        best_sentiment = "NEUTRAL"

        for sentiment, anchor_vec_list in active_anchor.items():
            scores = util.cos_sim(input_vec, anchor_vec_list)
            max_score = scores.max().item()
            
            if max_score > best_score:
                best_score = max_score
                best_sentiment = sentiment

        # Порог отсечения: если сходство низкое, текст нейтрален
        if best_score < 0.20:
            return "NEUTRAL", best_score

        return best_sentiment, best_score

    def _get_vader_sentiment(self, text):
        """Метод 2: Лексическая оценка тональности (только EN)."""
        vs = self.analyzer.polarity_scores(text) 
        compound = vs['compound']

        if compound >= 0.4:
            v_sentiment = "POSITIVE"
        elif compound <= -0.4:
            v_sentiment = "NEGATIVE"
        else:
            v_sentiment = "NEUTRAL"
            
        return v_sentiment, compound

    def _get_transformer_sentiment(self, text, is_ru):
        """Универсальный метод для получения сентимента от нейросети."""
        pipe = self.sentiment_pipe_ru if is_ru else self.sentiment_pipe_en
        result = pipe(text[:1500])[0]
        label = result['label'].upper()
        # Модель DistilBERT выдает 'POSITIVE'/'NEGATIVE', а RuBERT иногда цифры или другие метки
        # Приведем всё к единому стандарту:
        if "POS" in label: label = "POSITIVE"
        elif "NEG" in label: label = "NEGATIVE"
        else: label = "NEUTRAL"

        return label, result['score']
    

    def analyze_json_payload(self,body):
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return "ERROR: Invalid JSON"

        text = data.get("text", "")
        if not text:
            return "ERROR: No text provided"
            
        return self.smart_analyze(text)




    def smart_analyze(self, text):
            
        is_ru = self._is_russian(text)

        # 1. Инференс контекстной нейросети (Transformer)
        trans_sent, trans_score = self._get_transformer_sentiment(text, is_ru)
        
        # 2. Инференс векторной модели (Embeddings)
        active_model = self.embedder_ru if is_ru else self.embedder_en
        active_anchors = self.ru_sentiment_anchors if is_ru else self.en_sentiment_anchors
        embed_sent, embed_score = self._get_embedding_sentiment(active_model, active_anchors, text)

        if not is_ru:
            # --- АНГЛИЙСКАЯ ВЕТКА (Тройная архитектура + Триггеры) ---
            vader_sent, vader_score = self._get_vader_sentiment(text)
            
            # Основная матрица решений
            if embed_sent == trans_sent:
                final_sentiment, status = embed_sent, "CONFIRMED_MATCH"
            elif trans_sent == "POSITIVE" and embed_sent == "NEGATIVE":
                final_sentiment, status = "NEGATIVE", "SARCASM_DETECTED"
            elif trans_sent == "NEUTRAL" and embed_sent != "NEUTRAL":
                final_sentiment, status = embed_sent, "EMBED_DOMINANT"
            elif embed_sent == "NEUTRAL" and trans_sent != "NEUTRAL":
                final_sentiment, status = trans_sent, "TRANSFORMER_DOMINANT"
            else:
                # Разрешение конфликтов с участием VADER
                if vader_sent != "NEUTRAL":
                    if vader_sent == trans_sent:
                        final_sentiment, status = trans_sent, "RESOLVED_BY_VADER_AND_TRANS"
                    elif vader_sent == embed_sent:
                        final_sentiment, status = embed_sent, "RESOLVED_BY_VADER_AND_EMBED"
                    else:
                        final_sentiment, status = trans_sent, "CONFLICT_RESOLVED_BY_TRANS"
                else:
                    final_sentiment, status = trans_sent, "CONFLICT_RESOLVED_BY_TRANS"

            # Предохранительный лексический триггер (Fallback)
            if final_sentiment == "POSITIVE" and embed_score < 0.55:
                sarcasm_triggers = ["ignore", "ignoring", "wait", "waited", "weeks", "months", "never", "nothing", "bug", "crash"]
                if any(word in text.lower() for word in sarcasm_triggers):
                    final_sentiment = "NEGATIVE"
                    status = "SARCASM_BY_TRIGGER"

            return f"[{final_sentiment}] (Status: {status} | DistilBERT: {trans_sent} {trans_score:.2f} | Embed: {embed_sent} {embed_score:.2f} | VADER: {vader_sent} {vader_score:.2f})"

        else:
            # --- РУССКАЯ ВЕТКА (Двойная архитектура) ---
            if embed_sent == trans_sent:
                final_sentiment, status = embed_sent, "CONFIRMED_MATCH"
            elif trans_sent == "POSITIVE" and embed_sent == "NEGATIVE":
                final_sentiment, status = "NEGATIVE", "SARCASM_DETECTED"
            elif trans_sent == "NEUTRAL" and embed_sent != "NEUTRAL":
                final_sentiment, status = embed_sent, "EMBED_DOMINANT"
            elif embed_sent == "NEUTRAL" and trans_sent != "NEUTRAL":
                final_sentiment, status = trans_sent, "TRANSFORMER_DOMINANT"
            else:
                final_sentiment, status = trans_sent, "CONFLICT_RESOLVED_BY_TRANS"

            return f"[{final_sentiment}] (Status: {status} | RuBERT: {trans_sent} {trans_score:.2f} | Embed: {embed_sent} {embed_score:.2f})"


            
if __name__ == "__main__":
    analyzer = SentimentAnalyzer(
        ru_anchors_path='sentiment_anchors_ru.json', 
        en_anchors_path='anchors.json'
    )


    '''
    with open("someComments.json", 'r', encoding='utf-8') as f:
        data = json.load(f)

    for item in data:
        en_input = json.dumps({"text": item["text_en"]})

        ru_input = json.dumps({"text": item["text_ru"]})

        result = smart_analyze(ru_input)
        print(f"Текст: {item['text_ru']}")
        print(f"Итог: {result}")
        print("-" * 20)
    '''