import streamlit as st
import pandas as pd
import pdfplumber
import re

st.set_page_config(page_title="One Way Tours - BSP Auditor", layout="wide")

st.title("✈️ نظام مطابقة تذاكر BSP والحسابات")

def process_acc(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        all_data = []
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                df = pd.DataFrame(table)
                all_data.append(df)
        
        if not all_data:
            return None
            
        final_df = pd.concat(all_data, ignore_index=True)
        
        # البحث الذكي عن رأس الجدول وتجنب الأخطاء
        ticket_col_index = None
        header_row_index = None
        
        for index, row in final_df.iterrows():
            # تحويل الصف لنصوص مع تجاهل القيم الفارغة
            row_values = [str(val) if val is not None else "" for val in row]
            for i, cell in enumerate(row_values):
                if 'Ticket' in cell:
                    header_row_index = index
                    ticket_col_index = i
                    break
            if header_row_index is not None: break
            
        if header_row_index is not None:
            # تعيين الصف الذي وجدنا فيه كلمة Ticket كعنوان للأعمدة
            final_df.columns = final_df.iloc[header_row_index]
            final_df = final_df.iloc[header_row_index+1:].reset_index(drop=True)
            return final_df
        return None

def process_bsp(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""
        # نمط البحث عن التذاكر في ملف BSP
        pattern = r"(\d{3})\sTKTT\s(\d{10})"
        matches = re.findall(pattern, text)
        return pd.DataFrame(matches, columns=['AirCode', 'Ticket'])

acc_file = st.file_uploader("ارفع ملف الحسابات (PDF)", type="pdf")
bsp_file = st.file_uploader("ارفع ملف الـ BSP (PDF)", type="pdf")

if acc_file and bsp_file:
    with st.spinner('جاري معالجة الملفات...'):
        df_acc = process_acc(acc_file)
        df_bsp = process_bsp(bsp_file)

        if df_acc is not None and not df_bsp.empty:
            # تنظيف أرقام التذاكر من الفراغات
            acc_ticket_col = [c for c in df_acc.columns if c and 'Ticket' in str(c)][0]
            df_acc['Ticket_Clean'] = df_acc[acc_ticket_col].astype(str).str.replace(r'\s+', '', regex=True)
            df_bsp['Ticket'] = df_bsp['Ticket'].astype(str).str.replace(r'\s+', '', regex=True)

            # المقارنة: تذاكر في BSP وغير موجودة في الحسابات
            missing_in_acc = df_bsp[~df_bsp['Ticket'].isin(df_acc['Ticket_Clean'])]
            
            st.divider()
            st.subheader("📊 ملخص الفحص")
            
            col1, col2 = st.columns(2)
            col1.metric("تذاكر في BSP", len(df_bsp))
            col2.metric("تذاكر مفقودة من حساباتك", len(missing_in_acc))

            st.subheader("❌ التذاكر المفقودة (موجودة في BSP فقط)")
            if not missing_in_acc.empty:
                st.dataframe(missing_in_acc, use_container_width=True)
            else:
                st.success("ممتاز! جميع تذاكر BSP مسجلة في حساباتك.")
        else:
            st.error("تعذر قراءة البيانات. تأكد أن الملفات تحتوي على جداول واضحة.")
