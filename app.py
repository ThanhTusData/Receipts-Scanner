import streamlit as st
import pandas as pd
from PIL import Image
from datetime import datetime
import time
import json
import os
import requests
from requests import RequestException
from io import BytesIO

from receipt_processor_old import ReceiptProcessor
from category_classifier_old import CategoryClassifier
from data_manager import DataManager
from analytics import Analytics
from config import EXPENSE_CATEGORIES, CATEGORY_ICONS

# Page config
st.set_page_config(
    page_title="ReceiptsScanner",
    page_icon="🧾",
    layout="wide"
)

# API endpoint (leave empty to use local processing fallback)
API_URL = os.getenv("API_URL", "").rstrip("/")

# Initialize components - FIXED
@st.cache_resource
def get_components():
    data_manager = DataManager()
    return (
        ReceiptProcessor(),
        CategoryClassifier(),
        data_manager,
        Analytics(data_manager)  # Pass the same instance
    )

processor, classifier, data_manager, analytics = get_components()

# Helper functions - ENHANCED
def validate_form_data(store_name, total_amount, date_str):
    """Validate form data with specific error messages"""
    errors = []
    
    if not store_name or not store_name.strip() or len(store_name.strip()) < 2:
        errors.append("Tên cửa hàng phải có ít nhất 2 ký tự")
    
    if total_amount <= 0 or total_amount > 100000000:
        errors.append("Số tiền phải từ 0 đến 100 triệu VNĐ")
    
    if not date_str or not date_str.strip():
        errors.append("Ngày không được để trống")
    else:
        try:
            datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            errors.append("Định dạng ngày không hợp lệ (dd/mm/yyyy)")
    
    return errors

def save_receipt_data(receipt_data, form_data):
    """Save receipt with metadata - ENHANCED"""
    try:
        enhanced_data = {
            **receipt_data,
            **form_data,
            'processed_date': datetime.now().isoformat(),
            'id': f"receipt_{int(time.time() * 1000)}"
        }
        return data_manager.add_receipt(enhanced_data)
    except Exception as e:
        print(f"Error saving receipt data: {e}")
        return False

def format_currency(amount):
    """Format currency consistently"""
    try:
        return f"{float(amount):,.0f} VNĐ"
    except (ValueError, TypeError):
        return "0 VNĐ"

def get_confidence_indicator(confidence):
    """Get confidence indicator with color"""
    try:
        confidence = float(confidence)
        if confidence >= 80: return "🟢", "Rất tốt"
        elif confidence >= 60: return "🟡", "Tốt"
        elif confidence >= 40: return "🟠", "Trung bình"
        else: return "🔴", "Cần kiểm tra"
    except (ValueError, TypeError):
        return "🔴", "Cần kiểm tra"

# Sidebar
st.sidebar.title("🧾 ReceiptsScanner")
page = st.sidebar.selectbox("📋 Chọn chức năng", [
    "Quét hóa đơn", "Xem hóa đơn", "Phân tích", "Cài đặt"
])

# Quick stats - ENHANCED
try:
    receipts = data_manager.get_receipts()
    receipts_count = len(receipts)

    if receipts_count > 0:
        total_spending = sum(float(r.get('total_amount', 0)) for r in receipts)
        st.sidebar.markdown("---")
        st.sidebar.markdown("📊 **Thống kê nhanh**")
        st.sidebar.write(f"📄 Hóa đơn: {receipts_count}")
        st.sidebar.write(f"💰 Tổng: {format_currency(total_spending)}")
except Exception as e:
    st.sidebar.error("Lỗi tải dữ liệu")
    receipts = []
    receipts_count = 0

# === SCAN PAGE ===
if page == "Quét hóa đơn":
    st.title("📱 Quét hóa đơn mới")

    # Upload ảnh
    uploaded_file = st.file_uploader(
        "📸 Chọn ảnh hóa đơn", 
        type=['png', 'jpg', 'jpeg'],
        help="Chọn ảnh rõ nét, ánh sáng tốt để kết quả OCR chính xác hơn."
    )

    # Option: Force local processing even if API_URL configured
    use_local = st.checkbox("⚙️ Xử lý cục bộ (không gọi API)", value=False)

    # Xử lý quét khi bấm nút
    if uploaded_file and st.button("🔍 Quét ngay", type="primary", use_container_width=True):
        with st.spinner("🔄 Đang xử lý..."):
            # If API is configured and user didn't choose local, upload to API
            if API_URL and not use_local:
                try:
                    files = {
                        "file": (
                            uploaded_file.name or f"upload_{int(time.time())}.jpg",
                            uploaded_file.getvalue(),
                            getattr(uploaded_file, "type", "application/octet-stream")
                        )
                    }
                    resp = requests.post(f"{API_URL}/upload", files=files, timeout=30)
                    resp.raise_for_status()
                    data = resp.json()
                    job_id = data.get("job_id")
                    if not job_id:
                        st.error("API trả về không có job_id")
                    else:
                        st.session_state["job_id"] = job_id
                        st.success(f"Đã tạo job: {job_id}. Vui lòng kiểm tra trạng thái.")
                except RequestException as e:
                    st.error(f"Lỗi khi upload lên API: {e}")
                    # Fallback to local processing automatically
                    st.info("Chuyển sang xử lý cục bộ...")
                    try:
                        receipt_data = processor.process_receipt(Image.open(uploaded_file))
                        if receipt_data.get("confidence", 0) == 0:
                            st.error("❌ Không thể đọc được nội dung từ ảnh (cục bộ)!")
                        else:
                            receipt_data["category"] = classifier.predict_category(receipt_data)
                            st.session_state["receipt_data"] = receipt_data
                            st.success("Đã xử lý cục bộ thành công")
                    except Exception as e2:
                        st.error(f"Lỗi xử lý cục bộ: {e2}")
            else:
                # Local processing fallback / explicit
                try:
                    receipt_data = processor.process_receipt(Image.open(uploaded_file))
                    if receipt_data.get("confidence", 0) == 0:
                        st.error("❌ Không thể đọc được nội dung từ ảnh!")
                    else:
                        receipt_data["category"] = classifier.predict_category(receipt_data)
                        st.session_state["receipt_data"] = receipt_data
                        st.success("Đã xử lý cục bộ thành công")
                except Exception as e:
                    st.error(f"Lỗi xử lý ảnh (cục bộ): {e}")

    # If job_id present, allow checking status
    job_id = st.session_state.get("job_id")
    if job_id:
        st.markdown("### 🟡 Job đã được tạo (API xử lý bất đồng bộ)")
        st.write(f"Job ID: `{job_id}`")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔁 Kiểm tra trạng thái", key=f"check_{job_id}"):
                if not API_URL:
                    st.error("API_URL chưa cấu hình, không thể kiểm tra trạng thái")
                else:
                    try:
                        resp = requests.get(f"{API_URL}/status/{job_id}", timeout=10)
                        resp.raise_for_status()
                        job = resp.json()
                        st.write(job)
                        status = job.get("status")
                        if status == "done":
                            result = job.get("result", {})
                            if result:
                                # Map result into expected receipt_data shape if necessary
                                # Prefer result as-is (result should contain parsed entities)
                                receipt_data = result
                                # ensure category exists
                                if not receipt_data.get("category"):
                                    try:
                                        receipt_data["category"] = classifier.predict_category(receipt_data)
                                    except Exception:
                                        receipt_data["category"] = list(EXPENSE_CATEGORIES.keys())[0] if EXPENSE_CATEGORIES else "Khác"
                                st.session_state["receipt_data"] = receipt_data
                                st.success("✅ Job hoàn thành — dữ liệu đã sẵn sàng để lưu")
                                # clear job_id after success to avoid duplicate checks
                                del st.session_state["job_id"]
                        elif status == "failed":
                            st.error(f"Job thất bại: {job.get('error')}")
                            del st.session_state["job_id"]
                        else:
                            st.info(f"Trạng thái hiện tại: {status}")
                    except RequestException as e:
                        st.error(f"Lỗi khi gọi API: {e}")

        with col2:
            if st.button("🗑️ Hủy job", key=f"cancel_{job_id}"):
                # We don't have cancel endpoint; just drop local reference
                del st.session_state["job_id"]
                st.info("Đã hủy tham chiếu job cục bộ (API có thể vẫn xử lý).")

    # ✅ Lấy lại dữ liệu sau khi quét từ session
    receipt_data = st.session_state.get("receipt_data", {})

    # Nếu đã có dữ liệu thì hiển thị preview & form lưu
    if receipt_data:
        # Hiển thị thông tin quét
        st.success(f"📄 Đã quét: {receipt_data.get('store_name', 'Không rõ')} - {format_currency(receipt_data.get('total_amount', 0))}")

        # Form xác nhận và lưu
        with st.form("receipt_form"):
            st.subheader("✏️ Xác nhận và chỉnh sửa")

            col1, col2 = st.columns(2)
            with col1:
                store_name = st.text_input("🏪 Tên cửa hàng", value=receipt_data.get("store_name", ""))
                total_amount = st.number_input("💰 Số tiền", value=float(receipt_data.get("total_amount", 0)), step=1000.0)
            with col2:
                date_input = st.text_input("📅 Ngày mua", value=receipt_data.get("date", ""))
                category = st.selectbox("📂 Danh mục", list(EXPENSE_CATEGORIES.keys()), index=0)

            notes = st.text_area("📝 Ghi chú", placeholder="Ví dụ: Thanh toán tiền ăn trưa...")

            submit = st.form_submit_button("💾 Lưu hóa đơn")
            if submit:
                form_data = {
                    "store_name": store_name.strip(),
                    "total_amount": total_amount,
                    "date": date_input.strip(),
                    "category": category,
                    "notes": notes.strip(),
                    "confidence": receipt_data.get("confidence", 0),
                    "phone": receipt_data.get("phone", ""),
                    "address": receipt_data.get("address", ""),
                    "items": receipt_data.get("items", []),
                }

                with st.spinner("Đang lưu..."):
                    if save_receipt_data(receipt_data, form_data):
                        st.success("✅ Đã lưu hóa đơn thành công!")
                        st.balloons()

                        # Xóa session để tránh lưu trùng
                        del st.session_state["receipt_data"]
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Có lỗi khi lưu dữ liệu!")

# === VIEW PAGE === (ENHANCED)
elif page == "Xem hóa đơn":
    st.title("📋 Danh sách hóa đơn")
    
    if not receipts:
        st.info("📝 **Chưa có hóa đơn nào!**")
        st.info("💡 Hãy quét hóa đơn đầu tiên của bạn ở trang 'Quét hóa đơn'")
    else:
        # Filters
        st.markdown("### 🔍 **Bộ lọc**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search = st.text_input("🔍 Tìm kiếm", placeholder="Tên cửa hàng...")
        with col2:
            filter_category = st.selectbox("📂 Dan mục", ["Tất cả"] + list(EXPENSE_CATEGORIES.keys()))
        with col3:
            sort_by = st.selectbox("📊 Sắp xếp", ["Mới nhất", "Cũ nhất", "Số tiền cao", "Số tiền thấp"])
        
        # Filter logic
        filtered = receipts.copy()
        
        if search:
            filtered = [r for r in filtered if 
                       search.lower() in r.get('store_name', '').lower() or
                       search.lower() in r.get('notes', '').lower()]
        
        if filter_category != "Tất cả":
            filtered = [r for r in filtered if r.get('category') == filter_category]
        
        # Sort logic
        sort_keys = {
            "Mới nhất": lambda x: x.get('processed_date', ''),
            "Cũ nhất": lambda x: x.get('processed_date', ''),
            "Số tiền cao": lambda x: float(x.get('total_amount', 0)),
            "Số tiền thấp": lambda x: float(x.get('total_amount', 0))
        }
        
        filtered.sort(key=sort_keys[sort_by], reverse=sort_by in ["Mới nhất", "Số tiền cao"])
        
        # Display results
        st.markdown(f"### 📄 **Kết quả: {len(filtered)} hóa đơn**")
        
        if filtered:
            total_filtered = sum(float(r.get('total_amount', 0)) for r in filtered)
            col1, col2, col3 = st.columns(3)
            col1.metric("💰 Tổng", format_currency(total_filtered))
            col2.metric("📊 TB", format_currency(total_filtered / len(filtered)) if len(filtered) > 0 else format_currency(0))
            col3.metric("📄 Số lượng", len(filtered))
            
            # Display receipts
            for i, receipt in enumerate(filtered):
                confidence_icon, _ = get_confidence_indicator(receipt.get('confidence', 0))
                
                with st.expander(
                    f"{confidence_icon} 🏪 **{receipt.get('store_name', 'Unknown')}** - "
                    f"**{format_currency(receipt.get('total_amount', 0))}** "
                    f"({receipt.get('date', 'N/A')})"
                ):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        info_items = [
                            f"📂 **Danh mục:** {receipt.get('category', 'N/A')}",
                            f"📅 **Ngày:** {receipt.get('date', 'N/A')}",
                            f"🎯 **Độ tin cậy:** {receipt.get('confidence', 0)}%"
                        ]
                        
                        if receipt.get('phone'):
                            info_items.append(f"📞 **SĐT:** {receipt.get('phone')}")
                        if receipt.get('notes'):
                            info_items.append(f"📝 **Ghi chú:** {receipt.get('notes')}")
                        
                        for item in info_items:
                            st.markdown(item)
                        
                        # Show items preview
                        if receipt.get('items'):
                            st.markdown(f"#### 🛍️ Sản phẩm ({len(receipt['items'])})")

                            for item in receipt['items'][:3]:
                                # Kiểm tra nếu là dict thì lấy name + price
                                if isinstance(item, dict):
                                    name = item.get('name', 'Unknown')
                                    price = item.get('price', 0)
                                else:
                                    name = str(item)
                                    price = 0
                                st.write(f"• {name}: {format_currency(price)}")

                            if len(receipt['items']) > 3:
                                st.write(f"... và {len(receipt['items'])-3} sản phẩm khác")

                    with col2:
                        if st.button("🗑️ Xóa", key=f"del_{i}"):
                            if data_manager.delete_receipt(receipt.get('id')):
                                st.success("✅ Đã xóa!")
                                st.rerun()

# === ANALYTICS PAGE === (ENHANCED)
elif page == "Phân tích":
    st.title("📊 Phân tích chi tiêu")
    
    if not receipts:
        st.info("📊 **Chưa có dữ liệu để phân tích!**")
    else:
        try:
            insights = analytics.get_spending_insights()
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("💰 Tổng chi tiêu", format_currency(insights.get('total_spending', 0)))
            col2.metric("📊 TB/hóa đơn", format_currency(insights.get('avg_spending', 0)))
            col3.metric("📄 Tổng HĐ", insights.get('total_receipts', 0))
            col4.metric("🎯 Tin cậy TB", f"{insights.get('avg_confidence', 0):.0f}%")
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🥧 **Chi tiêu theo danh mục**")
                try:
                    chart = analytics.create_category_pie_chart()
                    st.plotly_chart(chart, use_container_width=True)
                except Exception as e:
                    st.error(f"Lỗi tạo biểu đồ: {e}")
            
            with col2:
                st.markdown("#### 📅 **Xu hướng theo tháng**")
                try:
                    chart = analytics.create_monthly_comparison()
                    st.plotly_chart(chart, use_container_width=True)
                except Exception as e:
                    st.error(f"Lỗi tạo biểu đồ: {e}")
        
        except Exception as e:
            st.error(f"Lỗi phân tích dữ liệu: {e}")

# === SETTINGS PAGE === (ENHANCED)
elif page == "Cài đặt":
    st.title("⚙️ Cài đặt")
    
    # Statistics
    try:
        col1, col2, col3 = st.columns(3)
        total_amount = sum(float(r.get('total_amount', 0)) for r in receipts)
        avg_confidence = sum(float(r.get('confidence', 0)) for r in receipts) / len(receipts) if receipts else 0
        
        col1.metric("📄 Hóa đơn", len(receipts))
        col2.metric("💰 Tổng", format_currency(total_amount))
        col3.metric("🎯 Tin cậy TB", f"{avg_confidence:.1f}%")
    except Exception as e:
        st.error(f"Lỗi tải thống kê: {e}")
    
    # Data export
    st.markdown("### 📥 **Xuất dữ liệu**")
    if receipts:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📄 Tải CSV", type="primary"):
                try:
                    df = data_manager.get_receipts_df()
                    if not df.empty:
                        csv = df.to_csv(index=False)
                        st.download_button(
                            "⬇️ Tải ngay",
                            csv,
                            f"receipts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            "text/csv"
                        )
                    else:
                        st.error("Không có dữ liệu để xuất")
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")
    
    # Data management
    st.markdown("### 🗃️ **Quản lý dữ liệu**")
    with st.expander("⚠️ **Xóa dữ liệu**"):
        st.warning("⚠️ Hành động này không thể hoàn tác!")
        if st.button("🗑️ Xóa tất cả", type="secondary"):
            if st.button("⚠️ XÁC NHẬN", type="primary"):
                if data_manager.clear_all_data():
                    st.success("✅ Đã xóa!")
                    st.rerun()
                else:
                    st.error("❌ Có lỗi khi xóa dữ liệu!")

# Sidebar footer
st.sidebar.markdown("---")
st.sidebar.markdown("📱 **ReceiptsScanner v2.0**")

# Performance indicator
try:
    if receipts_count > 50:
        st.sidebar.success(f"🎉 Power User!")
    elif receipts_count > 10:
        st.sidebar.info(f"📈 Đang phát triển!")
    elif receipts_count > 0:
        st.sidebar.info(f"🌱 Bắt đầu tốt!")
except:
    pass
