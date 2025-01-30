import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pyrebase
import re
import os
import base64
import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image
import tempfile
from dotenv import load_dotenv
import uuid
import pandas as pd
import plotly.express as px
import time
from datetime import datetime

def local_css(file_name):
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except UnicodeDecodeError as e:
        st.error(f"⚠ حدث خطأ أثناء قراءة ملف CSS: {str(e)}")


# Call the function to load the CSS
local_css("style.css")

# Load environment variables
load_dotenv()

# Set background image
def set_background(image_file):
    with open(image_file, "rb") as file:
        image_data = file.read()
    b64_image = base64.b64encode(image_data).decode()
    page_bg = f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpeg;base64,{b64_image}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(page_bg, unsafe_allow_html=True)

 
set_background("Background3.jpg")


# Firebase initialization with error handling
def initialize_firebase():
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate('firebase_credentials.json')
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Error initializing Firebase: {e}")
        return None

db = initialize_firebase()

firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY", "AIzaSyAPYyu4wh9bxlv_YSbjBmcQNfj6m_YdPZU"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", "ppe1detection.firebaseapp.com"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID", "ppe1detection"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", "ppe1detection.appspot.com"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", "652601014456"),
    "appId": os.getenv("FIREBASE_APP_ID", "1:652601014456:web:d63699755d5625be285c4d"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL", "https://ppe1detection-default-rtdb.firebaseio.com/")
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# Initialize session state
st.session_state.setdefault("logged_in", False)
st.session_state.setdefault("page", None)
st.session_state.setdefault("user_name", "")

# Validation functions
def is_valid_email(email):
    return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email))

def is_valid_firefighter_id(firefighter_id):
    return bool(re.match(r'^\d{9}$', firefighter_id))

def is_valid_name(name):
    return bool(re.match(r'^[\u0600-\u06FFa-zA-Z]+$', name))

def is_valid_password(password):
    return bool(re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{9,}$', password))

def logout():
    st.session_state["logged_in"] = False
    st.session_state["page"] = None
    auth.current_user = None


def sidebar_navigation():
    st.sidebar.markdown("<div style='text-align: left;'>", unsafe_allow_html=True)
    if st.sidebar.button("الكشف على المعدات الشخصية"):
        navigate_to("Detection")

    if st.sidebar.button("إدراج صورة/فيديو"):
        navigate_to("Upload")

    with st.sidebar.expander("وضع التدريب"):
        if st.button("الاختبارات القصيرة"):
            navigate_to("Quiz")
        if st.button("المؤقت"):
            navigate_to("Timer")
        if st.button("مدى التقدم"):
            navigate_to("Progress")

    if st.sidebar.button("تسجيل الخروج"):
        logout()

    def sidebar_Logo():
        # تصغير الشعار
        image_path = "Logo2.png"
        image = Image.open(image_path)
        st.sidebar.image(image, use_container_width=False)  # تم إزالة التسمية التوضيحية

    sidebar_Logo()

# Page navigation helper
def navigate_to(page):
    st.session_state["page"] = page
    st.rerun()

# Main page routing
def home_page():
    st.markdown('<div class="page-center">', unsafe_allow_html=True)
    if st.button("تسجيل الدخول"):
        navigate_to("تسجيل الدخول")
    if st.button("إنشاء حساب جديد"):
        navigate_to("إنشاء حساب جديد")
    st.markdown('</div>', unsafe_allow_html=True)

def signup_page():
    st.markdown("""
    <style>
    div.stColumn {
        display: flex;
        justify-content: center; /* توسيط أفقي */
        align-items: center; /* توسيط عمودي */
    }
    </style>
    """, unsafe_allow_html=True)
    with st.form("signup_form"):
        first_name = st.text_input("الاسم الأول")
        last_name = st.text_input("الاسم الأخير")
        email = st.text_input("البريد الإلكتروني")
        firefighter_id = st.text_input("رقم معرف رجل الإطفاء")
        password = st.text_input("كلمة السر", type="password")
        

        col1, col2 = st.columns(2)
        with col1:
            login_button = st.form_submit_button("لديك حساب بالفعل؟ تسجيل الدخول")

        with col2:
            signup_button = st.form_submit_button("إنشاء حساب")



    if signup_button:
        errors = []
        if not is_valid_name(first_name):
            errors.append("❌ الاسم الأول يجب أن يحتوي على أحرف فقط.")
        if not is_valid_name(last_name):
            errors.append("❌ الاسم الأخير يجب أن يحتوي على أحرف فقط.")
        if not is_valid_email(email):
            errors.append("❌ البريد الإلكتروني غير صحيح.")
        if not is_valid_firefighter_id(firefighter_id):
            errors.append("❌ رقم المعرف يجب أن يكون مكونًا من 9 أرقام فقط.")
        if not is_valid_password(password):
            errors.append("❌ كلمة السر يجب أن تكون 9 أرقام على الأقل، وتحتوي على حرف كبير، وحرف صغير، ورقم، ورمز.")

        if not errors:
            try:
                users_ref = db.collection('firefighter_data')
                existing_email = users_ref.where('email', '==', email).get()
                existing_id = users_ref.where('firefighter_id', '==', firefighter_id).get()

                if existing_email or existing_id:
                    st.error("❌ البريد الإلكتروني أو رقم المعرف مستخدم مسبقًا.")
                else:
                    user = auth.create_user_with_email_and_password(email, password)
                    users_ref.add({
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'firefighter_id': firefighter_id
                    })
                    st.success("✅ تم إنشاء الحساب بنجاح!")
                    navigate_to("تسجيل الدخول")
            except Exception as e:
                st.error(f"⚠ حدث خطأ أثناء إنشاء الحساب: {str(e)}")
        else:
            for error in errors:
                st.error(error)

    if login_button:
        navigate_to("تسجيل الدخول")

def login_page():
    with st.form("login_form"):
        # إدخال معرف رجل الإطفاء وكلمة السر
        firefighter_id = st.text_input("رقم معرف رجل الإطفاء")
        password = st.text_input("كلمة السر", type="password", key="login_password")
        
        # تخصيص الأزرار
        col1, col2, col3 = st.columns(3)
        with col1:
            forgot_password_button = st.form_submit_button("نسيت كلمة السر؟")
        with col2:
            create_account_button = st.form_submit_button("ليس لديك حساب؟ إنشاء حساب جديد")
        with col3:
            login_button = st.form_submit_button("تسجيل الدخول")

    # التحقق من الضغط على زر تسجيل الدخول
    if login_button:
        try:
            users_ref = db.collection('firefighter_data')
            user_doc = users_ref.where('firefighter_id', '==', firefighter_id).get()

            if len(user_doc) > 0:
                email = user_doc[0].to_dict().get('email', None)
                if email:
                    user = auth.sign_in_with_email_and_password(email, password)
                    st.success("✅ تم تسجيل الدخول بنجاح!")
                    # تحديث حالة الجلسة
                    st.session_state["logged_in"] = True
                    st.session_state["firefighter_id"] = firefighter_id
                    st.session_state["user_name"] = user_doc[0].to_dict().get('first_name', 'User')
                    
                    # التنقل إلى صفحة الكشف
                    navigate_to("Detection")
                else:
                    st.error("❌ لا يوجد بريد إلكتروني مرتبط بمعرف رجل الإطفاء.")
            else:
                st.error("❌ معرف رجل الإطفاء غير موجود.")
        
        except Exception as e:
            if "INVALID_LOGIN_CREDENTIALS" in str(e):
                st.error("❌ بيانات تسجيل الدخول غير صحيحة. يرجى المحاولة مرة أخرى.")
            else:
                st.error(f"⚠ حدث خطأ أثناء تسجيل الدخول: {str(e)}")

    # التحقق من الضغط على زر "إنشاء حساب جديد"
    if create_account_button:
        navigate_to("إنشاء حساب جديد")

    # التحقق من الضغط على زر "نسيت كلمة السر"
    if forgot_password_button:
        st.session_state["page"] = "استرجاع كلمة المرور"
        st.rerun()

def check_email_exists(email):
    users_ref = db.collection('firefighter_data')  # افتراضاً أن مجموعة المستخدمين اسمها 'users'
    user_docs = users_ref.where('email', '==', email).get()
    
    # إذا تم العثور على مستند مستخدم، يعني أن البريد الإلكتروني موجود
    if len(user_docs) > 0:
        return True
    else:
        return False

def password_reset_page():
    st.markdown("""
    <style>
    div.stColumn {
        display: flex;
        justify-content: center; /* توسيط أفقي */
        align-items: center; /* توسيط عمودي */
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.form("reset_password_form"):
        email = st.text_input("أدخل بريدك الإلكتروني")
        
        col1, col2 = st.columns(2)
        with col1:
            # زر "العودة لتسجيل الدخول" داخل الفورم
            back_to_login_button = st.form_submit_button("العودة لتسجيل الدخول")
            
        with col2:
            # زر "إرسال رابط إعادة التعيين"
            reset_button = st.form_submit_button("إرسال رابط إعادة التعيين")
    
    # التحقق من الضغط على زر "إرسال رابط إعادة التعيين"
    if reset_button:
        # التحقق من صحة البريد الإلكتروني
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            st.error("⚠ صيغة البريد الإلكتروني غير صحيحة.")
        else:
            if check_email_exists(email):
                try:
                    # إرسال رابط إعادة تعيين كلمة المرور
                    auth.send_password_reset_email(email)
                    st.success("✅ تم إرسال رابط إعادة تعيين كلمة المرور بنجاح.")
                except Exception as e:
                    st.error(f"⚠ حدث خطأ أثناء إرسال الرابط: {str(e)}")
            else:
                st.error("⚠ لم يتم العثور على حساب مرتبط بهذا البريد الإلكتروني.")

    # التحقق من الضغط على زر "العودة لتسجيل الدخول"
    if back_to_login_button:
        st.session_state["page"] = "تسجيل الدخول"
        st.rerun()



def detection_page():
    set_background("Background2.jpg")
    st.markdown("""
    <div class="instructions">
        <h3>تعليمات استخدام الكاميرا</h3>
        <ul>
            <li>تأكد من إضاءة المكان بشكل جيد</li>
            <li>قف على بعد مناسب من الكاميرا (1-2 متر)</li>
            <li>تأكد من ظهور جميع معدات الوقاية في إطار الكاميرا</li>
            <li>انتظر حتى يتم التعرف على جميع المعدات</li>
            <li>يمكنك إيقاف العملية في أي وقت بالضغط على زر الإيقاف</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        start_button = st.button("✅ بدء التحقق", use_container_width=True)
    with col2:
        stop_button = st.button("🛑 إيقاف العملية", use_container_width=True)

    status_text = st.empty()
    
    if start_button:
        model_path = "safety_equipment_best.pt"
        @st.cache_resource
        def load_yolo_model(model_path: str):
            """Cached YOLO model loading"""
            try:
                return YOLO(model_path)
            except Exception as e:
                st.error("فشل تحميل نموذج YOLO")
                return None
        
        model=load_yolo_model(model_path)
        
        class_names_arabic = {
            "Helmet": "خوذة",
            "Gloves": "قفازات",
            "boots": "حذاء",
            "Fire_Suit": "بدلة الحريق",
            "SCBA": "جهاز التنفس"
        }
        
        cap = cv2.VideoCapture(0)
        stframe = st.empty()
        
        if not cap.isOpened():
            st.error("❌ لا يمكن فتح الكاميرا. تأكد من توصيلها.")
        else:
            stop = False
            while not stop:
                ret, frame = cap.read()
                if not ret:
                    st.warning("⚠️ لم يتم التقاط أي إطار. تأكد من أن الكاميرا تعمل.")
                    break

                results = model(frame)
                annotated_frame = results[0].plot()
                detected_classes = [results[0].names[int(box.cls)] for box in results[0].boxes]
                
                missing_equipment = [eq for eq in class_names_arabic.keys() if eq not in detected_classes]
                missing_equipment_arabic = [class_names_arabic[eq] for eq in missing_equipment]
                
                if missing_equipment_arabic:
                    missing_text = "، ".join(missing_equipment_arabic) + " مفقودة"
                    status_text.error(f"🚨 {missing_text}")
                else:
                    status_text.success("✅ جميع معدات الوقاية الشخصية مكتملة!")

                stframe.image(cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB), channels="RGB", use_container_width=True)
                
                if stop_button:
                    stop = True
                    break
            
            cap.release()
            st.success("✅ تم إيقاف الكاميرا بنجاح!")


def Upload_page():
    set_background("Background2.jpg")
    # تحميل النموذج
    model_path = "safety_equipment_best.pt"
    @st.cache_resource
    def load_yolo_model(model_path: str):
        """Cached YOLO model loading"""
        try:
            return YOLO(model_path)
        except Exception as e:
            st.error("فشل تحميل نموذج YOLO")
            return None
    
    model = load_yolo_model(model_path)
    st.markdown('<h2 style="font-size: 32px; color: black; text-align: center;">الكشف عن معدات الوقاية الشخصية</h2>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="file-upload-container"><h3>رفع صورة</h3></div>', unsafe_allow_html=True)
        uploaded_image = st.file_uploader("", type=["jpg", "jpeg", "png"], key="image")

    with col2:
        st.markdown('<div class="file-upload-container"><h3>رفع فيديو</h3></div>', unsafe_allow_html=True)
        uploaded_video = st.file_uploader("", type=["mp4", "avi", "mov"], key="video")
        
    # التحقق من صيغة الصورة
    if uploaded_image and uploaded_image.type.split('/')[1] not in ["jpeg", "png", "jpg"]:
        st.error("❌ صيغة الصورة غير مدعومة. الرجاء رفع صورة بصيغة JPG أو JPEG أو PNG.")
    elif uploaded_image:
        st.subheader("نتيجة الكشف عن الصورة")
        img = Image.open(uploaded_image)
        img_np = np.array(img)  
        results = model(img_np)
        annotated_frame = results[0].plot()  
        st.image(annotated_frame, caption="نتيجة الكشف", use_container_width=True)
        st.success("✅ تم اكتشاف معدات الوقاية في الصورة!")

    # التحقق من صيغة الفيديو
    if uploaded_video and uploaded_video.type.split('/')[1] not in ["mp4", "avi", "mov"]:
        st.error("❌ صيغة الفيديو غير مدعومة. الرجاء رفع فيديو بصيغة MP4 أو AVI أو MOV.")
    elif uploaded_video:
        st.subheader("نتيجة الكشف عن الفيديو")

        # حفظ الفيديو مؤقتًا لقراءته من OpenCV
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        tfile.write(uploaded_video.read())
        video_path = tfile.name

        cap = cv2.VideoCapture(video_path)

        stframe = st.empty()  # عنصر فارغ لعرض الفيديو مباشرة

        with st.spinner(" جارٍ معالجة الفيديو، الرجاء الانتظار..."):
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                results = model(frame)
                annotated_frame = results[0].plot()

                # عرض الفيديو مباشرة بعد الكشف
                stframe.image(annotated_frame, channels="BGR", use_container_width=True)
        cap.release()
        st.success("✅ تم اكتشاف معدات الوقاية في الفيديو!")


def Quiz_page():
    set_background("Background2.jpg")
    st.markdown("""
        <style>
        .stButton > button {
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)

    # دالة لجلب أسئلة الاختبار
    def fetch_quiz_questions(quiz_id):
        try:
            # جلب الأسئلة من قاعدة البيانات بناءً على Quiz_ID
            questions_ref = db.collection('Question_Bank').where("Quiz_ID", "==", quiz_id)
            docs = questions_ref.stream()
            quiz_data = []

            for doc in docs:
                data = doc.to_dict()
                quiz_data.append({
                    "question_id": doc.id,
                    "question": data.get("Question"),
                    "options": data.get("Options", []),
                    "correct_answer": data.get("Correct_Answer")
                })

            # التحقق إذا لم يتم العثور على أي أسئلة
            if not quiz_data:
                st.error("لا توجد أسئلة متوفرة لهذا الاختبار ، ستتوفر قريبًا.")
                return None

            return quiz_data

        except Exception as e:
            # معالجة أي خطأ في جلب البيانات
            st.error("حدث خطأ في جلب الأسئلة.")
            return None

    def save_or_update_progress(firefighter_id, quiz_id, score):
        now = datetime.now()
        today_date = now.date().strftime('%Y-%m-%d')
        progress_ref = db.collection('Progress_Tracking')

        existing_progress = progress_ref.where("FirefighterID", "==", firefighter_id).stream()

        found = False
        for doc in existing_progress:
            progress_date = doc.to_dict()["Progress_Date"]
            if progress_date == today_date:
                doc_ref = progress_ref.document(doc.id)
                doc_ref.update({
                    "Quiz_Score": score,
                    "Quiz_ID": quiz_id,
                    "Progress_Date": today_date
                })
                found = True
                break

        if not found:
            progress_id = str(uuid.uuid4())
            progress_ref.document(progress_id).set({
                "Progress_ID": progress_id,
                "FirefighterID": firefighter_id,
                "Quiz_ID": quiz_id,
                "Quiz_Score": score,
                "Progress_Date": today_date,
                "Timer_Result": 0
            })

    # دالة لتهيئة حالة الجلسة
    def initialize_session_state():
        if "submitted_answers" not in st.session_state:
            st.session_state.submitted_answers = {}
        if "all_attempts" not in st.session_state:
            st.session_state.all_attempts = {}
        if "quiz_started" not in st.session_state:
            st.session_state.quiz_started = False
        if "current_question" not in st.session_state:
            st.session_state.current_question = 0
        if "quiz_completed" not in st.session_state:
            st.session_state.quiz_completed = False

    # دالة لعرض ملخص الاختبار
    def show_quiz_summary():
        questions = st.session_state.quiz_questions
        total_questions = len(questions)
        correct_count = sum(1 for q in questions 
                           if q['question_id'] in st.session_state.submitted_answers 
                           and st.session_state.submitted_answers[q['question_id']] == q['correct_answer'])

        st.markdown("### 📊 ملخص الاختبار")
        st.markdown(f"*الدرجة النهائية:* {correct_count}/{total_questions}")
        st.markdown("### 📝 تفاصيل الإجابات")
        for i, question in enumerate(questions):
            question_id = question['question_id']
            submitted_answer = st.session_state.submitted_answers.get(question_id)

            st.markdown(f"*السؤال {i+1}:* {question['question']}")
            if submitted_answer:
                if submitted_answer == question['correct_answer']:
                    st.success(f"✅ إجابتك صحيحة: {submitted_answer}")
                else:
                    st.error(f"❌ إجابتك: {submitted_answer}")
                    st.success(f"✅ الإجابة الصحيحة: {question['correct_answer']}")
            st.markdown("---")

    # تهيئة حالة الجلسة
    initialize_session_state()

    firefighter_id = st.session_state.get("firefighter_id")

    # اختيار الاختبار
    quiz_id = st.selectbox("🔹 اختر الاختبار:", ["quiz_001", "quiz_002", "quiz_003"])

    if st.button("ابدأ الاختبار", type="primary"):
        quiz_questions = fetch_quiz_questions(quiz_id)
        if quiz_questions is None:
            return

        st.session_state.quiz_questions = quiz_questions
        st.session_state.current_question = 0
        st.session_state.quiz_started = True
        st.session_state.submitted_answers = {}
        st.session_state.quiz_completed = False

    if st.session_state.quiz_started:
        if st.session_state.quiz_completed:
            show_quiz_summary()
            if st.button("🔄 ابدأ اختبار جديد", type="primary"):
                st.session_state.quiz_started = False
                st.rerun()
            return

        current_index = st.session_state.current_question
        questions = st.session_state.quiz_questions
        total_questions = len(questions)

        if current_index < total_questions:
            question_data = questions[current_index]
            question_id = question_data['question_id']

            st.progress(current_index / total_questions)  # شريط التقدم

            st.markdown(f'<h3 class="question-text">السؤال {current_index + 1}: {question_data["question"]}</h3>', unsafe_allow_html=True)

            # عرض الخيارات
            for i, option in enumerate(question_data['options']):
                if st.button(option, 
                           key=f"option_{current_index}_{i}", 
                           use_container_width=True, 
                           type="primary"):
                    st.session_state.submitted_answers[question_id] = option
                    if current_index < total_questions - 1:
                        st.session_state.current_question += 1
                    st.rerun()

            # أزرار التنقل
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("⬅ السابق", 
                           disabled=current_index == 0, 
                           type="primary"):
                    st.session_state.current_question -= 1
                    st.rerun()
            with col2:
                if st.button("➡ التالي", 
                           disabled=current_index >= total_questions - 1,
                           type="primary",
                           key="next_button"):
                    st.session_state.current_question += 1
                    st.session_state.submitted_answers[question_id] = "selected"
                    st.rerun()

            # عرض زر الإنهاء عند الإجابة على جميع الأسئلة
            answered_all = all(q['question_id'] in st.session_state.submitted_answers 
                             for q in st.session_state.quiz_questions)
            if answered_all:
                if st.button("✅ إنهاء الاختبار", type="primary"):
                    correct_count = sum(1 for q in questions 
                                     if q['question_id'] in st.session_state.submitted_answers 
                                     and st.session_state.submitted_answers[q['question_id']] == q['correct_answer'])
                    save_or_update_progress(firefighter_id, quiz_id, correct_count)
                    st.session_state.quiz_completed = True
                    st.rerun()


def Timer_page():
    set_background("Background2.jpg")

    firefighter_id = st.session_state.get("firefighter_id") 
    if not firefighter_id:
        st.warning("⚠ لم يتم العثور على معرف رجل الإطفاء.")
        return

    def save_or_update_progress(firefighter_id, elapsed_time):
        today = datetime.today().strftime('%Y-%m-%d')
        progress_ref = db.collection('Progress_Tracking')
        existing_progress = progress_ref.where("FirefighterID", "==", firefighter_id).where("Progress_Date", "==", today).stream()

        found = False
        for doc in existing_progress:
            doc_ref = progress_ref.document(doc.id)
            doc_ref.update({
                "Timer_Result": elapsed_time,
                "Progress_Date": today  
            })
            found = True

        # إذا لم يتم العثور على أي سجلات، نقوم بإنشاء سجل جديد
        if not found:
            progress_id = str(uuid.uuid4())
            progress_ref.document(progress_id).set({
                "Progress_ID": progress_id,
                "FirefighterID": firefighter_id,
                "Timer_Result": elapsed_time,
                "Progress_Date": today, 
                "Quiz_ID": "",  
                "Quiz_Score": 0 
            })

    # تخزين حالة المؤقت في session_state
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None
    if 'elapsed_time' not in st.session_state:
        st.session_state.elapsed_time = 0
    if 'running' not in st.session_state:
        st.session_state.running = False
    if 'timer_result' not in st.session_state:
        st.session_state.timer_result = None
    if 'stopped' not in st.session_state:
        st.session_state.stopped = False  

    # دالة لتحديث الوقت
    def update_timer():
        if st.session_state.running:
            current_time = time.time()
            st.session_state.elapsed_time += current_time - st.session_state.start_time
            st.session_state.start_time = current_time

    # دالة لتنسيق الوقت لعرضه كـ 00:00 (دقائق:ثواني)
    def format_time(seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    # عرض الوقت في منتصف الصفحة باستخدام st.empty()
    time_placeholder = st.empty()

    # عرض الأزرار في خط واحد أسفل المؤقت
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        start_button = st.button('   البدء')
    with col2:
        pause_button = st.button('إيقاف مؤقت')
    with col3:
        stop_button = st.button('توقف')
    with col4:
        reset_button = st.button('إعادة التشغيل')

    # زر لتشغيل المؤقت
    if start_button:
        # إذا تم إيقاف المؤقت بالكامل (بعد الضغط على Stop) 
        if st.session_state.stopped:
            st.session_state.elapsed_time = 0
            st.session_state.stopped = False
        st.session_state.start_time = time.time()
        st.session_state.running = True

    # زر لإيقاف المؤقت مؤقتًا (Pause)
    if pause_button:
        if st.session_state.running:
            update_timer()
            st.session_state.running = False

    # زر للتوقف الكامل (Stop)
    if stop_button:
        if st.session_state.running:
            update_timer()
            st.session_state.running = False
        st.session_state.timer_result = st.session_state.elapsed_time
        st.session_state.stopped = True  

        # إذا كان معرف الفايرفايتر متاحًا، نقوم بحفظ النتائج في Firestore
        save_or_update_progress(firefighter_id, st.session_state.timer_result)

    # زر لإعادة تعيين المؤقت
    if reset_button:
        st.session_state.elapsed_time = 0
        st.session_state.start_time = None
        st.session_state.running = False
        st.session_state.timer_result = None
        st.session_state.stopped = False

    # تحديث الوقت بشكل تفاعلي أثناء تشغيل المؤقت
    while st.session_state.running:
        update_timer()
        formatted_time = format_time(st.session_state.elapsed_time)
        time_placeholder.markdown(f"<div class='timer-text'>{formatted_time}</div>", unsafe_allow_html=True)
        time.sleep(0.1)

    # عرض الوقت الحالي إذا كان المؤقت متوقفاً
    formatted_time = format_time(st.session_state.elapsed_time)
    time_placeholder.markdown(f"<div class='timer-text'>{formatted_time}</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="instructions">
        <h3>تعليمات استخدام المؤقت</h3>
        <ul>
            <li>هذا المؤقت مخصص لحساب الوقت الذي يحتاجه رجل الإطفاء لارتداء معدات الحماية بالكامل.</li>   
            <li>اضغط على زر البدء عند جاهزيتك للتمرين</li>
            <li>يمكنك إيقاف المؤقت مؤقتاً في أي وقت</li>
            <li>عند الانتهاء، اضغط على زر التوقف لحفظ النتيجة</li>
            <li>سيتم حفظ نتيجتك تلقائياً في سجل التقدم</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)




def Progress_page():
    set_background("Background2.jpg")

    # ✅ استدعاء بيانات التقدم بناءً على FirefighterID
    def fetch_progress_data(firefighter_id):
        try:
            progress_ref = db.collection('Progress_Tracking').where("FirefighterID", "==", firefighter_id)
            docs = progress_ref.stream()
            progress_data = [doc.to_dict() for doc in docs]
            if not progress_data:
                st.warning("لا توجد بيانات متعلقة بالمعرف المدخل.")
            return pd.DataFrame(progress_data)
        except Exception as e:
            st.error(f"حدث خطأ أثناء استرداد البيانات: {e}")
            return pd.DataFrame()

    # ✅ الأيام وترتيبها
    DAYS_TRANSLATION = {
        "Sunday": "الأحد",
        "Monday": "الإثنين",
        "Tuesday": "الثلاثاء",
        "Wednesday": "الأربعاء",
        "Thursday": "الخميس",
        "Friday": "الجمعة",
        "Saturday": "السبت"
    }

    def translate_day(day):
        return DAYS_TRANSLATION.get(day, "")

    def format_day_of_week(df):
        df = df.dropna(subset=["Progress_Date"])
        df["Progress_Date"] = pd.to_datetime(df["Progress_Date"])
        df["Day"] = df["Progress_Date"].dt.day_name().map(translate_day)
        df["Day_Num"] = df["Progress_Date"].dt.day
        df["Day_Display"] = df.apply(lambda row: f"{row['Day']} - {row['Day_Num']}", axis=1)
        return df.sort_values("Progress_Date", ascending=False)

    # ✅ رسم المخططات 
    def create_bar_chart(df, x_column, y_column, title, y_label, y_range=None):
        fig = px.bar(df, x=x_column, y=y_column, title=title, text=y_column, labels={x_column: "اليوم", y_column: y_label})
        fig.update_layout(xaxis=dict(autorange="reversed"))
        if y_range:
            fig.update_layout(yaxis=dict(range=y_range))

        fig.update_traces(marker_color="#218838")  # اللون الزيتي

        return fig

    # ✅ التايمر رزلت والكويز سكور
    def plot_timer_result(df):
        return create_bar_chart(df, "Day_Display", "Timer_Result", "التقدم بالوقت (بالثواني) خلال أيام الأسبوع", "الوقت (بالثواني)", [0, df["Timer_Result"].max() + 1])

    def plot_quiz_score(df):
        return create_bar_chart(df, "Day_Display", "Quiz_Score", "تقدم درجات الكويز خلال أيام الأسبوع", "الدرجة", [0, 10])

    st.markdown(
        "<h1 style='font-size: 50px; text-align: center;'>تتبع التقدم</h1>",
        unsafe_allow_html=True
    )

    # ✅ أخذ معرف الفايرفايتر من الجلسة بعد تسجيل الدخول
    firefighter_id = st.session_state.get("firefighter_id", None)
    user_name = st.session_state.get("user_name", "")

    # ✅ عرض المعرف والاسم في أعلى يمين الصفحة
    if firefighter_id and user_name:
        st.markdown(
            f"""
            <div style="text-align: right; font-size: 20px; font-weight: bold; margin-top: 20px;">
                <p>رقم المعرف: {firefighter_id}</p>
                <p>الاسم: {user_name}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    if firefighter_id:
        # جلب البيانات بناءً على المعرف
        data = fetch_progress_data(firefighter_id)

        if data.empty:
            st.warning("لم يتم العثور على بيانات.")
        else:
            # إضافة اليوم
            data = format_day_of_week(data)

            # عرض المخططات
            col1, col2 = st.columns(2)

            with col1:
                st.plotly_chart(plot_timer_result(data), use_container_width=True)

            with col2:
                st.plotly_chart(plot_quiz_score(data), use_container_width=True)
    else:
        st.error("⚠ الرجاء تسجيل الدخول لعرض التقدم.")


# Main App Logic
if st.session_state["logged_in"]:
    sidebar_navigation()
    if st.session_state["page"] == "Detection":
        detection_page()
    elif st.session_state["page"] == "Upload":
        Upload_page()
    elif st.session_state["page"] == "Quiz":
        Quiz_page()
    elif st.session_state["page"] == "Timer":
        Timer_page()  
    elif st.session_state["page"] == "Progress":
        Progress_page()
else:
    if st.session_state["page"] == "تسجيل الدخول":
        login_page()
    elif st.session_state["page"] == "إنشاء حساب جديد":
        signup_page()
    elif st.session_state["page"] == "استرجاع كلمة المرور":  
        password_reset_page()
    else:
        home_page()