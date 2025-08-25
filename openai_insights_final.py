"""
FINAL PRODUCTION OpenAI INSIGHTS GENERATOR
Complete AI analysis with promo and festival effectiveness
"""
import os
import openai
import json
import logging
from datetime import date, datetime
from typing import Dict, List, Optional, Any
import asyncpg
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# OpenAI Configuration
openai.api_key = os.getenv("OPENAI_API_KEY")

@dataclass
class InsightRequest:
    """Structure for insight generation request"""
    store_id: int
    period_start: date
    period_end: date
    insight_type: str  # "weekly", "monthly", "promo_effectiveness", "festival_analysis"
    metrics_data: Dict
    promotion_data: Optional[Dict] = None

@dataclass
class GeneratedInsight:
    """Structure for generated insight"""
    insights_text: str
    recommendations: List[Dict]
    confidence_score: float
    effectiveness_score: Optional[float] = None

class OpenAIInsightsGenerator:
    """AI-powered insights generation system"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def get_connection(self):
        """Get database connection"""
        return await asyncpg.connect(self.database_url)
    
    def create_base_prompt(self, store_name: str, metrics_data: Dict) -> str:
        """Create base prompt with store metrics"""
        return f"""
You are a retail analytics expert providing insights for {store_name}. 
Analyze the following store performance metrics and provide actionable insights.

CURRENT PERIOD METRICS:
- Analysis Period: {metrics_data['period']['start_date']} to {metrics_data['period']['end_date']}
- Total Days Analyzed: {metrics_data['period']['total_days']}

OVERALL PERFORMANCE:
- Average Daily Footfall: {metrics_data['overall_metrics']['avg_daily_footfall']} visitors
- Average Daily Unique Visitors: {metrics_data['overall_metrics']['avg_daily_unique_visitors']} people
- Average Dwell Time: {metrics_data['overall_metrics']['avg_dwell_time_minutes']} minutes
- Conversion Rate: {metrics_data['overall_metrics']['conversion_rate_percent']}%

PEAK HOURS ANALYSIS:
{json.dumps(metrics_data['peak_hours'], indent=2)}

ZONE PERFORMANCE:
{json.dumps(metrics_data['zone_performance'], indent=2)}
"""

    def add_comparison_data(self, base_prompt: str, metrics_data: Dict) -> str:
        """Add comparison data to prompt if available"""
        if 'comparison' in metrics_data:
            comparison = metrics_data['comparison']
            base_prompt += f"""

COMPARISON WITH PREVIOUS PERIOD ({comparison['period']['start_date']} to {comparison['period']['end_date']}):
- Previous Average Daily Footfall: {comparison['metrics']['avg_daily_footfall']} visitors
- Previous Average Daily Unique Visitors: {comparison['metrics']['avg_daily_unique_visitors']} people
- Previous Average Dwell Time: {comparison['metrics']['avg_dwell_time_minutes']} minutes
- Previous Conversion Rate: {comparison['metrics']['conversion_rate_percent']}%

PERFORMANCE CHANGES:
- Footfall Change: {metrics_data['overall_metrics']['avg_daily_footfall'] - comparison['metrics']['avg_daily_footfall']:+.1f} visitors/day
- Unique Visitors Change: {metrics_data['overall_metrics']['avg_daily_unique_visitors'] - comparison['metrics']['avg_daily_unique_visitors']:+.1f} people/day
- Dwell Time Change: {metrics_data['overall_metrics']['avg_dwell_time_minutes'] - comparison['metrics']['avg_dwell_time_minutes']:+.1f} minutes
- Conversion Rate Change: {metrics_data['overall_metrics']['conversion_rate_percent'] - comparison['metrics']['conversion_rate_percent']:+.2f}%
"""
        return base_prompt

    def create_weekly_analysis_prompt(self, store_name: str, metrics_data: Dict) -> str:
        """Create prompt for weekly analysis"""
        base_prompt = self.create_base_prompt(store_name, metrics_data)
        base_prompt = self.add_comparison_data(base_prompt, metrics_data)
        
        base_prompt += """

ANALYSIS REQUIREMENTS:
Provide a comprehensive weekly performance analysis focusing on:
1. Overall performance trends and patterns
2. Peak hours optimization opportunities
3. Zone-specific performance insights
4. Customer behavior patterns
5. Operational efficiency recommendations

RESPONSE FORMAT:
Provide insights in a professional, actionable format suitable for store management.
Include specific numerical targets and timeframes where applicable.
Focus on practical, implementable recommendations.
"""
        return base_prompt

    def create_promo_analysis_prompt(self, store_name: str, metrics_data: Dict, promo_data: Dict) -> str:
        """Create prompt for promotion effectiveness analysis"""
        base_prompt = self.create_base_prompt(store_name, metrics_data)
        base_prompt = self.add_comparison_data(base_prompt, metrics_data)
        
        base_prompt += f"""

PROMOTION DETAILS:
- Promotion Name: {promo_data.get('name', 'Unnamed Promotion')}
- Promotion Type: {promo_data.get('promotion_type', 'Unknown')}
- Duration: {promo_data.get('start_date')} to {promo_data.get('end_date')}
- Target Zones: {promo_data.get('target_zones', [])}
- Expected Impact: {promo_data.get('expected_impact_percentage', 0)}%

PROMOTION ANALYSIS REQUIREMENTS:
1. Effectiveness Assessment: Compare actual performance vs. baseline and expectations
2. Zone Impact Analysis: Evaluate performance in targeted vs. non-targeted zones  
3. Customer Behavior Changes: Analyze dwell time and conversion changes
4. ROI Implications: Assess the promotion's impact on overall store performance
5. Optimization Recommendations: Suggest improvements for future promotions

Provide an effectiveness score from 0-100 where:
- 90-100: Exceptional performance, exceeded all expectations
- 70-89: Good performance, met most objectives
- 50-69: Moderate performance, mixed results
- 30-49: Below expectations, limited impact
- 0-29: Poor performance, failed to achieve objectives

RESPONSE FORMAT:
Include the effectiveness score as a number at the end: EFFECTIVENESS_SCORE: [number]
"""
        return base_prompt

    def create_festival_analysis_prompt(self, store_name: str, metrics_data: Dict, festival_data: Dict) -> str:
        """Create prompt for festival/seasonal analysis"""
        base_prompt = self.create_base_prompt(store_name, metrics_data)
        base_prompt = self.add_comparison_data(base_prompt, metrics_data)
        
        base_prompt += f"""

FESTIVAL/SEASONAL EVENT DETAILS:
- Event Name: {festival_data.get('name', 'Seasonal Event')}
- Event Type: {festival_data.get('event_type', 'Festival')}
- Duration: {festival_data.get('start_date')} to {festival_data.get('end_date')}
- Expected Customer Behavior: {festival_data.get('expected_behavior', 'Increased shopping activity')}

FESTIVAL IMPACT ANALYSIS REQUIREMENTS:
1. Seasonal Spike Detection: Identify and quantify traffic increases
2. Shopping Pattern Changes: Analyze shifts in customer behavior
3. Zone Performance During Festival: Evaluate which areas benefited most
4. Peak Time Variations: Identify changes in busy hours
5. Preparation Recommendations: Suggest improvements for future seasonal events

RESPONSE FORMAT:
Focus on seasonal retail insights and crowd management recommendations.
Include specific observations about customer flow patterns during the festival period.
"""
        return base_prompt

    async def generate_insights(self, insight_request: InsightRequest) -> GeneratedInsight:
        """Generate AI insights based on request type"""
        try:
            # Get store information
            conn = await self.get_connection()
            store_info = await conn.fetchrow("""
                SELECT s.name, u.name as owner_name 
                FROM stores s 
                JOIN users u ON s.user_id = u.id 
                WHERE s.id = $1
            """, insight_request.store_id)
            await conn.close()
            
            store_name = store_info['name'] if store_info else f"Store {insight_request.store_id}"
            
            # Create appropriate prompt based on insight type
            if insight_request.insight_type == "promo_effectiveness":
                prompt = self.create_promo_analysis_prompt(
                    store_name, 
                    insight_request.metrics_data, 
                    insight_request.promotion_data
                )
            elif insight_request.insight_type == "festival_analysis":
                prompt = self.create_festival_analysis_prompt(
                    store_name, 
                    insight_request.metrics_data, 
                    insight_request.promotion_data
                )
            else:  # weekly, monthly, or general analysis
                prompt = self.create_weekly_analysis_prompt(
                    store_name, 
                    insight_request.metrics_data
                )
            
            # Generate insights using OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a professional retail analytics consultant with expertise in customer behavior analysis, store optimization, and data-driven business insights. Provide actionable, specific recommendations based on the data provided."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            insights_text = response.choices[0].message.content
            
            # Extract effectiveness score if present (for promo analysis)
            effectiveness_score = None
            if "EFFECTIVENESS_SCORE:" in insights_text:
                try:
                    score_text = insights_text.split("EFFECTIVENESS_SCORE:")[1].strip().split()[0]
                    effectiveness_score = float(score_text)
                    # Remove the score from the main text
                    insights_text = insights_text.split("EFFECTIVENESS_SCORE:")[0].strip()
                except:
                    pass
            
            # Generate structured recommendations using a second API call
            recommendations_prompt = f"""
Based on this retail analytics analysis, extract and format the key recommendations as a JSON array.
Each recommendation should have: "category", "action", "priority" (High/Medium/Low), "timeline" (Immediate/Short-term/Long-term), "expected_impact".

Analysis text:
{insights_text}

Return only valid JSON array format.
"""
            
            recommendations_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": recommendations_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            try:
                recommendations = json.loads(recommendations_response.choices[0].message.content)
                if not isinstance(recommendations, list):
                    recommendations = []
            except:
                recommendations = []
            
            # Calculate confidence score based on data completeness
            confidence_score = self.calculate_confidence_score(insight_request.metrics_data)
            
            return GeneratedInsight(
                insights_text=insights_text,
                recommendations=recommendations,
                confidence_score=confidence_score,
                effectiveness_score=effectiveness_score
            )
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            raise
    
    def calculate_confidence_score(self, metrics_data: Dict) -> float:
        """Calculate confidence score based on data completeness and quality"""
        score = 0.0
        
        # Base score for having data
        if metrics_data.get('overall_metrics'):
            score += 30
        
        # Bonus for comparison data
        if metrics_data.get('comparison'):
            score += 20
        
        # Bonus for zone performance data
        if metrics_data.get('zone_performance') and len(metrics_data['zone_performance']) > 0:
            score += 20
        
        # Bonus for peak hours data
        if metrics_data.get('peak_hours') and len(metrics_data['peak_hours']) > 0:
            score += 15
        
        # Bonus for sufficient data period
        total_days = metrics_data.get('period', {}).get('total_days', 0)
        if total_days >= 7:
            score += 15
        elif total_days >= 3:
            score += 10
        elif total_days >= 1:
            score += 5
        
        return min(score, 100.0)
    
    async def save_insights_to_db(self, 
                                 insight_request: InsightRequest, 
                                 generated_insight: GeneratedInsight,
                                 promotion_id: Optional[int] = None) -> int:
        """Save generated insights to database"""
        conn = await self.get_connection()
        try:
            insight_id = await conn.fetchval("""
                INSERT INTO ai_insights (
                    store_id, insight_type, period_start, period_end,
                    metrics_summary, insights_text, recommendations,
                    confidence_score, promotion_id, effectiveness_score
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
            """, 
                insight_request.store_id,
                insight_request.insight_type,
                insight_request.period_start,
                insight_request.period_end,
                json.dumps(insight_request.metrics_data),
                generated_insight.insights_text,
                json.dumps(generated_insight.recommendations),
                generated_insight.confidence_score,
                promotion_id,
                generated_insight.effectiveness_score
            )
            
            return insight_id
            
        except Exception as e:
            logger.error(f"Error saving insights to database: {e}")
            raise
        finally:
            await conn.close()
    
    async def get_insights_history(self, store_id: int, limit: int = 10) -> List[Dict]:
        """Get recent insights history for a store"""
        conn = await self.get_connection()
        try:
            insights = await conn.fetch("""
                SELECT 
                    id, insight_type, period_start, period_end,
                    insights_text, recommendations, confidence_score,
                    effectiveness_score, generated_at, p.name as promotion_name
                FROM ai_insights ai
                LEFT JOIN promotions p ON ai.promotion_id = p.id
                WHERE ai.store_id = $1
                ORDER BY generated_at DESC
                LIMIT $2
            """, store_id, limit)
            
            return [
                {
                    "id": insight['id'],
                    "type": insight['insight_type'],
                    "period": {
                        "start": insight['period_start'].isoformat(),
                        "end": insight['period_end'].isoformat()
                    },
                    "insights": insight['insights_text'],
                    "recommendations": insight['recommendations'],
                    "confidence_score": insight['confidence_score'],
                    "effectiveness_score": insight['effectiveness_score'],
                    "promotion_name": insight['promotion_name'],
                    "generated_at": insight['generated_at'].isoformat()
                } for insight in insights
            ]
            
        except Exception as e:
            logger.error(f"Error getting insights history: {e}")
            raise
        finally:
            await conn.close()

# Main insights generation function
async def generate_store_insights(
    database_url: str,
    store_id: int,
    period_start: date,
    period_end: date,
    insight_type: str,
    metrics_data: Dict,
    promotion_data: Optional[Dict] = None
) -> Dict:
    """Generate and save insights for a store"""
    
    generator = OpenAIInsightsGenerator(database_url)
    
    # Create insight request
    request = InsightRequest(
        store_id=store_id,
        period_start=period_start,
        period_end=period_end,
        insight_type=insight_type,
        metrics_data=metrics_data,
        promotion_data=promotion_data
    )
    
    # Generate insights
    generated_insight = await generator.generate_insights(request)
    
    # Get promotion ID if applicable
    promotion_id = None
    if promotion_data and 'id' in promotion_data:
        promotion_id = promotion_data['id']
    
    # Save to database
    insight_id = await generator.save_insights_to_db(
        request, 
        generated_insight, 
        promotion_id
    )
    
    return {
        "id": insight_id,
        "insights": generated_insight.insights_text,
        "recommendations": generated_insight.recommendations,
        "confidence_score": generated_insight.confidence_score,
        "effectiveness_score": generated_insight.effectiveness_score,
        "generated_at": datetime.now().isoformat()
    }

# Initialize insights generator
def create_insights_generator(database_url: str) -> OpenAIInsightsGenerator:
    """Create insights generator instance"""
    return OpenAIInsightsGenerator(database_url)