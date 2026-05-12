import streamlit as st
import pandas as pd
import pdfplumber
import re

st.set_page_config(page_title="One Way Tours - BSP Auditor", layout="wide")

st.title("✈️ نظام مطابقة تذاكر BSP والحسابات")
st.info("قم برفع ملفات PDF (ملف الحسابات وملف الـ BSP) لاستخراج الاختلافات فوراً.")

# --- دالة استخراج البيانات من ملف الحسابات ---
def process_acc(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        all_data = []
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                # محاولة العثور على رؤوس الأعمدة الصحيحة
                df = pd.DataFrame(table[1:], columns=table[0])
                all_data.append(df)
        final_df = pd.concat(all_data)
        # تنظيف أرقام التذاكر من المسافات
        if 'Ticket No' in final_df.columns:
            final_df['Ticket No'] = final_df['Ticket No'].astype(str).str.replace(r'\s+', '', regex=True)
        return final_df

# --- دالة استخراج البيانات من ملف BSP ---
def process_bsp(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
        
        # البحث عن نمط التذاكر (رقم الطيران + TKTT + رقم التذكرة + التاريخ + المبلغ)
        pattern = r"(\d{3})\sTKTT\s(\d{10})\s(\d{2}\w{3}\d{2}).*?([\d,]+\.\d{2})"
        matches = re.findall(pattern, text)
        
        df = pd.DataFrame(matches, columns=['AirCode', 'Ticket', 'Date', 'Net_BSP'])
        df['Net_BSP'] = df['Net_BSP'].str.replace(',', '').astype(float)
        return df

# --- واجهة رفع الملفات ---
col1, col2 = st.columns(2)
with col1:
    acc_file = st.file_uploader("ارفع ملف الحسابات (acc - bsp.pdf)", type="pdf")
with col2:
    bsp_file = st.file_uploader("ارفع ملف الـ BSP الرسمي", type="pdf")

if acc_file and bsp_file:
    with st.spinner('جاري مراجعة البيانات...'):
        df_acc = process_acc(acc_file)
        df_bsp = process_bsp(bsp_file)

        # تحويل الأعمدة لنصوص لضمان دقة الربط
        df_acc['Ticket No'] = df_acc['Ticket No'].astype(str)
        df_bsp['Ticket'] = df_bsp['Ticket'].astype(str)

        # 1. المفقود في الحسابات (موجود في BSP فقط)
        missing_in_acc = df_bsp[~df_bsp['Ticket'].isin(df_acc['Ticket No'])]

        # 2. المفقود في BSP (موجود في الحسابات فقط)
        missing_in_bsp = df_acc[~df_acc['Ticket No'].isin(df_bsp['Ticket'])]

        # 3. فروقات ADM/ACM (الموجود في الاثنين ولكن السعر مختلف)
        merged = pd.merge(df_acc, df_bsp, left_on='Ticket No', right_on='Ticket')
        # تنظيف وتحويل مبالغ الحسابات لرقم عشري
        if 'Net to Airfine' in merged.columns:
            merged['Net to Airfine'] = merged['Net to Airfine'].str.replace(',', '').astype(float)
            merged['Diff'] = merged['Net_BSP'] - merged['Net to Airfine']
            discrepancies = merged[merged['Diff'].abs() > 0.1] # تجاهل الفروقات البسيطة جداً

        # --- عرض النتائج في تبويبات ---
        st.divider()
        t1, t2, t3 = st.tabs(["❌ مفقود في الحسابات", "🔍 مفقود في BSP", "💰 فروقات المبالغ (ADM/ACM)"])
        
        with t1:
            st.warning(f"تم العثور على {len(missing_in_acc)} تذكرة غير مسجلة في حساباتك")
            st.dataframe(missing_in_acc)
        
        with t2:
            st.info(f"تم العثور على {len(missing_in_bsp)} تذكرة مسجلة لديك ولم تظهر في الـ BSP")
            st.dataframe(missing_in_bsp[['Ticket No', 'Passenger', 'Net to Airfine']])
            
        with t3:
            if 'discrepancies' in locals() and not discrepancies.empty:
                st.error("تنبيه: هناك اختلافات مالية في التذاكر التالية")
                st.dataframe(discrepancies[['Ticket No', 'Net to Airfine', 'Net_BSP', 'Diff']])
            else:
                st.success("لا توجد فروقات مالية في التذاكر المشتركة!")