"""
MatsushibaDB Python - Test Runner
Runs all test suites in sequence
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the package to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestRunner:
    """Test runner for all MatsushibaDB Python test suites"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = None
        
    async def run_all_tests(self):
        """Run all test suites"""
        print("=" * 80)
        print("MatsushibaDB Python - Complete Test Suite Runner")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.start_time = datetime.now()
        
        # Import and run test suites
        test_suites = [
            ('Simple Test', 'simple_test'),
            ('Comprehensive Test', 'comprehensive_test_suite'),
            ('Stress Test', 'stress_test_suite'),
            ('Lightning Demo', 'lightning_demo')
        ]
        
        for suite_name, module_name in test_suites:
            try:
                print(f"\n{'='*20} Running {suite_name} {'='*20}")
                
                if module_name == 'simple_test':
                    from simple_test import main as simple_main
                    simple_main()
                    self.test_results.append({'suite': suite_name, 'status': 'PASS', 'error': None})
                    
                elif module_name == 'comprehensive_test_suite':
                    from comprehensive_test_suite import ComprehensiveTestSuite
                    suite = ComprehensiveTestSuite()
                    await suite.run_all_tests()
                    self.test_results.append({'suite': suite_name, 'status': 'PASS', 'error': None})
                    
                elif module_name == 'stress_test_suite':
                    from stress_test_suite import StressTestSuite
                    suite = StressTestSuite()
                    await suite.run_all_tests()
                    self.test_results.append({'suite': suite_name, 'status': 'PASS', 'error': None})
                    
                elif module_name == 'lightning_demo':
                    from lightning_demo import LightningDemo
                    demo = LightningDemo()
                    await demo.run_demo()
                    self.test_results.append({'suite': suite_name, 'status': 'PASS', 'error': None})
                
                print(f"+ {suite_name} completed successfully")
                
            except Exception as e:
                print(f"- {suite_name} failed: {e}")
                self.test_results.append({'suite': suite_name, 'status': 'FAIL', 'error': str(e)})
        
        # Print final results
        await self.print_final_results()
    
    async def print_final_results(self):
        """Print final test results"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print("\n" + "=" * 80)
        print("FINAL TEST RESULTS")
        print("=" * 80)
        
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        total = len(self.test_results)
        
        print(f"Total Test Suites: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print(f"Total Duration: {duration.total_seconds():.2f} seconds")
        
        print("\nTest Suite Results:")
        for result in self.test_results:
            status_symbol = "+" if result['status'] == 'PASS' else "-"
            print(f"  {status_symbol} {result['suite']}: {result['status']}")
            if result['error']:
                print(f"    Error: {result['error']}")
        
        if failed == 0:
            print("\n+ All test suites passed! MatsushibaDB Python package is ready for production.")
        else:
            print(f"\n- {failed} test suite(s) failed. Please review errors above.")
        
        print("=" * 80)


async def main():
    """Main test runner"""
    runner = TestRunner()
    await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
