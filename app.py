from anthropic import Anthropic
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)
CORS(app)

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

VISA_ANALYSIS_PROMPT = """You are an expert US immigration attorney. Analyze this candidate's profile and provide visa eligibility assessment.

Candidate Profile:
- Education: {education}
- Work Experience: {experience} years in {field}
- Current Status: {current_status}
- Has Job Offer: {has_offer}
- Job Details: {job_details}
- Special Achievements: {achievements}
- Country of Origin: {country}

Analyze eligibility for these visa categories:
1. H-1B (Specialty Occupation)
2. O-1A (Extraordinary Ability - Sciences/Business/Education)
3. O-1B (Extraordinary Ability - Arts/Entertainment)
4. EB-2 (Advanced Degree or Exceptional Ability)
5. EB-3 (Skilled Worker)
6. L-1 (Intracompany Transfer, if applicable)

For EACH visa type, provide:
- eligible: "yes" | "maybe" | "no"
- confidence: 1-10
- reasoning: detailed explanation (2-3 sentences)
- requirements_met: list of requirements they satisfy
- requirements_missing: list of requirements they don't meet
- next_steps: concrete actions they should take
- timeline: estimated processing time
- estimated_cost: filing fees + attorney fees range

Also provide:
- recommended_path: which visa to pursue first
- overall_assessment: 2-3 sentence summary
- risk_factors: potential issues to address

Respond with ONLY valid JSON. No markdown, no backticks, no additional text.

JSON structure:
{{
  "visas": {{
    "H1B": {{
      "eligible": "yes|maybe|no",
      "confidence": 8,
      "reasoning": "...",
      "requirements_met": [],
      "requirements_missing": [],
      "next_steps": [],
      "timeline": "...",
      "estimated_cost": "..."
    }},
    // ... other visas
  }},
  "recommended_path": "...",
  "overall_assessment": "...",
  "risk_factors": []
}}"""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json

        # Build prompt with user data
        prompt = VISA_ANALYSIS_PROMPT.format(
            education=data.get('education', ''),
            experience=data.get('experience', ''),
            field=data.get('field', ''),
            current_status=data.get('current_status', ''),
            has_offer=data.get('has_offer', 'No'),
            job_details=data.get('job_details', 'N/A'),
            achievements=data.get('achievements', 'None'),
            country=data.get('country', '')
        )

        # Call Claude API
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            temperature=0.3,  # Lower temp for more consistent analysis
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Parse response
        response_text = message.content[0].text

        # Clean up response (remove markdown if present)
        response_text = response_text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        result = json.loads(response_text)

        return jsonify({
            'success': True,
            'analysis': result
        })

    except json.JSONDecodeError as e:
        return jsonify({
            'success': False,
            'error': f'Failed to parse AI response: {str(e)}',
            'raw_response': response_text
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)