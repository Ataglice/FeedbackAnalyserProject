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
        """Метод 1: Оценка тональности через косинусное сходство векторов"""
        input_vec = active_model.encode(text)
        
        max_magnitude = -1.0
        final_best_score = 0.0
        other_scores = {}
        
        for sentiment, anchor_vec_list in active_anchor.items():
            scores = util.cos_sim(input_vec, anchor_vec_list)
            current_score = scores.max().item()
            
            if sentiment == "NEGATIVE":
                signed_score = -current_score
            else:
                signed_score = current_score
        
            other_scores[sentiment] = signed_score

            if current_score > max_magnitude:
                max_magnitude = current_score
                final_best_score = signed_score

        if max_magnitude < 0.20:
            other_scores["NEUTRAL"] = max_magnitude
            return max_magnitude, other_scores

        return final_best_score, other_scores

    def _get_vader_sentiment(self, text):
        """Метод 2: Лексическая оценка тональности для английского"""
        vs = self.analyzer.polarity_scores(text) 
        
        return vs

    def _get_transformer_sentiment(self, text, is_ru):
        """Метод 3: Универсальный метод для получения сентимента от нейросети."""

        pipe = self.sentiment_pipe_ru if is_ru else self.sentiment_pipe_en
        result = pipe(text[:1500])[0]
        
        label = result['label'].upper()
        score = result['score']

        if "POS" in label: 
            return score
        elif "NEG" in label: 
            return -score
        else: 
            return 0.0
    

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

        # 1. (Transformer)
        trans_score = self._get_transformer_sentiment(text, is_ru)
        
        # 2. (Embeddings)
        active_model = self.embedder_ru if is_ru else self.embedder_en
        active_anchors = self.ru_sentiment_anchors if is_ru else self.en_sentiment_anchors
        embed_fin_score, embed_scores = self._get_embedding_sentiment(active_model, active_anchors, text)

        NEU_THRESH = 0.20
        trans_is_pos = trans_score > NEU_THRESH
        trans_is_neg = trans_score < -NEU_THRESH
        trans_is_neu = abs(trans_score) <= NEU_THRESH

        embed_is_pos = embed_fin_score > NEU_THRESH
        embed_is_neg = embed_fin_score < -NEU_THRESH
        embed_is_neu = abs(embed_fin_score) <= NEU_THRESH

        final_val = 0.0
        status = "UNKNOWN"

        if not is_ru:
            # 3. (VADER)
            vader_scores = self._get_vader_sentiment(text)
            vader_comp = vader_scores['compound']
            
            vader_is_pos = vader_comp > NEU_THRESH
            vader_is_neg = vader_comp < -NEU_THRESH
            vader_is_neu = abs(vader_comp) <= NEU_THRESH
            
            # --- АНГЛИЙСКАЯ ВЕТКА (Числовая матрица) ---
            if (trans_is_pos and embed_is_pos) or (trans_is_neg and embed_is_neg) or (trans_is_neu and embed_is_neu):
                # Если направление совпадает, усредняем показатели трех моделей
                final_val = (trans_score + embed_fin_score + vader_comp) / 3.0
                status = "CONFIRMED_MATCH"
            elif trans_is_pos and embed_is_neg:
                # Нейросеть видит позитив, но векторы указывают на явный негатив
                final_val = embed_fin_score 
                status = "SARCASM_DETECTED"
            elif trans_is_neu and not embed_is_neu:
                final_val = embed_fin_score
                status = "EMBED_DOMINANT"
            elif embed_is_neu and not trans_is_neu:
                final_val = trans_score
                status = "TRANSFORMER_DOMINANT"
            else:
                # Разрешение конфликтов (разнонаправленные сильные сигналы)
                if not vader_is_neu:
                    if (vader_is_pos and trans_is_pos) or (vader_is_neg and trans_is_neg):
                        final_val = (trans_score + vader_comp) / 2.0
                        status = "RESOLVED_BY_VADER_AND_TRANS"
                    elif (vader_is_pos and embed_is_pos) or (vader_is_neg and embed_is_neg):
                        final_val = (embed_fin_score + vader_comp) / 2.0
                        status = "RESOLVED_BY_VADER_AND_EMBED"
                    else:
                        final_val = trans_score
                        status = "CONFLICT_RESOLVED_BY_TRANS"
                else:
                    final_val = trans_score
                    status = "CONFLICT_RESOLVED_BY_TRANS"

            # Предохранительный лексический триггер (Fallback)
            if final_val > 0 and embed_fin_score < 0.55:
                sarcasm_triggers = ["ignore", "ignoring", "wait", "waited", "weeks", "months", "never", "nothing", "bug", "crash"]
                if any(word in text.lower() for word in sarcasm_triggers):
                    # Принудительная инверсия оценки
                    final_val = -abs(final_val) if final_val != 0 else -0.5
                    status = "SARCASM_BY_TRIGGER"

            final_val = round(max(min(final_val, 1.0), -1.0), 4)

            return {
                "value": final_val, 
                "status": status, 
                "type": {
                    "DistilBERT": round(trans_score, 4), 
                    "Embed": {k: round(v, 4) for k, v in embed_scores.items()}, 
                    "VADER": vader_scores
                }
            }
            

        else:
            # --- РУССКАЯ ВЕТКА (Числовая матрица) ---
            if (trans_is_pos and embed_is_pos) or (trans_is_neg and embed_is_neg) or (trans_is_neu and embed_is_neu):
                final_val = (trans_score + embed_fin_score) / 2.0
                status = "CONFIRMED_MATCH"
            elif trans_is_pos and embed_is_neg:
                final_val = embed_fin_score
                status = "SARCASM_DETECTED"
            elif trans_is_neu and not embed_is_neu:
                final_val = embed_fin_score
                status = "EMBED_DOMINANT"
            elif embed_is_neu and not trans_is_neu:
                final_val = trans_score
                status = "TRANSFORMER_DOMINANT"
            else:
                final_val = trans_score
                status = "CONFLICT_RESOLVED_BY_TRANS"

            final_val = round(max(min(final_val, 1.0), -1.0), 4)

            return {
                "value": final_val, 
                "status": status, 
                "type": {
                    "RuBERT": round(trans_score, 4), 
                    "Embed": {k: round(v, 4) for k, v in embed_scores.items()}
                }
            }



   

            
if __name__ == "__main__":
    


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