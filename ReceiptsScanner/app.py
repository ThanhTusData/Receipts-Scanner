"""
Streamlit UI - Main entry point for Receipt Scanner application
"""
import streamlit as st
import requests
from PIL import Image
import io
import os
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any
import time

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Receipt Scanner",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)


def check_api_health():
    """Check if API is accessible"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def upload_receipt(files: List[Any]) -> Dict:
    """Upload receipt images to API"""
    file_data = []
    for file in files:
        file_data.append(("files", (file.name, file.getvalue(), file.type)))
    
    response = requests.post(f"{API_URL}/upload", files=file_data)
    return response.json()


def get_receipts(limit: int = 100, skip: int = 0) -> List[Dict]:
    """Fetch receipts from API"""
    response = requests.get(f"{API_URL}/receipts?limit={limit}&skip={skip}")
    return response.json()


def get_receipt(receipt_id: str) -> Dict:
    """Get single receipt by ID"""
    response = requests.get(f"{API_URL}/receipts/{receipt_id}")
    return response.json()


def update_receipt(receipt_id: str, data: Dict) -> Dict:
    """Update receipt data"""
    response = requests.put(f"{API_URL}/receipts/{receipt_id}", json=data)
    return response.json()


def delete_receipt(receipt_id: str) -> bool:
    """Delete receipt"""
    response = requests.delete(f"{API_URL}/receipts/{receipt_id}")
    return response.status_code == 200


def get_job_status(job_id: str) -> Dict:
    """Get job processing status"""
    response = requests.get(f"{API_URL}/jobs/{job_id}")
    return response.json()


def page_scan_receipts():
    """Page 1: Scan and upload receipts"""
    st.title("📸 Quét Hóa Đơn")
    
    # Check API connection
    if not check_api_health():
        st.error("⚠️ Không thể kết nối đến API server. Vui lòng kiểm tra lại.")
        return
    
    st.write("Tải lên hình ảnh hóa đơn để tự động trích xuất thông tin.")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Chọn file hình ảnh",
        type=["jpg", "jpeg", "png", "pdf"],
        accept_multiple_files=True,
        help="Hỗ trợ JPG, PNG, PDF (tối đa 10 files)"
    )
    
    if uploaded_files:
        st.write(f"**Đã chọn {len(uploaded_files)} file**")
        
        # Preview images
        cols = st.columns(min(len(uploaded_files), 3))
        for idx, file in enumerate(uploaded_files[:3]):
            with cols[idx]:
                try:
                    image = Image.open(file)
                    st.image(image, caption=file.name, use_column_width=True)
                except:
                    st.write(f"📄 {file.name}")
        
        if len(uploaded_files) > 3:
            st.write(f"... và {len(uploaded_files) - 3} file khác")
        
        # Upload button
        if st.button("🚀 Xử Lý Hóa Đơn", type="primary"):
            with st.spinner("Đang tải lên và xử lý..."):
                try:
                    result = upload_receipt(uploaded_files)
                    
                    if "job_ids" in result:
                        st.success(f"✅ Đã tạo {len(result['job_ids'])} tác vụ xử lý")
                        
                        # Track job progress
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        job_ids = result["job_ids"]
                        completed = 0
                        total = len(job_ids)
                        
                        while completed < total:
                            completed = 0
                            for job_id in job_ids:
                                job_status = get_job_status(job_id)
                                if job_status["status"] in ["completed", "failed"]:
                                    completed += 1
                            
                            progress = completed / total
                            progress_bar.progress(progress)
                            status_text.text(f"Hoàn thành: {completed}/{total}")
                            
                            if completed < total:
                                time.sleep(2)
                        
                        st.success("🎉 Hoàn thành xử lý!")
                        st.balloons()
                        
                        # Show results
                        st.subheader("Kết quả")
                        for job_id in job_ids:
                            job_status = get_job_status(job_id)
                            with st.expander(f"Job: {job_id[:8]}..."):
                                st.json(job_status)
                    else:
                        st.error("Lỗi khi tải lên")
                        
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")


def page_view_receipts():
    """Page 2: View and manage receipts"""
    st.title("📋 Xem Hóa Đơn")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        date_filter = st.date_input(
            "Từ ngày",
            value=datetime.now() - timedelta(days=30)
        )
    
    with col2:
        category_filter = st.selectbox(
            "Danh mục",
            ["Tất cả", "Thực Phẩm", "Điện Tử", "Quần Áo", "Y Tế", 
             "Giải Trí", "Du Lịch", "Gia Dụng", "Khác"]
        )
    
    with col3:
        search = st.text_input("Tìm kiếm", placeholder="Tên cửa hàng...")
    
    # Fetch receipts
    try:
        receipts = get_receipts(limit=100)
        
        if not receipts:
            st.info("Chưa có hóa đơn nào. Hãy quét hóa đơn đầu tiên!")
            return
        
        # Filter receipts
        df = pd.DataFrame(receipts)
        
        if category_filter != "Tất cả":
            df = df[df["category"] == category_filter]
        
        if search:
            df = df[df["merchant_name"].str.contains(search, case=False, na=False)]
        
        # Display count
        st.write(f"**Tìm thấy {len(df)} hóa đơn**")
        
        # Display receipts in grid
        for idx, receipt in df.iterrows():
            with st.expander(
                f"🧾 {receipt.get('merchant_name', 'Unknown')} - "
                f"{receipt.get('total_amount', 0):,.0f} VNĐ - "
                f"{receipt.get('receipt_date', 'N/A')}"
            ):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Mã hóa đơn:** {receipt['id']}")
                    st.write(f"**Ngày:** {receipt.get('receipt_date', 'N/A')}")
                    st.write(f"**Cửa hàng:** {receipt.get('merchant_name', 'Unknown')}")
                    st.write(f"**Tổng tiền:** {receipt.get('total_amount', 0):,.0f} VNĐ")
                    st.write(f"**Danh mục:** {receipt.get('category', 'Khác')}")
                    st.write(f"**Độ tin cậy:** {receipt.get('confidence', 0):.2%}")
                    
                    if receipt.get("items"):
                        st.write("**Sản phẩm:**")
                        for item in receipt["items"]:
                            st.write(f"- {item}")
                
                with col2:
                    # Action buttons
                    if st.button("✏️ Sửa", key=f"edit_{receipt['id']}"):
                        st.session_state[f"editing_{receipt['id']}"] = True
                    
                    if st.button("🗑️ Xóa", key=f"delete_{receipt['id']}"):
                        if delete_receipt(receipt['id']):
                            st.success("Đã xóa!")
                            st.rerun()
                        else:
                            st.error("Lỗi khi xóa")
                
                # Edit mode
                if st.session_state.get(f"editing_{receipt['id']}", False):
                    st.write("---")
                    st.write("**Chỉnh sửa thông tin**")
                    
                    new_merchant = st.text_input("Cửa hàng", value=receipt.get("merchant_name", ""))
                    new_amount = st.number_input("Tổng tiền", value=float(receipt.get("total_amount", 0)))
                    new_category = st.selectbox(
                        "Danh mục",
                        ["Thực Phẩm", "Điện Tử", "Quần Áo", "Y Tế", "Giải Trí", "Du Lịch", "Gia Dụng", "Khác"],
                        index=["Thực Phẩm", "Điện Tử", "Quần Áo", "Y Tế", "Giải Trí", "Du Lịch", "Gia Dụng", "Khác"].index(receipt.get("category", "Khác"))
                    )
                    
                    if st.button("💾 Lưu", key=f"save_{receipt['id']}"):
                        updated_data = {
                            "merchant_name": new_merchant,
                            "total_amount": new_amount,
                            "category": new_category
                        }
                        update_receipt(receipt['id'], updated_data)
                        st.success("Đã cập nhật!")
                        st.session_state[f"editing_{receipt['id']}"] = False
                        st.rerun()
        
    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu: {str(e)}")


def page_analytics():
    """Page 3: Analytics and insights"""
    st.title("📊 Phân Tích Chi Tiêu")
    
    try:
        receipts = get_receipts(limit=1000)
        
        if not receipts:
            st.info("Chưa có dữ liệu để phân tích")
            return
        
        df = pd.DataFrame(receipts)
        df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce')
        df['receipt_date'] = pd.to_datetime(df['receipt_date'], errors='coerce')
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_spent = df['total_amount'].sum()
            st.metric("Tổng Chi Tiêu", f"{total_spent:,.0f} VNĐ")
        
        with col2:
            avg_receipt = df['total_amount'].mean()
            st.metric("Trung Bình/Hóa Đơn", f"{avg_receipt:,.0f} VNĐ")
        
        with col3:
            total_receipts = len(df)
            st.metric("Tổng Số Hóa Đơn", f"{total_receipts}")
        
        with col4:
            this_month = df[df['receipt_date'].dt.month == datetime.now().month]['total_amount'].sum()
            st.metric("Chi Tháng Này", f"{this_month:,.0f} VNĐ")
        
        st.write("---")
        
        # Category breakdown
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Chi Tiêu Theo Danh Mục")
            category_spend = df.groupby('category')['total_amount'].sum().sort_values(ascending=False)
            
            fig = px.pie(
                values=category_spend.values,
                names=category_spend.index,
                title="Phân Bổ Chi Tiêu"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Top 10 Cửa Hàng")
            merchant_spend = df.groupby('merchant_name')['total_amount'].sum().sort_values(ascending=False).head(10)
            
            fig = px.bar(
                x=merchant_spend.values,
                y=merchant_spend.index,
                orientation='h',
                title="Chi Tiêu Theo Cửa Hàng"
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        
        # Time series
        st.subheader("Xu Hướng Chi Tiêu Theo Thời Gian")
        
        df_sorted = df.sort_values('receipt_date')
        daily_spend = df_sorted.groupby(df_sorted['receipt_date'].dt.date)['total_amount'].sum()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_spend.index,
            y=daily_spend.values,
            mode='lines+markers',
            name='Chi tiêu hàng ngày'
        ))
        fig.update_layout(
            xaxis_title="Ngày",
            yaxis_title="Số tiền (VNĐ)",
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Lỗi khi tạo biểu đồ: {str(e)}")


def page_settings():
    """Page 4: Settings and admin"""
    st.title("⚙️ Cài Đặt")
    
    tab1, tab2, tab3 = st.tabs(["Hệ Thống", "Mô Hình ML", "Thông Tin"])
    
    with tab1:
        st.subheader("Cài Đặt Hệ Thống")
        
        st.write("**Trạng thái API**")
        if check_api_health():
            st.success("✅ API đang hoạt động")
        else:
            st.error("❌ Không kết nối được API")
        
        st.write("**Cơ sở dữ liệu**")
        try:
            receipts = get_receipts(limit=1)
            st.info(f"Kết nối thành công")
        except:
            st.error("Lỗi kết nối database")
    
    with tab2:
        st.subheader("Quản Lý Mô Hình ML")
        
        st.write("**Huấn luyện lại mô hình**")
        st.write("Sử dụng dữ liệu phản hồi để cải thiện độ chính xác phân loại")
        
        if st.button("🔄 Retrain Model", type="primary"):
            with st.spinner("Đang huấn luyện..."):
                try:
                    response = requests.post(f"{API_URL}/admin/retrain")
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ Hoàn thành! Job ID: {result.get('job_id')}")
                    else:
                        st.error("Lỗi khi retrain")
                except Exception as e:
                    st.error(f"Lỗi: {str(e)}")
    
    with tab3:
        st.subheader("Thông Tin Ứng Dụng")
        st.write("**Receipt Scanner v1.0**")
        st.write("Hệ thống quét và phân loại hóa đơn tự động")
        st.write("")
        st.write("**Công nghệ:**")
        st.write("- OCR: Tesseract")
        st.write("- ML: Sentence-BERT + Logistic Regression")
        st.write("- Backend: FastAPI + Celery")
        st.write("- Frontend: Streamlit")
        st.write("- Storage: MinIO/S3")


# Main app
def main():
    # Sidebar navigation
    st.sidebar.title("🧾 Receipt Scanner")
    
    pages = {
        "📸 Quét Hóa Đơn": page_scan_receipts,
        "📋 Xem Hóa Đơn": page_view_receipts,
        "📊 Phân Tích": page_analytics,
        "⚙️ Cài Đặt": page_settings
    }
    
    selection = st.sidebar.radio("Chọn trang", list(pages.keys()))
    
    # Display selected page
    pages[selection]()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("Made with ❤️ using Streamlit")


if __name__ == "__main__":
    main()