'''
Created on May 23, 2012

@author: Fabio Zadrozny
'''
import unittest
import os.path
from mu_repo.config import Config
from mu_repo import action_diff, Params
import subprocess
import sys
import time
from mu_repo.rmtree import RmTree
from mu_repo.action_diff import NotifyErrorListeners


#===================================================================================================
# Test
#===================================================================================================
class Test(unittest.TestCase):


    def setUp(self):
        unittest.TestCase.setUp(self)
        self.clear()


    def tearDown(self):
        unittest.TestCase.tearDown(self)
        self.clear()


    def clear(self):
        if os.path.exists('test_diff_command_git_repo_dir'):
            try:
                RmTree('test_diff_command_git_repo_dir')
            except:
                time.sleep(1)
                RmTree('test_diff_command_git_repo_dir')


    def CallDiff(self, branch=None, check_structure=None):
        config = Config(repos=['test_diff_command_git_repo_dir'], git=self.git)
        params = Params(config, ['dd'] + [branch] if branch else [], config_file=None, stream=sys.stdout)

        called = []
        def Call(cmd, *args, **kwargs):
            try:
                if check_structure:
                    check_structure()
            except:
                NotifyErrorListeners()
            called.append(cmd[0].lower())

        errors = []
        def OnError(error):
            errors.append(error)

        #Mock things
        original_call = subprocess.call
        subprocess.call = Call
        action_diff.on_errors_listeners.add(OnError)
        try:
            action_diff.Run(params)
        finally:
            action_diff.on_errors_listeners.remove(OnError)
            subprocess.call = original_call
        if errors:
            self.fail('\n\n'.join(errors))
        return called



    def testActionDiff(self):
        temp_dir = 'test_diff_command_git_repo_dir'
        git = r'C:\D\bin\git\bin\git.exe'
        if not os.path.exists(git):
            git = 'git'
        self.git = git

        # Test diffing with new folder structure
        subprocess.call([git] + 'init test_diff_command_git_repo_dir'.split(), cwd='.')
        os.mkdir(os.path.join(temp_dir, 'folder1'))
        with open(os.path.join(temp_dir, 'folder1', 'out.txt'), 'w') as f:
            f.write('out')
        called = self.CallDiff()

        self.assertEqual(['winmergeu.exe'], called)


        # Test diffing with previous version of HEAD without changes        
        subprocess.call([git] + 'add -A'.split(), cwd=temp_dir)
        subprocess.call([git] + 'commit -m "Second'.split(), cwd=temp_dir)
        called = self.CallDiff()
        self.assertEqual([], called) #Not called as we don't have any changes.


        # Test diffing with previous version of HEAD^
        def CheckStructure():
            prev = os.path.join('.mu.diff.git.tmp', 'REPO', 'test_diff_command_git_repo_dir', 'folder1', 'out.txt')
            curr = os.path.join('.mu.diff.git.tmp', 'WORKING', 'test_diff_command_git_repo_dir', 'folder1', 'out.txt')
            self.assert_(os.path.exists(prev))
            self.assert_(os.path.exists(curr))
            print 'prev', open(prev, 'r').read()
            print 'curr', open(curr, 'r').read()

        with open(os.path.join(temp_dir, 'folder1', 'out.txt'), 'w') as f:
            f.write('new out')
        subprocess.call([git] + 'add -A'.split(), cwd=temp_dir)
        subprocess.call([git] + 'commit -m "Second'.split(), cwd=temp_dir)
        called = self.CallDiff('HEAD^', check_structure=CheckStructure)
        self.assertEqual(['winmergeu.exe'], called)



        # Test diffing dir structure in git changed for file in working dir
        subprocess.call([git] + 'add -A'.split(), cwd=temp_dir)
        subprocess.call([git] + 'commit -m "Third'.split(), cwd=temp_dir)
        RmTree(os.path.join(temp_dir, 'folder1'))
        with open(os.path.join(temp_dir, 'folder1'), 'w') as f:
            f.write('folder1 is now file.')

        called = self.CallDiff()
        self.assertEqual(['winmergeu.exe'], called)

#===================================================================================================
# main
#===================================================================================================
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testMuRepo']
    unittest.main()