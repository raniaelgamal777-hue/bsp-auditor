import streamlit as st
import pandas as pd
import pdfplumber
import re

st.set_page_config(page_title="One Way Tours - Financial Auditor", layout="wide")
st.title("✈️ One Way Tours - تقرير مطابقة القيم المالية")

def extract_financial_data(pdf_file):
    data = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                # تقسيم النص إلى أسطر للبحث بدقة
                lines = text.split('\n')
                for line in lines:
                    # البحث عن رقم التذكرة (10 أرقام)
                    ticket_match = re.search(r'\d{10}', line)
                    # البحث عن مبالغ مالية (أرقام بها فواصل عشرية ونقطة)
                    price_match = re.search(r'[\d,]+\.\d{2}', line)
                    
                    if ticket_match:
                        t_no = ticket_match.group()[-10:]
                        price = price_match.group() if price_match else "0.00"
                        data.append({"Ticket": t_no, "Amount": price})
    return pd.DataFrame(data)

acc_file = st.file_uploader("ارفع ملف الحسابات (PDF)", type="pdf")
bsp_file = st.file_uploader("ارفع ملف الـ BSP (PDF)", type="pdf")

if acc_file and bsp_file:
    with st.spinner('جاري تحليل البيانات المالية...'):
        df_acc = extract_financial_data(acc_file)
        df_bsp = extract_financial_data(bsp_file)
        
        # تنظيف البيانات وتحويل المبالغ لأرقام حقيقية للحساب
        for df in [df_acc, df_bsp]:
            if not df.empty:
                df['Amount_Value'] = df['Amount'].str.replace(',', '').astype(float)

        if not df_bsp.empty:
            # ربط الملفين بناءً على رقم التذكرة
            comparison = pd.merge(df_bsp, df_acc, on="Ticket", how="left", suffixes=('_BSP', '_ACC'))
            
            # تحديد التذاكر المفقودة أو التي بها فرق سعر
            comparison['Status'] = "مطابق"
            comparison.loc[comparison['Amount_ACC'].isna(), 'Status'] = "مفقود من الحسابات"
            comparison.loc[(comparison['Status'] == "مطابق") & (comparison['Amount_Value_BSP'] != comparison['Amount_Value_ACC']), 'Status'] = "فرق سعر"

            st.divider()
            st.subheader("📊 التقرير المالي التفصيلي")
            
            # عرض النتائج في جدول احترافي
            display_df = comparison[['Ticket', 'Amount_BSP', 'Amount_ACC', 'Status']]
            display_df.columns = ['رقم التذكرة', 'القيمة في BSP', 'القيمة في حساباتك', 'الحالة']
            
            st.dataframe(display_df, use_container_width=True)
            
            # زر تحميل التقرير الشامل
            csv = display_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("تحميل تقرير المراجعة المالي (CSV)", csv, "financial_audit.csv")
            
        else:
            st.error("لم يتم العثور على بيانات مالية كافية في الملفات.")
