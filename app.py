import streamlit as st
import pandas as pd
import pdfplumber
import re

st.set_page_config(page_title="One Way Tours - Auditor", layout="wide")
st.title("✈️ One Way Tours - نظام المطابقة الاحترافي")

def extract_all_numbers(pdf_file):
    all_text = ""
    tickets = set()
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                all_text += text + " "
                # البحث عن أي تتابع للأرقام بين 10 و 14 رقم
                found = re.findall(r'\d{10,14}', text)
                for t in found:
                    tickets.add(t[-10:]) # نأخذ آخر 10 أرقام دائماً
    return tickets, all_text

acc_file = st.file_uploader("ارفع ملف الحسابات", type="pdf")
bsp_file = st.file_uploader("ارفع ملف الـ BSP", type="pdf")

if acc_file and bsp_file:
    with st.spinner('جاري المسح العميق للملفات...'):
        acc_tickets, acc_raw = extract_all_numbers(acc_file)
        bsp_tickets, bsp_raw = extract_all_numbers(bsp_file)
        
        if bsp_tickets:
            missing = [t for t in bsp_tickets if t not in acc_tickets]
            
            st.divider()
            col1, col2, col3 = st.columns(3)
            col1.metric("تذاكر تم اكتشافها في BSP", len(bsp_tickets))
            col2.metric("تذاكر مسجلة بالحسابات", len(acc_tickets))
            col3.metric("تذاكر مفقودة", len(missing))
            
            if missing:
                st.subheader("❌ قائمة التذاكر المفقودة")
                df_missing = pd.DataFrame(missing, columns=["رقم التذكرة"])
                st.dataframe(df_missing, use_container_width=True)
                
                csv = df_missing.to_csv(index=False).encode('utf-8-sig')
                st.download_button("تحميل التقرير CSV", csv, "missing_tickets.csv")
            else:
                st.success("✅ تطابق كامل! كل التذاكر مسجلة.")
        else:
            st.error("⚠️ لم يتم العثور على أرقام في ملف BSP.")
            with st.expander("معاينة النص الذي رآه البرنامج في ملف BSP (للتصحيح)"):
                st.write(bsp_raw[:1000] if bsp_raw else "الملف فارغ تماماً أو عبارة عن صورة (Scanner)")
