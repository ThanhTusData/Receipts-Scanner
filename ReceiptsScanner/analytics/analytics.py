"""
Analytics module for spending insights and visualizations
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict

from monitoring.logging_config import get_logger

logger = get_logger(__name__)


class SpendingAnalytics:
    """Analytics for receipt spending data"""
    
    def __init__(self, receipts: List[Dict[str, Any]]):
        """
        Initialize analytics with receipts data
        
        Args:
            receipts: List of receipt dictionaries
        """
        self.df = pd.DataFrame(receipts)
        
        if not self.df.empty:
            # Convert data types
            self.df['total_amount'] = pd.to_numeric(self.df['total_amount'], errors='coerce')
            self.df['receipt_date'] = pd.to_datetime(self.df['receipt_date'], errors='coerce')
            
            # Add derived columns
            self.df['year'] = self.df['receipt_date'].dt.year
            self.df['month'] = self.df['receipt_date'].dt.month
            self.df['day_of_week'] = self.df['receipt_date'].dt.day_name()
            self.df['week'] = self.df['receipt_date'].dt.isocalendar().week
        
        logger.info(f"Analytics initialized with {len(self.df)} receipts")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics
        
        Returns:
            dict: Summary statistics
        """
        if self.df.empty:
            return self._empty_stats()
        
        total_spent = self.df['total_amount'].sum()
        avg_receipt = self.df['total_amount'].mean()
        median_receipt = self.df['total_amount'].median()
        max_receipt = self.df['total_amount'].max()
        min_receipt = self.df['total_amount'].min()
        
        # Current month stats
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        this_month_df = self.df[
            (self.df['month'] == current_month) & 
            (self.df['year'] == current_year)
        ]
        this_month_spent = this_month_df['total_amount'].sum()
        
        # Last month stats
        last_month = current_month - 1 if current_month > 1 else 12
        last_month_year = current_year if current_month > 1 else current_year - 1
        
        last_month_df = self.df[
            (self.df['month'] == last_month) & 
            (self.df['year'] == last_month_year)
        ]
        last_month_spent = last_month_df['total_amount'].sum()
        
        # Calculate month-over-month change
        mom_change = 0
        if last_month_spent > 0:
            mom_change = ((this_month_spent - last_month_spent) / last_month_spent) * 100
        
        return {
            "total_spent": float(total_spent),
            "total_receipts": len(self.df),
            "avg_receipt": float(avg_receipt),
            "median_receipt": float(median_receipt),
            "max_receipt": float(max_receipt),
            "min_receipt": float(min_receipt),
            "this_month_spent": float(this_month_spent),
            "last_month_spent": float(last_month_spent),
            "mom_change": float(mom_change),
            "receipts_this_month": len(this_month_df)
        }
    
    def get_category_breakdown(self) -> Dict[str, float]:
        """
        Get spending breakdown by category
        
        Returns:
            dict: Category spending amounts
        """
        if self.df.empty:
            return {}
        
        category_totals = self.df.groupby('category')['total_amount'].sum()
        return category_totals.to_dict()
    
    def get_top_merchants(self, n: int = 10) -> Dict[str, float]:
        """
        Get top N merchants by spending
        
        Args:
            n: Number of top merchants to return
            
        Returns:
            dict: Merchant spending amounts
        """
        if self.df.empty:
            return {}
        
        merchant_totals = self.df.groupby('merchant_name')['total_amount'].sum()
        top_merchants = merchant_totals.nlargest(n)
        return top_merchants.to_dict()
    
    def get_daily_spending(self, days: int = 30) -> pd.DataFrame:
        """
        Get daily spending for last N days
        
        Args:
            days: Number of days to analyze
            
        Returns:
            pd.DataFrame: Daily spending data
        """
        if self.df.empty:
            return pd.DataFrame()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_df = self.df[self.df['receipt_date'] >= cutoff_date]
        
        daily_spending = recent_df.groupby(
            recent_df['receipt_date'].dt.date
        )['total_amount'].sum().reset_index()
        
        daily_spending.columns = ['date', 'amount']
        return daily_spending
    
    def get_monthly_spending(self) -> pd.DataFrame:
        """
        Get monthly spending trends
        
        Returns:
            pd.DataFrame: Monthly spending data
        """
        if self.df.empty:
            return pd.DataFrame()
        
        self.df['year_month'] = self.df['receipt_date'].dt.to_period('M')
        
        monthly_spending = self.df.groupby('year_month')['total_amount'].agg([
            ('total', 'sum'),
            ('count', 'count'),
            ('avg', 'mean')
        ]).reset_index()
        
        monthly_spending['year_month'] = monthly_spending['year_month'].astype(str)
        return monthly_spending
    
    def get_day_of_week_analysis(self) -> Dict[str, float]:
        """
        Analyze spending by day of week
        
        Returns:
            dict: Day of week spending
        """
        if self.df.empty:
            return {}
        
        dow_spending = self.df.groupby('day_of_week')['total_amount'].sum()
        
        # Sort by weekday order
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                     'Friday', 'Saturday', 'Sunday']
        dow_spending = dow_spending.reindex(day_order, fill_value=0)
        
        return dow_spending.to_dict()
    
    def get_spending_distribution(self) -> Dict[str, Any]:
        """
        Get spending amount distribution
        
        Returns:
            dict: Distribution statistics
        """
        if self.df.empty:
            return {}
        
        amounts = self.df['total_amount']
        
        return {
            "mean": float(amounts.mean()),
            "median": float(amounts.median()),
            "std": float(amounts.std()),
            "min": float(amounts.min()),
            "max": float(amounts.max()),
            "q25": float(amounts.quantile(0.25)),
            "q75": float(amounts.quantile(0.75)),
            "q90": float(amounts.quantile(0.90)),
            "q95": float(amounts.quantile(0.95))
        }
    
    def get_insights(self) -> List[str]:
        """
        Generate spending insights
        
        Returns:
            list: List of insight strings
        """
        insights = []
        
        if self.df.empty:
            insights.append("No receipts to analyze yet. Start scanning receipts!")
            return insights
        
        # Summary stats
        stats = self.get_summary_stats()
        
        # Insight 1: Total spending
        insights.append(
            f"Tổng chi tiêu: {stats['total_spent']:,.0f} VNĐ "
            f"từ {stats['total_receipts']} hóa đơn"
        )
        
        # Insight 2: Average receipt
        insights.append(
            f"Trung bình mỗi hóa đơn: {stats['avg_receipt']:,.0f} VNĐ"
        )
        
        # Insight 3: Month-over-month change
        if stats['mom_change'] > 0:
            insights.append(
                f"📈 Chi tiêu tháng này tăng {stats['mom_change']:.1f}% "
                f"so với tháng trước"
            )
        elif stats['mom_change'] < 0:
            insights.append(
                f"📉 Chi tiêu tháng này giảm {abs(stats['mom_change']):.1f}% "
                f"so với tháng trước"
            )
        
        # Insight 4: Top category
        category_breakdown = self.get_category_breakdown()
        if category_breakdown:
            top_category = max(category_breakdown, key=category_breakdown.get)
            top_amount = category_breakdown[top_category]
            pct = (top_amount / stats['total_spent']) * 100
            insights.append(
                f"🏆 Chi nhiều nhất cho {top_category}: "
                f"{top_amount:,.0f} VNĐ ({pct:.1f}%)"
            )
        
        # Insight 5: Most frequent day
        dow_analysis = self.get_day_of_week_analysis()
        if dow_analysis:
            most_frequent_day = max(dow_analysis, key=dow_analysis.get)
            insights.append(
                f"📅 Thường chi tiêu nhiều nhất vào {most_frequent_day}"
            )
        
        # Insight 6: Large purchases
        large_threshold = stats['q90']
        large_purchases = len(self.df[self.df['total_amount'] > large_threshold])
        if large_purchases > 0:
            insights.append(
                f"💰 Có {large_purchases} giao dịch lớn (>{large_threshold:,.0f} VNĐ)"
            )
        
        return insights
    
    def _empty_stats(self) -> Dict[str, Any]:
        """Return empty statistics"""
        return {
            "total_spent": 0,
            "total_receipts": 0,
            "avg_receipt": 0,
            "median_receipt": 0,
            "max_receipt": 0,
            "min_receipt": 0,
            "this_month_spent": 0,
            "last_month_spent": 0,
            "mom_change": 0,
            "receipts_this_month": 0
        }
    
    def create_category_pie_chart(self) -> go.Figure:
        """Create category spending pie chart"""
        category_data = self.get_category_breakdown()
        
        if not category_data:
            return go.Figure()
        
        fig = px.pie(
            names=list(category_data.keys()),
            values=list(category_data.values()),
            title="Chi Tiêu Theo Danh Mục",
            hole=0.3
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        
        return fig
    
    def create_monthly_trend_chart(self) -> go.Figure:
        """Create monthly spending trend chart"""
        monthly_data = self.get_monthly_spending()
        
        if monthly_data.empty:
            return go.Figure()
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=monthly_data['year_month'],
            y=monthly_data['total'],
            mode='lines+markers',
            name='Tổng chi tiêu',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Xu Hướng Chi Tiêu Theo Tháng",
            xaxis_title="Tháng",
            yaxis_title="Số tiền (VNĐ)",
            hovermode='x unified'
        )
        
        return fig
    
    def create_top_merchants_chart(self, n: int = 10) -> go.Figure:
        """Create top merchants bar chart"""
        merchant_data = self.get_top_merchants(n)
        
        if not merchant_data:
            return go.Figure()
        
        fig = px.bar(
            x=list(merchant_data.values()),
            y=list(merchant_data.keys()),
            orientation='h',
            title=f"Top {n} Cửa Hàng",
            labels={'x': 'Số tiền (VNĐ)', 'y': 'Cửa hàng'}
        )
        
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        
        return fig