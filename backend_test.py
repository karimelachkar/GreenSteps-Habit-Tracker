import requests
import unittest
import uuid
import time
from datetime import datetime

# Backend API URL
API_URL = "https://78299146-1fae-4c60-b8b7-8455ec49569c.preview.emergentagent.com"

class GreenStepsAPITest(unittest.TestCase):
    def setUp(self):
        self.api_url = API_URL
        self.test_user = {
            "name": f"Test User {uuid.uuid4()}",
            "email": f"test_{uuid.uuid4()}@example.com",
            "password": "TestPassword123!"
        }
        self.token = None
        self.habit_id = None

    def test_01_signup(self):
        """Test user signup"""
        print(f"\n🔍 Testing signup with {self.test_user['email']}...")
        
        response = requests.post(
            f"{self.api_url}/api/auth/signup",
            json=self.test_user
        )
        
        self.assertEqual(response.status_code, 200, f"Signup failed: {response.text}")
        self.assertIn("access_token", response.json(), "Token not found in response")
        
        # Save token for subsequent tests
        self.token = response.json()["access_token"]
        print(f"✅ Signup successful, token received")
        
        # Save token to class for other test methods
        GreenStepsAPITest.token = self.token

    def test_02_login_with_wrong_password(self):
        """Test login with incorrect credentials"""
        print(f"\n🔍 Testing login with incorrect password...")
        
        response = requests.post(
            f"{self.api_url}/api/auth/login",
            json={
                "email": self.test_user["email"],
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
                "email": self.test_user["email"],
                "password": self.test_user["password"]
            }
        )
        
        self.assertEqual(response.status_code, 200, f"Login failed: {response.text}")
        self.assertIn("access_token", response.json(), "Token not found in response")
        
        # Update token
        self.token = response.json()["access_token"]
        GreenStepsAPITest.token = self.token
        print(f"✅ Login successful, token received")

    def test_04_get_user_info(self):
        """Test getting current user info"""
        print(f"\n🔍 Testing get user info...")
        
        response = requests.get(
            f"{self.api_url}/api/auth/me",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        self.assertEqual(response.status_code, 200, f"Get user info failed: {response.text}")
        user_data = response.json()
        self.assertEqual(user_data["name"], self.test_user["name"], "User name doesn't match")
        self.assertEqual(user_data["email"], self.test_user["email"], "User email doesn't match")
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
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        self.assertEqual(response.status_code, 200, f"Create habit failed: {response.text}")
        habit = response.json()
        self.assertEqual(habit["habit_name"], habit_data["habit_name"], "Habit name doesn't match")
        self.assertEqual(habit["description"], habit_data["description"], "Habit description doesn't match")
        
        # Save habit ID for later tests
        self.habit_id = habit["id"]
        GreenStepsAPITest.habit_id = self.habit_id
        print(f"✅ Preset habit created successfully with ID: {self.habit_id}")

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
            headers={"Authorization": f"Bearer {self.token}"}
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
            headers={"Authorization": f"Bearer {self.token}"}
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
            headers={"Authorization": f"Bearer {self.token}"}
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
        
        if not self.habit_id:
            self.skipTest("No habit ID available to delete")
        
        response = requests.delete(
            f"{self.api_url}/api/habits/{self.habit_id}",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        self.assertEqual(response.status_code, 200, f"Delete habit failed: {response.text}")
        print(f"✅ Habit deleted successfully")
        
        # Verify habit is deleted
        response = requests.get(
            f"{self.api_url}/api/habits",
            headers={"Authorization": f"Bearer {self.token}"}
        )
        
        habits = response.json()
        habit_ids = [habit["id"] for habit in habits]
        self.assertNotIn(self.habit_id, habit_ids, "Habit still exists after deletion")

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

if __name__ == "__main__":
    # Run tests in order
    test_loader = unittest.TestLoader()
    test_loader.sortTestMethodsUsing = lambda x, y: 1 if x < y else -1 if x > y else 0
    
    test_suite = test_loader.loadTestsFromTestCase(GreenStepsAPITest)
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_runner.run(test_suite)
