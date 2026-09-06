from typing import Dict, List, Optional
from datetime import datetime

class ChangeDetector:
    """Detects meaningful changes in stock data"""
    
    def __init__(self):
        # Configurable thresholds
        self.thresholds = {
            'price': {
                'normal': 2.0,
                'worth_watching': 4.0,
                'significant': 7.0
            },
            'volume': {
                'normal': 30.0,
                'moderate': 70.0
            }
        }
    
    def detect_meaningful_changes(
        self,
        previous_snapshot: Dict,
        current_snapshot: Dict,
        events: List[Dict] = None
    ) -> Dict:
        """
        Detect if changes are meaningful
        
        Returns:
            {
                'is_meaningful': bool,
                'price_change_percent': float,
                'volume_change_percent': float,
                'severity': str,  # normal, worth_watching, significant, needs_attention
                'reasons': List[str],
                'attention_score': int
            }
        """
        if events is None:
            events = []
        
        price_change = self._calculate_price_change(previous_snapshot, current_snapshot)
        volume_change = self._calculate_volume_change(previous_snapshot, current_snapshot)
        
        severity = self._determine_severity(price_change, volume_change, events)
        reasons = self._generate_reasons(price_change, volume_change, events, current_snapshot)
        attention_score = self._calculate_attention_score(price_change, volume_change, events, current_snapshot)
        
        is_meaningful = severity != 'normal'
        
        return {
            'is_meaningful': is_meaningful,
            'price_change_percent': round(price_change, 2),
            'volume_change_percent': round(volume_change, 2),
            'severity': severity,
            'reasons': reasons,
            'attention_score': attention_score
        }
    
    def _calculate_price_change(self, previous: Dict, current: Dict) -> float:
        """Calculate percentage price change"""
        if not previous or not previous.get('price'):
            return 0.0
        
        prev_price = previous['price']
        curr_price = current['price']
        
        return ((curr_price - prev_price) / prev_price) * 100
    
    def _calculate_volume_change(self, previous: Dict, current: Dict) -> float:
        """Calculate percentage volume change"""
        if not previous or not previous.get('volume'):
            return 0.0
        
        prev_volume = previous['volume']
        curr_volume = current['volume']
        
        if prev_volume == 0:
            return 0.0
        
        return ((curr_volume - prev_volume) / prev_volume) * 100
    
    def _determine_severity(self, price_change: float, volume_change: float, events: List[Dict]) -> str:
        """Determine severity level"""
        abs_price_change = abs(price_change)
        abs_volume_change = abs(volume_change)
        
        # High severity
        if abs_price_change >= self.thresholds['price']['significant']:
            return 'needs_attention'
        
        if abs_price_change >= self.thresholds['price']['worth_watching'] and abs_volume_change >= self.thresholds['volume']['moderate']:
            return 'needs_attention'
        
        # Significant
        if abs_price_change >= self.thresholds['price']['worth_watching']:
            return 'significant'
        
        if abs_volume_change >= self.thresholds['volume']['moderate'] and abs_price_change >= self.thresholds['price']['normal']:
            return 'significant'
        
        # Worth watching
        if abs_price_change >= self.thresholds['price']['normal']:
            return 'worth_watching'
        
        if abs_volume_change >= self.thresholds['volume']['normal']:
            return 'worth_watching'
        
        if len(events) > 0:
            return 'worth_watching'
        
        return 'normal'
    
    def _generate_reasons(self, price_change: float, volume_change: float, events: List[Dict], current_snapshot: Dict) -> List[str]:
        """Generate human-readable reasons for the change"""
        reasons = []
        
        abs_price_change = abs(price_change)
        abs_volume_change = abs(volume_change)
        
        # Price movement reasons
        if abs_price_change >= self.thresholds['price']['significant']:
            reasons.append("Unusual price movement")
        elif abs_price_change >= self.thresholds['price']['worth_watching']:
            reasons.append("Notable price change")
        
        # Volume reasons
        if abs_volume_change >= self.thresholds['volume']['moderate']:
            reasons.append("Trading volume significantly increased")
        elif abs_volume_change >= self.thresholds['volume']['normal']:
            reasons.append("Volume higher than usual")
        
        # Event reasons
        if len(events) > 0:
            reasons.append(f"{len(events)} new market event(s)")
        
        # 52-week high/low
        if current_snapshot.get('week_52_high') and current_snapshot.get('price'):
            if current_snapshot['price'] >= current_snapshot['week_52_high'] * 0.99:
                reasons.append("Near 52-week high")
        
        if current_snapshot.get('week_52_low') and current_snapshot.get('price'):
            if current_snapshot['price'] <= current_snapshot['week_52_low'] * 1.01:
                reasons.append("Near 52-week low")
        
        if not reasons:
            reasons.append("No meaningful change")
        
        return reasons
    
    def _calculate_attention_score(self, price_change: float, volume_change: float, events: List[Dict], current_snapshot: Dict) -> int:
        """
        Calculate attention score (0-100)
        
        Weighting:
        - Price movement: 40%
        - Volume anomaly: 25%
        - News/events: 20%
        - Other signals: 15%
        """
        score = 0
        
        # Price movement score (0-40)
        abs_price_change = abs(price_change)
        if abs_price_change >= 10:
            price_score = 40
        elif abs_price_change >= 7:
            price_score = 35
        elif abs_price_change >= 4:
            price_score = 25
        elif abs_price_change >= 2:
            price_score = 15
        else:
            price_score = int(abs_price_change * 5)
        
        score += price_score
        
        # Volume anomaly score (0-25)
        abs_volume_change = abs(volume_change)
        if abs_volume_change >= 100:
            volume_score = 25
        elif abs_volume_change >= 70:
            volume_score = 20
        elif abs_volume_change >= 30:
            volume_score = 10
        else:
            volume_score = int(abs_volume_change * 0.2)
        
        score += volume_score
        
        # News/events score (0-20)
        event_score = min(len(events) * 7, 20)
        score += event_score
        
        # Other signals score (0-15)
        other_score = 0
        
        # 52-week high/low
        if current_snapshot.get('week_52_high') and current_snapshot.get('price'):
            if current_snapshot['price'] >= current_snapshot['week_52_high'] * 0.99:
                other_score += 10
        
        if current_snapshot.get('week_52_low') and current_snapshot.get('price'):
            if current_snapshot['price'] <= current_snapshot['week_52_low'] * 1.01:
                other_score += 10
        
        score += min(other_score, 15)
        
        return min(score, 100)
    
    def classify_attention_score(self, score: int) -> str:
        """Classify attention score into severity category"""
        if score >= 81:
            return 'needs_attention'
        elif score >= 61:
            return 'significant'
        elif score >= 31:
            return 'worth_watching'
        else:
            return 'normal'
