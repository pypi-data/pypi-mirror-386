from pathlib import Path
from dekgen.tmpl.generator import GeneratorFiles


class GeneratorBasic(GeneratorFiles):
    TEMPLATE_DIR = Path(__file__).resolve().parent / 'templatefiles'

    def variables_data(self):
        return self.instance


class ProjectGenerator(GeneratorBasic):
    template_name = 'project'
