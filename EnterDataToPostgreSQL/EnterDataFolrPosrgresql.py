import pandas as pd
import psycopg2
from transformers import AutoTokenizer, AutoModel
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from transformers import pipeline
import torch


host = "192.168.1.6"
database = "ctudb_v3"
user = "postgres"
password = "1324"
model_name = "VietAI/vit5-large-vietnews-summarization"

model_name_embedding = 'thenlper/gte-large'
tokenizer_embedding = AutoTokenizer.from_pretrained(model_name_embedding)
model_embedding = AutoModel.from_pretrained(model_name_embedding)

def edit_text(major):
    if major[1]["category_name"] == "kẹo":
        major[1]["category_name"] += " (Tân Huê Viên, Kẹo ngọt)".lower()

def expand_embedding(embedding, target_dim=2048):
    current_dim = len(embedding)
    if current_dim < target_dim:
        # Thêm giá trị 0 cho đến khi đạt được số chiều mong muốn
        expanded_embedding = embedding + [0] * (target_dim - current_dim)
    else:
        expanded_embedding = embedding[:target_dim]  # Cắt bớt nếu lớn hơn target_dim
    return expanded_embedding

def get_embedding_expand(text, target_dim=2048):
    if text is None:
        text = ""
    elif not isinstance(text, (str, list)):
        text = str(text)

    # Encode text input
    inputs = tokenizer_embedding(text, return_tensors='pt', truncation=False)
    input_ids = inputs['input_ids']
    attention_mask = inputs['attention_mask']

    # Chia nhỏ input thành các đoạn 512 token
    embeddings_list = []
    for i in range(0, input_ids.size(1), 512):
        input_chunk = input_ids[:, i:i+512]
        attention_chunk = attention_mask[:, i:i+512]

        # Tính toán embedding cho mỗi đoạn
        with torch.no_grad():
            outputs = model_embedding(input_chunk, attention_chunk)

        # Lấy trung bình embedding của đoạn
        chunk_embedding = outputs.last_hidden_state.mean(dim=1).squeeze()
        embeddings_list.append(chunk_embedding)

    # Concatenate tất cả các embedding
    final_embedding = torch.cat(embeddings_list, dim=0).numpy().tolist()

    # Mở rộng embedding tới target_dim
    final_embedding_expanded = expand_embedding(final_embedding, target_dim)

    return final_embedding_expanded



model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

pipe = pipeline("summarization", model=model, tokenizer=tokenizer, device=0)


conn = psycopg2.connect(
    dbname=database, 
    user=user, 
    password=password, 
    host=host, 
    port="5432"
)
cur = conn.cursor()
# Đường dẫn tới tệp Excel
excel_file_path = 'Các món ăn của tân huê viên (beta_v3).xlsx'
# Đọc tất cả các sheet
sheets_dict = pd.read_excel(excel_file_path, sheet_name=None, engine='openpyxl')
# In tên các sheet và hiển thị dữ liệu của từng sheet
for sheet_name, df in sheets_dict.items():
    print(f"Sheet name: {sheet_name}")
    for index, row in df.iterrows():
        print(f"Index: {index}")
    
        # Ví dụ dữ liệu ngành học
        major = [
            {
                "name": " ".join(str(row['name']).lower().replace("\n", " ").split()),
                "info": " ".join(str(row['info']).lower().replace("\n", " ").split()),
                "ingredient": " ".join(str(row['ingredient']).lower().replace("\n", " ").split()),
                "description": " ".join(str(row['desc']).lower().replace("\n", " ").split()),
                "price_agv": row['price_agv']
            },
            {
                "category_name": " ".join(str(row['category']).lower().replace("\n", " ").split()),
                "category_desc": " ".join(str(row['category_desc']).lower().replace("\n", " ").split()),
            },
            {
                "weight": " ".join(str(row['weight']).lower().replace("\n", " ").split()), 
                "expiry_date": " ".join(str(row['expiry_date']).lower().replace("\n", " ").split()), 
                "how_to_use": " ".join(str(row['how_to_use']).lower().replace("\n", " ").split()),
                "link": " ".join(str(row['link']).lower().replace("\n", " ").split()), 
            }
        ]

        edit_text(major)

        # Chèn dữ liệu vào bảng
        embedding_name = get_embedding_expand(major[0]["name"])
        summerizatin_info = " ".join(str(pipe(major[0]['info'])[0]['summary_text']).lower().replace("\n", " ").split())
        embedding_info = get_embedding_expand(summerizatin_info) 
        summerizatin_desc = " ".join(str(pipe(major[0]['description'])[0]['summary_text']).lower().replace("\n", " ").split())
        embedding_desc = get_embedding_expand(summerizatin_desc)
        embedding_ingredient = get_embedding_expand("được làm từ (bằng) nguyên liệu " + major[0]['ingredient'])
        cur.execute(
            """
            INSERT INTO Products (name, ingredient, price_agv, description, embedding_name, embedding_desc, embedding_ingredient)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (major[0]["name"], major[0]['ingredient'], major[0]["price_agv"], summerizatin_desc, embedding_name, embedding_desc, embedding_ingredient)
        )
        
        conn.commit()
        cur.close()
        cur = conn.cursor()
        
        queryCategory = "SELECT category_id FROM categories WHERE category_name = '" + major[1]["category_name"] + "'"
        cur.execute(queryCategory)
        category_ids = cur.fetchall()
        
        print("1. category_ids:", category_ids)
        
        if not category_ids:
            print("insert cateogries")
            embedding_name = get_embedding_expand(major[1]['category_name'])
            summerizatin_desc_category = major[1]['category_desc']
            embedding_desc = get_embedding_expand(summerizatin_desc_category)
            cur.execute(
                """
                INSERT INTO Categories (category_name, category_desc, embedding_name, embedding_desc)
                VALUES (%s, %s, %s, %s)
                """,
                (major[1]["category_name"], summerizatin_desc_category, embedding_name, embedding_desc)
            )
            cur.execute(queryCategory)
            
            conn.commit()
            cur.close()
            cur = conn.cursor()
            
            queryCategory = "SELECT category_id FROM categories WHERE category_name = '" + major[1]["category_name"] + "'"
            cur.execute(queryCategory)
            category_ids = cur.fetchall()
            
        
        cur.close()
        cur = conn.cursor()
        queryProduct = "SELECT id FROM Products ORDER BY id DESC LIMIT 1;"
        cur.execute(queryProduct)
        product_ids = cur.fetchall()
        print(f"1. product_ids: {product_ids}")    
        
        for i, product_id in enumerate(product_ids, 1):
            for i, category_id in enumerate(category_ids, 1):
                print (f"category_id {category_id[0]}, product_id {product_id[0]}")
                cur.execute(
                    """
                    INSERT INTO ProductDetails (info, weight, expiry_date, how_to_use, link, embedding_info, product_id_fk, category_id_fk) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (summerizatin_info, major[2]["weight"], major[2]["expiry_date"], major[2]["how_to_use"], major[2]["link"], embedding_info, int(product_id[0]), int(category_id[0]))
                )
        # Commit thay đổi 
        conn.commit()
        cur.close()
        cur = conn.cursor()
        # del pipe
        # torch.cuda.empty_cache()

conn.close()