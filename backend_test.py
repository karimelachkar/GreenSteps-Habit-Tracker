import requests
import unittest
import uuid
import time
from datetime import datetime

# Backend API URL
API_URL = "https://78299146-1fae-4c60-b8b7-8455ec49569c.preview.emergentagent.com"

class GreenStepsAPITest(unittest.TestCase):
    # Class variables to share state between tests
    token = None
    habit_id = None
    test_user = None
    
    @classmethod
    def setUpClass(cls):
        cls.api_url = API_URL
        cls.test_user = {
            "name": f"Test User {uuid.uuid4()}",
            "email": f"test_{uuid.uuid4()}@example.com",
            "password": "TestPassword123!"
        }
        print(f"\n🔍 Testing with user: {cls.test_user['email']}")

    def test_01_signup(self):
        """Test user signup"""
        print(f"\n🔍 Testing signup...")
        
        response = requests.post(
            f"{self.api_url}/api/auth/signup",
            json=self.__class__.test_user
        )
        
        self.assertEqual(response.status_code, 200, f"Signup failed: {response.text}")
        self.assertIn("access_token", response.json(), "Token not found in response")
        
        # Save token for subsequent tests
        self.__class__.token = response.json()["access_token"]
        print(f"✅ Signup successful, token received")

    def test_02_login_with_wrong_password(self):
        """Test login with incorrect credentials"""
        print(f"\n🔍 Testing login with incorrect password...")
        
        response = requests.post(
            f"{self.api_url}/api/auth/login",
            json={
                "email": self.__class__.test_user["email"],
                "password": "WrongPassword123!"
            }
        )
        
        self.assertEqual(response.status_code, 401, "Login with wrong password should fail")
        print(f"✅ Login with wrong password correctly failed")

    def test_03_login(self):
        """Test login with correct credentials"""
        print(f"\n🔍 Testing login with correct credentials...")
        
        response = requests.post(
            f"{self.api_url}/api/auth/login",
            json={
                "email": self.__class__.test_user["email"],
                "password": self.__class__.test_user["password"]
            }
        )
        
        self.assertEqual(response.status_code, 200, f"Login failed: {response.text}")
        self.assertIn("access_token", response.json(), "Token not found in response")
        
        # Update token
        self.__class__.token = response.json()["access_token"]
        print(f"✅ Login successful, token received")

    def test_04_get_user_info(self):
        """Test getting current user info"""
        print(f"\n🔍 Testing get user info...")
        
        response = requests.get(
            f"{self.api_url}/api/auth/me",
            headers={"Authorization": f"Bearer {self.__class__.token}"}
        )
        
        self.assertEqual(response.status_code, 200, f"Get user info failed: {response.text}")
        user_data = response.json()
        self.assertEqual(user_data["name"], self.__class__.test_user["name"], "User name doesn't match")
        self.assertEqual(user_data["email"], self.__class__.test_user["email"], "User email doesn't match")
        print(f"✅ User info retrieved successfully")

    def test_05_get_preset_habits(self):
        """Test getting preset habits"""
        print(f"\n🔍 Testing get preset habits...")
        
        response = requests.get(f"{self.api_url}/api/preset-habits")
        
        self.assertEqual(response.status_code, 200, f"Get preset habits failed: {response.text}")
        habits = response.json()
        self.assertTrue(len(habits) > 0, "No preset habits returned")
        self.assertTrue(all("name" in habit and "description" in habit for habit in habits), 
                       "Habit format incorrect")
        print(f"✅ Retrieved {len(habits)} preset habits")

    def test_06_create_preset_habit(self):
        """Test creating a preset habit"""
        print(f"\n🔍 Testing create preset habit...")
        
        habit_data = {
            "habit_type": "preset",
            "habit_name": "Recycled items",
            "description": "Recycled paper, plastic, or other materials"
        }
        
        response = requests.post(
            f"{self.api_url}/api/habits",
            json=habit_data,
            headers={"Authorization": f"Bearer {self.__class__.token}"}
        )
        
        self.assertEqual(response.status_code, 200, f"Create habit failed: {response.text}")
        habit = response.json()
        self.assertEqual(habit["habit_name"], habit_data["habit_name"], "Habit name doesn't match")
        self.assertEqual(habit["description"], habit_data["description"], "Habit description doesn't match")
        
        # Save habit ID for later tests
        self.__class__.habit_id = habit["id"]
        print(f"✅ Preset habit created successfully with ID: {self.__class__.habit_id}")

    def test_07_create_custom_habit(self):
        """Test creating a custom habit"""
        print(f"\n🔍 Testing create custom habit...")
        
        habit_data = {
            "habit_type": "custom",
            "habit_name": f"Test Custom Habit {uuid.uuid4()}",
            "description": "This is a test custom habit"
        }
        
        response = requests.post(
            f"{self.api_url}/api/habits",
            json=habit_data,
            headers={"Authorization": f"Bearer {self.__class__.token}"}
        )
        
        self.assertEqual(response.status_code, 200, f"Create custom habit failed: {response.text}")
        habit = response.json()
        self.assertEqual(habit["habit_name"], habit_data["habit_name"], "Habit name doesn't match")
        self.assertEqual(habit["description"], habit_data["description"], "Habit description doesn't match")
        print(f"✅ Custom habit created successfully with ID: {habit['id']}")

    def test_08_get_habits(self):
        """Test getting user habits"""
        print(f"\n🔍 Testing get user habits...")
        
        response = requests.get(
            f"{self.api_url}/api/habits",
            headers={"Authorization": f"Bearer {self.__class__.token}"}
        )
        
        self.assertEqual(response.status_code, 200, f"Get habits failed: {response.text}")
        habits = response.json()
        self.assertTrue(len(habits) >= 2, f"Expected at least 2 habits, got {len(habits)}")
        print(f"✅ Retrieved {len(habits)} habits")

    def test_09_get_progress(self):
        """Test getting progress stats"""
        print(f"\n🔍 Testing get progress stats...")
        
        response = requests.get(
            f"{self.api_url}/api/progress",
            headers={"Authorization": f"Bearer {self.__class__.token}"}
        )
        
        self.assertEqual(response.status_code, 200, f"Get progress failed: {response.text}")
        stats = response.json()
        
        # Verify all required fields are present
        required_fields = [
            "total_habits", "this_week", "this_month", "current_streak",
            "completion_percentage", "weekly_progress", "monthly_progress"
        ]
        for field in required_fields:
            self.assertIn(field, stats, f"Missing field: {field}")
        
        # Verify weekly progress has 7 days
        self.assertEqual(len(stats["weekly_progress"]), 7, "Weekly progress should have 7 days")
        
        # Verify monthly progress has 30 days
        self.assertEqual(len(stats["monthly_progress"]), 30, "Monthly progress should have 30 days")
        
        print(f"✅ Progress stats retrieved successfully")
        print(f"   Total habits: {stats['total_habits']}")
        print(f"   Current streak: {stats['current_streak']}")
        print(f"   Completion percentage: {stats['completion_percentage']}%")

    def test_10_delete_habit(self):
        """Test deleting a habit"""
        print(f"\n🔍 Testing delete habit...")
        
        if not self.__class__.habit_id:
            self.skipTest("No habit ID available to delete")
        
        response = requests.delete(
            f"{self.api_url}/api/habits/{self.__class__.habit_id}",
            headers={"Authorization": f"Bearer {self.__class__.token}"}
        )
        
        self.assertEqual(response.status_code, 200, f"Delete habit failed: {response.text}")
        print(f"✅ Habit deleted successfully")
        
        # Verify habit is deleted
        response = requests.get(
            f"{self.api_url}/api/habits",
            headers={"Authorization": f"Bearer {self.__class__.token}"}
        )
        
        habits = response.json()
        habit_ids = [habit["id"] for habit in habits]
        self.assertNotIn(self.__class__.habit_id, habit_ids, "Habit still exists after deletion")

    def test_11_unauthorized_access(self):
        """Test unauthorized access to protected routes"""
        print(f"\n🔍 Testing unauthorized access...")
        
        # Test without token
        response = requests.get(f"{self.api_url}/api/habits")
        self.assertEqual(response.status_code, 401, "Should return 401 without token")
        
        # Test with invalid token
        response = requests.get(
            f"{self.api_url}/api/habits",
            headers={"Authorization": "Bearer invalid_token"}
        )
        self.assertEqual(response.status_code, 401, "Should return 401 with invalid token")
        
        print(f"✅ Unauthorized access correctly rejected")

    def test_12_ai_insights(self):
        """Test AI Sustainability Coach insights"""
        print(f"\n🔍 Testing AI insights...")
        
        # Ensure we have a valid token
        if not self.__class__.token:
            self.skipTest("No valid token available for AI insights test")
        
        response = requests.post(
            f"{self.api_url}/api/ai/insights",
            json={},  # Empty context is fine
            headers={"Authorization": f"Bearer {self.__class__.token}"}
        )
        
        self.assertEqual(response.status_code, 200, f"AI insights request failed: {response.text}")
        insights = response.json()
        
        # Verify we got exactly 3 insights
        self.assertEqual(len(insights), 3, f"Expected 3 insights, got {len(insights)}")
        
        # Verify each insight has the required fields
        required_fields = ["insight_type", "title", "content", "emoji"]
        insight_types = []
        
        for insight in insights:
            for field in required_fields:
                self.assertIn(field, insight, f"Missing field in insight: {field}")
            
            # Collect insight types to verify we have all three types
            insight_types.append(insight["insight_type"])
            
            # Verify content is not empty
            self.assertTrue(len(insight["content"]) > 0, "Insight content should not be empty")
            
            # Verify emoji is present
            self.assertTrue(len(insight["emoji"]) > 0, "Insight emoji should not be empty")
        
        # Verify we have the three expected insight types
        expected_types = ["tip", "motivation", "suggestion"]
        for expected_type in expected_types:
            self.assertIn(expected_type, insight_types, f"Missing insight type: {expected_type}")
        
        print(f"✅ AI insights retrieved successfully")
        for i, insight in enumerate(insights):
            print(f"   Insight {i+1}: {insight['insight_type']} - {insight['title']} {insight['emoji']}")

if __name__ == "__main__":
    # Run tests in specific order
    test_suite = unittest.TestSuite()
    test_suite.addTest(GreenStepsAPITest('test_01_signup'))
    test_suite.addTest(GreenStepsAPITest('test_02_login_with_wrong_password'))
    test_suite.addTest(GreenStepsAPITest('test_03_login'))
    test_suite.addTest(GreenStepsAPITest('test_04_get_user_info'))
    test_suite.addTest(GreenStepsAPITest('test_05_get_preset_habits'))
    test_suite.addTest(GreenStepsAPITest('test_06_create_preset_habit'))
    test_suite.addTest(GreenStepsAPITest('test_07_create_custom_habit'))
    test_suite.addTest(GreenStepsAPITest('test_08_get_habits'))
    test_suite.addTest(GreenStepsAPITest('test_09_get_progress'))
    test_suite.addTest(GreenStepsAPITest('test_10_delete_habit'))
    test_suite.addTest(GreenStepsAPITest('test_11_unauthorized_access'))
    test_suite.addTest(GreenStepsAPITest('test_12_ai_insights'))
    
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_runner.run(test_suite)
