from pathlib import Path

import yaml
import pandas as pd
from gpparser.session import ProjectSession


class GazePointProject:

    PRJ_FILE = {
        'coding': 'cp1251',
        'ext': '.prj',
    }

    USER_DIR = 'user'
    SRC_DIR = 'src'
    RESULT_DIR = 'result'
    PRJ_DIRS = [USER_DIR, SRC_DIR, RESULT_DIR]

    def __init__(self, path):
        """
        Creates GazePointProject instance.

        Parameters
        ----------
        path : str or pathlib.Path
            Path to project directory.
        """
        self.path = Path(path)  # root project path
        self.name = None
        self.user_path = None  # path to user dir
        self.src_path = None  # path to src dir
        self.result_path = None  # path to result dir
        self.prj_path = None  # path to .prj file
        self.sessions = []  # placeholder for session objects

        # check project files
        self._read_prj_files()
        self._read_user_data()

    def _read_prj_files(self):
        existing_files = sorted(list(self.path.glob("*")))
        assert existing_files

        for file_path in existing_files:
            file_name = file_path.name

            if file_path.is_dir():
                if file_name in self.PRJ_DIRS:
                    setattr(self, f'{file_name}_path', file_path)

            elif file_path.is_file():
                if file_path.suffix == self.PRJ_FILE['ext']:
                    self.name = file_name
                    self.prj_path = file_path

    def _read_user_data(self):
        with open(self.prj_path, 'rb') as prj_file:
            # fix file string by inserting after every `:` whitespace
            # and remove first 14 characters
            fixed_file_string = prj_file.read()[14:].replace(b':', b': ')

            # decode
            decoded_file_string = fixed_file_string.decode(
                    self.PRJ_FILE['coding']
                    )

            # load with yaml
            prj_data = yaml.load(decoded_file_string)['UserData']

            # iterate on every yaml entry creating session
            self.sessions = [ProjectSession.from_prj_entry(entry, self.path)
                             for entry in prj_data]

    def get_sessions_info(self):
        """
        Return pandas.DataFrame with information
        about available sessions.

        Return
        ------
            sessions_dataframe : pd.DataFrame
        """
        df = pd.DataFrame(
                [sess.get_session_info() for sess in self.sessions]
                ).set_index('index')
        return df

    def export_sessions(self, session_indices=None, **kwargs):
        """
        Export data to `result` dir for specified sessions in project.
        Results will be saved in (project_directory)/result/.

        Parameters
        ----------
        session_indices : list[int]
            Specifies which sessions need to be rendered.
            If `None` render all.
        kwargs : dict
            Will be passed to export_session method.
            screen : bool
                render video
            gaze : bool
                export all gaze
            fixation : bool
                export fixation data
            last_fixation_count : int
                how many fixations to render on each frame.
        """
        sessions = iter(self) if session_indices is None \
            else self[session_indices]

        for session in sessions:
            session.export(**kwargs)

    def split_sessions(self, session_indices=None, **kwargs):
        sessions = iter(self) if session_indices is None \
                              else self[session_indices]

        for session in sessions:
            session.split()

    def annotate_sessions(self, session_indices=None, **kwargs):
        sessions = iter(self) if session_indices is None \
            else self[session_indices]

        for sess in sessions:
            sess.annotate()

    def __iter__(self):
        return iter(self.sessions)

    def __len__(self):
        return len(self.sessions)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.sessions[key]
        elif isinstance(key, list):
            return [self.sessions[i] for i in key]
        else:
            raise IndexError(f'Wrong type of {key}: {type(key)}.')

    def __setitem__(self, key, value):
        assert isinstance(value, ProjectSession), type(value)
        self.sessions[key] = value


def test():
    import sys

    # define test paths with GP Analysis data
    test_prj_path = Path(sys.argv[1])

    gp_prj = GazePointProject(test_prj_path)
    gp_prj.export_sessions()


if __name__ == '__main__':
    test()
