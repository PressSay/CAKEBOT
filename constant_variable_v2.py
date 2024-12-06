QUERY_FOR_PRODUCT_LISTING_OLD = """
    SELECT 
    Categories.category_name,
    Categories.category_id
    FROM Categories 
    WHERE 1 - (Categories.embedding_name <=> %s::vector) >= 0.8
    AND 1 - (Categories.embedding_desc <=> %s::vector) >= 0.8
    ORDER BY
    CASE  
        WHEN (1 - (Categories.embedding_name <=> %s::vector)) >= (1 - (Categories.embedding_desc <=> %s::vector))
        THEN (1 - (Categories.embedding_name <=> %s::vector))
        ELSE (1 - (Categories.embedding_desc <=> %s::vector))
    END DESC
    LIMIT %s;   
"""

QUERY_FOR_PRODUCT_LISTING = """
    SELECT 
    Categories.category_name,
    Categories.category_id
    FROM Categories 
    WHERE 1 - (Categories.embedding_name <=> %s::vector) >= 0.8
    ORDER BY (1 - (Categories.embedding_name <=> %s::vector))
    DESC
    LIMIT %s;   
"""

QUERY_PRODUCT_LISTING = """
    SELECT 
    Products.name,
    Products.price_agv
    FROM Products 
    INNER JOIN ProductDetails ON Products.id = ProductDetails.product_id_fk 
    INNER JOIN Categories ON ProductDetails.category_id_fk = Categories.category_id 
    WHERE Categories.category_id = %s;
"""

QUERY_CATEGORY_LISTING = """
    SELECT category_name, category_desc FROM categories;
"""

QUERY_EXTRACT = """
    SELECT 
    name, 
    ingredient,
    Products.price_agv,
    info,
    description, 
    weight,
    expiry_date, 
    how_to_use,
    category_name
    FROM Products 
    INNER JOIN ProductDetails ON Products.id = ProductDetails.product_id_fk
    INNER JOIN Categories ON ProductDetails.category_id_fk = Categories.category_id
    WHERE
    1 - (Products.embedding_name <=> %s::vector) >= 0.8
    AND 1 - (ProductDetails.embedding_info <=> %s::vector) >= 0.8
    AND 1 - (Products.embedding_desc <=> %s::vector) >= 0.8
    AND 1 - (Categories.embedding_desc <=> %s::vector) >= 0.8
    AND 1 - (Categories.embedding_name <=> %s::vector) >= 0.8
    AND 1 - (Products.embedding_ingredient <=> %s::vector) >= 0.8
    ORDER BY 
        CASE 
            WHEN (1 - (Products.embedding_name <=> %s::vector)) > (1 - (ProductDetails.embedding_info <=> %s::vector)) 
                AND (1 - (Products.embedding_name <=> %s::vector)) > (1 - (Products.embedding_desc <=> %s::vector)) 
                AND (1 - (Products.embedding_name <=> %s::vector)) > (1 - (Categories.embedding_desc <=> %s::vector)) 
                AND (1 - (Products.embedding_name <=> %s::vector)) > (1 - (Categories.embedding_name <=> %s::vector)) 
                AND (1 - (Products.embedding_name <=> %s::vector)) > (1 - (Products.embedding_ingredient <=> %s::vector))
            THEN (1 - (Products.embedding_name <=> %s::vector))
            
            WHEN (1 - (ProductDetails.embedding_info <=> %s::vector)) > (1 - (Products.embedding_name <=> %s::vector)) 
                AND (1 - (ProductDetails.embedding_info <=> %s::vector)) > (1 - (Products.embedding_desc <=> %s::vector)) 
                AND (1 - (ProductDetails.embedding_info <=> %s::vector)) > (1 - (Categories.embedding_desc <=> %s::vector)) 
                AND (1 - (ProductDetails.embedding_info <=> %s::vector)) > (1 - (Categories.embedding_name <=> %s::vector))
                AND (1 - (ProductDetails.embedding_info <=> %s::vector)) > (1 - (Products.embedding_ingredient <=> %s::vector))
            THEN (1 - (ProductDetails.embedding_info <=> %s::vector))
            
            WHEN (1 - (Products.embedding_desc <=> %s::vector)) > (1 - (Products.embedding_name <=> %s::vector)) 
                AND (1 - (Products.embedding_desc <=> %s::vector)) > (1 - (ProductDetails.embedding_info <=> %s::vector)) 
                AND (1 - (Products.embedding_desc <=> %s::vector)) > (1 - (Categories.embedding_desc <=> %s::vector)) 
                AND (1 - (Products.embedding_desc <=> %s::vector)) > (1 - (Categories.embedding_name <=> %s::vector)) 
                AND (1 - (Products.embedding_desc <=> %s::vector)) > (1 - (Products.embedding_ingredient <=> %s::vector))
            THEN (1 - (Products.embedding_desc <=> %s::vector))
            
            WHEN (1 - (Categories.embedding_desc <=> %s::vector)) > (1 - (Products.embedding_name <=> %s::vector)) 
                AND (1 - (Categories.embedding_desc <=> %s::vector)) > (1 - (ProductDetails.embedding_info <=> %s::vector)) 
                AND (1 - (Categories.embedding_desc <=> %s::vector)) > (1 - (Products.embedding_desc <=> %s::vector)) 
                AND (1 - (Categories.embedding_desc <=> %s::vector)) > (1 - (Categories.embedding_name <=> %s::vector)) 
                AND (1 - (Categories.embedding_desc <=> %s::vector)) > (1 - (Products.embedding_ingredient <=> %s::vector))
            THEN (1 - (Categories.embedding_desc <=> %s::vector))
            
            WHEN (1 - (Products.embedding_ingredient <=> %s::vector)) > (1 - (Categories.embedding_name <=> %s::vector))
                AND (1 - (Products.embedding_ingredient <=> %s::vector)) > (1 - (Products.embedding_name <=> %s::vector)) 
                AND (1 - (Products.embedding_ingredient <=> %s::vector)) > (1 - (ProductDetails.embedding_info <=> %s::vector)) 
                AND (1 - (Products.embedding_ingredient <=> %s::vector)) > (1 - (Products.embedding_desc <=> %s::vector)) 
                AND (1 - (Products.embedding_ingredient <=> %s::vector)) > (1 - (Categories.embedding_name <=> %s::vector)) 
            THEN (1 - (Products.embedding_ingredient <=> %s::vector))
            
            ELSE (1 - (Categories.embedding_name <=> %s::vector))
        END DESC
    LIMIT %s;      
"""

# ,
#     Products.price_agv,
#     category_name

QUERY_GENERIC = """
    SELECT 
    name
    FROM Products 
    INNER JOIN ProductDetails ON Products.id = ProductDetails.product_id_fk
    INNER JOIN Categories ON ProductDetails.category_id_fk = Categories.category_id;
"""

BANH_PIA_CLASSES_NAME = ['Bánh pía bách vị', 'Bánh pía bí đỏ', 'Bánh pía chay đậu đen', 'Bánh pía chay đậu đỏ',
                         'Bánh pía chay đậu sầu riêng 480 gram', 'Bánh pía chay đậu sầu riêng it duong',
                         'Bánh pía chay đậu xanh', 'Bánh pía chay dứa', 'Bánh pía chay khóm', 'Bánh pía chay mè đen',
                         'Bánh pía chay môn', 'Bánh pía chay thập cẩm', 'Bánh pía đậu đen sầu riêng', 'Bánh pía đậu đỏ',
                         'Bánh pía đậu xanh sầu riêng ít đường có trứng', 'Bánh pía đậu xanh sầu riêng trứng',
                         'Bánh pía dứa', 'Bánh pía ít đường có trứng', 'Bánh pía khoai môn sầu riêng trứng',
                         'Bánh pía kim sa bắp', 'Bánh pía kim sa đậu', 'Bánh pía kim sa đậu 300 gram',
                         'Bánh pía kim sa đậu đen', 'Bánh pía kim sa đậu đỏ', 'Bánh pía kim sa dứa',
                         'Bánh pía kim sa mè đen', 'Bánh pía kim sa trà xanh', 'Bánh pía mè đen',
                         'Bánh pía một kg đặc biệt', 'Bánh pía 6 sao', 'Bánh pía số 1', 'Bánh pía thịt lạp']
BANH_CON_LAI_NAME = ['Bánh in cacao nhân đậu dứa', 'Bánh in cacao nhân đậu dứa 360 gram',
                      'Bánh in đậu xanh sầu riêng 400 gram', 'Bánh in nếp than đậu xanh dứa', 'Bánh in nếp than dứa',
                      'Bánh in nếp than đậu xanh sầu riêng', 'Bánh in nhân đậu xanh 200 gram',
                      'Bánh in nhân đậu xanh 400 gram', 'Bánh in nhân đậu xanh dứa 360 gram',
                      'Bánh in nhân đậu xanh dứa 4 cai', 'Bánh in nhân đậu xanh sầu riêng 360 gram',
                      'Bánh in trà xanh 360 gram', 'Bánh in trăng', 'Lạp xưởng ăn liền',
                      '	Lạp xưởng bò', 'Lạp xưởng gà', 'Lạp xưởng hồ lô', '	Lạp xưởng mai quế lộ',
                      'Lạp xưởng mai quế lộ vị tiêu', 'Lạp xưởng mai quế lộ vị tiêu 3 sao', 'Lạp xưởng tôm',
                      'Lạp xưởng tươi', 'Lạp xưởng xông khói']

GENERIC_CLASSES_NAME = ["người", "xe đạp", "ô tô", "xe máy", "máy bay", "xe buýt", "tàu hỏa", "xe tải", "thuyền",
                        "đèn giao thông", "vòi cứu hỏa", "biển báo dừng", "đồng hồ đỗ xe", "ghế dài", "chim", "mèo",
                        "chó", "ngựa", "cừu", "bò", "voi", "gấu", "ngựa vằn", "hươu cao cổ", "ba lô", "ô",
                        "túi xách", "cà vạt", "vali", "đĩa bay", "ván trượt tuyết", "ván trượt tuyết", "bóng thể thao", "diều",
                        "gậy bóng chày",
                        "găng tay bóng chày", "ván trượt", "ván lướt sóng", "vợt tennis", "chai", "ly rượu vang", "cốc",
                        "nĩa", "dao", "thìa", "bát", "chuối", "táo", "bánh sandwich", "cam", "súp lơ",
                        "cà rốt", "xúc xích", "pizza", "bánh rán", "bánh ngọt", "ghế", "ghế sofa", "cây trồng trong chậu", "giường",
                        "bàn ăn", "nhà vệ sinh", "màn hình tivi", "máy tính xách tay", "chuột", "điều khiển từ xa", "bàn phím", "điện thoại di động",
                        "lò vi sóng", "lò nướng", "máy nướng bánh mì", "bồn rửa", "tủ lạnh", "sách", "đồng hồ", "bình hoa", "kéo",
                        "gấu bông", "máy sấy tóc", "bàn chải đánh răng"]

CANT_QUERY = "Rất tiếc, tôi không thể giải đáp được thắc mắc của bạn."


CLASSIFY_QUERY = ("Phân loại câu hỏi sau cần thông tin gì, không giải thích thêm:\n"
                  "1=Danh sách thể loại sản phẩm,\n"
                  "2=Sản phẩm thuộc thể loại nào,\n"
                  "3=Thông tin sản phẩm cụ thể,\n"
                  "4=Danh sách tên tất cả sản phẩm,\n"
                  "5=Khác.\n"
                  "Câu hỏi: ")

CLASSIFY_QUERY_OLD = ("Phân loại câu hỏi sau cần thông tin gì, không giải thích thêm:\n"
                  "1=Danh sách các thể loại sản phẩm,\n"
                  "2=Sản phẩm thuộc thể loại nào,\n"
                  "3=Thông tin về sản phẩm cụ thể,\n"
                  "4=Danh sách tất cả các sản phẩm,\n"
                  "5=Câu hỏi không liên quan đến các mục trên hoặc không rõ ràng.\n"
                  "Câu hỏi: ")

CLASSIFY_QUERY_NOCASE = ("Phân loại câu hỏi sau cần thông tin gì, không giải thích thêm:\n"
                         "1=Thông tin hình ảnh,\n"
                         "2=Thông tin thường.\n"
                         "Câu hỏi: ")