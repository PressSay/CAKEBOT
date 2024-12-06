import psycopg2

host = "192.168.1.6"
database = "ctudb_v3"
user = "postgres"
password = "1324"

cur = None
conn = None

# Kết nối đến PostgreSQL
try:
    # Thiết lập kết nối
    conn = psycopg2.connect(
        dbname=database,     # Tên cơ sở dữ liệu
        user=user,         # Tên người dùng
        password=password,      # Mật khẩu
        host=host,   # Địa chỉ máy chủ, mặc định là localhost
        port="5432"         # Cổng, mặc định là 5432
    )

    # Tạo con trỏ để tương tác với cơ sở dữ liệu
    cur = conn.cursor()

    # Câu lệnh SQL để tạo bảng
    create_table_query = """
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE TABLE IF NOT EXISTS Products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        ingredient varchar(255),
        price_agv INT NOT NULL CHECK (price_agv >= 0),
        description TEXT,
        embedding_name VECTOR(2048),
        embedding_desc VECTOR(2048),
        embedding_ingredient VECTOR(2048)
    );
    CREATE TABLE IF NOT EXISTS Categories (
        category_id SERIAL PRIMARY KEY,
        category_name VARCHAR(255),
        category_desc TEXT,
        embedding_name VECTOR(2048),
        embedding_desc VECTOR(2048)
    );
    CREATE TABLE IF NOT EXISTS ProductDetails (
        product_id SERIAL PRIMARY KEY,
        info TEXT,
        weight VARCHAR(100),
        expiry_date VARCHAR(100),
        how_to_use VARCHAR(255),
        link VARCHAR(255),
        embedding_info VECTOR(2048),
        product_id_fk INTEGER REFERENCES Products(id),
        category_id_fk INTEGER REFERENCES Categories(category_id)
    );
    """

    # Thực thi câu lệnh SQL
    cur.execute(create_table_query)

    # Xác nhận thay đổi trong cơ sở dữ liệu
    conn.commit()

    print("Table created successfully!")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Đóng con trỏ và kết nối
    if cur is not None:
        cur.close()
    if conn is not None:
        conn.close()