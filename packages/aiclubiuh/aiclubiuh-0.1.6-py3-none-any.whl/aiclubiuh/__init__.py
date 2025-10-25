from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
import random

def introduce():
    intro_text = """
**AI_Club - Câu lạc bộ Trí tuệ nhân tạo IUH**

Câu lạc bộ Trí tuệ Nhân tạo (AI Club) tại Trường Đại học Công nghiệp TP.HCM được thành lập từ năm 2019, tọa lạc tại phòng Data Innovation Lab H2.2. Đây là nơi dành cho các sinh viên yêu thích và đam mê nghiên cứu trong lĩnh vực Khoa học Dữ liệu (KHDL) và Khoa học Máy tính (KHMT), tạo ra một môi trường học tập năng động và sân chơi học thuật để phát triển kỹ năng và kiến thức chuyên môn.

**Hoạt động chính:**
- Tham gia các khóa học miễn phí về Lập trình, Toán học, Trí tuệ Nhân tạo.
- Nghiên cứu khoa học và tham dự hội nghị.
- Tham gia các hoạt động giải trí như văn nghệ và thể thao.

**Trang thiết bị:**
- Phòng lab hiện đại tại Data Innovation Lab H2.2, Trường Đại học Công nghiệp TP.HCM.

**Đối tượng:**
- Tất cả sinh viên đam mê AI, khoa học dữ liệu, không phân biệt ngành học.

**Lý do tham gia:**
- Học hỏi từ giảng viên, mentor và tham gia các cuộc thi lớn.
- Tham gia các workshop, seminar và các hoạt động kết nối.
- Cơ hội học hỏi kinh nghiệm từ các anh chị khóa trước.

Hãy cùng tham gia AI Club để phát triển bản thân và khám phá những tiềm năng mới!
    """
    console = Console()
    markdown = Markdown(intro_text)
    panel = Panel(markdown, title="🎓 AI_Club IUH 🎓", expand=False, border_style="bold green")
    console.print(panel)


def kiem_ny():
    lovers = [
        "💘 Cô bạn học cùng lớp Python, mê Machine Learning hơn cả bạn",
        "💞 Một bạn trong Lab H2.2 hay mượn máy bạn train model",
        "💘 Cô sinh viên KHDL có nụ cười khiến loss giảm, accuracy tăng.",
        "💖 Một đàn anh dễ thương chuyên dạy bạn Docker và PyTorch",
        "💘 Người từng hỏi mượn bạn GPU một lần, giờ mượn luôn trái tim 💔.",
        "💕 Cô gái thích Data Visualization, luôn hỏi bạn về Matplotlib",
        "💓 Một mentor bí ẩn trong AI Club IUH, biết cách fix bug mọi thứ",
        "💝 Người yêu tương lai đang đợi bạn hoàn thành thesis AI 🤖",
        "💗 Một đồng đội cùng nhóm hackathon, code xuyên đêm cùng bạn",
        "💗 Cô gái thích học Python, nhưng thích bạn hơn cả syntax đẹp.",
        "💘 Cô nàng yêu AI đến mức gọi bạn là 'Model đẹp trai nhất em từng train'.",
        "💖 Một bạn thích Computer Vision – nhưng chỉ muốn nhìn thấy bạn.",
        "💘 Một thành viên trong AI Club luôn share meme về Data Science",
        "💓 Người giúp bạn setup môi trường Jupyter mà setup luôn trái tim 💕.",
        "💞 Một bạn học ngành Robotics, nói chuyện là toàn nhắc về ROS và SLAM",
        "💖 Cô gái thích NLP, nhắn tin cho bạn mà toàn dùng Transformer ẩn dụ",
        "💕 Một người bạn trong lớp Big Data, mỗi lần gặp là bàn về Spark vs Hadoop",
        "💓 Một crush trong lớp Deep Learning, chỉ thích bạn khi bạn hiểu Attention 😳",
        "💝 Một đàn em hay hỏi bạn cách fine-tune model trên Colab Pro",
        "💗 Cô bạn thích làm chatbot, nói chuyện với bạn mà tưởng đang prompt ChatGPT",
        "💘 Một người luôn chờ bạn release version mới của project AI của mình",
        "💞 Cậu bạn DevOps luôn nhắc bạn commit code đúng convention",
        "💖 Một bạn trong CLB AI luôn share paper arXiv mỗi sáng",
        "💗 Cô gái đam mê NLP, mỗi lần nói chuyện như đang fine-tune cảm xúc.",
        "💕 Cô gái mê Computer Vision, chụp bạn mọi góc rồi nói 'để train model nhận diện cảm xúc' 📸",
        "💓 Một đồng nghiệp trong trung tâm nghiên cứu, hay pha cà phê cùng debug TensorFlow",
        "💝 Cô gái chuyên viết prompt hay đến mức bạn muốn fine-tune chính mình cho hợp cô ấy",
        "💗 Một người luôn nhắc bạn đi ngủ sớm vì 'Overfitting với caffeine là không tốt' ☕",
        "💘 Một crush trong lớp Reinforcement Learning, luôn bảo bạn là 'optimal policy của lòng họ' 🥰",
        "💞 Một bạn gái UI/UX, nói chuyện với bạn mà toàn dùng từ như 'user-friendly' và 'responsive' 💻",
        "💖 Cô gái thích GitHub, thả tim vào mọi commit của bạn ❤️",
        "💕 Một người bạn thích Kaggle, mỗi lần nói chuyện là khoe leaderboard",
        "💓 Một người luôn nói rằng tình yêu của bạn là hàm loss tối thiểu toàn cục 💘",
        "💝 Một cô bạn học AI Ethics, mỗi lần bạn nói sai là bảo 'đó là bias trong model của bạn 😆'",
        "💗 Một người chỉ nhắn tin khi họ cần test API bạn mới viết 🤖",
        "💘 Một bạn học AI mà bạn nghi ngờ chính là AGI trong hình hài con người 👀",
        "💞 Một cô gái thích Data Storytelling, biến mọi buổi nói chuyện thành một dashboard cảm xúc 📊",
        "💖 Một người cùng lớp LLM, mỗi khi nói chuyện là 'let’s fine-tune our relationship' 💬",
        "💝 Một sinh viên năm nhất thần tượng bạn vì bạn biết AI và viết blog.",
        "💓 Một người từng hỏi: 'Em nên học ML hay DL?' – và bạn trả lời: 'Học anh trước đã 😳'.",
        "💝 Một người lạ từng nhìn bạn trong buổi seminar AI và mỉm cười nhẹ.",
    ]

    choice = random.choice(lovers)
    console = Console()
    panel = Panel(choice, title="💌 Người yêu của bạn hôm nay là:", border_style="magenta", expand=False)
    console.print(panel)

introduce()
