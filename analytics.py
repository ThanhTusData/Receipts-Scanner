import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

class Analytics:
    def __init__(self, data_manager):
        self.data_manager = data_manager
    
    def _get_df(self):
        """Get dataframe with error handling"""
        try:
            receipts = self.data_manager.get_receipts()
            if not receipts:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(receipts)
            
            # Ensure required columns exist with defaults
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y', errors='coerce')
                # Remove rows with invalid dates
                df = df.dropna(subset=['date'])
            else:
                df['date'] = pd.to_datetime('today')
            
            # Ensure total_amount is numeric
            if 'total_amount' in df.columns:
                df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce').fillna(0)
            else:
                df['total_amount'] = 0
            
            # Ensure category exists
            if 'category' not in df.columns:
                df['category'] = 'Khác'
            
            # Ensure store_name exists
            if 'store_name' not in df.columns:
                df['store_name'] = 'Unknown'
            
            return df
        except Exception as e:
            print(f"Error in _get_df: {e}")
            return pd.DataFrame()
    
    def get_category_summary(self):
        """Category summary statistics"""
        df = self._get_df()
        if df.empty:
            return pd.DataFrame()
        
        try:
            summary = df.groupby('category')['total_amount'].agg(['sum', 'count', 'mean']).round(2)
            summary.columns = ['Tổng tiền', 'Số lượng', 'Trung bình']
            return summary
        except Exception:
            return pd.DataFrame()
    
    def create_category_pie_chart(self):
        """Category spending pie chart"""
        df = self._get_df()
        if df.empty:
            return go.Figure().add_annotation(text="Chưa có dữ liệu", showarrow=False, 
                                            xref="paper", yref="paper", x=0.5, y=0.5,
                                            font=dict(size=16))
        
        try:
            category_sum = df.groupby('category')['total_amount'].sum()
            
            return px.pie(
                values=category_sum.values,
                names=category_sum.index,
                title="Phân bổ chi tiêu theo danh mục",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
        except Exception:
            return go.Figure().add_annotation(text="Lỗi tạo biểu đồ", showarrow=False,
                                            xref="paper", yref="paper", x=0.5, y=0.5)
    
    def create_spending_trend(self):
        """Daily spending trend chart"""
        df = self._get_df()
        if df.empty:
            return go.Figure().add_annotation(text="Chưa có dữ liệu", showarrow=False,
                                            xref="paper", yref="paper", x=0.5, y=0.5,
                                            font=dict(size=16))
        
        try:
            daily_spending = df.groupby(df['date'].dt.date)['total_amount'].sum()
            
            fig = px.line(
                x=daily_spending.index,
                y=daily_spending.values,
                title="Xu hướng chi tiêu theo ngày",
                markers=True
            )
            fig.update_layout(
                xaxis_title="Ngày", 
                yaxis_title="Số tiền (VNĐ)",
                showlegend=False
            )
            return fig
        except Exception:
            return go.Figure().add_annotation(text="Lỗi tạo biểu đồ", showarrow=False,
                                            xref="paper", yref="paper", x=0.5, y=0.5)
    
    def create_monthly_comparison(self):
        """Monthly spending comparison"""
        df = self._get_df()
        if df.empty:
            return go.Figure().add_annotation(text="Chưa có dữ liệu", showarrow=False,
                                            xref="paper", yref="paper", x=0.5, y=0.5,
                                            font=dict(size=16))
        
        try:
            df['month_year'] = df['date'].dt.to_period('M')
            monthly_spending = df.groupby('month_year')['total_amount'].sum()
            
            fig = px.bar(
                x=monthly_spending.index.astype(str),
                y=monthly_spending.values,
                title="Chi tiêu theo tháng",
                color=monthly_spending.values,
                color_continuous_scale="Blues"
            )
            fig.update_layout(
                xaxis_title="Tháng", 
                yaxis_title="Số tiền (VNĐ)",
                showlegend=False
            )
            return fig
        except Exception:
            return go.Figure().add_annotation(text="Lỗi tạo biểu đồ", showarrow=False,
                                            xref="paper", yref="paper", x=0.5, y=0.5)
    
    def create_category_bar_chart(self):
        """Category spending bar chart"""
        df = self._get_df()
        if df.empty:
            return go.Figure().add_annotation(text="Chưa có dữ liệu", showarrow=False,
                                            xref="paper", yref="paper", x=0.5, y=0.5,
                                            font=dict(size=16))
        
        try:
            category_sum = df.groupby('category')['total_amount'].sum().sort_values(ascending=True)
            
            return px.bar(
                x=category_sum.values,
                y=category_sum.index,
                orientation='h',
                title="Chi tiêu theo danh mục",
                color=category_sum.values,
                color_continuous_scale="Viridis"
            )
        except Exception:
            return go.Figure().add_annotation(text="Lỗi tạo biểu đồ", showarrow=False,
                                            xref="paper", yref="paper", x=0.5, y=0.5)
    
    def get_spending_insights(self):
        """Comprehensive spending insights"""
        df = self._get_df()
        if df.empty:
            return {
                'total_spending': 0,
                'avg_spending': 0,
                'total_receipts': 0,
                'avg_confidence': 0,
                'most_expensive': {},
                'top_category': 'Khác',
                'category_breakdown': {},
                'recent_trend': 0,
                'monthly_avg': 0
            }
        
        try:
            # Basic stats
            insights = {
                'total_spending': df['total_amount'].sum(),
                'avg_spending': df['total_amount'].mean(),
                'total_receipts': len(df),
                'avg_confidence': df.get('confidence', pd.Series([0])).mean()
            }
            
            # Additional insights
            if not df.empty:
                max_idx = df['total_amount'].idxmax()
                top_category = df.groupby('category')['total_amount'].sum()
                
                insights.update({
                    'most_expensive': df.loc[max_idx].to_dict() if pd.notna(max_idx) else {},
                    'top_category': top_category.idxmax() if not top_category.empty else 'Khác',
                    'category_breakdown': top_category.to_dict(),
                    'recent_trend': self._get_recent_trend(df),
                    'monthly_avg': self._get_monthly_average(df)
                })
            
            return insights
        
        except Exception as e:
            print(f"Error in get_spending_insights: {e}")
            return {
                'total_spending': 0,
                'avg_spending': 0,
                'total_receipts': 0,
                'avg_confidence': 0,
                'most_expensive': {},
                'top_category': 'Khác',
                'category_breakdown': {},
                'recent_trend': 0,
                'monthly_avg': 0
            }
    
    def _get_recent_trend(self, df):
        """Get recent spending trend (last 7 days vs previous 7 days)"""
        try:
            if len(df) < 2:
                return 0
            
            today = datetime.now().date()
            recent_7days = df[df['date'].dt.date >= (today - pd.Timedelta(days=7))]
            previous_7days = df[
                (df['date'].dt.date >= (today - pd.Timedelta(days=14))) &
                (df['date'].dt.date < (today - pd.Timedelta(days=7)))
            ]
            
            recent_sum = recent_7days['total_amount'].sum()
            previous_sum = previous_7days['total_amount'].sum()
            
            if previous_sum == 0:
                return 100 if recent_sum > 0 else 0
            
            return ((recent_sum - previous_sum) / previous_sum) * 100
        except Exception:
            return 0
    
    def _get_monthly_average(self, df):
        """Get monthly average spending"""
        try:
            if df.empty:
                return 0
            
            df['month_year'] = df['date'].dt.to_period('M')
            monthly_totals = df.groupby('month_year')['total_amount'].sum()
            
            return monthly_totals.mean() if not monthly_totals.empty else 0
        except Exception:
            return 0
    
    def get_top_stores(self, limit=5):
        """Get top stores by spending"""
        df = self._get_df()
        if df.empty:
            return pd.DataFrame()
        
        try:
            return df.groupby('store_name')['total_amount'].agg(['sum', 'count']).sort_values('sum', ascending=False).head(limit)
        except Exception:
            return pd.DataFrame()
    
    def get_spending_by_weekday(self):
        """Spending analysis by weekday"""
        df = self._get_df()
        if df.empty:
            return pd.DataFrame()
        
        try:
            df['weekday'] = df['date'].dt.day_name()
            weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            weekday_spending = df.groupby('weekday')['total_amount'].agg(['sum', 'mean'])
            return weekday_spending.reindex(weekday_order).fillna(0)
        except Exception:
            return pd.DataFrame()