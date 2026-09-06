from typing import Dict, Optional
import os
try:
    import google.genai as genai
    GENAI_NEW = True
    print("✅ Using new google.genai package")
except ImportError:
    try:
        import google.generativeai as genai
        GENAI_NEW = False
        print("⚠️ Using deprecated google.generativeai package")
    except ImportError:
        genai = None
        GENAI_NEW = False
        print("❌ No Gemini package found")
import requests
import json

class ExplanationService:
    """Generates explanations for stock changes using AI"""
    
    def __init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        
        # Initialize Gemini if key available
        if self.gemini_api_key and self.gemini_api_key != 'demo' and genai:
            try:
                if GENAI_NEW:
                    # New google.genai package
                    client = genai.Client(api_key=self.gemini_api_key)
                    self.gemini_client = client
                    self.gemini_model = 'gemini-1.5-pro'
                else:
                    # Old google.generativeai package
                    genai.configure(api_key=self.gemini_api_key)
                    self.gemini_model = genai.GenerativeModel('gemini-pro')
                self.use_gemini = True
                print("✅ Gemini AI initialized")
            except Exception as e:
                print(f"⚠️  Gemini initialization failed: {e}")
                self.use_gemini = False
        else:
            self.use_gemini = False
        
        # Check Groq availability
        self.use_groq = bool(self.groq_api_key and self.groq_api_key != 'demo')
        if self.use_groq:
            print("✅ Groq API available as fallback")
    
    def generate_explanation(self, ticker: str, change_data: Dict, current_data: Dict) -> str:
        """
        Generate explanation for why a stock change matters
        
        Priority:
        1. Gemini AI (primary)
        2. Groq API (fallback)
        3. Template-based (last resort)
        """
        # Try Gemini first
        if self.use_gemini:
            try:
                return self._generate_gemini_explanation(ticker, change_data, current_data)
            except Exception as e:
                print(f"Gemini failed: {e}, trying Groq...")
        
        # Try Groq as fallback
        if self.use_groq:
            try:
                return self._generate_groq_explanation(ticker, change_data, current_data)
            except Exception as e:
                print(f"Groq failed: {e}, using template...")
        
        # Fallback to template
        return self._generate_template_explanation(ticker, change_data, current_data)
    
    def _generate_gemini_explanation(self, ticker: str, change_data: Dict, current_data: Dict) -> str:
        """Generate AI-powered explanation using Gemini"""
        price_change = change_data.get('price_change_percent', 0)
        volume_change = change_data.get('volume_change_percent', 0)
        severity = change_data.get('severity', 'normal')
        reasons = change_data.get('reasons', [])
        company_name = current_data.get('company_name', ticker)
        
        prompt = f"""You are a financial analyst explaining stock movements to investors. Be concise and actionable.

Stock: {company_name} ({ticker})
Price Change: {price_change:.2f}%
Volume Change: {volume_change:.2f}%
Severity: {severity}
Factors: {', '.join(reasons)}

Generate a 2-3 sentence explanation focusing on:
1. What changed (the movement)
2. Why it matters (context and significance)
3. What to watch next (if severity is high)

Keep it conversational, clear, and under 100 words."""

        if GENAI_NEW:
            # New google.genai API
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=prompt
            )
            if response and response.text:
                return response.text.strip()
        else:
            # Old google.generativeai API
            response = self.gemini_model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        
        raise Exception("Empty Gemini response")
    
    def _generate_groq_explanation(self, ticker: str, change_data: Dict, current_data: Dict) -> str:
        """Generate explanation using Groq API"""
        price_change = change_data.get('price_change_percent', 0)
        volume_change = change_data.get('volume_change_percent', 0)
        severity = change_data.get('severity', 'normal')
        reasons = change_data.get('reasons', [])
        company_name = current_data.get('company_name', ticker)
        
        prompt = f"""You are a financial analyst. Explain this stock movement concisely:

{company_name} ({ticker}):
- Price: {price_change:+.2f}%
- Volume: {volume_change:+.2f}%
- Severity: {severity}
- Factors: {', '.join(reasons)}

Provide a brief 2-3 sentence explanation. Focus on what changed and why it matters."""

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": "You are a concise financial analyst."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data['choices'][0]['message']['content'].strip()
    
    def _generate_template_explanation(self, ticker: str, change_data: Dict, current_data: Dict) -> str:
        """Generate template-based explanation (fallback)"""
        price_change = change_data.get('price_change_percent', 0)
        volume_change = change_data.get('volume_change_percent', 0)
        severity = change_data.get('severity', 'normal')
        
        company_name = current_data.get('company_name', ticker)
        
        if severity == 'normal':
            return f"{company_name} is trading normally with minimal price movement."
        
        # Build explanation
        parts = []
        
        # Price movement
        direction = "up" if price_change > 0 else "down"
        abs_change = abs(price_change)
        
        if abs_change >= 7:
            parts.append(f"{company_name} moved {abs_change:.1f}% {direction} since your last visit, significantly above its recent normal movement.")
        elif abs_change >= 4:
            parts.append(f"{company_name} experienced a {abs_change:.1f}% {direction} movement since your last check.")
        elif abs_change >= 2:
            parts.append(f"{company_name} moved {abs_change:.1f}% {direction}.")
        
        # Volume
        if abs(volume_change) >= 70:
            parts.append(f"Trading volume is {abs(volume_change):.0f}% higher, indicating unusually strong market activity.")
        elif abs(volume_change) >= 30:
            parts.append(f"Volume increased by {abs(volume_change):.0f}%.")
        
        # Combine
        if not parts:
            return f"{company_name} shows some activity worth monitoring."
        
        return " ".join(parts)
    
    def generate_batch_summary(self, changes: list) -> str:
        """Generate summary of all changes"""
        if not changes:
            return "No significant changes in your watchlist."
        
        needs_attention = [c for c in changes if c.get('severity') == 'needs_attention']
        significant = [c for c in changes if c.get('severity') == 'significant']
        worth_watching = [c for c in changes if c.get('severity') == 'worth_watching']
        
        parts = []
        
        if needs_attention:
            parts.append(f"{len(needs_attention)} stock(s) need immediate attention")
        
        if significant:
            parts.append(f"{len(significant)} showing significant movement")
        
        if worth_watching:
            parts.append(f"{len(worth_watching)} worth monitoring")
        
        if not parts:
            return "Your watchlist is stable with minimal changes."
        
        summary = ", ".join(parts) + "."
        
        # Try AI-powered batch summary if available
        if self.use_gemini and len(changes) > 0:
            try:
                return self._generate_ai_batch_summary(changes, summary)
            except Exception:
                pass
        
        return summary
    
    def _generate_ai_batch_summary(self, changes: list, basic_summary: str) -> str:
        """Generate AI-powered batch summary"""
        top_changes = sorted(changes, key=lambda x: x.get('attention_score', 0), reverse=True)[:5]
        
        prompt = f"""Summarize these stock movements for an investor who hasn't checked in a while:

{basic_summary}

Top movements:
"""
        for c in top_changes:
            prompt += f"- {c.get('ticker')}: {c.get('price_change_percent', 0):+.1f}% ({c.get('severity')})\n"
        
        prompt += "\nProvide a 1-2 sentence executive summary. What's the overall market sentiment for this watchlist?"
        
        try:
            if GENAI_NEW:
                response = self.gemini_client.models.generate_content(
                    model=self.gemini_model,
                    contents=prompt
                )
                if response and response.text:
                    return response.text.strip()
            else:
                response = self.gemini_model.generate_content(prompt)
                if response and response.text:
                    return response.text.strip()
        except Exception:
            pass
        
        return basic_summary
