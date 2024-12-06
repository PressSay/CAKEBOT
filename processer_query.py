import threading
import time

import constant_variable_v2
from model_nlp_v2 import RAG


class HandlerQuery:
    def __init__(self, tts):
        self.rag = RAG()
        self.new_question = True
        self.vision_response = ''
        self.tts = tts

    def split_text_on_last_space(self, text):
        """Tách chuỗi dựa trên khoảng trắng cuối cùng."""
        trimmed_text = text.rstrip()
        last_space_idx = trimmed_text.rfind(" ")
        if last_space_idx != -1:
            return trimmed_text[:last_space_idx], trimmed_text[last_space_idx + 1:]
        return trimmed_text, ""

    def process_text_stream(self, response):
        complete_text = ""
        buffer_text = ""
        for chunk in response:
            chunk_text = chunk.text.replace('*', '')
            complete_text += chunk_text
            buffer_text += chunk_text
            # Nếu có khoảng trắng, xử lý văn bản
            if ' ' in buffer_text:
                before_last, last_word = self.split_text_on_last_space(buffer_text)
                if before_last:
                    print(before_last)
                    self.tts.speak_text(before_last)
                buffer_text = last_word
            elif buffer_text[-1] in [".", ",", ":", ";"]:
                print(buffer_text)
                self.tts.speak_text(buffer_text)
                buffer_text = ""
        # Phát văn bản còn lại
        if buffer_text:
            print(buffer_text)
            self.tts.speak_text(buffer_text)
        return complete_text

    def process_handling(self, query, model_vision):
        self.tts.stop_current_speak()
        time_start = time.time()
        source_information_vision = ([class_name for class_name in model_vision.classNames[1]
                                      if model_vision.classFlags[1][class_name]] +
                                     [class_name for class_name in model_vision.classNames[0]
                                      if model_vision.classFlags[0][class_name]])
        source_information_vision = source_information_vision[:3]
        classified = self.rag.classify_content(query)
        classified_compare = self.rag.classified_compare_enum
        finish_time = time.time() - time_start
        print(f"classified is {classified}")
        print(f"Thời gian thực hiện phân lớp {finish_time}")
        self.new_question = True
        response = ""
        if not classified == classified_compare.NoneOfThese:
            source_information = self.rag.enhance_prompt(classified, 2, query, source_information_vision)
            if source_information == "Không tìm thấy thông tin liên quan.":
                return response
            combined_information = (
                f"Bạn là trợ lý tư vấn sản phẩm. Trả lời dựa trên danh sách sản phẩm dưới đây. "
                f"Nếu không có thông tin phù hợp, trả lời: '{constant_variable_v2.CANT_QUERY}'\n"
                f"Danh sách sản phẩm (Tân Huê Viên):{source_information}\n"
                f"Câu hỏi: {query}"
            )
            response = self.rag.generate_content(combined_information)
        else:
            classified_6 = self.rag.classify_content_6(query)
            source_information = self.rag.enhance_prompt(classified, classified_6, query, source_information_vision)
            if source_information == "Không tìm thấy thông tin liên quan.":
                return response
            if classified_6 == 1:
                if len(source_information_vision) > 1:
                    response = f"Ở đây có nhiều đối tượng quá, bạn có thể đưa gần camera hơn không?"
                    self.new_question = False
                    thread_monitor_yolo = threading.Thread(target=self.monitor_yolo_and_update_response,
                                                           args=(model_vision,))
                    thread_monitor_yolo.start()
                elif len(source_information_vision) == 1:
                    response = f"Tôi đoán không lằm thì đây là {", ".join(source_information_vision)}"
                else:
                    response = f"Bạn thông cảm nhé, tôi không thấy rõ!"
                self.tts.speak_text(response)
                return response
            else:
                combined_information = (
                    "Bạn là trợ lý tư vấn sản phẩm. Trả lời dựa trên danh sách sản phẩm dưới đây.\n"
                    "Nếu câu hỏi không khớp trực tiếp với thông tin có sẵn, "
                    "hãy suy diễn.\n"
                    f"Nếu vẫn không thể trả lời, đáp lại: '{constant_variable_v2.CANT_QUERY}'. "
                    f"Danh sách sản phẩm (Tân Huê Viên):{source_information}\n"
                    f"Câu hỏi: {query}")
                response = self.rag.generate_content(combined_information)
        finish_time = time.time() - time_start
        print(f"Thời gian phản hồi {finish_time}")
        response = self.process_text_stream(response)
        finish_time = time.time() - time_start
        print(f"Thông tin {source_information}")
        print(f"Thời gian thực hiện hoàn thiện văn bản {finish_time}")
        print(f"Thông tin Yolo: {source_information_vision}")
        print(f"Query: {query}")
        return response

    def monitor_yolo_and_update_response(self, model_vision):
        current_time = time.time()
        while not self.new_question:
            time_interval = time.time() - current_time
            if time_interval >= 1/30:
                # print(time_interval)
                current_time = time.time()
                detected_objects = ([class_name for class_name in model_vision.classNames[1]
                                         if model_vision.classFlags[1][class_name]] +
                                         [class_name for class_name in model_vision.classNames[0]
                                          if model_vision.classFlags[0][class_name]])
                if len(detected_objects) == 1:
                    self.vision_response = f"Tôi đoán không lằm thì đây là {detected_objects}"
                    self.tts.speak_text(self.vision_response)
                    break
            else:
                time.sleep(1/30)
        print("kết thúc monitor")
