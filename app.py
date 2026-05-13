import streamlit as st
import pandas as pd
import pdfplumber
import re

st.set_page_config(page_title="One Way Tours - Auditor", layout="wide")
st.title("✈️ نظام المطابقة الذكي - One Way Tours")

def extract_tickets_from_pdf(pdf_file):
    tickets = set()
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                # البحث عن أي رقم مكون من 10 أرقام متتالية (نمط التذكرة)
                found = re.findall(r'\b\d{10}\b', text)
                tickets.update(found)
    return tickets

acc_file = st.file_uploader("ارفع ملف الحسابات (PDF)", type="pdf")
bsp_file = st.file_uploader("ارفع ملف الـ BSP (PDF)", type="pdf")

if acc_file and bsp_file:
    with st.spinner('جاري المسح الشامل للملفات...'):
        # استخراج كل أرقام التذاكر من الملفين
        acc_tickets = extract_tickets_from_pdf(acc_file)
        bsp_tickets = extract_tickets_from_pdf(bsp_file)
        
        if bsp_tickets:
            # التذاكر الموجودة في BSP وغير موجودة في الحسابات
            missing_in_acc = [t for t in bsp_tickets if t not in acc_tickets]
            
            st.divider()
            col1, col2, col3 = st.columns(3)
            col1.metric("تذاكر الـ BSP", len(bsp_tickets))
            col2.metric("تذاكر الحسابات", len(acc_tickets))
            col3.metric("تذاكر مفقودة", len(missing_in_acc))
            
            st.subheader("❌ التذاكر الموجودة في BSP ومفقودة من حساباتك")
            if missing_in_acc:
                df_missing = pd.DataFrame(missing_in_acc, columns=["رقم التذكرة المفقودة"])
                st.table(df_missing)
                
                # إضافة زر تحميل النتيجة
                csv = df_missing.to_csv(index=False).encode('utf-8-sig')
                st.download_button("تحميل قائمة النواقص CSV", csv, "missing_tickets.csv", "text/csv")
            else:
                st.success("🎉 تطابق كامل! كل تذاكر الـ BSP مسجلة في حساباتك.")
        else:
            st.error("لم أتمكن من استخراج أي أرقام تذاكر من ملف الـ BSP. تأكد من جودة الملف.")
