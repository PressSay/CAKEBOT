import re
import psycopg2
from transformers import AutoTokenizer, AutoModel
import torch
import textwrap
import google.generativeai as genai
from IPython.display import Markdown
import constant_variable_v2 as const_var

class RAG:
    def __init__(self,
                 postgres_host='localhost',
                 db_name='ctudb_v3',
                 port='5432',
                 user='postgres',
                 password='1324',
                 llm_api_key='',
                 llm_api_key_classify='',
                 llm_name='gemini-1.5-pro',
                 llm_classify='gemini-1.5-flash'):
        model_embedding_name = 'thenlper/gte-large'
        self.tokenizer_model_embedding = AutoTokenizer.from_pretrained(model_embedding_name)
        self.model_embedding = AutoModel.from_pretrained(model_embedding_name)

        self.conn = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=postgres_host,
            port=port)
        # Configure LLM
        genai.configure(api_key=llm_api_key)
        self.llm = genai.GenerativeModel(llm_name)
        genai.configure(api_key=llm_api_key_classify)
        self.llm_classify = genai.GenerativeModel(llm_classify)
        self.classified_compare_enum = self.enum(
            ListOfCategories=1, ListOfProductsInASpecificCategory=2,
            DetailProductSpecifications=3, CompleteListOfProducts=4,
            NoneOfThese=5)

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

    @staticmethod
    def normalize_and_split(text):
        # Loại bỏ ký tự đặc biệt và chuyển về chữ thường
        text = re.sub(r"[^\w\s]", "", text).lower()
        return set(text.split())
    @staticmethod
    def enum(**enums):
        return type('Enum', (), enums)

    @staticmethod
    def expand_embedding(embedding, target_dim=2048):
        current_dim = len(embedding)
        if current_dim < target_dim:
            # Thêm giá trị 0 cho đến khi đạt được số chiều mong muốn
            expanded_embedding = embedding + [0] * (target_dim - current_dim)
        else:
            expanded_embedding = embedding[:target_dim]  # Cắt bớt nếu lớn hơn target_dim
        return expanded_embedding

    def get_embedding(self, text, target_dim=2048):
        if text is None:
            text = ""
        elif not isinstance(text, (str, list)):
            text = str(text)

        # Encode text input
        inputs = self.tokenizer_model_embedding(text, return_tensors='pt', truncation=False)
        input_ids = inputs['input_ids']
        attention_mask = inputs['attention_mask']

        # Chia nhỏ input thành các đoạn 512 token
        embeddings_list = []
        for i in range(0, input_ids.size(1), 512):
            input_chunk = input_ids[:, i:i + 512]
            attention_chunk = attention_mask[:, i:i + 512]

            # Tính toán embedding cho mỗi đoạn
            with torch.no_grad():
                outputs = self.model_embedding(input_chunk, attention_chunk)

            # Lấy trung bình embedding của đoạn
            chunk_embedding = outputs.last_hidden_state.mean(dim=1).squeeze()
            embeddings_list.append(chunk_embedding)

        # Concatenate tất cả các embedding
        final_embedding = torch.cat(embeddings_list, dim=0).numpy().tolist()

        # Mở rộng embedding tới target_dim
        final_embedding_expanded = self.expand_embedding(final_embedding, target_dim)

        return final_embedding_expanded

    def vector_search(self, classified, classified_6, query_text: str, source_information_vision, top_k=4):
        # Kết nối đến PostgreSQL
        conn = self.conn
        cur = conn.cursor()
        # Tính toán embedding cho truy vấn
        classified_compare = self.classified_compare_enum
        if classified == classified_compare.NoneOfThese:
            if classified_6 == 1:
                query_text = f"{query_text}, {source_information_vision}"
                top_k = 3
        query_embedding = self.get_embedding(query_text)

        if classified == classified_compare.ListOfProductsInASpecificCategory:
            query_for_product_listing = const_var.QUERY_FOR_PRODUCT_LISTING
            query_var = [query_embedding] * 2
            query_var.append(top_k)
            cur.execute(
                query_for_product_listing,
                tuple(query_var)
            )
            result_qfpl = cur.fetchall()
            words_query_text = self.normalize_and_split(query_text)
            # suppose response is integer
            matched_elements = [item for item in result_qfpl if self.normalize_and_split(item[0]) & words_query_text]
            category_id = matched_elements[0][1]
            category_name = matched_elements[0][0]
            query = const_var.QUERY_PRODUCT_LISTING
            print(f"category_id = {category_id}")
            cur.execute(
                query,
                (category_id, )
            )
            results = cur.fetchall()
            results.append((0, category_name))
            cur.close()
            return  results
        elif classified == classified_compare.CompleteListOfProducts:
            query = const_var.QUERY_GENERIC
            cur.execute(
                query
            )
        elif classified == classified_compare.ListOfCategories:
            query = const_var.QUERY_CATEGORY_LISTING
            cur.execute(
                query
            )
        else:
            query = const_var.QUERY_EXTRACT
            query_var = [query_embedding] * 62  # 66 là số lượng placeholders
            query_var.append(top_k)  # Thêm top_k ở cuối
            cur.execute(
                query,
                tuple(query_var)
            )
        results = cur.fetchall()
        cur.close()
        # conn.close()
        return results

    def enhance_prompt(self, classified, classified_6, query, source_information_vision):
        classified_compare = self.classified_compare_enum
        enhanced_prompt = ""
        get_knowledge = self.vector_search(classified, classified_6, query, source_information_vision)
        count = 0
        if classified == classified_compare.ListOfProductsInASpecificCategory:
            for i, result in enumerate(get_knowledge, 1):
                if result[0] == 0:
                    enhanced_prompt += f"\nThuộc loại = {result[1]};"
                    continue
                enhanced_prompt += f"\n{i}) tên = {result[0]}; "
                enhanced_prompt += f"giá trung bình = {result[1]};"
                count += 1
        elif classified == classified_compare.ListOfCategories:
            for i, result in enumerate(get_knowledge, 1):
                enhanced_prompt += f"\n{i}. tên thế loại  = {result[0]}; "
                enhanced_prompt += f"mô tả = {result[1]}"
                count += 1
        elif classified == classified_compare.CompleteListOfProducts:
            for i, result in enumerate(get_knowledge, 1):
                enhanced_prompt += f"\n{i}) tên = {result[0]}; "
                count += 1
                # enhanced_prompt += f"giá trung bình = {result[1]}"
                # enhanced_prompt += f"tên thế loại = {result[2]}"
        else:
            for i, result in enumerate(get_knowledge, 1):
                enhanced_prompt += f"\n{i}) tên = {result[0]}; "
                enhanced_prompt += f"nguyên liệu = {result[1]}; "
                enhanced_prompt += f"giá trung bình = {result[2]}; "
                enhanced_prompt += f"thông tin = {result[3]}; "
                enhanced_prompt += f"mô tả = {result[4]}; "
                enhanced_prompt += f"trọng lượng = {result[5]}; "
                enhanced_prompt += f"hạn sử dụng = {result[6]}; "
                enhanced_prompt += f"cách dùng = {result[7]}; "
                enhanced_prompt += f"tên thể loại = {result[8]}"
                count += 1

        if not enhanced_prompt:
            return "Không tìm thấy thông tin liên quan."

        enhanced_prompt += f"\nTổng số lượng: {count}"

        return enhanced_prompt

    def generate_content(self, prompt):
        return self.llm.generate_content(prompt, stream=True)
        # return self.llm_classify.generate_content(prompt)

    def classify_content(self, query):
        # improve
        if query == "":
            # return 6
            return 5
        combined_information = const_var.CLASSIFY_QUERY + f"{query}"
        response = self.llm_classify.generate_content(combined_information)
        if not any(compare in response.text[0] for compare in ["1", "2", "3", "4"]):
            return 5
        return int(response.text)

    def classify_content_6(self, query):
        if query == "":
            return 2
        combined_information = const_var.CLASSIFY_QUERY_NOCASE + f"{query}"
        response = self.llm_classify.generate_content(combined_information)
        if not any(compare in response.text for compare in ["1"]):
            return 2

        return int(response.text)

    @staticmethod
    def _to_markdown(text):
        # Thay thế dấu '•' bằng '*'
        text = text.replace('•', '  *')
        # Thêm dấu > trước mỗi dòng
        indented_text = textwrap.indent(text, '> ')
        # Trả về Markdown
        return Markdown(indented_text)
