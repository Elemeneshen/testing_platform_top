import requests
import json

BASE_URL = "http://localhost:8000"

def login_teacher():
    """Log in as teacher and return the session (cookie jar)."""
    session = requests.Session()
    login_url = f"{BASE_URL}/auth/teacher-login"
    # Using form data as per OAuth2PasswordRequestForm
    data = {
        'username': 'teacher@example.com',
        'password': 'password123'
    }
    resp = session.post(login_url, data=data)
    print(f"Teacher login status: {resp.status_code}")
    print(f"Teacher login response: {resp.json()}")
    # The cookie is automatically handled by the session
    return session

def login_student(full_name, access_code):
    """Log in as student and return the session (cookie jar)."""
    session = requests.Session()
    login_url = f"{BASE_URL}/auth/student-login"
    data = {
        'full_name': full_name,
        'access_code': access_code
    }
    resp = session.post(login_url, json=data)
    print(f"Student login status: {resp.status_code}")
    print(f"Student login response: {resp.json()}")
    return session

def create_test(session, title, access_code=None):
    """Create a test via admin endpoint."""
    url = f"{BASE_URL}/admin/tests"
    data = {
        'title': title,
        'access_code': access_code
    }
    # Remove access_code if None to let the server generate one
    if access_code is None:
        data.pop('access_code')
    resp = session.post(url, json=data)
    print(f"Create test status: {resp.status_code}")
    print(f"Create test response: {resp.json()}")
    return resp.json() if resp.status_code == 200 else None

def get_tests(session):
    """Get list of tests for the current teacher."""
    url = f"{BASE_URL}/admin/tests"
    resp = session.get(url)
    print(f"Get tests status: {resp.status_code}")
    print(f"Get tests response: {resp.json()}")
    return resp.json() if resp.status_code == 200 else None

def create_task(session, test_id, task_type, **kwargs):
    """Create a task in a test."""
    url = f"{BASE_URL}/admin/tests/{test_id}/tasks"
    data = {
        'type': task_type,
        'title': kwargs.get('title'),
        'description': kwargs.get('description')
    }
    if task_type == 'auto_check':
        data['checker_type'] = kwargs.get('checker_type')
        data['expected_value'] = kwargs.get('expected_value')
    elif task_type == 'code_review':
        data['source_code'] = kwargs.get('source_code')
        data['language'] = kwargs.get('language')
    resp = session.post(url, json=data)
    print(f"Create task status: {resp.status_code}")
    print(f"Create task response: {resp.json()}")
    return resp.json() if resp.status_code == 200 else None

def update_task(session, task_id, **kwargs):
    """Update a task."""
    url = f"{BASE_URL}/admin/tasks/{task_id}"
    data = {}
    if 'title' in kwargs:
        data['title'] = kwargs['title']
    if 'description' in kwargs:
        data['description'] = kwargs['description']
    if 'checker_type' in kwargs:
        data['checker_type'] = kwargs['checker_type']
    if 'expected_value' in kwargs:
        data['expected_value'] = kwargs['expected_value']
    if 'source_code' in kwargs:
        data['source_code'] = kwargs['source_code']
    if 'language' in kwargs:
        data['language'] = kwargs['language']
    resp = session.patch(url, json=data)
    print(f"Update task status: {resp.status_code}")
    print(f"Update task response: {resp.json()}")
    return resp.json() if resp.status_code == 200 else None

def delete_task(session, task_id):
    """Delete a task."""
    url = f"{BASE_URL}/admin/tasks/{task_id}"
    resp = session.delete(url)
    print(f"Delete task status: {resp.status_code}")
    if resp.status_code == 204:
        print("Delete task response: No Content")
    else:
        print(f"Delete task response: {resp.text}")
    return resp.status_code == 204

def get_test_students(session, test_id):
    """Get students and their progress for a test."""
    url = f"{BASE_URL}/admin/tests/{test_id}/students"
    resp = session.get(url)
    print(f"Get test students status: {resp.status_code}")
    print(f"Get test students response: {resp.json()}")
    return resp.json() if resp.status_code == 200 else None

if __name__ == "__main__":
    # First, log in as teacher
    teacher_session = login_teacher()

    # Create a test
    test = create_test(teacher_session, "Test for Admin API")
    if not test:
        print("Failed to create test")
        exit(1)
    test_id = test['id']
    print(f"Created test with ID: {test_id}")

    # Get tests to verify
    tests = get_tests(teacher_session)
    if tests:
        print(f"Teacher has {len(tests)} tests")

    # Create an auto_check task
    auto_check_task = create_task(
        teacher_session,
        test_id,
        'auto_check',
        title="Auto Check Task",
        description="A simple auto check task",
        checker_type='exact',
        expected_value='42'
    )
    if auto_check_task:
        auto_check_task_id = auto_check_task['id']
        print(f"Created auto_check task with ID: {auto_check_task_id}")

    # Create a code_review task
    code_review_task = create_task(
        teacher_session,
        test_id,
        'code_review',
        title="Code Review Task",
        description="Review this code",
        source_code='print("Hello, World!")',
        language='python'
    )
    if code_review_task:
        code_review_task_id = code_review_task['id']
        print(f"Created code_review task with ID: {code_review_task_id}")

    # Update the auto_check task
    updated_task = update_task(
        teacher_session,
        auto_check_task_id,
        title="Updated Auto Check Task",
        expected_value='100'
    )
    if updated_task:
        print(f"Updated auto_check task: {updated_task}")

    # Get students for the test (we need to have at least one student who has taken the test)
    # Let's create a student and log them in to generate some data
    student_session = login_student("Иван Иванов", test['access_code'])
    # Now the student is associated with the test (via the student-login endpoint)
    # We can also have the student submit something to see progress, but for now, we just check the progress endpoint.

    # Get the progress
    progress = get_test_students(teacher_session, test_id)
    if progress:
        print(f"Progress for test {test_id}:")
        for p in progress:
            print(f"  Student {p['full_name']} (ID {p['student_id']}): {p['submitted_tasks']}/{p['total_tasks']} tasks submitted, {p['pending_code_review']} pending code review")

    # Clean up: delete the tasks we created
    delete_task(teacher_session, auto_check_task_id)
    delete_task(teacher_session, code_review_task_id)

    print("Done.")