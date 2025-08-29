#!/usr/bin/env python3
"""
Example script demonstrating agent performance analysis functionality.
This script shows how to:
1. Create a call with agent type specification
2. Analyze agent performance using OpenAI
3. View the analysis results
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
CALL_ID = f"example_call_{int(time.time())}"

# Sample transcript data
SAMPLE_TRANSCRIPT = {
    "turns": [
        {
            "role": "agent",
            "content": "Hello! Thank you for calling our customer support line. My name is Sarah, and I'm here to help you today. How may I assist you?",
            "timestamp": "2024-01-15T10:00:00Z"
        },
        {
            "role": "customer",
            "content": "Hi Sarah, I'm having trouble with my account login. I keep getting an error message when I try to sign in.",
            "timestamp": "2024-01-15T10:00:15Z"
        },
        {
            "role": "agent",
            "content": "I understand that can be frustrating. Let me help you resolve this login issue. Can you tell me what specific error message you're seeing?",
            "timestamp": "2024-01-15T10:00:30Z"
        },
        {
            "role": "customer",
            "content": "It says 'Invalid credentials' but I know my password is correct.",
            "timestamp": "2024-01-15T10:00:45Z"
        },
        {
            "role": "agent",
            "content": "Thank you for that information. Let me check your account status. Can you confirm your email address so I can look up your account?",
            "timestamp": "2024-01-15T10:01:00Z"
        },
        {
            "role": "customer",
            "content": "Sure, it's customer@example.com",
            "timestamp": "2024-01-15T10:01:15Z"
        },
        {
            "role": "agent",
            "content": "Perfect, I can see your account. It looks like your account was temporarily locked due to multiple failed login attempts. I can unlock it for you right now. Would you like me to do that?",
            "timestamp": "2024-01-15T10:01:45Z"
        },
        {
            "role": "customer",
            "content": "Yes, please! That would be great.",
            "timestamp": "2024-01-15T10:02:00Z"
        },
        {
            "role": "agent",
            "content": "Excellent! I've unlocked your account. You should now be able to log in successfully. I also recommend changing your password to something unique if you haven't done so recently. Is there anything else I can help you with today?",
            "timestamp": "2024-01-15T10:02:15Z"
        },
        {
            "role": "customer",
            "content": "No, that's all I needed. Thank you so much for your help, Sarah!",
            "timestamp": "2024-01-15T10:02:30Z"
        },
        {
            "role": "agent",
            "content": "You're very welcome! I'm glad I could help resolve your login issue. Have a wonderful day, and don't hesitate to call back if you need anything else. Goodbye!",
            "timestamp": "2024-01-15T10:02:45Z"
        }
    ],
    "participants": ["agent", "customer"],
    "duration": 165,
    "call_type": "customer_support"
}

def create_call_with_agent_analysis():
    """Create a call with agent type specification for automatic analysis."""
    
    print(f"🚀 Creating call with agent analysis...")
    print(f"Call ID: {CALL_ID}")
    print(f"Agent Type: customer_support")
    print()
    
    # Create call data with agent type
    call_data = {
        "call_id": CALL_ID,
        "transcript": SAMPLE_TRANSCRIPT,
        "audio_file_url": "https://example.com/sample-audio.mp3",  # Placeholder URL
        "agent_type": "customer_support",
        "call_context": "Customer experiencing login issues, needs account unlocked",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Create the call
        response = requests.post(
            f"{API_BASE_URL}/api/calls/",
            json=call_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            call_result = response.json()
            print("✅ Call created successfully!")
            print(f"   Call ID: {call_result['call_id']}")
            print(f"   Timestamp: {call_result['timestamp']}")
            
            # Check if agent analysis was performed
            if call_result.get('processed_data', {}).get('agent_analysis'):
                print("✅ Agent analysis completed automatically!")
                return call_result
            else:
                print("⚠️  Call created but agent analysis not performed")
                return call_result
        else:
            print(f"❌ Failed to create call: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def analyze_existing_call():
    """Analyze an existing call with a different agent type."""
    
    print(f"\n🔍 Analyzing existing call with different agent type...")
    
    # Request analysis with sales agent perspective
    analysis_request = {
        "call_id": CALL_ID,
        "agent_type": "sales_agent",
        "call_context": "Analyze from sales perspective - identify upsell opportunities"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/calls/{CALL_ID}/analyze-agent",
            json=analysis_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            analysis_result = response.json()
            print("✅ Agent analysis completed!")
            print(f"   Agent Type: {analysis_result['agent_type']}")
            print(f"   Agent Name: {analysis_result['agent_name']}")
            print(f"   Success: {analysis_result['success']}")
            
            if analysis_result['success']:
                overall_score = analysis_result['analysis_result'].get('overall_assessment', {}).get('overall_score', 0)
                print(f"   Overall Score: {overall_score}/100")
                
                # Show key insights
                goal_achievement = analysis_result['analysis_result'].get('goal_achievement', {})
                if goal_achievement:
                    print(f"   Goals Achieved: {goal_achievement.get('achieved', False)}")
                    print(f"   Goal Score: {goal_achievement.get('score', 0)}/100")
                
                return analysis_result
            else:
                print(f"   Error: {analysis_result.get('error_message', 'Unknown error')}")
                return None
        else:
            print(f"❌ Analysis failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def get_call_details():
    """Retrieve and display call details including analysis."""
    
    print(f"\n📋 Retrieving call details...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/calls/{CALL_ID}")
        
        if response.status_code == 200:
            call_details = response.json()
            print("✅ Call details retrieved!")
            print(f"   Call ID: {call_details['call_id']}")
            print(f"   Timestamp: {call_details['timestamp']}")
            
            # Check for processed data
            if call_details.get('processed_data'):
                print("   ✅ Has processed data")
                
                # Check for agent analysis
                if call_details['processed_data'].get('agent_analysis'):
                    agent_analysis = call_details['processed_data']['agent_analysis']
                    print("   ✅ Has agent analysis")
                    
                    # Display analysis summary
                    if 'overall_assessment' in agent_analysis:
                        overall = agent_analysis['overall_assessment']
                        print(f"      Overall Score: {overall.get('overall_score', 0)}/100")
                        print(f"      Summary: {overall.get('summary', 'No summary available')}")
                    
                    if 'goal_achievement' in agent_analysis:
                        goals = agent_analysis['goal_achievement']
                        print(f"      Goals Achieved: {goals.get('achieved', False)}")
                        print(f"      Goal Score: {goals.get('score', 0)}/100")
                    
                    if 'script_adherence' in agent_analysis:
                        script = agent_analysis['script_adherence']
                        print(f"      Script Followed: {script.get('followed_script', False)}")
                        print(f"      Script Score: {script.get('score', 0)}/100")
                else:
                    print("   ❌ No agent analysis found")
                
                # Check for other processed data
                if call_details['processed_data'].get('summary'):
                    print("   ✅ Has call health summary")
                if call_details['processed_data'].get('pauses'):
                    print("   ✅ Has pause analysis")
            else:
                print("   ❌ No processed data found")
            
            return call_details
        else:
            print(f"❌ Failed to retrieve call: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def main():
    """Main function to demonstrate the agent analysis functionality."""
    
    print("=" * 60)
    print("🤖 AGENT PERFORMANCE ANALYSIS DEMONSTRATION")
    print("=" * 60)
    print()
    
    # Step 1: Create a call with agent analysis
    call_result = create_call_with_agent_analysis()
    if not call_result:
        print("❌ Cannot continue without creating a call")
        return
    
    # Wait a moment for processing
    print("\n⏳ Waiting for processing to complete...")
    time.sleep(2)
    
    # Step 2: Get call details to see the analysis
    call_details = get_call_details()
    if not call_details:
        print("❌ Cannot retrieve call details")
        return
    
    # Step 3: Analyze with different agent type
    analysis_result = analyze_existing_call()
    if not analysis_result:
        print("❌ Cannot perform additional analysis")
        return
    
    # Step 4: Get updated call details
    print("\n⏳ Waiting for reanalysis to complete...")
    time.sleep(2)
    
    updated_call = get_call_details()
    
    print("\n" + "=" * 60)
    print("🎉 DEMONSTRATION COMPLETED!")
    print("=" * 60)
    print()
    print("What was demonstrated:")
    print("✅ Created a call with automatic agent analysis")
    print("✅ Analyzed the same call with a different agent type")
    print("✅ Retrieved call details including analysis results")
    print()
    print("Next steps:")
    print("1. View the call in the web interface")
    print("2. Explore the agent analysis results")
    print("3. Try different agent types and contexts")
    print("4. Use the re-analyze functionality in the UI")
    print()
    print(f"Call ID for reference: {CALL_ID}")

if __name__ == "__main__":
    main()
