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
        
        # البحث التلقائي عن السطر الذي يحتوي على كلمة Ticket
        ticket_col = None
        for index, row in final_df.iterrows():
            row_str = row.astype(str).values
            for i, cell in enumerate(row_str):
                if 'Ticket' in cell:
                    final_df.columns = final_df.iloc[index]
                    final_df = final_df.iloc[index+1:].reset_index(drop=True)
                    ticket_col = cell
                    break
            if ticket_col: break
            
        return final_df

def process_bsp(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
        pattern = r"(\d{3})\sTKTT\s(\d{10})\s(\d{2}\w{3}\d{2}).*?([\d,]+\.\d{2})"
        matches = re.findall(pattern, text)
        return pd.DataFrame(matches, columns=['AirCode', 'Ticket', 'Date', 'Net_BSP'])

acc_file = st.file_uploader("ارفع ملف الحسابات", type="pdf")
bsp_file = st.file_uploader("ارفع ملف الـ BSP", type="pdf")

if acc_file and bsp_file:
    df_acc = process_acc(acc_file)
    df_bsp = process_bsp(bsp_file)

    if df_acc is not None:
        # محاولة إيجاد اسم العمود الصحيح لرقم التذكرة
        acc_col = [c for c in df_acc.columns if 'Ticket' in str(c)]
        price_col = [c for c in df_acc.columns if 'Net' in str(c) or 'Payable' in str(c)]
        
        if acc_col:
            df_acc['Ticket_Clean'] = df_acc[acc_col[0]].astype(str).str.replace(r'\s+', '', regex=True)
            df_bsp['Ticket'] = df_bsp['Ticket'].astype(str)

            # المقارنة
            missing_in_acc = df_bsp[~df_bsp['Ticket'].isin(df_acc['Ticket_Clean'])]
            
            st.divider()
            st.subheader("نتائج الفحص")
            t1, t2 = st.tabs(["❌ مفقود في الحسابات", "✅ البيانات المطابقة"])
            
            with t1:
                st.warning(f"تذاكر موجودة في BSP وغير مسجلة عندك: {len(missing_in_acc)}")
                st.dataframe(missing_in_acc)
            with t2:
                st.success("تم الربط بنجاح، يمكنك الآن مراجعة باقي البيانات")
        else:
            st.error("لم أتمكن من العثور على عمود 'Ticket No' في ملف الحسابات. تأكد من جودة الملف.")
