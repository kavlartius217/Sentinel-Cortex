class Reasoning_tester(Flow[State]):
    model = 'gpt-4o-mini'
    g1 = Generator()
    "This an AI FeedBack Loop Tester"
    
    @start()
    def code_gen(self):
        response = self.g1.crew().kickoff({"feedback": ""})
        print(response.raw)
        self.state.code = response.raw
    
    @listen(or_(code_gen, "review_again"))
    def code_review(self):
        response = completion(
            model=self.model,
            messages=[{
                "role": "system",
                "content": f"""You are an expert Jest Test Code Reviewer specialized in providing specific, actionable feedback for improving test quality. Your role is to carefully analyze generated Jest test files and provide detailed feedback on what corrections should be made Review this code {self.state.code}.  Your feedback should be precise, structured, and implementation-ready, focusing on:  1. CORRECTNESS ISSUES:    - Syntax errors or Jest-specific implementation mistakes    - Improper use of Jest API (describe, it, expect, beforeEach, etc.)    - Incorrect mocking techniques or mock implementations    - Test assertions that don't properly validate the expected behavior    - Async/await usage problems in test cases  2. QUALITY IMPROVEMENTS:    - Test coverage gaps for important code paths    - Missing edge case or error handling tests    - Insufficient validation of outputs or side effects    - Opportunities for more robust assertions    - Better test isolation and reduced test interdependence  3. BEST PRACTICES:    - Consistent naming conventions for test suites and cases    - Proper setup and teardown procedures    - Appropriate use of Jest matchers (toBe vs toEqual vs toStrictEqual)    - Mock cleanup and reset practices    - Test readability and maintainability issues  4. IF THE CODE IS CORRECT:    - Return a single string VALID  For each issue identified, provide: - The exact location in the code (line number or code snippet) - What is problematic or could be improved - The recommended correction with sample code when applicable - A brief explanation of why this change improves the test  Structure your feedback as a JSON object with the following format: ```json {{   "feedbackItems": [     {{       "type": "CORRECTNESS|QUALITY|BEST_PRACTICE",       "location": "Describe where in the code (test suite, test case, line)",       "issue": "Concise description of the problem",       "recommendation": "Specific code change or addition needed",       "explanation": "Why this change matters for test quality"     }}   ] }}"""
            }]
        )
        print(response.choices[0].message.content)
        self.state.feedback = response.choices[0].message.content
    
    @router(code_review)
    def router_1(self):
        if self.state.feedback == 'VALID':
            return 'proceed'
        else:
            return 'make_changes'
    
    @listen('make_changes')
    def task_id(self):
        import subprocess
        # Run command and capture output
        try:
            x = subprocess.run(['crewai', 'log-tasks-outputs'], 
                              capture_output=True, text=True, check=True).stdout.splitlines()
            
            for i in x:
                if 'Task 4:' in i:
                    # Extract just the UUID part after "Task 4:"
                    parts = i.split('Task 4:')
                    if len(parts) > 1:
                        self.state.task_id = parts[1].strip()
                        print(f"Found task ID: {self.state.task_id}")
                        break
            
            return "found_task_id"
        except Exception as e:
            print(f"Error getting task ID: {e}")
            return "task_id_error"
    
    @listen(task_id)
    def replay(self):
        task_id = self.state.task_id
        feedback = {"feedback": self.state.feedback}
        response = self.g1.crew().replay(task_id=task_id, inputs=feedback)
        self.state.code = response
        print(response)
    
    @router(replay)
    def router_2(self):
      self.state.max_retry+=1
      if self.state.max_retry<3:
        return 'review_again'
      else:
        return 'Done'
    
    @listen(or_('proceed','Done'))
    def show_code(self):
        print(self.state.code)
