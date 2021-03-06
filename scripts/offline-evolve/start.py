import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
tol_path = os.path.abspath(os.path.join(here, '..', '..'))
rv_path = os.path.abspath(os.path.join(tol_path, '..', 'revolve'))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from revolve.util import Supervisor
from offline_evolve import parser


class OfflineEvolutionSupervisor(Supervisor):
    """
    Supervisor class that adds some output filtering for ODE errors
    """

    def __init__(self, *args, **kwargs):
        super(OfflineEvolutionSupervisor, self).__init__(*args, **kwargs)
        self.ode_errors = 0

    def write_stderr(self, data):
        """
        :param data:
        :return:
        """
        if 'ODE Message 3' in data:
            self.ode_errors += 1
        elif data.strip():
            sys.stderr.write(data)

        if self.ode_errors >= 100:
            self.ode_errors = 0
            sys.stderr.write('ODE Message 3 (100)\n')

    def write_stdout(self, data):
        """
        :param data:
        :return:
        """
        # filter out some body analyzer messages
        if 'request' in data:
            pass
        elif 'world now contains' in data:
            pass
        elif 'Robot loaded' in data:
            pass
        elif data.strip():
            sys.stdout.write(data)

args = parser.parse_args()

os.environ['GAZEBO_PLUGIN_PATH'] = os.path.join(tol_path, 'build')
os.environ['GAZEBO_MODEL_PATH'] = os.path.join(tol_path, 'tools', 'models') + \
                                  ':'+os.path.join(rv_path, 'tools', 'models') + \
                                  ':'+os.path.join('models')

supervisor = OfflineEvolutionSupervisor(
    manager_cmd=[sys.executable, "offline_evolve.py"],
    analyzer_cmd=os.path.join(rv_path, 'tools', 'analyzer', 'run-analyzer'),
    gazebo_cmd="gzserver",
    #gazebo_cmd="gazebo", #enable this to visualize the evolution
    #world_file=os.path.join(here, 'offline-evolve.world'),
    world_file=os.path.join(here, args.world_file),
    output_directory=args.output_directory,
    manager_args=sys.argv[1:],
    restore_directory=args.restore_directory
)

print("using world file: %s" % supervisor.world_file)
supervisor.launch()
