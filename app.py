import streamlit as st
import pandas as pd
import pdfplumber
import re

st.set_page_config(page_title="One Way Tours - Auditor", layout="wide")
st.title("✈️ One Way Tours - نظام المطابقة الذكي")

def extract_tickets_from_pdf(pdf_file):
    tickets = set()
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                # البحث عن أي رقم مكون من 10 أو 13 رقم (لتغطية كافة أشكال التذاكر)
                found = re.findall(r'\b\d{10,13}\b', text)
                for t in found:
                    # نأخذ آخر 10 أرقام دائماً لتوحيد الشكل
                    tickets.add(t[-10:])
    return tickets

acc_file = st.file_uploader("(PDF) ارفع ملف الحسابات", type="pdf")
bsp_file = st.file_uploader("(PDF) BSP ارفع ملف الـ", type="pdf")

if acc_file and bsp_file:
    with st.spinner('جاري فحص التذاكر بدقة...'):
        acc_tickets = extract_tickets_from_pdf(acc_file)
        bsp_tickets = extract_tickets_from_pdf(bsp_file)
        
        if bsp_tickets:
            missing_in_acc = [t for t in bsp_tickets if t not in acc_tickets]
            
            st.divider()
            c1, c2, c3 = st.columns(3)
            c1.metric("إجمالي تذاكر BSP", len(bsp_tickets))
            c2.metric("تذاكر مسجلة بالحسابات", len(acc_tickets))
            c3.metric("تذاكر مفقودة", len(missing_in_acc))
            
            if missing_in_acc:
                st.subheader("❌ التذاكر المفقودة من الحسابات")
                df_missing = pd.DataFrame(missing_in_acc, columns=["رقم التذكرة"])
                st.table(df_missing)
                
                csv = df_missing.to_csv(index=False).encode('utf-8-sig')
                st.download_button("تحميل القائمة CSV", csv, "missing_tickets.csv", "text/csv")
            else:
                st.success("✅ مبروك! كل تذاكر الـ BSP موجودة في حساباتك.")
        else:
            st.error("لم أتمكن من العثور على أرقام تذاكر. تأكد من أن الملف ليس 'صورة' (Scanner).")
