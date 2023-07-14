import unittest

from observer_toolkit import get_action, Step, StepPlan


class StepPlanTestCase(unittest.TestCase):

    def test_step(self):
        step_1 = Step(action='step_1')

        step_2 = Step('step_2')

        step_3 = Step('step_3', dependency_actions=['step_1'])

        with self.subTest('property action'):
            self.assertIs(step_1.action, get_action('step_1'))
            self.assertIs(step_2.action, get_action('step_2'))
            self.assertIs(step_3.action, get_action('step_3'))

        with self.subTest('property dependency_actions'):
            self.assertEqual(step_3.dependency_actions, {get_action('step_1')})

    def test_step_plan(self):
        step_1 = Step('step_1')
        step_1_1 = Step('step_1_1', dependency_actions=['step_1'])

        plan = StepPlan()
        plan.append(step_1)
        plan.append(step_1_1)

        plan.append(Step('step_0'))
        plan.append(Step('step_isolated', dependency_actions=['step_isolated_dependency']))
        plan.append(Step('step_2', dependency_actions=['step_1']))
        plan.append(Step('step_2_1', dependency_actions=['step_1', 'step_2']))

        for step_level in plan.walk():
            print(step_level)

        # id
        self.assertEqual(list(plan.walk()), list(plan.walk()))

if __name__ == '__main__':
    unittest.main()
